#!/usr/bin/env bash
# Post-fleet-pull verification for CI and operators (read-only over SSH).
# Requires AGR_FLEET_KEY or AGR_FLEET_KEY_CONTENT (same as fleet-pull-main-restart.sh)
# for **remote** steps only. Set FLEET_CI_POST_VERIFY_SKIP_REMOTE_SSH=1 to run only
# local/repo checks (syntax gate, optional launch-readiness, AGENT_PROGRESS verify) — used
# when GitHub Actions has no fleet key but still should gate progress-doc structure.
#
# -0.5) bash -n — sovereign/scripts/fleet-bash-syntax-check.sh (fleet-deploy-pull lib + fleet shells).
#       Chat QA matrix path is a documented peer in that script's header (sovereign/CHAT_ENGINE_VERIFICATION_MATRIX.md).
#       Set FLEET_CI_POST_VERIFY_SKIP_BASH_N=1 to skip.
# -0.25) Optional: Tower launch-readiness — set FLEET_CI_POST_VERIFY_LAUNCH_READINESS=1
#       (runs sovereign/scripts/agr-launch-readiness-tower-smoke.sh; sets AGR_LAUNCH_READINESS_RUN_TOWER1_BASH=0
#       by default). Skipped by default so fleet-deploy-pull does not double-call Tower in the same job
#       (that workflow runs launch-readiness after tower1-public-smoke.sh).
# 0) verify-agent-progress-guardian-node.py — AGENT_PROGRESS markdown structure (no SSH)
# When FLEET_CI_POST_VERIFY_SKIP_REMOTE_SSH is not 1:
# 1) fleet-vault-verify-remote.sh — exit non-zero if vault tree incomplete on any host
# 1b) fleet-guardian-secrets-verify-remote.sh — read-only Guardian .secrets / profile presence (SSH)
# 2) fleet-status-read-only.sh — JSON snapshot (FLEET_STATUS_FORMAT=json)
# 3) Optional WARN (stderr only, never fails): hosts with SSH ok but no non-empty
#    fleet or root guardian-device-profile.json (env-only binding may set
#    FLEET_CI_POST_VERIFY_GUARDIAN_WARN=0).
#
# Example (from repo root):
#   bash sovereign/fleet-ci-post-verify.sh
#
# Local-only Tower + Hetzner snapshot (no SSH): OPERATOR_HETZNER_FLEET_STATUS=1 bash sovereign/scripts/run-operator-full-verify.sh
#   (see sovereign/AGENT_MINIMUM_BASELINE.md).
# Phones-only / modular smoke WARN triage: sovereign/PHONES_ONLY_PUBLIC_SURFACE.md §8, HANDOFF_FOR_NEXT_AGENT.md operator cadence.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x \
  sovereign/lib/hetzner-token-from-secrets-md.sh \
  sovereign/lib/cloudflare-token-from-secrets-md.sh \
  sovereign/lib/fleet-key-from-secrets-md.sh \
  sovereign/lib/fleet-secrets-md-fleet-key-hint.sh \
  sovereign/lib/fleet-resolve-key-from-secrets-md.sh \
  sovereign/lib/fleet-github-read-token-from-secrets-md.sh \
  sovereign/lib/fleet-github-actions-write-token-from-secrets-md.sh \
  sovereign/scripts/fleet-actions-set-agr-fleet-key-secret.sh \
  sovereign/scripts/fleet-secrets-md-print-agr-fleet-key-b64-line.sh \
  sovereign/scripts/fleet-ssh-keygen-new.sh \
  sovereign/scripts/fleet-secrets-md-replace-fleet-key-b64-lines.sh \
  sovereign/scripts/hetzner-rescue-install-fleet-key.sh \
  sovereign/scripts/hetzner-rescue-chroot-firewall-flush.sh \
  sovereign/scripts/fleet-mirror-repo-to-nodes.sh \
  sovereign/export-operator-env-from-secrets-md.sh \
  sovereign/fleet-pull-main-restart.sh \
  sovereign/fleet-pull-with-secrets-md.sh \
  sovereign/fleet-git-init-with-secrets-md.sh \
  sovereign/scripts/fleet-git-init-opt-agr.sh \
  sovereign/fleet-status-read-only.sh \
  sovereign/fleet-ci-post-verify.sh \
  sovereign/scripts/vault-kora-stagedir-init.sh \
  sovereign/scripts/fleet-vault-layout-remote-init.sh \
  sovereign/scripts/fleet-vault-rag-build-remote.sh \
  sovereign/scripts/fleet-llm-openai-smoke-remote.sh \
  sovereign/scripts/fleet-republic-chat-smoke-remote.sh \
  sovereign/scripts/fleet-guardian-secrets-remote-init.sh \
  sovereign/scripts/fleet-guardian-secrets-verify-remote.sh \
  sovereign/scripts/fleet-guardian-profile-from-secrets-md.sh \
  sovereign/scripts/handset-profile-from-secrets-md-termux.sh \
  sovereign/scripts/fleet-bash-syntax-check.sh \
  sovereign/scripts/fleet-ci-post-verify-guardian-warn.py \
  sovereign/scripts/fleet-vault-verify-remote.sh \
  sovereign/scripts/fleet-merge-gate-constitutional-tower-smoke-remote.sh \
  sovereign/scripts/fleet-republic-hard-restart.sh \
  sovereign/scripts/fleet-install-agr-republic-unit.sh \
  sovereign/scripts/fleet-vault-kora-rsync.sh \
  sovereign/scripts/print-phase-g-operator-commands.sh \
  sovereign/lib/termux-ssh-host-from-secrets-md.sh \
  sovereign/lib/termux-ssh-repo-dir-from-secrets-md.sh \
  sovereign/lib/termux-bridge-key-path.sh \
  sovereign/lib/termux-fleet-jump-host-from-secrets-md.sh \
  sovereign/lib/termux-fleet-tunnel-pubkey-from-secrets-md.sh \
  sovereign/lib/termux-reverse-tunnel-port-from-secrets-md.sh \
  sovereign/lib/termux-ssh-user-from-secrets-md.sh \
  sovereign/scripts/termux-append-fleet-bridge-vault.sh \
  sovereign/scripts/termux-fleet-tunnel-keygen.sh \
  sovereign/scripts/termux-operator-return-one-paste.sh \
  sovereign/scripts/fleet-append-termux-tunnel-pubkey.sh \
  sovereign/scripts/termux-remote-ssh.sh \
  sovereign/scripts/termux-remote-git-pull.sh \
  sovereign/scripts/termux-remote-origin-sweep.sh \
  sovereign/scripts/termux-remote-ssh-via-fleet-jump.sh \
  sovereign/scripts/termux-reverse-ssh-to-fleet.sh \
  sovereign/scripts/termux-remote-git-pull-via-fleet-jump.sh \
  sovereign/scripts/termux-remote-origin-sweep-via-fleet-jump.sh \
  sovereign/scripts/mint_cloudflare_tunnel_token_stdout.py \
  sovereign/scripts/termux-republic-one-shot-bootstrap.sh \
  sovereign/scripts/termux-phone-one-shot-recover.sh \
  sovereign/scripts/agent-sync-origin-main.sh \
  sovereign/scripts/workspace-autonomous-fleet-tower-verify.sh \
  sovereign/scripts/termux-boot-republic-example.sh \
  sovereign/scripts/verify-agent-progress-guardian-node.py \
  agr_start_wrapper.sh \
  sovereign/scripts/install-git-hooks.sh \
  sovereign/scripts/agr-builder-worktree-init.sh \
  sovereign/scripts/agr-builder-worktree-remove.sh \
  sovereign/scripts/agr-launch-readiness-tower-smoke.sh \
  sovereign/scripts/run-operator-full-verify.sh \
  sovereign/scripts/tower1-origin-probe.sh \
  sovereign/scripts/operator-next-steps-fleet-tower.sh \
  sovereign/scripts/agr_autonomous_merge_gate.py \
  sovereign/fleet-verify-public-http.sh \
  sovereign/indexnow-submit-sitemap.sh

