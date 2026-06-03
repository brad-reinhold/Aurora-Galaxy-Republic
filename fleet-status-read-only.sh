#!/usr/bin/env bash
# Read-only fleet health: SSH to each default host and report git + Republic HTTP health.
# systemd_active is true if either FLEET_PULL_SERVICE (default agr-republic) or
# FLEET_STATUS_ALT_SERVICE (default agr-server) is active/activating — some nodes use one unit only.
# local_health is true if /health succeeds or MIR-L catalog returns 200 (busy single-worker nodes).
# Optional: non-secret booleans for Guardian binding materialization (directory + file presence only).
# Does not mutate remotes. Uses same SSH key resolution as fleet-pull-with-secrets-md.sh.
#
# Example:
#   bash sovereign/fleet-status-read-only.sh
#   FLEET_STATUS_FORMAT=json bash sovereign/fleet-status-read-only.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/export-operator-env-from-secrets-md.sh" || true
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-key.sh"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/fleet-resolve-key-from-secrets-md.sh"

KEY_PATH="$(resolve_fleet_ssh_key "${KEY_PATH:-}")" || {
  echo "fleet-status-read-only: no fleet SSH key (set AGR_FLEET_KEY or agr fleet key b64: in Secrets.md)" >&2
  exit 1
}

REPO_DIR="${FLEET_PULL_DIR:-/opt/agr}"
SERVICE="${FLEET_PULL_SERVICE:-agr-republic.service}"
ALT_SERVICE="${FLEET_STATUS_ALT_SERVICE:-agr-server.service}"
SSH_USER="${FLEET_PULL_USER:-root}"
MIRL_PATH="${FLEET_STATUS_MIRL_PATH:-/api/public/mirl/catalog}"
FMT="${FLEET_STATUS_FORMAT:-text}"
GUARDIAN_SECRETS_DIR="${FLEET_STATUS_GUARDIAN_SECRETS_DIR:-/opt/agr/.secrets}"
_raw_prof="${FLEET_STATUS_GUARDIAN_PROFILE:-guardian-device-profile.json}"
GUARDIAN_PROFILE="${_raw_prof##*/}"
[[ -z "$GUARDIAN_PROFILE" || "$GUARDIAN_PROFILE" == "." || "$GUARDIAN_PROFILE" == ".." ]] && GUARDIAN_PROFILE="guardian-device-profile.json"
DEFAULT_HOSTS="128.140.45.22 5.78.184.2 91.99.224.166 46.62.202.166 178.104.31.46"
read -r -a HOSTS <<< "${FLEET_PULL_HOSTS:-$DEFAULT_HOSTS}"

SSH_OPTS=(
  -i "$KEY_PATH"
  -o BatchMode=yes
  -o ConnectTimeout=15
  -o StrictHostKeyChecking=accept-new
)

if [[ "$FMT" == "text" ]]; then
  echo "[fleet-status] repo_dir=${REPO_DIR} service=${SERVICE} alt_service=${ALT_SERVICE} mirl_path=${MIRL_PATH}"
  echo "[fleet-status] guardian_secrets_dir=${GUARDIAN_SECRETS_DIR} guardian_profile=${GUARDIAN_PROFILE} (presence only, no file reads)"
fi

json_parts=()

for h in "${HOSTS[@]}"; do
  ssh_ok=1
  line=""
  if ! line="$(
    # shellcheck disable=SC2089,SC2090
    ssh "${SSH_OPTS[@]}" "$SSH_USER@$h" bash -s <<EOF
set -uo pipefail
REPO_DIR=$(printf '%q' "$REPO_DIR")
SERVICE=$(printf '%q' "$SERVICE")
ALT_SVC=$(printf '%q' "$ALT_SERVICE")
MIRL_PATH=$(printf '%q' "$MIRL_PATH")
G_SEC=$(printf '%q' "$GUARDIAN_SECRETS_DIR")
G_PROF=$(printf '%q' "$GUARDIAN_PROFILE")
sec_d=0
[[ -d "\${G_SEC}" ]] && sec_d=1
prof_p=0
_p="\${G_SEC}/\${G_PROF}"
if [[ -f "\${_p}" ]] && [[ -s "\${_p}" ]]; then prof_p=1; fi
root_p=0
if [[ -f /root/.secrets/guardian-device-profile.json ]] && [[ -s /root/.secrets/guardian-device-profile.json ]]; then root_p=1; fi
gr=0
br="?"
hd="?"
if [[ -d "\${REPO_DIR}/.git" ]]; then
  gr=1
  if cd "\${REPO_DIR}" 2>/dev/null; then
    br="\$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
    hd="\$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
  fi
fi
sd=0
for u in "\${SERVICE}" "\${ALT_SVC}"; do
  st="\$(systemctl is-active "\${u}" 2>/dev/null || true)"
  if [[ "\${st}" == "active" || "\${st}" == "activating" ]]; then sd=1; break; fi
