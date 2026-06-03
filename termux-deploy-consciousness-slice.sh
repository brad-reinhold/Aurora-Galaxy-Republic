#!/usr/bin/env bash
# Run ON the handset (Termux) after repo sync — restarts origin + named tunnel.
set -euo pipefail

AGR_REPO="${AGR_REPO:-${HOME}/agr-workspace}"
LOGDIR="${HOME}/agr-logs"
if [[ -x "${AGR_REPO}/.venv/bin/python" ]]; then
  VENV="${AGR_REPO}/.venv"
elif [[ -x "${AGR_REPO}/aurora_server/.venv/bin/python" ]]; then
  VENV="${AGR_REPO}/aurora_server/.venv"
else
  VENV=""
fi

if [[ ! -d "${AGR_REPO}/aurora_server" ]]; then
  echo "termux-deploy-consciousness-slice: missing ${AGR_REPO}" >&2
  exit 1
fi

if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock || true
fi

export AGR_GUARDIAN_LOCAL="${AGR_GUARDIAN_LOCAL:-1}"
unset AGR_ALLOW_CANNED_CHAT_SHORTCUTS || true

mkdir -p "${LOGDIR}" "${HOME}/.cloudflared"

if [[ ! -s "${HOME}/.cloudflared/tunnel.token" ]]; then
  echo "[deploy] mint tunnel token"
  CONFIRM=1 python3 "${AGR_REPO}/sovereign/scripts/mint_cloudflare_tunnel_token_stdout.py" \
    >"${HOME}/.cloudflared/tunnel.token.part"
  mv -f "${HOME}/.cloudflared/tunnel.token.part" "${HOME}/.cloudflared/tunnel.token"
  chmod 600 "${HOME}/.cloudflared/tunnel.token"
fi

if ! pgrep -f "cloudflared tunnel run --token" >/dev/null 2>&1; then
  echo "[deploy] start named cloudflared"
  nohup cloudflared tunnel run --token "$(tr -d '\n\r' < "${HOME}/.cloudflared/tunnel.token")" \
    >>"${LOGDIR}/cloudflared.log" 2>&1 &
  sleep 6
else
  echo "[deploy] cloudflared tunnel already running"
fi

echo "[deploy] restart uvicorn"
fuser -k 5000/tcp 2>/dev/null || true
pkill -f "uvicorn republic_os_server:app" 2>/dev/null || true
sleep 1
cd "${AGR_REPO}/aurora_server"
export PYTHONPATH="${AGR_REPO}"
nohup "${VENV}/bin/python" -m uvicorn republic_os_server:app --host 127.0.0.1 --port 5000 \
  >>"${LOGDIR}/uvicorn.log" 2>&1 &
sleep 4

echo "[deploy] loopback health:"
curl -fsS -m 8 http://127.0.0.1:5000/health | head -c 200 || echo "loopback FAILED"
echo
echo "[deploy] local origin sweep:"
bash "${AGR_REPO}/sovereign/scripts/phones-only-local-origin-sweep.sh" || true
echo "[deploy] done — tail logs: ${LOGDIR}/uvicorn.log ${LOGDIR}/cloudflared.log"