if [[ "${FLEET_CI_POST_VERIFY_SKIP_BASH_N:-0}" != "1" ]]; then
  bash sovereign/scripts/fleet-bash-syntax-check.sh
fi

if [[ "${FLEET_CI_POST_VERIFY_LAUNCH_READINESS:-}" == "1" ]]; then
  export AGR_LAUNCH_READINESS_RUN_TOWER1_BASH="${AGR_LAUNCH_READINESS_RUN_TOWER1_BASH:-0}"
  bash "${ROOT}/sovereign/scripts/agr-launch-readiness-tower-smoke.sh"
fi

python3 sovereign/scripts/verify-agent-progress-guardian-node.py
if [[ "${FLEET_CI_POST_VERIFY_SKIP_REMOTE_SSH:-0}" == "1" ]]; then
  echo "[fleet-ci-post-verify] remote SSH steps skipped (FLEET_CI_POST_VERIFY_SKIP_REMOTE_SSH=1)"
  exit 0
fi
bash sovereign/scripts/fleet-vault-verify-remote.sh
bash sovereign/scripts/fleet-guardian-secrets-verify-remote.sh
echo "--- fleet-status (json) ---"
STAT_JSON="$(FLEET_STATUS_FORMAT=json bash sovereign/fleet-status-read-only.sh)"
echo "${STAT_JSON}"
if [[ "${FLEET_CI_POST_VERIFY_GUARDIAN_WARN:-1}" != "0" ]]; then
  echo "${STAT_JSON}" | python3 "${ROOT}/sovereign/scripts/fleet-ci-post-verify-guardian-warn.py"
fi
