#!/usr/bin/env bash
set -euo pipefail

# Runs a full private-mesh SSH matrix from each Hetzner node.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-key.sh"
ADMIN_KEY="${1:-${SSH_KEY_PATH:-}}"
ADMIN_KEY="$(resolve_fleet_ssh_key "${ADMIN_KEY}")" || {
  echo "No SSH key found for mesh matrix run" >&2
  exit 1
}

declare -A PUB
PUB[chimaera]='5.78.184.2'
PUB[yggdrasil]='128.140.45.22'
PUB[enterprise]='91.99.224.166'
PUB[prometheus]='46.62.202.166'
PUB[galactica]='178.104.31.46'

for src in chimaera yggdrasil enterprise prometheus galactica; do
  ip="${PUB[$src]}"
  echo "=== ${src} (${ip}) ==="
  # Copy active key to a temporary runtime path to avoid relying on stale
  # key filenames that may have been rotated by prior agents.
  scp -i "$ADMIN_KEY" -o StrictHostKeyChecking=no "$ADMIN_KEY" "root@${ip}:/tmp/agr_runtime_key" >/dev/null 2>&1 || true
  ssh -i "$ADMIN_KEY" -o StrictHostKeyChecking=no "root@${ip}" '
    chmod 600 /tmp/agr_runtime_key 2>/dev/null || true
    for host in 10.10.0.1 10.10.0.2 10.10.0.3 10.10.0.4 10.10.0.5 10.10.0.10; do
      out=$(ssh -i /tmp/agr_runtime_key -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=6 root@$host "echo ok" 2>/dev/null || true)
      if [[ "$out" == "ok" ]]; then
        echo "$host PASS"
      else
        echo "$host FAIL"
      fi
    done
    rm -f /tmp/agr_runtime_key
  '
  echo
done
