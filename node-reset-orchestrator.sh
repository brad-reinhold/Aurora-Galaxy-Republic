#!/usr/bin/env bash
set -euo pipefail

# AGR Node Reset Orchestrator (safe gate)
# Purpose: require fresh verified snapshot before any destructive server reset action.

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <server-name> <server-id> <required-snapshot-description-substring>"
  exit 2
fi

SERVER_NAME="$1"
SERVER_ID="$2"
REQUIRED_DESC="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

: "${HCLOUD_TOKEN:?HCLOUD_TOKEN environment variable required}"
API='https://api.hetzner.cloud/v1'
AUTH=(-H "Authorization: Bearer ${HCLOUD_TOKEN}" -H 'Content-Type: application/json')

echo "[gate] checking fresh snapshot for ${SERVER_NAME} (id=${SERVER_ID}) containing '${REQUIRED_DESC}'"
IMAGES_JSON=$(curl -fsS "${AUTH[@]}" "${API}/images?type=snapshot&per_page=100&sort=created:desc")
MATCH_COUNT=$(python3 - <<'PY2' "$IMAGES_JSON" "$SERVER_ID" "$REQUIRED_DESC"
import json,sys
j=json.loads(sys.argv[1])
sid=int(sys.argv[2]); needle=sys.argv[3]
imgs=j.get('images',[])
hits=[img for img in imgs if (img.get('created_from') or {}).get('id')==sid and needle in (img.get('description') or '')]
print(len(hits))
PY2
)

if [ "${MATCH_COUNT}" -lt 1 ]; then
  echo "[gate] BLOCKED: required snapshot not found"
  exit 3
fi

echo "[gate] snapshot found; requesting reboot reset for ${SERVER_NAME}"
curl -fsS -X POST "${AUTH[@]}" "${API}/servers/${SERVER_ID}/actions/reset" >/tmp/agr-reset-${SERVER_NAME}.json

echo "[action] reset requested. response stored: /tmp/agr-reset-${SERVER_NAME}.json"
