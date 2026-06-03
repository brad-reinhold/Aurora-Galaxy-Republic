#!/usr/bin/env bash
# Fleet entrypoint for nodes whose systemd unit uses ExecStart=/opt/agr/agr_start_wrapper.sh
# (e.g. agr-server.service). WorkingDirectory in the unit should be /opt/agr/aurora_server.
set -euo pipefail
ROOT="/opt/agr"
cd "${ROOT}/aurora_server"
exec /opt/agr-venv/bin/uvicorn republic_os_server:app --host 0.0.0.0 --port 5000 "$@"
