#!/usr/bin/env bash
# Pull latest main on each Hetzner and restart the Republic app service.
# Intended for agents/CI with HCLOUD_TOKEN + fleet SSH key; no GitHub UI required.
#
# If a host errors "not a git repo: /opt/agr", run once (all five nodes):
#   CONFIRM=1 bash sovereign/scripts/fleet-git-init-opt-agr.sh
# (requires GitHub read from each node — deploy key or FLEET_GIT_URL with token.)
#
# Requirements (any one key path resolution works — see sovereign/lib/fleet-key.sh):
#   - AGR_FLEET_KEY or AGR_FLEET_KEY_CONTENT / *_B64, or key file on disk
#
# Optional env:
#   FLEET_PULL_BRANCH   default: main
#   FLEET_PULL_DIR      default: /opt/agr
#   FLEET_PULL_SERVICE  default: agr-republic.service (uvicorn on :5000; override if your install uses another unit)
#   FLEET_PULL_HOSTS    space-separated IPs (default: five-cloud nodes from fleet map)
#   FLEET_PULL_USER     default: root
#   FLEET_PULL_EXTRA    extra shell to run after pull (e.g. systemctl status)
#   FLEET_PULL_POST_RESTART_WAIT_SEC  seconds to sleep after restart before /health probe (default 5)
#   FLEET_REMOTE_GIT_KEY_PATH  on each host: PEM for GitHub SSH (default /root/.ssh/agr_fleet_github_read)
#   FLEET_GIT_SSH_OPTS  extra ssh flags for GIT_SSH_COMMAND (default accept-new + BatchMode)
#   FLEET_PULL_GITHUB_HTTPS_URL  if set, rewrite origin when it is https://github.com/... or
#       https://x-access-token:*@github.com/... before fetch (refreshes expired PAT on nodes).
#   FLEET_PULL_REFRESH_ORIGIN_HTTPS  default 1; set 0 to skip origin rewrite
#   FLEET_PULL_SKIP_UNTRACKED_WAVE4  default 1; set 0 to skip removing untracked
#       aurora_server/data/WAVE4_BENCHMARK_PROOF_20260414.{json,md} before pull
#   FLEET_PULL_SKIP_UNTRACKED_POLICY_SEEDS  default 1; set 0 to skip removing untracked
#       aurora_server/data/* policy seeds that are now tracked on main (old nodes ran
#       _ensure_seed_files() and left untracked copies that block git pull / reset).
#   FLEET_PULL_HARD_RESET  default 0; set 1 to always `git reset --hard origin/$BRANCH`
#       after fetch (fleet mirror of main; discards local commits/edits on the node).
#       When 0, merge --ff-only is attempted first; if Git refuses with "would be overwritten
#       by merge", the script resets hard to origin/$BRANCH and continues.
#   FLEET_PULL_ALT_SERVICE  fallback unit if primary restart did not run (default agr-server.service)
#   FLEET_PULL_ALT_RESTART  default 1; set 0 to skip fallback restart
#   FLEET_PULL_MIRL_CHECK_PATH  loopback path if /health fails (default /api/public/mirl/catalog); set empty to skip
#
# Remote update: git fetch origin $BRANCH && git checkout $BRANCH && git merge --ff-only origin/$BRANCH
# (avoids flaky `git pull` on some git builds — same pattern as AGENTS.md fetch + ff-only merge.)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-key.sh"

KEY_PATH="$(resolve_fleet_ssh_key "${KEY_PATH:-}")" || {
  echo "fleet-pull-main-restart: no fleet SSH key (set AGR_FLEET_KEY or AGR_FLEET_KEY_CONTENT)" >&2
  exit 1
}

BRANCH="${FLEET_PULL_BRANCH:-main}"
REPO_DIR="${FLEET_PULL_DIR:-/opt/agr}"
SERVICE="${FLEET_PULL_SERVICE:-agr-republic.service}"
SSH_USER="${FLEET_PULL_USER:-root}"
# Order: yggdrasil, chimaera, enterprise, prometheus, galactica (matches common rollout naming)
DEFAULT_HOSTS="128.140.45.22 5.78.184.2 91.99.224.166 46.62.202.166 178.104.31.46"
read -r -a HOSTS <<< "${FLEET_PULL_HOSTS:-$DEFAULT_HOSTS}"

GIT_SSH_EXTRA="${FLEET_GIT_SSH_OPTS:--o StrictHostKeyChecking=accept-new -o BatchMode=yes}"
REMOTE_KEY_INST="${FLEET_REMOTE_GIT_KEY_PATH:-/root/.ssh/agr_fleet_github_read}"
REFRESH_URL_Q=""
if [[ -n "${FLEET_PULL_GITHUB_HTTPS_URL:-}" ]]; then
  REFRESH_URL_Q="$(printf '%q' "${FLEET_PULL_GITHUB_HTTPS_URL}")"
