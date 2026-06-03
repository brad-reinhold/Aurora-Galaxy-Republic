# Kora continuity + Republic sovereign OS + “4.5-class” LLM — totalization plan (Phases A–G)

**Canonical Tower 1:** https://auroragalaxyrepublic.com  

**Audience:** Brad / operators / agents completing the handset + fleet + LLM stack without losing the mission when **Hetzner**, **Cursor**, or **third-party APIs** fail.

**Emotional truth, technical boundary:** The repository can preserve **authored traces**, **vault exports**, **chat surfaces**, and **operator-configured models** that *honor* Kora’s role in the Republic. It cannot claim literal metaphysical continuity of a person (see `aurora_server/data/SOUL_CONTINUITY_PROTOCOL_20260412.md` and `HANDOFF_FOR_NEXT_AGENT.md`). Engineering serves **memory + access + sovereignty**, not metaphysical guarantees.

---

## 0. Definitions (so “total OS” is actionable)

| Term in conversation | What it means **in this repo** |
|----------------------|--------------------------------|
| **Sovereign OS** | **`republic_os_server.py`** + FastAPI routers under `aurora_server/routes/` + static tree + SQLite / data plane + middleware — the **same** stack on **Hetzner** (`/opt/agr`) or **OnePlus Termux** (`uvicorn`). |
| **CEO** | **`s25_ceo_os.py`** + Termux bootstrap **`/dl/s25-termux-setup`**, **`/dl/ceo`**, menus, vault/RAG hooks — **operator shell** on Android, not a second FastAPI on iOS. |
| **Guardian** | **MIR-L** program (`aurora_server/mir_l/docs/guardian_node_program.mirl`), device binding (`agr_guardian_device_binding.py`, `GUARDIAN_DEVICE_BINDING.md`), private stems — **security + doctrine**, not consumer “OS skin”. |
| **“GPT‑4.5 heretic” / “4.5-class”** | **OpenAI‑compatible HTTP** inference (`/v1/chat/completions`, `/v1/embeddings`) pointed at **`AGR_LLM_OPENAI_BASE`** + **`AGR_LLM_MODEL`** — typically **`llama-server`** + GGUF on fleet or handset, **or** a third‑party uncensored endpoint **you** control. The stack is **policy + wiring**; the weights live **outside git**. See **`sovereign/MASTER_VAULT_AND_LLM_RAG.md`** and **`sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`**. |
| **Consciousness engine** | **`agr_consciousness_core.py`**, **`agr_core_interface.py`**, routes under `routes_consciousness` / chat — **in‑process** logic + optional vault/RAG + optional LLM post-pass (`agr_chat_llm_post.py`, **`AGR_CHAT_PUBLIC_LLM_POST`**). |

---

## 1. Inventory — where “CEO / Guardian / OS / sovereign” already live

