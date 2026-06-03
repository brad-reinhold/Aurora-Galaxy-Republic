#!/usr/bin/env bash
set -euo pipefail

# Create fresh snapshots for all five Hetzner sovereign nodes.
# Requires: HCLOUD_TOKEN and node-map.env in this directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_MAP="${SCRIPT_DIR}/node-map.env"

# shellcheck disable=SC1091
if [[ -f "${SCRIPT_DIR}/lib/cursor-secrets-bridge.sh" ]]; then
  # shellcheck disable=SC1090
  source "${SCRIPT_DIR}/lib/cursor-secrets-bridge.sh"
fi
if [[ -f "${SCRIPT_DIR}/lib/hetzner-token-from-secrets-md.sh" ]] && [[ -z "${HCLOUD_TOKEN:-}" ]]; then
  if tok="$(bash "${SCRIPT_DIR}/lib/hetzner-token-from-secrets-md.sh" 2>/dev/null)"; then
    export HCLOUD_TOKEN="$tok"
  fi
fi

if [[ ! -f "$NODE_MAP" ]]; then
  echo "missing node-map.env at $NODE_MAP" >&2
  exit 2
fi

# shellcheck disable=SC1090
source "$NODE_MAP"
: "${HCLOUD_TOKEN:?HCLOUD_TOKEN is required}"

API='https://api.hetzner.cloud/v1'
AUTH=(-H "Authorization: Bearer ${HCLOUD_TOKEN}" -H 'Content-Type: application/json')
TS="$(date -u +%Y%m%dT%H%M%SZ)"
TAG="${SNAPSHOT_TAG:-cursor-reset-gate-}${TS}"

create_snapshot() {
  local server_name="$1"
  local server_id="$2"
  local desc="${TAG}-${server_name}"
  local payload
  payload="$(printf '{"description":"%s","type":"snapshot"}' "$desc")"
  echo "[snapshot] ${server_name} (id=${server_id}) -> ${desc}"
  curl -fsS -X POST "${AUTH[@]}" -d "$payload" \
    "${API}/servers/${server_id}/actions/create_image" \
    >/tmp/agr-snap-"${server_name}".json
  echo "[snapshot] queued ${server_name}"
}

create_snapshot "chimaera"   "${CHIMAERA_ID}"
create_snapshot "yggdrasil"  "${YGGDRASIL_ID}"
create_snapshot "enterprise" "${ENTERPRISE_ID}"
create_snapshot "prometheus" "${PROMETHEUS_ID}"
create_snapshot "galactica"  "${GALACTICA_ID}"

echo "[done] snapshot wave queued with tag prefix: ${TAG}"
