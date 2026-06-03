#!/usr/bin/env bash
# Run fleet-git-init-opt-agr.sh after loading operator tokens + optional fleet key from Secrets.md.
#
# Same key resolution as fleet-pull-with-secrets-md.sh.
# Still requires CONFIRM=1 (safety latch inside fleet-git-init-opt-agr.sh).
#
# If **FLEET_GIT_URL** is unset, clone URL is resolved in order:
#   1) **Secrets.md** line ``agr fleet github read token:`` (PAT) → HTTPS ``x-access-token`` URL (not printed).
#   2) Else if **`gh auth token`** is available (e.g. GitHub Actions or Cursor with `gh` logged in) → same HTTPS pattern for **this** repo only.
#   3) Else default **SSH** ``git@github.com:...`` (requires deploy key on GitHub).
#
# Example:
#   CONFIRM=1 bash sovereign/fleet-git-init-with-secrets-md.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/export-operator-env-from-secrets-md.sh" || true
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-key.sh"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-resolve-key-from-secrets-md.sh"

owner="${FLEET_GITHUB_OWNER:-TBR3661}"
repo="${FLEET_GITHUB_REPO:-O3r6v2s9b5d7b0m1x7b5}"

if [[ -z "${FLEET_GIT_URL:-}" ]]; then
  tok=""
  if tok="$(bash "${SCRIPT_DIR}/lib/fleet-github-read-token-from-secrets-md.sh" 2>/dev/null)"; then
    :
  elif [[ "${FLEET_USE_GH_AUTH_TOKEN:-1}" != "0" ]] && command -v gh >/dev/null 2>&1; then
    if tok="$(gh auth token 2>/dev/null)"; then
      if [[ -z "$tok" ]]; then
        tok=""
      fi
    fi
  fi
  if [[ -z "$tok" ]] && [[ -n "${GITHUB_TOKEN:-}" ]]; then
    tok="${GITHUB_TOKEN}"
  fi
  if [[ -n "$tok" ]]; then
    export FLEET_GIT_URL="https://x-access-token:${tok}@github.com/${owner}/${repo}.git"
  fi
fi

exec bash "${SCRIPT_DIR}/scripts/fleet-git-init-opt-agr.sh"
