#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="/opt/agr/aurora_server/data"
mkdir -p "$OUT_DIR"
TS="$(date -u +%Y%m%d-%H%M%SZ)"
REPORT_MD="$OUT_DIR/release_readiness_${TS}.md"
REPORT_JSON="$OUT_DIR/release_readiness_${TS}.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/fleet-key.sh"

NODES=("chimaera:5.78.184.2" "yggdrasil:128.140.45.22" "enterprise:91.99.224.166" "prometheus:46.62.202.166" "galactica:178.104.31.46")
CANONICAL_PUBLIC_DOMAIN="https://auroragalaxyrepublic.com/"
REDIRECT_DOMAINS=(
  "https://aurora-galaxy-republic.com/"
  "https://aurora-galaxy-republic.org/"
  "https://auroragalaxy.org/"
  "https://auroragalaxy.net/"
  "https://auroragalaxy.io/"
  "https://auroragalaxy.pw/"
  "https://auroragalaxy.us/"
  "https://auroragalaxy.uk/"
)

SSH_KEY="$(resolve_fleet_ssh_key "${SSH_KEY_PATH:-}")" || SSH_KEY=""

PASS=1

echo "# Release Readiness Report" > "$REPORT_MD"
echo "Generated: $(date -u +%FT%TZ)" >> "$REPORT_MD"
echo >> "$REPORT_MD"

echo "## Hetzner Node Service Checks (all 5 required)" >> "$REPORT_MD"
NODE_JSON='[]'
for entry in "${NODES[@]}"; do
  NAME="${entry%%:*}"; IP="${entry##*:}"
  if [[ "$NAME" == "chimaera" ]]; then
    HOSTNAME="$(hostname)"
    HUB="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/consciousness/hub || echo 000)"
    STRIPE="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/stripe/status || echo 000)"
    OSR="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/os || echo 000)"
  else
    if [[ -n "$SSH_KEY" ]]; then
      OUT="$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@"$IP" 'h=$(hostname); hub=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/consciousness/hub || echo 000); stripe=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/stripe/status || echo 000); osr=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/os || echo 000); echo "$h $hub $stripe $osr"' 2>/dev/null || echo "UNREACH 000 000 000")"
    else
      OUT="UNREACH 000 000 000"
    fi
    HOSTNAME="$(awk '{print $1}' <<< "$OUT")"
    HUB="$(awk '{print $2}' <<< "$OUT")"
    STRIPE="$(awk '{print $3}' <<< "$OUT")"
    OSR="$(awk '{print $4}' <<< "$OUT")"
  fi

  STATUS="ok"
  if [[ "$HUB" != "200" || "$STRIPE" != "200" || "$OSR" != "200" ]]; then
    STATUS="fail"
    PASS=0
  fi

  echo "- $NAME: host=$HOSTNAME hub=$HUB stripe=$STRIPE os=$OSR status=$STATUS" >> "$REPORT_MD"
  NODE_JSON="$(python3 - <<'PY2' "$NODE_JSON" "$NAME" "$HOSTNAME" "$HUB" "$STRIPE" "$OSR" "$STATUS"
import json,sys
arr=json.loads(sys.argv[1])
arr.append({"name":sys.argv[2],"host":sys.argv[3],"hub":sys.argv[4],"stripe":sys.argv[5],"os":sys.argv[6],"status":sys.argv[7]})
print(json.dumps(arr))
PY2
)"
done

echo >> "$REPORT_MD"
echo "## S25 CEO Node Gate" >> "$REPORT_MD"
S25_FILE="/opt/agr/state/s25_heartbeat.last"
S25_STATUS="fail"
S25_AGE="unknown"
if [[ -s "$S25_FILE" ]]; then
  NOW=$(date +%s)
  LAST=$(cat "$S25_FILE" 2>/dev/null || echo 0)
  if [[ "$LAST" =~ ^[0-9]+$ ]]; then
    S25_AGE=$((NOW-LAST))
    if [[ "$S25_AGE" -le 3600 ]]; then
      S25_STATUS="ok"
    fi
  fi
fi
if [[ "$S25_STATUS" != "ok" ]]; then PASS=0; fi
echo "- s25_heartbeat_file=$S25_FILE age_seconds=$S25_AGE status=$S25_STATUS" >> "$REPORT_MD"

echo >> "$REPORT_MD"
echo "## Public Domain Canonicalization Checks" >> "$REPORT_MD"
DOMAIN_JSON='[]'
CANONICAL_CODE="$(curl -s -L -o /dev/null -w '%{http_code}' "$CANONICAL_PUBLIC_DOMAIN" || echo 000)"
CANONICAL_STATUS="ok"
if [[ ! "$CANONICAL_CODE" =~ ^2 ]]; then
  CANONICAL_STATUS="fail"
  PASS=0
fi
echo "- canonical=$CANONICAL_PUBLIC_DOMAIN code=$CANONICAL_CODE status=$CANONICAL_STATUS" >> "$REPORT_MD"
DOMAIN_JSON="$(python3 - <<'PY3' "$DOMAIN_JSON" "$CANONICAL_PUBLIC_DOMAIN" "$CANONICAL_CODE" "canonical" "$CANONICAL_STATUS"
import json,sys
arr=json.loads(sys.argv[1])
arr.append({"url":sys.argv[2],"code":sys.argv[3],"tag":sys.argv[4],"status":sys.argv[5]})
print(json.dumps(arr))
PY3
)"

for U in "${REDIRECT_DOMAINS[@]}"; do
  REDIRECT_CODE="$(curl -s -o /dev/null -w '%{http_code}' "$U" || echo 000)"
  EFFECTIVE_URL="$(curl -s -L -o /dev/null -w '%{url_effective}' "$U" || echo "")"
  TAG="redirect"
  DST="ok"
  case "$REDIRECT_CODE" in
    301|302|307|308) ;;
    *) DST="fail" ;;
  esac
  if [[ "$EFFECTIVE_URL" != https://auroragalaxyrepublic.com/* ]]; then
    DST="fail"
  fi
  if [[ "$DST" != "ok" ]]; then
    PASS=0
  fi
  echo "- $U => code=$REDIRECT_CODE effective=$EFFECTIVE_URL tag=$TAG status=$DST" >> "$REPORT_MD"
  DOMAIN_JSON="$(python3 - <<'PY4' "$DOMAIN_JSON" "$U" "$REDIRECT_CODE" "$TAG" "$DST"
import json,sys
arr=json.loads(sys.argv[1])
arr.append({"url":sys.argv[2],"code":sys.argv[3],"tag":sys.argv[4],"status":sys.argv[5]})
print(json.dumps(arr))
PY4
)"
done

RESULT="PASS"
if [[ "$PASS" -ne 1 ]]; then RESULT="FAIL"; fi

echo >> "$REPORT_MD"
echo "## Gate Result" >> "$REPORT_MD"
echo "- Release readiness: $RESULT" >> "$REPORT_MD"

python3 - <<'PY5' "$REPORT_JSON" "$TS" "$RESULT" "$NODE_JSON" "$DOMAIN_JSON" "$S25_STATUS" "$S25_AGE"
import json,sys
obj={
  "timestamp":sys.argv[2],
  "result":sys.argv[3],
  "nodes":json.loads(sys.argv[4]),
  "domains":json.loads(sys.argv[5]),
  "s25":{"status":sys.argv[6],"age_seconds":sys.argv[7]}
}
with open(sys.argv[1],'w') as f:
  json.dump(obj,f,indent=2)
PY4

sha256sum "$REPORT_MD" "$REPORT_JSON"
echo "$RESULT"