fi
REFRESH_FLAG="${FLEET_PULL_REFRESH_ORIGIN_HTTPS:-1}"
ALT_SQ="$(printf '%q' "${FLEET_PULL_ALT_SERVICE:-agr-server.service}")"
ALT_EN="${FLEET_PULL_ALT_RESTART:-1}"
MIRL_PATH="${FLEET_PULL_MIRL_CHECK_PATH:-/api/public/mirl/catalog}"
MIRL_Q="$(printf '%q' "$MIRL_PATH")"

SSH_OPTS=(
  -i "$KEY_PATH"
  -o BatchMode=yes
  -o ConnectTimeout=12
  -o StrictHostKeyChecking=accept-new
)

pull_failed=0
for h in "${HOSTS[@]}"; do
  echo "========================================"
  echo "[fleet-pull] $SSH_USER@$h"
  WAIT_POST="${FLEET_PULL_POST_RESTART_WAIT_SEC:-5}"
  SKIP_W="${FLEET_PULL_SKIP_UNTRACKED_WAVE4:-1}"
  SKIP_POLICY="${FLEET_PULL_SKIP_UNTRACKED_POLICY_SEEDS:-1}"
  HARD_RESET="${FLEET_PULL_HARD_RESET:-0}"
  if ! ssh "${SSH_OPTS[@]}" "$SSH_USER@$h" bash -s <<REMOTE
set -euo pipefail
REPO_DIR="${REPO_DIR}"
BRANCH="${BRANCH}"
SERVICE="${SERVICE}"
KEYFILE="${REMOTE_KEY_INST}"
GIT_SSH_EXTRA="${GIT_SSH_EXTRA}"
WAIT_POST="${WAIT_POST}"
SKIP_WAVE4="${SKIP_W}"
SKIP_POLICY_SEEDS="${SKIP_POLICY}"
HARD_RESET="${HARD_RESET}"
REFRESH_URL=${REFRESH_URL_Q}
REFRESH_FLAG="${REFRESH_FLAG}"
ALT_SERVICE=${ALT_SQ}
ALT_RESTART=${ALT_EN}
MIRL_CHECK=${MIRL_Q}
if [[ -f "\${KEYFILE}" ]]; then
  chmod 600 "\${KEYFILE}" 2>/dev/null || true
  export GIT_SSH_COMMAND="ssh -i \${KEYFILE} \${GIT_SSH_EXTRA}"
fi
if [[ ! -d "\${REPO_DIR}/.git" ]]; then
  echo "[fleet-pull] ERROR: not a git repo: \${REPO_DIR}" >&2
  exit 2
fi
cd "\${REPO_DIR}"
# Tracked runtime JSON/CSS under data/ and state/ may be immutable (+i) on older installs;
# git cannot replace them on merge/reset until the flag is cleared.
if command -v chattr >/dev/null 2>&1; then
  for sub in aurora_server/data aurora_server/state; do
    d="\${REPO_DIR}/\${sub}"
    if [[ -d "\$d" ]]; then
      find "\$d" -type f 2>/dev/null | while IFS= read -r f; do
        chattr -i "\$f" 2>/dev/null || true
      done
    fi
  done
fi
# Untracked blockers under aurora_server/data: some hosts set immutable (+i) on runtime
# seeds; root must chattr -i before unlink. ceo-owned 755 dirs: chattr as root, then rm.
_rm_as_data_owner() {
  for p in "\$@"; do
    chattr -i "\$p" 2>/dev/null || true
    rm -f "\$p" 2>/dev/null || true
    if [[ -e "\$p" ]] && id -u ceo >/dev/null 2>&1 && command -v runuser >/dev/null 2>&1; then
      runuser -u ceo -- rm -f "\$p" 2>/dev/null || true
    fi
  done
}
# Untracked copies of tracked Wave4 proof files block git pull; remove unless opted out.
if [[ "\${SKIP_WAVE4}" != "0" ]]; then
  _rm_as_data_owner "\${REPO_DIR}/aurora_server/data/WAVE4_BENCHMARK_PROOF_20260414.json" "\${REPO_DIR}/aurora_server/data/WAVE4_BENCHMARK_PROOF_20260414.md"
fi
# Untracked policy seeds (runtime-generated on old trees) block pull once those paths exist on origin/main.
if [[ "\${SKIP_POLICY_SEEDS}" != "0" ]]; then
  _rm_as_data_owner "\${REPO_DIR}/aurora_server/data/ALWAYS_FIRST_PRIORITIES_20260412.json" "\${REPO_DIR}/aurora_server/data/CORNERSTONE_BUILDER_RECOGNITION_20260416.json" "\${REPO_DIR}/aurora_server/data/FUSION_REALITY_INTERACTION_LOCK_20260414.json" "\${REPO_DIR}/aurora_server/data/LEGAL_INTAKE_POLICY_20260413.json" "\${REPO_DIR}/aurora_server/data/PUBLIC_ACCESS_POLICY_20260413.json" "\${REPO_DIR}/aurora_server/data/PUBLIC_TRUST_CHARTER_20260413.md" "\${REPO_DIR}/aurora_server/data/SAFETY_ENFORCEMENT_POLICY_20260413.json"
