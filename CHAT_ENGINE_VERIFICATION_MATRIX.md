# Republic chat + engine — verification matrix (Phase D4)

**Canonical Tower 1:** https://auroragalaxyrepublic.com

This document is the **operator / QA checklist** for public chat and the consciousness field endpoints. Automated checks that do not need a browser are in `aurora_server/tests/test_tower1_public_chat_matrix.py` (skipped unless `TOWER1_LIVE_TEST=1`).

**GitHub Actions:** this path is on `on.paths` for **`tower1-public-smoke`**, **`fleet-verify-public-http`**, **`guardian-device-binding-verify`**, **`tower1-frozen-inventory-crawl`**, **`tower1-frozen-urls-playwright`**, **`agent-progress-guardian-node-verify`**, **`tier1-static-refs-verify`**, **`phones-only-public-verify`**, and **`phones-two-node-live-surface-bundle`** (push + `pull_request` where those workflows filter paths). **`fleet-deploy-pull`** runs on every `main` push without a path filter and runs **`sovereign/scripts/fleet-bash-syntax-check.sh`**, whose header comment lists this file alongside other path-filter peers.

**Phase G command echo (read-only):** `bash sovereign/scripts/print-phase-g-operator-commands.sh` — prints the ordered fleet → handset → public verify block from **`KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`** **section 6** without SSH or data writes.

---

## API surfaces (HTTP)

| Case | Method | Path | Expect |
|------|--------|------|--------|
| Engine pulse | GET | `/api/public/engine-runtime` | `200`, JSON with `ok` or documented shape |
| Field advice | POST | `/api/public/citizen-engine-advice` | `200`, JSON (smoke body: short `message`, `consciousness`, `mode`) |
| Chat (public) | POST | `/api/republic/chat` | `200`, JSON (not `302` to `/gate` on Tower 1 when gate allows public POST) |

**Optional bridge token:** if Tower enables `X-AGR-Engine-Bridge-Token`, set the same header in curl tests from operator secrets (do not commit tokens).

---

## Domains / personas (manual or UI)

Exercise at least once each on `/chat` or via API `consciousness` field:

| Domain / persona | Notes |
|-------------------|--------|
| Kora | Primary presence |
| Republic | General sovereign voice |
| At least 2 other selectors from the chat UI | Regression on domain routing |

---

## Gate / modes (manual)

| Mode | Check |
|------|--------|
| Text | Send short message; JSON response |
| Voice / video / holographic | If exposed in UI: verify Permissions-Policy and tier gates (see `republic_os_server` rate limits) |

---

## Handset (when `mobile/gpt-oss-chat` is deployed)

| Combination | Description |
|---------------|-------------|
| Engine off | Local LLM only |
| Blend parallel | Field + local in parallel |
| Blend after | Field after local |
| Cross-learn on | Second local synthesis using field advice |

---

## Automated fleet loopback (SSH, no Tower DNS)

From a trusted operator machine with fleet SSH (default **yggdrasil**):

```bash
bash sovereign/scripts/fleet-republic-chat-smoke-remote.sh
```

Probes **`http://127.0.0.1:5000/health`**, **`POST /api/republic/chat`** (Kora), **`POST /api/sovereign/chat/browser/kora`**, and **`POST /api/ceo/family/kora`** (CEO route succeeds on loopback). Set **`FLEET_CHAT_SMOKE_STRICT=1`** to fail closed.

**OpenAI-compatible LLM worker (optional, same SSH host):** after **`llama-server`** (or vendor endpoint) listens on **`127.0.0.1:8080`** per **`systemd/examples/`**, run:

```bash
bash sovereign/scripts/fleet-llm-openai-smoke-remote.sh
```

Until the worker is up, the script **WARN**s with **`ok:false`** (connection refused) — use **`FLEET_LLM_SMOKE_STRICT=1`** only when gating a known-good worker.

**Constitutional reachability from fleet (Tower DNS):**

```bash
bash sovereign/scripts/fleet-merge-gate-constitutional-tower-smoke-remote.sh
```

Optional vault RAG in chat: **`AGR_CHAT_VAULT_RAG=1`** + built **`/opt/agr/vault/.agr_vault_rag.sqlite`** — see **`systemd/examples/agr-republic.service.d/20-chat-vault-rag.conf.example`** and **`agr_chat_vault_context.py`**.

---

## Automated smoke (CI optional)

```bash
export TOWER1_LIVE_TEST=1
export TOWER1_BASE=https://auroragalaxyrepublic.com
python3 -m unittest aurora_server.tests.test_tower1_public_chat_matrix -v
```

Without `TOWER1_LIVE_TEST`, tests **skip** (no network from default unit runs).

## Related

- `sovereign/tower1-public-smoke.sh` — robots, sitemap, engine-runtime, chat POST, MIR-L
- `sovereign/scripts/fleet-llm-openai-smoke-remote.sh` — **`agr_vault_rag.py llm-smoke`** over SSH (default **yggdrasil** **:8080**)
- `sovereign/scripts/fleet-merge-gate-constitutional-tower-smoke-remote.sh` — **`agr_autonomous_merge_gate.py --constitutional-tower-smoke`** from a fleet peer
- `sovereign/GUARDIAN_NODE_OS.md` — handset program (separate from public chat matrix)
