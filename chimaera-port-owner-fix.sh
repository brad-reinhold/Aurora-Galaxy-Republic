#!/usr/bin/env bash
set -euo pipefail

# Chimaera runtime parity fix:
# Ensure the Republic Python runtime is the only owner of port 5000.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-key.sh"
KEY_PATH="$(resolve_fleet_ssh_key "${KEY_PATH:-}")" || {
  echo "No SSH key found for chimaera port owner fix" >&2
  exit 1
}
HOST="${HOST:-5.78.184.2}"

SSH_OPTS=(
  -i "$KEY_PATH"
  -o StrictHostKeyChecking=no
)

echo "[fix] applying chimaera port-ownership hardening on ${HOST}"

ssh "${SSH_OPTS[@]}" "root@${HOST}" '
set -euo pipefail

systemctl stop agr-api.service 2>/dev/null || true
systemctl disable agr-api.service 2>/dev/null || true
systemctl mask agr-api.service 2>/dev/null || true
systemctl reset-failed agr-api.service 2>/dev/null || true

for pid in $(ps -eo pid,cmd | awk "/node .*\\/opt\\/agr-api\\/dist\\/index\\.mjs/{print \\$1}"); do
  kill -9 "$pid" 2>/dev/null || true
done

systemctl restart agr-republic.service
sleep 3

echo "[state] agr-api enabled: $(systemctl is-enabled agr-api.service 2>/dev/null || true)"
echo "[state] agr-api active: $(systemctl is-active agr-api.service 2>/dev/null || true)"
echo "[state] agr-republic active: $(systemctl is-active agr-republic.service 2>/dev/null || true)"
echo "[state] listener:"
ss -lptn "sport = :5000" | sed -n "1,2p"
echo "[state] health:"
curl -s --max-time 8 http://localhost:5000/health || true
echo
'

echo "[fix] done"
