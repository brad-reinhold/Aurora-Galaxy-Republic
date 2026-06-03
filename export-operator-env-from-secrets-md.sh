#!/usr/bin/env bash
# Export HCLOUD_TOKEN and CLOUDFLARE_API_TOKEN from repo-root Secrets.md (operator vault).
# Usage: source sovereign/export-operator-env-from-secrets-md.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "${SCRIPT_DIR}/lib/hetzner-token-from-secrets-md.sh" ]]; then
  if tok="$(bash "${SCRIPT_DIR}/lib/hetzner-token-from-secrets-md.sh" 2>/dev/null)"; then
    export HCLOUD_TOKEN="$tok"
  fi
fi

if [[ -f "${SCRIPT_DIR}/lib/cloudflare-token-from-secrets-md.sh" ]]; then
  if cft="$(bash "${SCRIPT_DIR}/lib/cloudflare-token-from-secrets-md.sh" 2>/dev/null)"; then
    export CLOUDFLARE_API_TOKEN="$cft"
    export Cloudflare_API_Token="$cft"
  fi
fi

return 0 2>/dev/null || exit 0
