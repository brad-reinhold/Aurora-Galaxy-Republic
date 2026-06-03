#!/usr/bin/env bash
set -euo pipefail

OUT_ROOT="${OUT_ROOT:-/opt/agr/aurora_server/data/continuity_quorum_bundles}"
TS="$(date -u +%Y%m%d-%H%M%SZ)"
WORK_DIR="${OUT_ROOT}/${TS}"
mkdir -p "${WORK_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib/fleet-key.sh"

NODES=(
  "chimaera:5.78.184.2"
  "yggdrasil:128.140.45.22"
  "enterprise:91.99.224.166"
  "prometheus:46.62.202.166"
  "galactica:178.104.31.46"
)

if ! SSH_KEY="$(resolve_fleet_ssh_key "${SSH_KEY:-}")"; then
  echo "No SSH key found for quorum bundling (set AGR_FLEET_KEY/AGR_SSH_KEY/FLEET_SSH_KEY/HETZNER_SSH_KEY)" >&2
  exit 1
fi

FILES=(
  "/opt/agr/state/constitution_lock_manifest.json"
  "/opt/agr/state/constitution_integrity_audit.jsonl"
  "/opt/agr/state/civilization_memory_state.json"
  "/opt/agr/state/continuity_consents.jsonl"
  "/opt/agr/state/continuity_snapshots.jsonl"
  "/opt/agr/aurora_server/data/SOUL_CONTINUITY_PROTOCOL_20260412.md"
  "/opt/agr/aurora_server/data/SOUL_CONTINUITY_PROFILE_20260412.json"
  "/opt/agr/aurora_server/data/public_cinematic_rollout.json"
  "/opt/agr/aurora_server/data/public_aesthetic_baseline.css"
)

MANIFEST_JSON="${WORK_DIR}/manifest.json"
MANIFEST_MD="${WORK_DIR}/manifest.md"
ROWS='[]'
SUCCESS_COUNT=0

for entry in "${NODES[@]}"; do
  NAME="${entry%%:*}"
  IP="${entry##*:}"
  REMOTE_BUNDLE="/tmp/${NAME}_continuity_${TS}.tar.gz"
  LOCAL_BUNDLE="${WORK_DIR}/${NAME}.tar.gz"

  FILE_LIST=""
  for f in "${FILES[@]}"; do
    FILE_LIST="${FILE_LIST} ${f}"
  done

  RC=0
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@"$IP" \
    "tar -czf '${REMOTE_BUNDLE}' --ignore-failed-read ${FILE_LIST}" >/dev/null 2>&1 || RC=$?

  STATUS="ok"
  SHA=""
  SIZE=0
  if [[ "$RC" -ne 0 ]]; then
    STATUS="ssh_or_tar_fail"
  else
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no root@"$IP":"${REMOTE_BUNDLE}" "${LOCAL_BUNDLE}" >/dev/null 2>&1 || STATUS="scp_fail"
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@"$IP" "rm -f '${REMOTE_BUNDLE}'" >/dev/null 2>&1 || true
  fi

  if [[ "$STATUS" == "ok" ]]; then
    SHA="$(sha256sum "${LOCAL_BUNDLE}" | awk '{print $1}')"
    SIZE="$(stat -c%s "${LOCAL_BUNDLE}")"
    SUCCESS_COUNT=$((SUCCESS_COUNT+1))
  fi

  ROWS="$(python3 - <<'PY' "$ROWS" "$NAME" "$IP" "$STATUS" "$SHA" "$SIZE"
import json,sys
arr=json.loads(sys.argv[1])
arr.append({
  "node":sys.argv[2],
  "ip":sys.argv[3],
  "status":sys.argv[4],
  "sha256":sys.argv[5],
  "size_bytes":int(sys.argv[6]) if sys.argv[6].isdigit() else 0
})
print(json.dumps(arr))
PY
)"
done

QUORUM="fail"
if [[ "$SUCCESS_COUNT" -ge 3 ]]; then
  QUORUM="pass"
fi

python3 - <<'PY' "$MANIFEST_JSON" "$TS" "$ROWS" "$SUCCESS_COUNT" "$QUORUM"
import json,sys
payload={
  "timestamp":sys.argv[2],
  "bundles":json.loads(sys.argv[3]),
  "successful_bundles":int(sys.argv[4]),
  "quorum_rule":"3-of-5",
  "quorum_result":sys.argv[5]
}
with open(sys.argv[1],"w") as f:
  json.dump(payload,f,indent=2)
PY

{
  echo "# Continuity Quorum Bundle"
  echo "Generated: $(date -u +%FT%TZ)"
  echo "Output dir: ${WORK_DIR}"
  echo
  echo "- successful_bundles: ${SUCCESS_COUNT}"
  echo "- quorum_rule: 3-of-5"
  echo "- quorum_result: ${QUORUM}"
  echo
  echo "## Bundles"
  python3 - <<'PY' "$ROWS"
import json,sys
rows=json.loads(sys.argv[1])
for r in rows:
  print(f"- {r['node']} ({r['ip']}): status={r['status']} size={r['size_bytes']} sha256={r['sha256']}")
PY
} > "${MANIFEST_MD}"

sha256sum "${WORK_DIR}"/*.tar.gz "${MANIFEST_JSON}" "${MANIFEST_MD}" 2>/dev/null || true
echo "continuity_quorum_bundle_dir=${WORK_DIR}"
echo "quorum_result=${QUORUM}"
