#!/usr/bin/env bash
set -euo pipefail

# Generate latest snapshot restore mapping per sovereign Hetzner node.
# Requires: HCLOUD_TOKEN and node-map.env in same directory.

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

IMAGES_JSON="$(curl -fsS "${AUTH[@]}" "${API}/images?type=snapshot&per_page=100&sort=created:desc")"

python3 - <<'PY' \
"$IMAGES_JSON" \
"$CHIMAERA_ID" \
"$YGGDRASIL_ID" \
"$ENTERPRISE_ID" \
"$PROMETHEUS_ID" \
"$GALACTICA_ID" \
"${SNAPSHOT_TAG:-cursor-reset-gate-}"
import json
import sys

images = json.loads(sys.argv[1]).get("images", [])
ids = {
    "chimaera": int(sys.argv[2]),
    "yggdrasil": int(sys.argv[3]),
    "enterprise": int(sys.argv[4]),
    "prometheus": int(sys.argv[5]),
    "galactica": int(sys.argv[6]),
}
prefix = sys.argv[7]

print("SOVEREIGN RESTORE PLAN")
print("======================")
for name, sid in ids.items():
    candidates = [
        img for img in images
        if (img.get("created_from") or {}).get("id") == sid
        and (img.get("description") or "").startswith(prefix)
    ]
    if not candidates:
        print(f"- {name}: NO MATCHING SNAPSHOT (prefix={prefix})")
        continue
    chosen = candidates[0]
    print(
        f"- {name}: image_id={chosen.get('id')} "
        f"created={chosen.get('created')} "
        f"desc={chosen.get('description')}"
    )
PY