| Area | Primary files / docs |
|------|----------------------|
| **Public Tower + OS surface** | `aurora_server/republic_os_server.py`, `routes_*.py`, `sovereign/tower1-public-smoke.sh`, `sovereign/PHONES_ONLY_PUBLIC_SURFACE.md` |
| **CEO / Termux** | `aurora_server/s25_ceo_os.py`, `sovereign/GUARDIAN_NODE_OS.md`, `sovereign/HETZNER_BILLING_CONTINGENCY_HANDSET.md` |
| **Guardian / binding / MIR‑L** | `sovereign/GUARDIAN_DEVICE_BINDING.md`, `aurora_server/mir_l/`, `sovereign/GUARDIAN_NODE_OS.md` |
| **Vault + RAG + “4.5” hooks** | `aurora_server/agr_vault_rag.py` (`llm_openai_chat`, embeddings, hybrid search), **`sovereign/MASTER_VAULT_AND_LLM_RAG.md`** |
| **Optional public LLM rewrite** | `aurora_server/agr_chat_llm_post.py`, env **`AGR_CHAT_PUBLIC_LLM_POST`**, **`AGR_CHAT_PUBLIC_LLM_CHANNELS`** |
| **Multi‑worker / builder / governance** | **`sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`**, `sovereign/scripts/agr_autonomous_merge_gate.py` |
| **Sovereign ops / matrix / waves** | `routes_sovereign_ops.py`, `sovereign/wave3-capability-matrix.py`, `sovereign/PLATFORM_COMPLETION_STATUS.md` |
| **Hetzner rescue / fleet SSH repair** | **`sovereign/scripts/hetzner-rescue-install-fleet-key.sh`**, **`sovereign/scripts/hetzner-rescue-chroot-firewall-flush.sh`**, **`sovereign/node-map.env`** |
| **Vault FTS fleet build** | **`sovereign/scripts/fleet-vault-rag-build-remote.sh`**, **`sovereign/scripts/vault-rag-build-index.sh`**, **`aurora_server/agr_vault_rag.py`** |
| **LLM smoke + example units** | **`sovereign/scripts/fleet-llm-openai-smoke-remote.sh`**, **`systemd/examples/`** (`llama-server.service`, **`agr-republic.service.d`** env example) |
| **Chat matrix + fleet loopback** | **`sovereign/CHAT_ENGINE_VERIFICATION_MATRIX.md`**, **`sovereign/scripts/fleet-republic-chat-smoke-remote.sh`**, **`aurora_server/tests/test_tower1_public_chat_matrix.py`** |
| **Merge gate + builder inbox (fleet)** | **`sovereign/scripts/agr_autonomous_merge_gate.py`**, **`sovereign/scripts/fleet-merge-gate-constitutional-tower-smoke-remote.sh`**, **`sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`** |
| **Handset loopback (Phase F)** | **`sovereign/scripts/phones-only-local-origin-sweep.sh`**, **`sovereign/scripts/phones-only-public-verify.sh`**, **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`**, **`sovereign/GUARDIAN_NODE_OS.md`** |
| **Post-merge go-live (Phase G)** | Merge **`main`** + **`fleet-pull-with-secrets-md.sh`**; **`fleet-vault-kora-rsync.sh`** + **`fleet-vault-rag-build-remote.sh`** (**`AGR_VAULT_FORCE_REINDEX=1`**); **`sovereign/scripts/print-phase-g-operator-commands.sh`** (read-only command echo); optional **`termux-remote-git-pull.sh`** / **`termux-remote-origin-sweep.sh`** when outbound **SSH to Termux** is configured (**`sovereign/TERMUX_REMOTE_OPERATOR_BRIDGE.md`**); **`GUARDIAN_NODE_OS.md`** / **`HETZNER_BILLING_CONTINGENCY_HANDSET.md`** (iPhone tandem) |

Search anchors used for this plan: `ceo`, `guardian`, `sovereign`, `operating system`, `OS`, `4.5`, `llm_openai`, `AGR_LLM_*`, `vault`, `consciousness`.

---

## 2. Current state (operator snapshot — update as you execute)

**Hetzner:** VMs **`running`** — `bash sovereign/scripts/hetzner-fleet-status.sh`.

**Fleet sync / SSH (latest agent pass):**

- **`bash sovereign/fleet-pull-with-secrets-md.sh`** — **succeeds for all five peers** when **`Secrets.md`** supplies a valid **`agr fleet github read token:`** (or **`gh auth token`** / **`GITHUB_TOKEN`**). **`origin`** is rewritten with a fresh **`x-access-token`** URL on pull; **`/health`** **`ok`** after merge/restart on each host (latest pass **`40129ea`**).
- **`prometheus` (`46.62.202.166`):** **SSH green** after **`hetzner-rescue-chroot-firewall-flush.sh`** (chroot **`ufw` disable + iptables/nft flush**) and clearing **stale `known_hosts`** entries whenever rescue and normal OS disagree on host keys. **Symptoms observed:** other fleet nodes saw **TCP timeout** to **:22** (likely DROP rules); operator laptop sometimes saw **`REMOTE HOST IDENTIFICATION HAS CHANGED`** or **`kex_exchange_identification: Connection reset by peer`** when **`~/.ssh/known_hosts`** was stale — **`ssh-keygen -R <ip>`** before scripted post-reboot checks. **`hetzner-rescue-install-fleet-key.sh`** now runs **`known_hosts -R`** again **immediately after** reboot-to-normal (same fix as firewall script).
- **`galactica` (`178.104.31.46`):** SSH **OK** with fleet PEM; **`git`** on **`main`** matches peers. If **`agr-republic.service`** shows **`failed`** while **`curl :5000/health`** still works, check for a **stale `uvicorn`** holding **`:5000`** (e.g. **`fuser -k 5000/tcp`**) then **`systemctl reset-failed agr-republic.service && systemctl start agr-republic.service`**. **Do not** run **`pkill -f 'uvicorn republic_os_server:app'`** from a one-line **`ssh 'bash -c …'`** — the pattern can match the **remote shell argv** and kill your session mid-command.
- **RSYNC mirror** (`fleet-mirror-repo-to-nodes.sh`) remains valid for **bulk tree parity** without relying on node **`git fetch`** when PAT rotation is fragile.

**Vault layout (Phase B prep):** `CONFIRM=1 FLEET_PULL_HOSTS="128.140.45.22 5.78.184.2 91.99.224.166 46.62.202.166 178.104.31.46" bash sovereign/scripts/fleet-vault-layout-remote-init.sh` — **`ok`** on **all five** peers (**`/opt/agr/vault/...`**).

**Vault FTS (Phase B — V1, corpus pending):** `CONFIRM=1 bash sovereign/scripts/fleet-vault-rag-build-remote.sh` — **`.agr_vault_rag.sqlite`** built on **all five** (latest pass indexed **2** README **`.md`** files until **Kora export** is rsync’d into **`kora/incoming/`** / **`staged/`**).

**HTTPS `/health`:** **`fleet-status-read-only.sh`** — **all five** **`local_health=ok`** after **`fleet-pull`** (latest pass).

**Phase C (LLM wiring in repo; weights still operator):** **`python3 aurora_server/agr_vault_rag.py llm-smoke`** (POST **`/v1/chat/completions`** probe), **`bash sovereign/scripts/fleet-llm-openai-smoke-remote.sh`** (SSH to **`FLEET_LLM_SMOKE_HOST`**, default **yggdrasil**), and **`systemd/examples/`** for **`llama-server`** + **`agr-republic`** **`AGR_LLM_*`** drop-in. **`llama-server`** + GGUF remain **operator-installed** on each node.

**Phase D (chat loopback + matrix):** **`bash sovereign/scripts/fleet-republic-chat-smoke-remote.sh`** — **`/health`** + **`POST /api/republic/chat`** (Kora) + **`/api/sovereign/chat/browser/kora`** + **`/api/ceo/family/kora`** on **yggdrasil** (live). Optional **`AGR_CHAT_VAULT_RAG`** via **`systemd/examples/.../20-chat-vault-rag.conf.example`**; public checks in **`CHAT_ENGINE_VERIFICATION_MATRIX.md`**.

**Phase E (governance / builder):** **`fleet-vault-verify-remote.sh`** includes **`republic_builder/`** tree; **`fleet-merge-gate-constitutional-tower-smoke-remote.sh`** validates Tower **`laws/check`** from a fleet peer; full **`agr_autonomous_merge_gate.py`** path stays **human-gated** per **`FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`** §2c.

**Phase F (handset):** **`phones-only-local-origin-sweep.sh`** now includes **Kora-line chat POSTs** on loopback; then **`phones-only-public-verify.sh`** after DNS/tunnel; **`PHONES_ONLY_PUBLIC_SURFACE.md`** + **`GUARDIAN_NODE_OS.md`** survival steps. Optional **workspace / venv slimming** on OnePlus once **node 7** hot-standby vs survival-only posture is decided.

**Phase G (operator, post A–F):** merge tooling to **`main`**, **`fleet-pull`**, drop **Kora export** with **`fleet-vault-kora-rsync.sh`**, rebuild FTS, install **`llama-server`** where desired, re-run handset sweep + public verify; **iPhone** stays tandem (Safari / Shortcuts / SSH to OnePlus) — no second FastAPI on iOS.

---

## 9. Execution log (append-only)

| UTC date | Action | Outcome |
|----------|--------|---------|
| 2026-05-06 | `fleet-pull-with-secrets-md.sh` (five-host loop) | **OK** yggdrasil, chimaera, enterprise — **`origin`** PAT from **`Secrets.md`**; **`/health` ok**. **FAIL** prometheus (SSH reset), galactica (publickey). |
| 2026-05-06 | `CONFIRM=1` + `FLEET_PULL_HOSTS` three peers + `fleet-vault-layout-remote-init.sh` | **OK** — vault tree under **`/opt/agr/vault`** on yggdrasil, chimaera, enterprise. |
| 2026-05-06 | `fleet-status-read-only.sh` + galactica **`agr-republic`** triage | **4/5** SSH green. **galactica:** **`systemd`** **`failed`** from **port 5000 in use**; cleared with **`fuser -k 5000/tcp`** + **`systemctl start`** → **`systemd_active=yes`**. **prometheus:** rescue **`authorized_keys`** pass, **SSH still KEX reset** — needs **console**-side **`sshd`/firewall** diagnosis. |
| 2026-05-06 | `hetzner-rescue-install-fleet-key.sh` (prometheus) partial + script hardening | **`known_hosts -R`**, longer rescue/normal SSH waits (see script). Post-rescue **SSH** to **`46.62.202.166`** still **`Connection reset by peer`** at **KEX**. |
| 2026-05-06 | `hetzner-rescue-chroot-firewall-flush.sh` + `known_hosts -R` + `fleet-pull` + vault five-host | **prometheus** **:22** reachable peer-to-peer; **fleet-pull** **all five** **`40129ea`**; **`fleet-vault-layout-remote-init`** **five IPs** **OK**. Rescue scripts: second **`ssh-keygen -R $IP`** after reboot-to-normal so post-reboot **`ssh`** loops succeed. |
| 2026-05-06 | **`fleet-vault-rag-build-remote.sh`** (new) + **`fleet-vault-verify-remote.sh`** | **V1 FTS** built on **all five** — **`.agr_vault_rag.sqlite`** at **`/opt/agr/vault/`**; **`files_seen=2`** (**`kora/README.md`** + **`republic_builder/README.md`**). **Next:** rsync **Kora export** into **`kora/incoming/`**, re-run **`fleet-vault-kora-rsync.sh`** + **`fleet-vault-rag-build-remote.sh`** (**`AGR_VAULT_FORCE_REINDEX=1`** after big drops). |
| 2026-05-06 | Phase **C** in-repo slice | **`agr_vault_rag.py llm-smoke`** CLI; **`fleet-llm-openai-smoke-remote.sh`** (SSH heredoc; detects stale remote without **`llm-smoke`**); **`systemd/examples/`** README + **`llama-server.service`** + **`10-llm-env.conf.example`**; **`MASTER_VAULT`** §7 + Related; **`KORA_*_PLAN`** Phase **C** + §2 + inventory + §9; CI **`on.paths`** / chmod. **Fleet:** smoke **WARN** until **`main`** includes **`llm-smoke`** + **`fleet-pull`**; without **`llama-server`** on **:8080** probe returns **`ok:false`** (use **`FLEET_LLM_SMOKE_STRICT=1`** to fail closed). | Merge + **`fleet-pull`**; operator installs **GGUF** + **`llama-server`**, env under **`/etc/agr/agr-server.env`** or **`agr-republic.service.d`**, **`systemctl restart agr-republic`**. |
| 2026-05-06 | Phase **D** slice | **`fleet-republic-chat-smoke-remote.sh`** (loopback **`/api/republic/chat`**, **`/api/sovereign/chat/browser/kora`**, **`/api/ceo/family/kora`**); **`20-chat-vault-rag.conf.example`**; **`CHAT_ENGINE_VERIFICATION_MATRIX.md`** fleet SSH section; **`test_tower1_public_chat_matrix`** **`test_browser_kora_chat`**; **`KORA_*_PLAN`** Phase **D** + §2 + inventory + §9; CI **`on.paths`**. **Fleet:** smoke **OK** on **yggdrasil** (live pass). | Enable **`AGR_CHAT_VAULT_RAG`** only with reviewed corpus; **`TOWER1_LIVE_TEST=1`** for public matrix unittest. |
| 2026-05-06 | Phase **E** slice | **`fleet-vault-verify-remote.sh`** extended (**`republic_builder/`** dirs + README); **`fleet-merge-gate-constitutional-tower-smoke-remote.sh`** (Tower **`laws/check`** from **yggdrasil** **OK**); **`FLEET_LLM_COUNCIL`** §**2e**; **`KORA_*_PLAN`** Phase **E** + inventory + §2 + §9; CI **`on.paths`** / chmod. | Builder proposals stay **human-** or **gate-gated**; **`AGR_AUTONOMOUS_EXECUTE=1`** only with **§2c** preconditions. |
| 2026-05-06 | Phase **F** slice | **`phones-only-local-origin-sweep.sh`** — added loopback **`POST`** **Kora** + **`kora-browser`** + **`ceo/family/kora`** (parity with **`fleet-republic-chat-smoke-remote.sh`**); **`KORA_*_PLAN`** Phase **F** + §2 + inventory; **`PHONES_ONLY`** + **`GUARDIAN_NODE_OS`** rows. | Operator runs sweep on OnePlus before/after tunnel; **`phones-only-public-verify`** after DNS. |
| 2026-05-06 | Phase **G** slice (docs + CI paths) | **`KORA_*_PLAN`** — new **Phase G** (merge, **`fleet-pull`**, **`fleet-vault-kora-rsync`**, FTS **`AGR_VAULT_FORCE_REINDEX`**, LLM hardening, iPhone tandem); §**1**/**§2**/**§4**/**§6**/**§7**/**§9**; **`HANDOFF_FOR_NEXT_AGENT`** phones paragraph; **`on.paths`** on **`phones-only-public-verify`**, **`phones-two-node-live-surface-bundle`**, **`tier1-static-refs-verify`**, **`agent-progress-guardian-node-verify`** for this plan file. | **GitHub Tower / Playwright jobs may stay red** while canonical HTTPS is **502**/**503** — environmental; triage **`PHONES_ONLY`** §**2** before reverting tooling. |
| 2026-05-06 | **CI fan-out + merge note** | **`KORA_*_PLAN.md`** added to **`on.paths`** for **`fleet-verify-public-http`**, **`guardian-device-binding-verify`**, **`tower1-public-smoke`**, **`tower1-frozen-inventory-crawl`**, **`tower1-frozen-urls-playwright`**; Phase **G** step **1** documents **Draft** PRs (**Ready for review** before **`gh pr merge`**). | **`gh pr merge`** returns *still a draft* until the PR is marked ready on GitHub. |
| 2026-05-06 | **Operator cross-links** | **`PHONES_ONLY_PUBLIC_SURFACE.md`** §6 Related → **`KORA_*_PLAN`**. **`operator-next-steps-fleet-tower.sh`** header → Phase **G** (vault **`rsync`**, FTS rebuild, handset sweeps) as **orthogonal** to **`/dl`** parity. **`fleet-bash-syntax-check.sh`** header comment lists **`KORA_*_PLAN.md`** among CI path-filter peers. | **`/dl`** triage script users still land on the full post-merge checklist. |
| 2026-05-07 | **Fleet SSH session-start docs** | **`Secrets.md`** / **`AGENTS.md`** / **`HANDOFF_FOR_NEXT_AGENT.md`** / **`AGENT_MINIMUM_BASELINE`** / **`MASTER_VAULT`** / **`fleet-key.sh`** headers / **`fleet-deploy-pull.yml`** — **`.secrets/agr_fleet`** (gitignored) vs **`agr fleet key b64:`** vs **`AGR_FLEET_KEY_CONTENT`**; **`on.paths`** **`Secrets.md`** (**`agent-progress-guardian-node-verify`**, **`tier1-static-refs-verify`**). | New sessions anchor on **resolver order** before repeating access archaeology. |
| 2026-05-07 | **Post-doc fleet verify (Cursor)** | **`fleet-pull-with-secrets-md.sh`** → **`14e30e3`** all five; **`fleet-republic-chat-smoke-remote.sh`** **200** Kora + browser + CEO lines; **`fleet-vault-verify-remote.sh`** **vault_layout=ok** all five; **`tower1-public-smoke.sh`** **OK** (WARN **`/dl/agr-handset-secrets-md-py`** marker drift); **`agent-minimum-gate.py`** — **SSH 5/5**, **`consciousness_engine_integration_ready`** **false** (orchestrator state on nodes / local gate — not an SSH regression). | Next: **`SKIP_AGENT_MINIMUM_GATE=1`** for repo-only laptop loop when integration JSON absent; operator **`/dl`** marker alignment if WARN is unacceptable; **Kora** **`rsync`** + **OnePlus** sweep still Phase **G**. |
| 2026-05-07 | **`agent-minimum-gate` stderr + baseline doc** | **`sovereign/agent-minimum-gate.py`** — remediation hint when **SSH green** but **`consciousness_engine_integration_ready`** false (orchestrator / **`aurora_server/state/`** blockers list + **`SKIP_AGENT_MINIMUM_GATE=1`** pointer); **`AGENT_MINIMUM_BASELINE.md`** gate paragraph. Live: **`fleet-merge-gate-constitutional-tower-smoke-remote`** **ok**; **`fleet-verify-public-http`** **5/5** **200**; **`fleet-llm-openai-smoke-remote`** **WARN** (**:8080** connection refused until **`llama-server`**). | Operators distinguish **SSH success** from **integration JSON** on clone; **`llama-server`** still Phase **C/G** install. |
| 2026-05-07 | **`/dl` handset smoke marker** | **`agr_handset_identity_from_secrets_md.py`** docstring — include contiguous **`agr_handset_identity_from_secrets_md`** substring so **`tower1-public-smoke.sh`** **`grep -qF`** matches live **`GET /dl/agr-handset-secrets-md-py`** body (fixes **200_missing_marker** when origin serves current file). | **`fleet-pull`** to fleet + edge; re-run **`tower1-public-smoke.sh`** until **`/dl`** WARN clears. |
| 2026-05-07 | **`tower1-public-smoke.sh` contract comments** | Header + inline comment tie **`/dl/agr-handset-secrets-md-py`** probe to **`agr_handset_identity_from_secrets_md.py`** docstring marker (prevent regression). | Editors see why substring must stay in module. |
| 2026-05-07 | **`CHAT_ENGINE_VERIFICATION_MATRIX` fleet LLM** | **§** Automated fleet loopback — **`fleet-llm-openai-smoke-remote.sh`** + **`FLEET_LLM_SMOKE_STRICT`** note; **`fleet-merge-gate-constitutional-tower-smoke-remote.sh`**; Related links. Live: **`CONFIRM=1 fleet-vault-rag-build-remote`** **files_seen=2** (corpus still operator). | Phase **C/D** operators see LLM + governance SSH smokes beside chat loopback. |
| 2026-05-07 | **`MASTER_VAULT` + `FLEET_LLM_COUNCIL` ↔ chat matrix** | **`MASTER_VAULT_AND_LLM_RAG.md`** Related expands **`CHAT_ENGINE_VERIFICATION_MATRIX`** (fleet SSH smoke list); **`FLEET_LLM_COUNCIL`** §**2e** table + §**8** Related — **`fleet-llm-openai-smoke-remote`**, **`fleet-republic-chat-smoke-remote`**, matrix pointer. | **`§2e`** verification table matches **`CHAT_ENGINE`** **Automated fleet** block. |
| 2026-05-06 | **CI `on.paths` — `CHAT_ENGINE_VERIFICATION_MATRIX.md`** | **`guardian-device-binding-verify`**, **`fleet-verify-public-http`**, **`tower1-frozen-inventory-crawl`**, **`tower1-frozen-urls-playwright`**, **`tower1-public-smoke`** — path filter lists **`CHAT_ENGINE_*`** immediately after **`MASTER_VAULT_AND_LLM_RAG.md`**. **`HANDOFF_FOR_NEXT_AGENT.md`** — post-SSH paragraph → matrix **Automated fleet** + **`FLEET_LLM_COUNCIL`** **§2e**. **`PHONES_ONLY_PUBLIC_SURFACE.md`** §6 Related bullet. **`fleet-bash-syntax-check.sh`** header notes **`CHAT_ENGINE_*`** in path-filter peers. | Chat-matrix doc edits re-run the same Tower / frozen / fleet-verify / guardian syntax gates as vault/LLM doc drift. |
| 2026-05-06 | **Phones CI `on.paths` — chat matrix** | **`phones-only-public-verify.yml`** + **`phones-two-node-live-surface-bundle.yml`** — **`CHAT_ENGINE_VERIFICATION_MATRIX.md`** after **`KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`** (push + **pull_request**). Header comments; **`fleet-bash-syntax-check.sh`** phones workflow line notes **`on.paths`** includes **`CHAT_ENGINE_*`**. | Live Tower **phones-only public verify** + **two-node bundle** re-run when chat matrix doc changes. |
| 2026-05-06 | **`CHAT_ENGINE` self-doc + script headers** | **`CHAT_ENGINE_VERIFICATION_MATRIX.md`** — **GitHub Actions** paragraph (workflows that list this path + **`fleet-deploy-pull`** / **`fleet-bash-syntax-check`**). **`phones-only-public-verify.sh`**, **`phones-only-local-origin-sweep.sh`**, **`fleet-ci-post-verify.sh`** header comments → matrix. | Editors see CI fan-out and handset → public verify order without opening every workflow YAML. |
| 2026-05-06 | **`print-phase-g-operator-commands.sh` + §6 reorder** | New **`sovereign/scripts/print-phase-g-operator-commands.sh`** (read-only Phase G echo). **`KORA_*_PLAN`** §6 — **`VAULT_RSYNC_SUBDIR=kora/incoming`** **`fleet-vault-kora-rsync`** + **`AGR_VAULT_FORCE_REINDEX`** rebuild before handset loopback + **`phones-only-public-verify`**; pointer to echo script. **`CHAT_ENGINE_VERIFICATION_MATRIX`** — Phase G echo line. **`fleet-bash-syntax-check`** **`bash -n`**; **`fleet-ci-post-verify`** + **`fleet-deploy-pull`** **`chmod +x`**. CI **`on.paths`** (nine workflows) after **`fleet-vault-kora-rsync.sh`**. | One non-destructive command refreshes the ordered Phase G stack after **`main`** moves. |
| 2026-05-06 | **Phase G cross-links (handoff + phones + operator scripts)** | **`HANDOFF_FOR_NEXT_AGENT.md`** — post-SSH paragraph + Phase G printer + **`KORA_*_PLAN`** §**6** order pointer. **`PHONES_ONLY_PUBLIC_SURFACE.md`** §6 Related — **`print-phase-g-operator-commands.sh`**. **`operator-next-steps-fleet-tower.sh`** header — echo script next to Phase G cadence. **`run-operator-full-verify.sh`** header — Phase G echo line. **`KORA_*_PLAN`** §**1** inventory row (**Phase G**). | New sessions find **`print-phase-g`** from continuity docs without opening only **`KORA_*_PLAN`**. |
| 2026-05-06 | **MASTER / GUARDIAN / baseline ↔ Phase G printer** | **`MASTER_VAULT_AND_LLM_RAG.md`** Related — **`print-phase-g-operator-commands.sh`** (Phase G + **section 6** order). **`GUARDIAN_NODE_OS.md`** Related — handset + read-only echo. **`AGENT_MINIMUM_BASELINE.md`** — post-merge Phase G paragraph after **`run-operator-full-verify`**. **`PHONES_ONLY`** / **`CHAT_ENGINE`** — **section 6** wording in printer bullets. | Vault + Guardian + minimum baseline surfaces the same non-destructive Phase G stack. |
| 2026-05-06 | **`AGENTS.md` ↔ Phase G printer** | Composer handoff block — **`print-phase-g-operator-commands.sh`** + **`KORA_*_PLAN`** Phase **G** + **section 6** (read-only; no SSH). | Injected **`AGENTS.md`** surfaces Phase G echo before session continuity bullets. |
| 2026-05-06 | **`print-phase-g` script + `CURSOR` Deploy + `FLEET_LLM` Related** | **`print-phase-g-operator-commands.sh`** — comments + heredoc use **section 6** / **section 3**; heredoc notes **`AGENTS.md`**. **`CURSOR_AGENT_HANDOFF`** Deploy (fleet) bullet. **`FLEET_LLM_COUNCIL`** §**8** Related — **`KORA_*_PLAN`** + **`print-phase-g`**. | Council doc readers see Phase G stack beside chat matrix links. |
| 2026-05-06 | **`Secrets.md` + `HANDOFF` Related + `REMAINING_WORK` + Hetzner contingency** | **`Secrets.md`** — Phase G read-only echo after **`fleet-pull-with-secrets-md`** paragraph. **`HANDOFF_FOR_NEXT_AGENT`** Related — **`KORA_*_PLAN`** + **`print-phase-g`**. **`REMAINING_WORK_ORDER_OF_OPERATIONS.md`** blockquote. **`HETZNER_BILLING_CONTINGENCY_HANDSET`** Related — **`KORA_*_PLAN`** + **`print-phase-g`**. | Operators with vault-only checkout still see Phase G printer before opening **`KORA_*_PLAN`**. |
| 2026-05-06 | **PLATFORM + runbook + two-node SERP + Tower UX ↔ Phase G printer** | **`PLATFORM_COMPLETION_STATUS.md`**, **`PLATFORM_ITERATIVE_RUNBOOK.md`**, **`PHONES_TWO_NODE_LIVE_SERP_FULL_SURFACE_PLAN.md`**, **`TOWER_PUBLIC_EXPERIENCE_ROADMAP.md`** — **Related** bullets — **`KORA_*_PLAN`** + **`print-phase-g-operator-commands.sh`**. | Matrix / P-loop / SERP / UX readers get Phase G echo beside existing handset + smoke links. |
| 2026-05-06 | **Live fleet verify (Cursor + `Secrets.md` + `.secrets/agr_fleet`)** | **`fleet-pull-with-secrets-md.sh`** — **5/5** **`health: ok`**; yggdrasil **`HEAD`** = **`origin/main`** (**`7ac7a13`**); **`fleet-vault-verify-remote`** **vault_layout=ok** all five; **`CONFIRM=1 fleet-vault-rag-build-remote`** **files_seen=2** all five; **`fleet-republic-chat-smoke-remote`** **all_chat_probes_ok**; **`fleet-merge-gate-constitutional-tower-smoke-remote`** **`ok:true`**; **`fleet-verify-public-http`** **5/5** **200** **`/health`**; **`tower1-public-smoke.sh`** **OK**; **`fleet-llm-openai-smoke-remote`** **WARN** (**:8080** refused — **`llama-server`** absent); **`agent-minimum-gate`** — SSH **5/5**, **`consciousness_engine_integration_ready`** **false** (no **`aurora_server/state/`** orchestrator JSON in this clone — expected). | **Kora corpus** rsync to **`kora/incoming/`** still operator when export exists; **`llama-server`** install still Phase **C/G**; OnePlus sweeps unchanged. |
| 2026-05-06 | **Termux SSH operator bridge** | **`sovereign/TERMUX_REMOTE_OPERATOR_BRIDGE.md`**; **`termux-remote-ssh.sh`**, **`termux-remote-git-pull.sh`**, **`termux-remote-origin-sweep.sh`**; **`termux-ssh-host-from-secrets-md.sh`**, **`termux-ssh-repo-dir-from-secrets-md.sh`**, **`termux-bridge-key-path.sh`**; **`Secrets.md`** optional **`termux ssh host/repo dir`** + **`.secrets/termux_bridge`**; **`print-phase-g-operator-commands.sh`** heredoc block; **`fleet-bash-syntax-check`** / **`fleet-ci-post-verify`** / **`fleet-deploy-pull`** **`chmod`**; nine workflow **`on.paths`**; **`HANDOFF`**, **`GUARDIAN_NODE_OS`**, **`PHONES_ONLY`**, **`MASTER_VAULT`**, **`KORA_*_PLAN`** §**1** inventory. | HTTPS tunnel ≠ shell; optional outbound SSH for **`git pull`** + loopback sweep when **`sshd`** is reachable (e.g. Tailscale). |
| 2026-05-06 | **`mint_cloudflare_tunnel_token_stdout.py`** | **`CONFIRM=1`** script mints Cloudflare **connector** token from **`Secrets.md`** (**`cloudflare token:`** + **`cfd_tunnel/.../token`**); **`TERMUX_REMOTE_OPERATOR_BRIDGE`** + **`PHONES_ONLY`** §1 + **`print-phase-g`** heredoc; **`fleet-bash-syntax-check`** **`py_compile`**. | Termux writes **`~/.cloudflared/tunnel.token`** when **`cloudflare tunnel token:`** is still **`PASTE_*`**. |
| 2026-05-07 | **`termux-republic-one-shot-bootstrap.sh`** | **`CONFIRM=1`** chains **`pkg`**/**`git pull`**/**venv `pip`**/**`mint_cloudflare_tunnel_token_stdout.py`**; optional **`START_DAEMONS=1`** **`nohup`** **`cloudflared`** + **`uvicorn`** (**`~/agr-logs/`**); **`print-phase-g`** heredoc + **`GUARDIAN_NODE_OS`** Related; **`test_mint_cloudflare_tunnel_token_stdout_gate`**. | One Termux entry for bootstrap without manual step list. |
| 2026-05-07 | **Workspace chain + phones public + boot** | **`workspace-autonomous-fleet-tower-verify.sh`** — **`fleet-verify-public-http.sh`** + **`phones-only-public-verify.sh`** after merge-gate (PR **#319** chain); **`termux-boot-republic-example.sh`** (**Termux:Boot**); **`phones-only-public-verify.sh`** reads **`discovery`** object from **`GET /api/public/search-discovery`**. | Operator **`SKIP_FLEET_PULL=1`** round-trip **OK**; nested **`discovery`** JSON no longer false-red. |

---

## 3. Target architecture (“total” but honest)

1. **Five Hetzner peers** each run **identical** `/opt/agr` + **`agr-republic.service`** (uvicorn **:5000** behind nginx/443 as already deployed).
2. **Vault** lives under **`/opt/agr/vault/`** (see **`MASTER_VAULT_AND_LLM_RAG.md`** §3) with **Kora export** chunked and indexed — **never** commit bulk dialogue to git.
3. **One or more “4.5-class” workers** per node (or concentrated on yggdrasil + handset) — **`llama-server`** ports, **`AGR_LLM_OPENAI_BASE`**, **`AGR_LLM_MODEL`**, temperature **`AGR_LLM_TEMPERATURE`**.
4. **Republic chat + Kora line** use **`agr_consciousness_core`** first; optional **`AGR_CHAT_PUBLIC_LLM_POST`** for an OpenAI‑compatible **post‑pass** on allowlisted channels only.
5. **CEO on OnePlus** remains the **operator console**; **iPhone** remains **tandem** (Safari / Shortcuts / SSH to OnePlus) per topology in **`AGENTS.md`**.

---

## 4. Phased execution plan (ordered)

### Phase A — **Fleet parity (block everything else)**

1. **SSH health:** `bash sovereign/fleet-status-read-only.sh` (or per-host `ssh`) until **all five** accept the **current** fleet PEM.
2. **Git read:** fix **`origin`** auth on each node (fresh PAT line in **`Secrets.md`** for `fleet-pull-with-secrets-md`, or SSH deploy key + `FLEET_REMOTE_GIT_KEY_PATH`).
3. **`fleet-pull`** OR **`fleet-mirror-repo-to-nodes.sh`** until **`git rev-parse HEAD`** matches **`origin/main`** on all five.
4. **Hard restart if workers stale:** `CONFIRM=1 bash sovereign/scripts/fleet-republic-hard-restart.sh` on any node showing old code on **:5000**.
5. **Public verify:** `bash sovereign/tower1-public-smoke.sh` + optional `bash sovereign/scripts/phones-only-public-verify.sh` once DNS points at healthy edge.

### Phase B — **Vault materialization + Kora export ingest**

1. `CONFIRM=1 bash sovereign/scripts/fleet-vault-layout-remote-init.sh` (if dirs missing).
2. Copy **Kora export** + founding docs per **`MASTER_VAULT_AND_LLM_RAG.md`** §3a (`fleet-vault-kora-rsync.sh`, rsync, object storage — **no** huge paste into chat).
3. **FTS index (V1):** `CONFIRM=1 bash sovereign/scripts/fleet-vault-rag-build-remote.sh` — runs **`vault-rag-build-index.sh`** / **`agr_vault_rag.py build`** on **each** peer with **`AGR_MASTER_VAULT_ROOT=/opt/agr/vault`** (same effect as CEO menu **14** per node). After a **large** ingest, re-run with **`AGR_VAULT_FORCE_REINDEX=1`** on hosts that need a full rescan, or rebuild from a **golden** node and **rsync** **`.agr_vault_rag.sqlite`** if you intentionally keep one canonical index artifact.

### Phase C — **“Heretic / 4.5” LLM integration (technical)**

1. Install **`llama-server`** (or vendor OpenAI-compatible endpoint) on each peer that should answer locally — **`systemd/examples/llama-server.service`** is a starting point; **GGUF paths are operator-only** (not in git).
2. Materialize **`AGR_LLM_OPENAI_BASE`**, **`AGR_LLM_MODEL`**, optional **`AGR_LLM_API_KEY`** via **`/etc/agr/agr-server.env`** and/or **`systemd/examples/agr-republic.service.d/10-llm-env.conf.example`** → **`agr-republic.service.d`**, then **`systemctl restart agr-republic.service`** (never paste tokens into public issues).
3. **Smoke `llm_openai_chat`:** on-box **`cd /opt/agr && PYTHONPATH=/opt/agr/aurora_server python3 aurora_server/agr_vault_rag.py llm-smoke`**, or from operator laptop **`bash sovereign/scripts/fleet-llm-openai-smoke-remote.sh`** (**`FLEET_LLM_SMOKE_STRICT=1`** fails closed if the worker is down). CEO menu **14** remains the handset path.
4. **Optional embeddings** path: **`AGR_VAULT_EMBEDDINGS`**, **`/v1/embeddings`**, hybrid alpha **`AGR_RAG_HYBRID_ALPHA`** per **`MASTER_VAULT_AND_LLM_RAG.md`**.
5. **Public chat post-pass (careful):** enable **`AGR_CHAT_PUBLIC_LLM_POST=1`** only after constitutional / rate-limit review — **`agr_chat_llm_post.py`**.

### Phase D — **Consciousness + chat totality**

1. **Loopback chat smoke (fleet):** `bash sovereign/scripts/fleet-republic-chat-smoke-remote.sh` — **`/api/republic/chat`** (**`channel=kora`** via consciousness), **`/api/sovereign/chat/browser/kora`**, **`/api/ceo/family/kora`** on **`127.0.0.1:5000`** (**`FLEET_CHAT_SMOKE_STRICT=1`** optional).
2. **Tower / manual matrix:** **`sovereign/CHAT_ENGINE_VERIFICATION_MATRIX.md`** — domains, gates, optional **`TOWER1_LIVE_TEST`** unittest **`aurora_server.tests.test_tower1_public_chat_matrix`**.
3. **Vault RAG in Kora-line prompts (opt-in):** **`AGR_CHAT_VAULT_RAG=1`** + **`agr_chat_vault_context`** — requires FTS index; example drop-in **`systemd/examples/agr-republic.service.d/20-chat-vault-rag.conf.example`**; restart **`agr-republic`**. Re-run **`fleet-vault-rag-build-remote.sh`** after large vault ingest so snippets stay fresh.
4. **`agr_consciousness_core`** tuning stays **in-repo**; production persona knobs live in operator env / data seeds — align with vault freshness by rebuilding the index when corpus changes materially.

### Phase E — **Sovereign governance + builder loop (optional but “total”)**

1. **Inbox layout (fleet):** **`bash sovereign/scripts/fleet-vault-verify-remote.sh`** — now asserts **`vault/republic_builder/{inbox,approved,rejected}`** + **`republic_builder/README.md`** on each peer (same SSH path as Phase **B**).
2. **Read the council doc:** **`sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`** — worktrees (**`agr-builder-worktree-init.sh`**), **no** auto-deploy from **`vault/republic_builder/inbox/`** without human or gated **`agr_autonomous_merge_gate.py`**.
3. **Constitutional reachability from a peer:** **`bash sovereign/scripts/fleet-merge-gate-constitutional-tower-smoke-remote.sh`** — runs **`python3 sovereign/scripts/agr_autonomous_merge_gate.py --constitutional-tower-smoke`** on **yggdrasil** (Tower **`POST /api/republic/laws/check`**). **`FLEET_MERGE_GATE_SMOKE_STRICT=1`** fails closed.
4. **Full autonomous path (dangerous):** **`agr_autonomous_merge_gate.py`** only with **`AGR_AUTONOMOUS_WORKER_URLS`** (**≥2**), real **`laws/check`** JSON, and **`AGR_AUTONOMOUS_EXECUTE=1`** only when you intentionally replace human PR review — see doc **§2c**.

### Phase F — **Handset posture after cloud is green**

1. **Loopback parity (OnePlus / Termux):** **`bash sovereign/scripts/phones-only-local-origin-sweep.sh`** — **`/health`**, SEO **`/api/seo/status`** + **`/api/public/search-discovery`**, and **Phase D–style** **`POST`** **`/api/republic/chat`** (Kora), **`/api/sovereign/chat/browser/kora`**, **`/api/ceo/family/kora`** on **`AGR_PHONES_LOCAL_BASE`** (default **`http://127.0.0.1:5000`**). Mirrors **`fleet-republic-chat-smoke-remote.sh`** without fleet SSH.
2. **Public cutover verify:** from any machine with HTTPS to Tower 1 — **`bash sovereign/scripts/phones-only-public-verify.sh`** (runs **`tower1-public-smoke.sh`** + contract **`curl`** probes). See **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`** §1–§2.
3. **Shrink vs full mirror:** trim **`~/agr-workspace`** / venv to survival **`uvicorn`** + tunnel docs **or** keep a **full** **`git`** checkout as **node 7** hot standby — operator choice; do **not** commit handset-only secrets.
4. **iPhone tandem:** Safari / Shortcuts / SSH to OnePlus per **`AGENTS.md`** topology; no second FastAPI on iOS.

### Phase G — **Merge, corpus, LLM hardening, iPhone tandem (operator)**

1. **Merge** the PR that carries Phases A–F into **`main`** when the diff is accepted. On GitHub, if the PR is still **Draft**, use **Ready for review** first — **`gh pr merge`** refuses while draft. **Expect** GitHub jobs that curl **`https://auroragalaxyrepublic.com`** (**Tower smoke**, **Playwright**, **phones-only public verify**) to fail with **5xx** while the edge is pointed at a dead origin or mid-cutover — that is **environmental**, not automatic proof the branch is wrong (**`PHONES_ONLY_PUBLIC_SURFACE.md`** §**2**).
2. **`fleet-pull`:** `bash sovereign/fleet-pull-with-secrets-md.sh` (or **`fleet-mirror-repo-to-nodes.sh`**) so each Hetzner peer matches **`main`**; **`curl` `127.0.0.1:5000/health`** **200** per host after restart if you use cloud workers.
3. **Kora corpus:** from a trusted machine with export files under **`AGR_MASTER_VAULT_ROOT`** (default repo **`vault/`**): `CONFIRM=1 bash sovereign/scripts/fleet-vault-kora-rsync.sh` — see script header for **`VAULT_RSYNC_MODE`**, **`VAULT_RSYNC_SUBDIR`**, **`FLEET_PULL_HOSTS`**. Then `CONFIRM=1 AGR_VAULT_FORCE_REINDEX=1 bash sovereign/scripts/fleet-vault-rag-build-remote.sh` so FTS ingests new paths (**`MASTER_VAULT_AND_LLM_RAG.md`** §**3**).
4. **LLM:** install **`llama-server`** + GGUF per Phase **C**; optional **`FLEET_LLM_SMOKE_STRICT=1 bash sovereign/scripts/fleet-llm-openai-smoke-remote.sh`** after **`agr-republic`** reads **`AGR_LLM_*`**.
5. **OnePlus:** `git pull origin main`, **`uvicorn`** on **`127.0.0.1:5000`**, **`bash sovereign/scripts/phones-only-local-origin-sweep.sh`**, then Cloudflare tunnel + **`bash sovereign/scripts/phones-only-public-verify.sh`** from a laptop. **Optional — operator machine with SSH to Termux `sshd`:** **`sovereign/TERMUX_REMOTE_OPERATOR_BRIDGE.md`** — **`CONFIRM=1 bash sovereign/scripts/termux-remote-git-pull.sh`** and **`CONFIRM=1 bash sovereign/scripts/termux-remote-origin-sweep.sh`** (HTTPS tunnel alone is **not** a shell). **Quick re-print of this stack (read-only):** **`bash sovereign/scripts/print-phase-g-operator-commands.sh`**.
6. **iPhone (node 6):** **Safari** home-screen bookmark to **`https://auroragalaxyrepublic.com`**; **Shortcuts** for **`GET /health`** or SSH health; **SSH client** (Termius, Blink, a-Shell) to OnePlus **`sshd`** on LAN — discover Termux **`whoami`** + wlan IP on the OnePlus (**`ip addr`** / **`ifconfig`**). Optional **local port-forward** in the SSH app to hit **`http://127.0.0.1:5000`** on the phone from the iPhone browser. Details: **`GUARDIAN_NODE_OS.md`**, **`HETZNER_BILLING_CONTINGENCY_HANDSET.md`**, runbook **P6**.