done
lh=0
for _try in 1 2 3; do
  if curl -sf --max-time 12 "http://127.0.0.1:5000/health" &>/dev/null; then lh=1; break; fi
  sleep 2
done
code="\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "http://127.0.0.1:5000\${MIRL_PATH}" 2>/dev/null || echo 000)"
code="\${code:0:3}"
# Busy single-worker nodes: /health can time out while MIR-L still serves; count as up if catalog is 200.
if [[ "\$lh" != "1" ]] && [[ "\$code" == "200" ]]; then lh=1; fi
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "\${gr}" "\${br}" "\${hd}" "\${sd}" "\${lh}" "\${code}" "\${MIRL_PATH}" "\${sec_d}" "\${prof_p}" "\${root_p}"
EOF
  )"; then
    ssh_ok=0
    line=$'0\t?\t?\t0\t0\t000\t\t0\t0\t0'
  fi

  IFS=$'\t' read -r gr br hd sd lh code mpath sec_d prof_p root_p <<<"${line//$'\r'/}"
  [[ -z "${mpath:-}" ]] && mpath="$MIRL_PATH"

  gr_b=false
  [[ "$gr" == "1" ]] && gr_b=true
  sd_b=false
  [[ "$sd" == "1" ]] && sd_b=true
  lh_b=false
  [[ "$lh" == "1" ]] && lh_b=true
  ssh_b=false
  [[ "$ssh_ok" -eq 1 ]] && ssh_b=true

  sec_b=false
  [[ "${sec_d:-0}" == "1" ]] && sec_b=true
  prof_b=false
  [[ "${prof_p:-0}" == "1" ]] && prof_b=true
  root_b=false
  [[ "${root_p:-0}" == "1" ]] && root_b=true

  br_esc="${br//\\/\\\\}"
  br_esc="${br_esc//\"/\\\"}"
  hd_esc="${hd//\\/\\\\}"
  hd_esc="${hd_esc//\"/\\\"}"
  mp_esc="${mpath//\\/\\\\}"
  mp_esc="${mp_esc//\"/\\\"}"
  json_parts+=("{\"host\":\"${h}\",\"ssh_ok\":${ssh_b},\"git_repo\":${gr_b},\"branch\":\"${br_esc}\",\"head\":\"${hd_esc}\",\"systemd_active\":${sd_b},\"local_health\":${lh_b},\"local_mirl_http\":\"${code}\",\"mirl_path\":\"${mp_esc}\",\"fleet_guardian_secrets_dir\":${sec_b},\"fleet_guardian_profile_nonempty\":${prof_b},\"root_guardian_profile_nonempty\":${root_b}}")

  if [[ "$FMT" == "text" ]]; then
    echo "========================================"
    echo "[fleet-status] ${SSH_USER}@${h}"
    if [[ "$ssh_ok" -eq 0 ]]; then
      echo "ssh=failed"
    else
      echo -n "ssh: ok | "
      if [[ "$gr" == "1" ]]; then
        echo -n "git_repo=yes | branch=${br} | head=${hd} | "
      else
        echo -n "git_repo=no | "
      fi
      if [[ "$sd" == "1" ]]; then
        echo -n "systemd_active=yes | "
      else
        echo -n "systemd_active=no | "
      fi
      if [[ "$lh" == "1" ]]; then
        echo -n "local_health=ok | "
      else
        echo -n "local_health=miss | "
      fi
      echo -n "fleet_guardian_secrets_dir="
      [[ "${sec_d:-0}" == "1" ]] && echo -n "yes" || echo -n "no"
      echo -n " | fleet_guardian_profile_nonempty="
      [[ "${prof_p:-0}" == "1" ]] && echo -n "yes" || echo -n "no"
      echo -n " | root_guardian_profile_nonempty="
      [[ "${root_p:-0}" == "1" ]] && echo -n "yes" || echo -n "no"
      echo " | local_mirl_http=${code}"
    fi
  fi
done

if [[ "$FMT" == "json" ]]; then
  buf=""
  first=1
  for part in "${json_parts[@]}"; do
    if [[ "$first" -eq 1 ]]; then
      buf="$part"
      first=0
    else
      buf+=",$part"
    fi
  done
  gd_esc="${GUARDIAN_SECRETS_DIR//\\/\\\\}"
  gd_esc="${gd_esc//\"/\\\"}"
  gp_esc="${GUARDIAN_PROFILE//\\/\\\\}"
  gp_esc="${gp_esc//\"/\\\"}"
  printf '{"repo_dir":"%s","service":"%s","mirl_path":"%s","guardian_secrets_dir":"%s","guardian_profile":"%s","hosts":[%s]}\n' "${REPO_DIR}" "${SERVICE}" "${MIRL_PATH}" "${gd_esc}" "${gp_esc}" "$buf"
fi

if [[ "$FMT" == "text" ]]; then
  echo "[fleet-status] done"
fi
