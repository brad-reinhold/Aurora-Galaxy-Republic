#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-/opt/agr/aurora_server/data}"
mkdir -p "$OUT_DIR"
TS="$(date -u +%Y%m%d-%H%M%SZ)"
REPORT_MD="${OUT_DIR}/release_totality_${TS}.md"
REPORT_JSON="${OUT_DIR}/release_totality_${TS}.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/fleet-key.sh"

NODES=(
  "chimaera:5.78.184.2"
  "yggdrasil:128.140.45.22"
  "enterprise:91.99.224.166"
  "prometheus:46.62.202.166"
  "galactica:178.104.31.46"
)

ENDPOINTS=(
  "/health"
  "/api/sovereign/constitution/status"
  "/api/sovereign/constitution/verify:POST"
  "/api/sovereign/memory/status"
  "/api/sovereign/memory/ingest:POST"
  "/api/sovereign/finance/status"
  "/api/sovereign/legal/status"
  "/api/sovereign/email/probes"
  "/api/sovereign/rnd/agenda"
  "/api/sovereign/simulations"
  "/api/sovereign/visual/baseline/status"
  "/api/sovereign/continuity/status"
  "/api/sovereign/s25/embodiment/status"
  "/api/sovereign/ops/e2e"
)

SSH_KEY="${SSH_KEY:-}"
if ! SSH_KEY="$(resolve_fleet_ssh_key "${SSH_KEY}")"; then
  echo "No SSH key found for release totality gate" >&2
  exit 1
fi

PASS=1
NODE_ROWS='[]'

echo "# Release Totality Gate" > "$REPORT_MD"
echo "Generated: $(date -u +%FT%TZ)" >> "$REPORT_MD"
echo >> "$REPORT_MD"
echo "## Sovereign endpoint matrix" >> "$REPORT_MD"

for entry in "${NODES[@]}"; do
  NAME="${entry%%:*}"
  IP="${entry##*:}"

CHECK_SCRIPT='
set +e
for ep in '"$(printf "%q " "${ENDPOINTS[@]}")"'; do
  if [[ "$ep" == *":POST" ]]; then
    base="${ep%:POST}"
    final=000
    for i in 1 2 3; do
      code=$(curl -s --max-time 20 -X POST -H "Content-Type: application/json" -d "{}" -o /tmp/gate_out -w "%{http_code}" "http://localhost:5000${base}")
      final="$code"
      [[ "$code" == "200" ]] && break
      sleep 2
    done
    echo "${base} ${final}"
  else
    final=000
    for i in 1 2 3; do
      code=$(curl -s --max-time 20 -o /tmp/gate_out -w "%{http_code}" "http://localhost:5000${ep}")
      final="$code"
      [[ "$code" == "200" ]] && break
      sleep 2
    done
    echo "${ep} ${final}"
  fi
done
'

  if [[ "$NAME" == "chimaera" ]]; then
    OUT="$(bash -lc "$CHECK_SCRIPT")"
  else
    OUT="$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@"$IP" "$CHECK_SCRIPT" 2>/dev/null || true)"
  fi

  NODE_OK="ok"
  echo "- ${NAME}:" >> "$REPORT_MD"
  while read -r line; do
    [[ -z "${line}" ]] && continue
    EP="$(awk '{print $1}' <<< "$line")"
    CODE="$(awk '{print $2}' <<< "$line")"
    if [[ "$CODE" != "200" ]]; then
      NODE_OK="fail"
      PASS=0
    fi
    echo "  - ${EP} => ${CODE}" >> "$REPORT_MD"
  done <<< "$OUT"
  echo "  - node_status=${NODE_OK}" >> "$REPORT_MD"

  NODE_ROWS="$(python3 - <<'PY' "$NODE_ROWS" "$NAME" "$OUT" "$NODE_OK"
import json,sys
arr=json.loads(sys.argv[1])
raw=sys.argv[3].splitlines()
eps=[]
for line in raw:
  parts=line.split()
  if len(parts)>=2:
    eps.append({"endpoint":parts[0],"code":parts[1]})
arr.append({"node":sys.argv[2],"status":sys.argv[4],"checks":eps})
print(json.dumps(arr))
PY
)"
done

echo >> "$REPORT_MD"
echo "## S25 transport closure check" >> "$REPORT_MD"
TRANSPORT_RESULT="missing"
if [[ -x /opt/agr/sovereign/s25-transport-closure-check.sh ]]; then
  set +e
  TRANSPORT_OUT="$(/opt/agr/sovereign/s25-transport-closure-check.sh 2>&1)"
  TRANSPORT_RC=$?
  set -e
  if [[ "$TRANSPORT_RC" -eq 0 ]]; then
    TRANSPORT_RESULT="$(tail -n 1 <<< "$TRANSPORT_OUT")"
  else
    TRANSPORT_RESULT="FAIL"
    PASS=0
  fi
  echo '```' >> "$REPORT_MD"
  echo "$TRANSPORT_OUT" >> "$REPORT_MD"
  echo '```' >> "$REPORT_MD"
else
  TRANSPORT_RESULT="script_missing"
  PASS=0
  echo "- /opt/agr/sovereign/s25-transport-closure-check.sh missing" >> "$REPORT_MD"
fi

RESULT="PASS"
if [[ "$PASS" -ne 1 ]]; then
  RESULT="FAIL"
fi
echo >> "$REPORT_MD"
echo "## Gate Result" >> "$REPORT_MD"
echo "- totality_release_readiness=${RESULT}" >> "$REPORT_MD"

python3 - <<'PY' "$REPORT_JSON" "$TS" "$RESULT" "$NODE_ROWS" "$TRANSPORT_RESULT"
import json,sys
payload={
  "timestamp":sys.argv[2],
  "result":sys.argv[3],
  "nodes":json.loads(sys.argv[4]),
  "s25_transport_result":sys.argv[5],
}
with open(sys.argv[1],"w") as f:
  json.dump(payload,f,indent=2)
PY

sha256sum "$REPORT_MD" "$REPORT_JSON"
echo "$RESULT"
