#!/usr/bin/env bash
# Fleet public HTTP verify — no SSH. Hits each node's bound Republic port from outside.
#
# Default host list: sovereign/fleet-public-node-env.txt (see sovereign/lib/fleet-public-node-env-read.sh).
# Override:
#   FLEET_VERIFY_HOSTS="name:ip ..."  space-separated host:ip pairs
#   FLEET_PUBLIC_NODE_ENV_FILE=/path/to/custom.txt
#   FLEET_VERIFY_PATH=/api/health     if set, probe exactly this path (single try per host)
#   FLEET_VERIFY_SCHEME=https   (or http)
#   FLEET_VERIFY_PORT=443       (set empty with scheme-only URLs if needed)
#
# When FLEET_VERIFY_PATH is unset, each host is probed in order: /health then /api/health
# (first HTTP 2xx wins). Some reverse proxies route /health reliably while /api/health 404s.
#
# If every host fails (000/5xx) and Hetzner VMs are intentionally off, public Tower may still be
# healthy via handset + tunnel — see sovereign/PHONES_ONLY_PUBLIC_SURFACE.md §2 + §8,
# bash sovereign/scripts/hetzner-fleet-status.sh (API), and bash sovereign/scripts/operator-next-steps-fleet-tower.sh.
#
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=sovereign/lib/fleet-public-node-env-read.sh
source "${ROOT}/sovereign/lib/fleet-public-node-env-read.sh"

SCHEME="${FLEET_VERIFY_SCHEME:-https}"
PORT="${FLEET_VERIFY_PORT:-443}"
CUSTOM_PATH="${FLEET_VERIFY_PATH:-}"
if [[ -n "$CUSTOM_PATH" ]]; then
  PATHS=("$CUSTOM_PATH")
else
  PATHS=("/health" "/api/health")
fi

DEFAULT_SPACE="$(fleet_public_node_env_space "$ROOT")"
read -r -a ENTRIES <<< "${FLEET_VERIFY_HOSTS:-$DEFAULT_SPACE}"

fail=0
if [[ -n "$CUSTOM_PATH" ]]; then
  echo "[fleet-verify-http] ${SCHEME} port=${PORT} path=${CUSTOM_PATH}"
else
  echo "[fleet-verify-http] ${SCHEME} port=${PORT} paths=${PATHS[*]} (first 2xx per host)"
fi

for entry in "${ENTRIES[@]}"; do
  name="${entry%%:*}"
  ip="${entry##*:}"
  ok=0
  used_path=""
  last_code="000"
  for PATHONLY in "${PATHS[@]}"; do
    if [[ "$PORT" == "443" ]] && [[ "$SCHEME" == "https" ]]; then
      url="${SCHEME}://${ip}${PATHONLY}"
    else
      url="${SCHEME}://${ip}:${PORT}${PATHONLY}"
    fi
    code="$(curl -k -sS -o /tmp/fv_body.txt -w "%{http_code}" "$url" --connect-timeout 8 --max-time 15 2>/dev/null || echo "000")"
    last_code="$code"
    if [[ "$code" =~ ^2 ]]; then
      ok=1
      used_path="$PATHONLY"
      break
    fi
  done
  snippet="$(head -c 80 /tmp/fv_body.txt 2>/dev/null | tr '\n\r\t' ' ')"
  if [[ "$ok" -eq 1 ]]; then
    echo "  OK  $name ($ip) -> ${last_code}  ${used_path}  ${snippet}"
  else
    echo "  BAD $name ($ip) -> ${last_code}  (tried: ${PATHS[*]})  ${snippet}" >&2
    fail=1
  fi
done

if [[ "$fail" -ne 0 ]]; then
  echo "[fleet-verify-http] FAILED (one or more nodes not HTTP 2xx on any probe path)" >&2
  echo "[fleet-verify-http] If the five Hetzner VMs are powered **off**, direct HTTPS to **fleet-public-node-env.txt** IPs is expected to fail — public Tower may still be **live** on **OnePlus + Cloudflare tunnel** per **sovereign/PHONES_ONLY_PUBLIC_SURFACE.md** §2; **bash sovereign/scripts/hetzner-fleet-status.sh**; **bash sovereign/scripts/operator-next-steps-fleet-tower.sh**." >&2
  exit 1
fi
echo "[fleet-verify-http] all nodes responded 2xx"
