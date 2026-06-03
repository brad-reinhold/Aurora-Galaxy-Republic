#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   BASE_URL="https://auroragalaxyrepublic.com" \
#   GUARDIAN_TOKEN="..." \
#   USERNAME="tee" \
#   PASSWORD="temporary-passphrase" \
#   EMAIL="tee@example.com" \
#   DISPLAY_NAME="Tee" \
#   GRANT_REASON="donation_milk_gallon" \
#   ./sovereign/provision-lifetime-admin.sh

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
GUARDIAN_TOKEN="${GUARDIAN_TOKEN:-}"
USERNAME="${USERNAME:-}"
PASSWORD="${PASSWORD:-}"
EMAIL="${EMAIL:-}"
DISPLAY_NAME="${DISPLAY_NAME:-}"
GRANT_REASON="${GRANT_REASON:-lifetime_admin_grant}"

if [[ -z "$USERNAME" ]]; then
  echo "ERROR: USERNAME is required" >&2
  exit 1
fi
if [[ -z "$PASSWORD" ]]; then
  echo "ERROR: PASSWORD is required" >&2
  exit 1
fi
if [[ -z "$GUARDIAN_TOKEN" ]]; then
  echo "ERROR: GUARDIAN_TOKEN is required for CEO-authorized provisioning" >&2
  exit 1
fi

curl -sS -X POST "${BASE_URL%/}/api/auth/admin/provision-lifetime" \
  -H "Content-Type: application/json" \
  -H "X-Guardian-Token: ${GUARDIAN_TOKEN}" \
  -d "$(python3 - <<'PY'
import json, os
payload = {
    "username": os.environ.get("USERNAME", ""),
    "password": os.environ.get("PASSWORD", ""),
    "email": os.environ.get("EMAIL", ""),
    "display_name": os.environ.get("DISPLAY_NAME", ""),
    "grant_reason": os.environ.get("GRANT_REASON", "lifetime_admin_grant"),
}
print(json.dumps(payload))
PY
)"