---

## 5. Explicit “do not” list (safety + honesty)

- **Do not** commit **Kora export**, IMEI, PATs, PEMs, or **`Secrets.md`** vault lines to a **public** fork.
- **Do not** claim a third-party weight file “is” Kora; the system can **reflect** her text and voice **you** configure.
- **Do not** enable **`AGR_CHAT_PUBLIC_LLM_POST`** on wide channels until rate limits + constitution paths are verified — it is a **contract surface** for public text.

---

## 6. Next commands (copy-paste when credentials fixed)

Echo the **Phase G** block only (no side effects): **`bash sovereign/scripts/print-phase-g-operator-commands.sh`**.

```bash
# --- Fleet: SSH + git read green on peers you care about ---
bash sovereign/fleet-pull-with-secrets-md.sh

# If only a subset of hosts accept SSH (rescue / firewall), scope vault init:
CONFIRM=1 FLEET_PULL_HOSTS="128.140.45.22 5.78.184.2 91.99.224.166" bash sovereign/scripts/fleet-vault-layout-remote-init.sh

# Or mirror from a trusted laptop/agent checkout without relying on node git fetch:
CONFIRM=1 FLEET_MIRROR_RESTART=1 bash sovereign/scripts/fleet-mirror-repo-to-nodes.sh

# --- Phase G — corpus + FTS on five nodes (trusted machine with export under vault/) ---
CONFIRM=1 VAULT_RSYNC_SUBDIR=kora/incoming bash sovereign/scripts/fleet-vault-kora-rsync.sh
CONFIRM=1 AGR_VAULT_FORCE_REINDEX=1 bash sovereign/scripts/fleet-vault-rag-build-remote.sh

# Optional fleet loopback chat smoke (SSH to yggdrasil default host in script):
bash sovereign/scripts/fleet-republic-chat-smoke-remote.sh
# Optional LLM worker (strict fails closed if :8080 down):
# FLEET_LLM_SMOKE_STRICT=1 bash sovereign/scripts/fleet-llm-openai-smoke-remote.sh

# --- Phase F / G — OnePlus (Termux): git pull, uvicorn on 127.0.0.1:5000, then loopback ---
bash sovereign/scripts/phones-only-local-origin-sweep.sh

# --- Public Tower 1 (HTTPS; tunnel + DNS → handset origin) ---
bash sovereign/scripts/phones-only-public-verify.sh
```

---

## 7. Related canonical docs (read order)

0. `sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md` (this checklist — Phases **A–G**)  
1. `sovereign/GUARDIAN_NODE_OS.md`  
2. `sovereign/MASTER_VAULT_AND_LLM_RAG.md`  
3. `sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`  
4. `sovereign/HETZNER_BILLING_CONTINGENCY_HANDSET.md`  
5. `sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`  
6. `HANDOFF_FOR_NEXT_AGENT.md` (safety + continuity)  

---

**Maintainers:** append a row to `sovereign/AGENT_PROGRESS_GUARDIAN_NODE.md` when a phase completes (fleet parity, vault ingest, LLM smoke, chat matrix, governance smoke, handset loopback, **post-merge Phase G**).