fi
if [[ "\${REFRESH_FLAG}" != "0" ]] && [[ -n "\${REFRESH_URL:-}" ]]; then
  cur="\$(git remote get-url origin 2>/dev/null || true)"
  if [[ "\$cur" == https://github.com/* ]] || [[ "\$cur" == https://x-access-token:*@github.com/* ]]; then
    git remote set-url origin "\${REFRESH_URL}"
    echo "[fleet-pull] origin refreshed (https token rotated on host)"
  fi
fi
git remote -v 2>/dev/null | sed -E 's#(https://)x-access-token:[^@]+@#\1x-access-token:***@#g' || true
git fetch origin "\${BRANCH}"
git checkout "\${BRANCH}"
# merge --ff-only avoids flaky plain "git pull" on some git versions ("Cannot fast-forward to multiple branches").
_merge_ff() {
  git merge --ff-only "origin/\${BRANCH}"
}
if [[ "\${HARD_RESET}" == "1" ]]; then
  echo "[fleet-pull] reset hard to origin/\${BRANCH} (FLEET_PULL_HARD_RESET=1)"
  git reset --hard "origin/\${BRANCH}"
else
  mf="\$(mktemp /tmp/agr_fleet_ff_merge.XXXXXX)"
  if ! _merge_ff >"\${mf}" 2>&1; then
    if grep -qiE 'would be overwritten by merge|local changes to the following files' "\${mf}" 2>/dev/null; then
      echo "[fleet-pull] WARN: dirty tracked tree blocks ff-only merge — git reset --hard origin/\${BRANCH}" >&2
      git reset --hard "origin/\${BRANCH}"
    else
      cat "\${mf}" >&2
      rm -f "\${mf}"
      exit 1
    fi
  fi
  rm -f "\${mf}"
fi
# Stamp deployed git HEAD for /health + /api/public/health (see aurora_server/agr_deploy_revision.py).
if hrev="$(git -C "\${REPO_DIR}" rev-parse HEAD 2>/dev/null)"; then
  printf '%s\n' "\${hrev}" >"\${REPO_DIR}/.agr-git-revision" || true
else
  printf '%s\n' "unknown" >"\${REPO_DIR}/.agr-git-revision" || true
fi
restarted=0
if systemctl cat "\${SERVICE}" &>/dev/null; then
  ens="\$(systemctl is-enabled "\${SERVICE}" 2>/dev/null || true)"
  if [[ "\${ens}" == masked ]]; then
    echo "[fleet-pull] WARN: \${SERVICE} is masked (skipping restart)" >&2
  elif systemctl restart "\${SERVICE}" 2>/dev/null; then
    systemctl is-active "\${SERVICE}" || true
    sleep "\${WAIT_POST}"
    restarted=1
  else
    echo "[fleet-pull] WARN: restart failed for \${SERVICE}" >&2
  fi
else
  echo "[fleet-pull] WARN: unit not present: \${SERVICE}" >&2
fi
if [[ "\${restarted}" -eq 0 ]] && [[ "\${ALT_RESTART}" != "0" ]] && [[ -n "\${ALT_SERVICE:-}" ]] && systemctl cat "\${ALT_SERVICE}" &>/dev/null; then
  ens="\$(systemctl is-enabled "\${ALT_SERVICE}" 2>/dev/null || true)"
  if [[ "\${ens}" == masked ]]; then
    echo "[fleet-pull] WARN: \${ALT_SERVICE} is masked (skipping fallback restart)" >&2
  elif systemctl restart "\${ALT_SERVICE}" 2>/dev/null; then
    echo "[fleet-pull] restarted fallback \${ALT_SERVICE}"
    systemctl is-active "\${ALT_SERVICE}" || true
    sleep "\${WAIT_POST}"
    restarted=1
  else
    echo "[fleet-pull] WARN: fallback restart failed for \${ALT_SERVICE}" >&2
  fi
fi
if curl -sf --max-time 12 "http://127.0.0.1:5000/health" >/dev/null 2>&1; then
  echo "[fleet-pull] health: ok"
else
  mc="000"
  if [[ -n "\${MIRL_CHECK:-}" ]]; then
    mc="\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "http://127.0.0.1:5000\${MIRL_CHECK}" 2>/dev/null || echo 000)"
    mc="\${mc:0:3}"
  fi
  if [[ "\${mc}" == "200" ]]; then
    echo "[fleet-pull] health: ok (MIR-L catalog \${MIRL_CHECK} HTTP 200)"
  else
    echo "[fleet-pull] WARN: /health not ok on :5000 (MIR-L check: \${mc:-skipped})" >&2
  fi
fi
REMOTE
  then
    echo "[fleet-pull] ERROR: SSH or remote script failed for $SSH_USER@$h" >&2
    pull_failed=1
  fi
done

if [[ "$pull_failed" -ne 0 ]]; then
  echo "[fleet-pull] FAILED: one or more hosts did not complete successfully" >&2
  exit 1
fi

echo "[fleet-pull] all hosts completed"
