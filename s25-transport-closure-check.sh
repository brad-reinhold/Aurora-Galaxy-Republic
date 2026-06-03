#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-key.sh"

OUT_DIR="${OUT_DIR:-/opt/agr/aurora_server/data}"
mkdir -p "$OUT_DIR"
TS="$(date -u +%Y%m%d-%H%M%SZ)"
REPORT_MD="$OUT_DIR/s25_transport_closure_${TS}.md"
REPORT_JSON="$OUT_DIR/s25_transport_closure_${TS}.json"

NODES=(
  "chimaera:5.78.184.2"
  "yggdrasil:128.140.45.22"
  "enterprise:91.99.224.166"
  "prometheus:46.62.202.166"
  "galactica:178.104.31.46"
)

S25_WG_IP="${S25_WG_IP:-10.10.0.10}"
S25_HEARTBEAT_FILE="${S25_HEARTBEAT_FILE:-/opt/agr/state/s25_heartbeat.last}"

SSH_KEY=""
if ! SSH_KEY="$(resolve_fleet_ssh_key "${SSH_KEY_PATH:-}")"; then
  echo "No SSH key found for fleet checks" >&2
  echo "Set AGR_FLEET_KEY (or SSH_KEY_PATH) to rotated key path." >&2
  exit 1
fi

PASS=1
ROWS='[]'

cat > "$REPORT_MD" <<EOF
# S25 Transport Closure Report
Generated: $(date -u +%FT%TZ)
S25 target: ${S25_WG_IP}

## Per-node checks
EOF

for entry in "${NODES[@]}"; do
  NAME="${entry%%:*}"
  IP="${entry##*:}"

  if [[ "$NAME" == "chimaera" ]]; then
    OUT="$(
      set +e
      h="$(hostname)"
      ping_code="fail"
      peer_code="fail"
      if ping -c 1 -W 2 "${S25_WG_IP}" >/dev/null 2>&1; then ping_code="ok"; fi
      if wg show all dump 2>/dev/null | awk -v ip="${S25_WG_IP}" 'index($0, ip){found=1} END{exit(found?0:1)}'; then peer_code="ok"; fi
      printf "%s %s %s\n" "$h" "$ping_code" "$peer_code"
    )"
  else
    OUT="$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@"$IP" '
      set +e
      h="$(hostname)"
      ping_code="fail"
      peer_code="fail"
      if ping -c 1 -W 2 '"${S25_WG_IP}"' >/dev/null 2>&1; then ping_code="ok"; fi
      if wg show all dump 2>/dev/null | awk -v ip="'"${S25_WG_IP}"'" '"'"'index($0, ip){found=1} END{exit(found?0:1)}'"'"'; then peer_code="ok"; fi
      printf "%s %s %s\n" "$h" "$ping_code" "$peer_code"
    ' 2>/dev/null || echo "UNREACH fail fail")"
  fi

  HOST="$(awk '{print $1}' <<< "$OUT")"
  PING_OK="$(awk '{print $2}' <<< "$OUT")"
  PEER_OK="$(awk '{print $3}' <<< "$OUT")"

  STATUS="ok"
  if [[ "$PING_OK" != "ok" || "$PEER_OK" != "ok" ]]; then
    STATUS="degraded"
    PASS=0
  fi

  echo "- ${NAME}: host=${HOST} ping_s25=${PING_OK} wg_peer_for_s25=${PEER_OK} status=${STATUS}" >> "$REPORT_MD"

  ROWS="$(python3 - <<'PY' "$ROWS" "$NAME" "$HOST" "$PING_OK" "$PEER_OK" "$STATUS"
import json,sys
arr=json.loads(sys.argv[1])
arr.append({
  "node":sys.argv[2],
  "host":sys.argv[3],
  "ping_s25":sys.argv[4],
  "wg_peer_for_s25":sys.argv[5],
  "status":sys.argv[6],
})
print(json.dumps(arr))
PY
)"
done

echo >> "$REPORT_MD"
echo "## S25 heartbeat gate" >> "$REPORT_MD"
HB_STATUS="missing"
HB_AGE="unknown"
if [[ -s "$S25_HEARTBEAT_FILE" ]]; then
  NOW="$(date +%s)"
  LAST="$(cat "$S25_HEARTBEAT_FILE" 2>/dev/null || echo 0)"
  if [[ "$LAST" =~ ^[0-9]+$ ]]; then
    HB_AGE="$((NOW-LAST))"
    if [[ "$HB_AGE" -le 3600 ]]; then
      HB_STATUS="ok"
    else
      HB_STATUS="stale"
      PASS=0
    fi
  fi
else
  PASS=0
fi
echo "- file=${S25_HEARTBEAT_FILE} age_seconds=${HB_AGE} status=${HB_STATUS}" >> "$REPORT_MD"

RESULT="PASS"
if [[ "$PASS" -ne 1 ]]; then
  RESULT="FAIL"
fi

echo >> "$REPORT_MD"
echo "## Result" >> "$REPORT_MD"
echo "- transport_closure=${RESULT}" >> "$REPORT_MD"

python3 - <<'PY' "$REPORT_JSON" "$TS" "$RESULT" "$ROWS" "$HB_STATUS" "$HB_AGE"
import json,sys
payload={
  "timestamp":sys.argv[2],
  "result":sys.argv[3],
  "nodes":json.loads(sys.argv[4]),
  "heartbeat":{"status":sys.argv[5], "age_seconds":sys.argv[6]},
}
with open(sys.argv[1],"w") as f:
  json.dump(payload,f,indent=2)
PY

sha256sum "$REPORT_MD" "$REPORT_JSON"
echo "$RESULT"
