# Platform completion — Tower 1 vs Guardian node

**Canonical Tower 1:** https://auroragalaxyrepublic.com  

**Guardian handset program (MIR-L + Termux):** **`sovereign/GUARDIAN_NODE_OS.md`** — single plan; canonical MIR-L: `aurora_server/mir_l/docs/guardian_node_program.mirl`. Append-only progress: **`sovereign/AGENT_PROGRESS_GUARDIAN_NODE.md`**. **Iterative operator loop:** **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md`**.

---

## 0. Iterative process (start here)

| Step | Doc / action |
|------|----------------|
| 1 | **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md`** — P0–P6 loop (gates → Tower → fleet → SEO → builders → handsets last). |
| 1b | **Hetzner fleet off / two-phone live:** **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`**, **`sovereign/PHONES_TWO_NODE_LIVE_SERP_FULL_SURFACE_PLAN.md`** — OnePlus tunnel origin; **`phones-two-node-live-surface-bundle.sh`** (loopback + public verify + frozen crawl); **`.github/workflows/phones-two-node-live-surface-bundle.yml`** (CI mirror, **`PHONES_BUNDLE_SKIP_LOCAL=1`**); **`phones-only-public-verify.sh`**; **`phones-only-local-origin-sweep.sh`** on device; **`hetzner-fleet-status.sh`** (read-only); **`hetzner-fleet-poweroff-all.sh`** / **`hetzner-fleet-poweron-all.sh`** when deliberately powering cloud VMs down or back up. |
| 2 | **Topology:** **`AGENTS.md`** — seven nodes; **`GUARDIAN_NODE_OS.md`** — **`iphone_17_pro`** node 6, OnePlus node 7 (legacy **`s25_ultra`** sync id). |
| 3 | **Public path baseline:** **`sovereign/TOWER1_FROZEN_URL_INVENTORY.md`** + CI crawl / Playwright workflows (count in file header). |

---

## 1. What is **complete in-repo** (recent `main`)

| Area | Delivered |
|------|-----------|
| **Public Tower** | Chat, engine, MIR-L public catalog + public stems, frozen URL tooling, smoke script, optional Postgres bridge pilots, etc. (see git history for MIR-L rollout PR). |
| **Guardian node** | `guardian_node_program.mirl` (private stem); **`/dl/s25-termux-setup`** (full bootstrap); **`/dl/ceo`** (launcher → **`/dl/ceo-os-py`**); Tower-1-only `s25_termux_setup.sh`; optional `AGR_S25_CLIENT_GATE_TOKEN` on enroll when server env set. |
| **Guardian fleet binding (no PII in git)** | `agr_guardian_device_binding.py`; `republic_os_server` loads profile at startup. Default fleet file: **`/opt/agr/.secrets/guardian-device-profile.json`** (after **`fleet-guardian-secrets-remote-init.sh`**). Operator: **`AGR_GUARDIAN_DEVICE_PROFILE_PATH`** or **`~/.secrets/...`** or **`AGR_DEVICE_*`** / **`AGR_GUARDIAN_WHITELIST_IPS`** / **`AGR_GUARDIAN_BEACON_SECRET`** — see **`GUARDIAN_DEVICE_BINDING.md` section 4**. |
| **RAG V1–V4 + V3b + V2 partial (FTS + hybrid + PDF/DOCX + vault images + Kora + PR export)** | `agr_vault_rag.py`; **`agr_vault_github_export.py`**; CEO **14–15**; `/dl/agr-vault-rag-py`; **`/dl/agr-vault-github-export-py`**; `vault-rag-build-index.sh`; **`vault-github-pr-export.sh`** |
| **Covert MIR-L** | Stem `guardian_node_program` excluded from public catalog; `/sovereign/mirl/guardian_node_program/*` requires guardian token. |

---

## 2. Verification (run from repo root)

These commands **materialize** progress; they are not placeholders.

| Check | Command | Pass criteria |
|-------|---------|-----------------|
| **Python — vault RAG + PR export** | `python3 -m unittest aurora_server.tests.test_agr_vault_rag aurora_server.tests.test_agr_vault_github_export -v` | All tests OK |
| **Python — Guardian device binding** | `PYTHONPATH=aurora_server python3 -m unittest tests.test_agr_guardian_device_binding -v` | All tests OK |
| **Python — fleet-ci Guardian WARN** | `PYTHONPATH=aurora_server python3 -m unittest tests.test_fleet_ci_post_verify_guardian_warn -v` | All tests OK |
| **Python — Wave 3 capability matrix** | `PYTHONPATH=aurora_server python3 -m unittest tests.test_wave3_capability_matrix -v` | All tests OK |
| **Agent progress Guardian node (GitHub Actions)** | **`.github/workflows/agent-progress-guardian-node-verify.yml`** | **Push**/**pull_request** to **`main`** (path filters + steps **match the workflow file** — includes **`fleet-bash-syntax-check`**, launch-readiness, **`verify-agent-progress-guardian-node.py`**, Wave 3 / matrix artifact paths after PR **#171**) or **`workflow_dispatch`**. Job timeout **15m**. |
| **Tier 1 static refs (GitHub Actions)** | **`.github/workflows/tier1-static-refs-verify.yml`** | **Push**/**pull_request** to **`main`** (path filters + steps **match the workflow file** — includes **`fleet-bash-syntax-check`**, launch-readiness, **`verify-tier1-static-refs.py`**, Wave 3 / matrix paths) or **`workflow_dispatch`**. Job timeout **20m**. |
| **Fleet verify public HTTP (GitHub Actions)** | **`.github/workflows/fleet-verify-public-http.yml`** | Cron + **`workflow_dispatch`** + path-filtered **push**/**pull_request** on **`main`**. **Exact `paths` + job steps** live in the workflow YAML (**`fleet-bash-syntax-check`**, launch-readiness, **`sovereign/fleet-verify-public-http.sh`** — host list from **`sovereign/fleet-public-node-env.txt`** unless **`FLEET_VERIFY_HOSTS`** set; default **`/health`** then **`/api/health`** per node, first **2xx** wins; optional **`FLEET_VERIFY_PATH`** for a single path). **Origin probe** step runs **`tower1-origin-probe.sh`** and emits **`::warning`** when **`/dl/agr-handset-secrets-md-py`** is not **200**. Job timeout **15m**. |
| **CI — Guardian binding (GitHub Actions)** | **`.github/workflows/guardian-device-binding-verify.yml`** | **Push**/**pull_request** to **`main`** when paths in the workflow file match (binding, **`republic_os_server`**, **`routes_*.py`**, contract tests, **`fleet-bash-syntax-check`**, linked fleet/Tower workflows, Wave 3 / matrix paths — **see YAML `on.push.paths` / `on.pull_request.paths`**). Job: **`fleet-bash-syntax-check.sh`** → **`agr_autonomous_merge_gate.py --launch-readiness-tower-smoke`** (**`AGR_LAUNCH_READINESS_RUN_TOWER1_BASH=0`**) → **`unittest`** modules in step **Guardian binding + fleet-ci warn tests** (same order as the workflow file). Job timeout **20m**. |
| **Fleet shell syntax (local)** | `bash sovereign/scripts/fleet-bash-syntax-check.sh` | Exit 0 — behavior matches **`sovereign/scripts/fleet-bash-syntax-check.sh`** (see script header + **`MASTER_VAULT_AND_LLM_RAG.md`** §6 for **`bash -n`** / **`py_compile`** coverage). |
| **Operator full verify (local)** | `bash sovereign/scripts/run-operator-full-verify.sh` | **`fleet-bash-syntax-check`** → Guardian progress verify → launch-readiness (Python) → CI unittest list → **`tower1-public-smoke.sh`** → **`tower1-origin-probe.sh`** (unless **`SKIP_TOWER1_ORIGIN_PROBE=1`**) → optional **`hetzner-fleet-status.sh`** when **`OPERATOR_HETZNER_FLEET_STATUS=1`** (non-fatal) → **`agent-minimum-gate.py`** (unless **`SKIP_AGENT_MINIMUM_GATE=1`**). See script header + **`GUARDIAN_NODE_OS.md`**. |
| **Tower 1 frozen inventory crawl (scheduled)** | GitHub Actions **`.github/workflows/tower1-frozen-inventory-crawl.yml`** | Cron + **`workflow_dispatch`** + path-filtered **push**/**pull_request** on **`main`**. **Exact `paths` + job steps** live in the workflow YAML (includes **`fleet-bash-syntax-check`**, launch-readiness, **`tower1-frozen-inventory-crawl.py`**, Wave 3 / matrix paths). |
| **Tower 1 frozen URLs Playwright (manual)** | GitHub Actions **`.github/workflows/tower1-frozen-urls-playwright.yml`** | **`workflow_dispatch`** + path-filtered **push**/**pull_request** on **`main`**. **Exact `paths` + Playwright job** live in the workflow YAML (includes **`fleet-bash-syntax-check`**, launch-readiness, **`sovereign/e2e/frozen-urls/`**, Wave 3 / matrix paths). |
| **Tower 1 public** | `bash sovereign/tower1-public-smoke.sh` | **Local / operator:** exit **0** (outbound HTTPS). Retries **`TOWER1_SMOKE_MAX_TRIES`** / **`TOWER1_SMOKE_RETRY_SLEEP`** on curl **000**. Probes **`engine-runtime`**, **`citizen-engine-advice`**, **`/api/republic/chat`**, MIR-L (strict default), public **`/dl/*`** handset **`GET`s**, **`POST /api/republic/laws/check`**. Warns on **`GET /api/justice`** and **`GET /api/tower`** when not **200** JSON (LB mixing stale origins, edge rules, or code lag — **`TOWER1_SMOKE_MODULAR_DRIFT=0`** to skip; **`TOWER1_SMOKE_STRICT_MODULAR_API=1`** to fail). With **`GITHUB_ACTIONS=true`**, modular drift also emits **`::warning`** to stdout for the Actions summary UI. **`TOWER1_SMOKE_STRICT_MIRL=0`** only during transitional deploys. **CI:** **`.github/workflows/tower1-public-smoke.yml`** — cron + **`workflow_dispatch`** + path-filtered **push**/**pull_request**; **`on.paths`** and job step order **match the workflow file** (Wave 3 / matrix paths per PR **#171**). **Fleet deploy:** **`.github/workflows/fleet-deploy-pull.yml`** runs **`tower1-origin-probe.sh`** after smoke, then launch-readiness. |
| **Two-phone live + full GET surface** | `bash sovereign/scripts/phones-two-node-live-surface-bundle.sh` | **(1)** **`phones-only-local-origin-sweep.sh`** unless **`PHONES_BUNDLE_SKIP_LOCAL=1`**; **(2)** **`phones-only-public-verify.sh`**; **(3)** **`tower1-frozen-inventory-crawl.py`** unless **`PHONES_BUNDLE_SKIP_CRAWL=1`** — over **`TOWER1_FROZEN_URL_INVENTORY.md`** (header count — **119** today). Use **`TOWER1_CRAWL_ATTEMPTS`** **5–6** behind Cloudflare. **SERP/aesthetics:** still **P4b** manual — **`PHONES_TWO_NODE_LIVE_SERP_FULL_SURFACE_PLAN.md`**. **CI:** **`.github/workflows/phones-two-node-live-surface-bundle.yml`** — **`workflow_dispatch`** + path-filtered **push**/**pull_request**; job sets **`PHONES_BUNDLE_SKIP_LOCAL=1`**. |
| **Phones-only public (tunnel → handset)** | `bash sovereign/scripts/phones-only-public-verify.sh` | Exit **0** after **`tower1-public-smoke.sh`** plus **`GET /api/seo/status`** and **`GET /api/public/search-discovery`** JSON key checks (top-level keys aligned with **`test_public_search_discovery_contract`**). Use when the **Hetzner ring is off**; **`TOWER1_BASE`** defaults to **`https://auroragalaxyrepublic.com`**. See **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`**. **CI:** **`.github/workflows/phones-only-public-verify.yml`** — **`workflow_dispatch`** + path-filtered **push**/**pull_request** on **`main`** (see YAML **`on.paths`**). |
| **Handset loopback (pre-tunnel)** | `bash sovereign/scripts/phones-only-local-origin-sweep.sh` | **`GET /health`** **200** on **`AGR_PHONES_LOCAL_BASE`** (default **`http://127.0.0.1:5000`**) plus same **`/api/seo/status`** and **`/api/public/search-discovery`** JSON key checks as public verify — no public DNS required. Run on **OnePlus / Termux** after **`uvicorn`** is listening. |
| **Hetzner fleet power (API)** | `CONFIRM=1 bash sovereign/scripts/hetzner-fleet-poweroff-all.sh` **or** `hetzner-fleet-poweron-all.sh` | **`HCLOUD_TOKEN`** or **`Secrets.md`** (**`hetzner-token-from-secrets-md.sh`**). **Poweroff** issues **`poweroff`** for all five **`node-map.env`** IDs. **Poweron** **`GET`s** each server’s status then **`poweron`** unless already **`running`** / **`starting`**. |
| **Hetzner fleet status (read-only)** | `bash sovereign/scripts/hetzner-fleet-status.sh` | TSV **`server_id`**, **`name`**, **`status`**, **`datacenter`**, **`ipv4`** for the five **`node-map.env`** IDs — no **`CONFIRM`**; same token resolution as power scripts. |
| **Tower 1 origin vs fleet IPs** | `bash sovereign/scripts/tower1-origin-probe.sh` | Compares **`TOWER1_BASE`** to **`https://<ip>`** for each **`name:ip`** in **`sovereign/fleet-public-node-env.txt`** (**`/health`**, **`/dl/ceo-os-py`**, **`/dl/agr-handset-secrets-md-py`**). Override list: **`TOWER1_ORIGIN_NODES_FILE`**. **Fleet deploy** appends this table to the job summary. **Action list:** **`bash sovereign/scripts/operator-next-steps-fleet-tower.sh`** (exit **2** until **`dl_handset_secrets`** is **200** everywhere in the table). |
| **Fleet pull + restart** | After adding **`agr fleet key b64:`** to `Secrets.md` (see `sovereign/lib/fleet-key-from-secrets-md.sh`) **or** exporting `AGR_FLEET_KEY_CONTENT`: `bash sovereign/fleet-pull-with-secrets-md.sh` | SSH to all five default hosts succeeds; `git pull` completes; **`agr-republic.service`** restart attempted; if missing/failed, **`agr-server.service`** fallback when present (**`FLEET_PULL_ALT_RESTART=0`** to skip). Post-pull log: **`health: ok`** from **`/health`** or, if that fails, from **`GET`** **`FLEET_PULL_MIRL_CHECK_PATH`** (default **`/api/public/mirl/catalog`** **200**; empty env skips MIR-L probe). **Align units:** **`CONFIRM=1 bash sovereign/scripts/fleet-install-agr-republic-unit.sh`** installs repo **`systemd/agr-republic.service`** and retires legacy **`agr-server`** (see **`GUARDIAN_NODE_OS.md`** deploy table). |
| **Fleet read-only status** | `bash sovereign/fleet-status-read-only.sh` | Prints per-host `git_repo`, `systemd_active`, `local_health`, `local_mirl_http`, and Guardian binding **presence** (`fleet_guardian_secrets_dir`, `fleet_guardian_profile_nonempty`, `root_guardian_profile_nonempty` — booleans only, no file reads). **`FLEET_STATUS_FORMAT=json`** for machine output; optional **`FLEET_STATUS_GUARDIAN_SECRETS_DIR`**, **`FLEET_STATUS_GUARDIAN_PROFILE`** (basename). Same checks run in **GitHub Actions** after `fleet-pull` (`.github/workflows/fleet-deploy-pull.yml`). Public IP list for docs: **`sovereign/fleet-public-node-env.txt`**. |
| **Fleet post-pull verify (CI + local)** | `bash sovereign/fleet-ci-post-verify.sh` | **`bash sovereign/scripts/fleet-bash-syntax-check.sh`** first (skip: **`FLEET_CI_POST_VERIFY_SKIP_BASH_N=1`**). Optional Tower go-live when **`FLEET_CI_POST_VERIFY_LAUNCH_READINESS=1`** (**`bash sovereign/scripts/agr-launch-readiness-tower-smoke.sh`**; sets **`AGR_LAUNCH_READINESS_RUN_TOWER1_BASH=0`** by default; off in **fleet-deploy-pull** so Tower is not probed twice in one job). Same script list as **fleet-deploy-pull** **`chmod`** shells. Then progress verifier, vault verify, **`fleet-guardian-secrets-verify-remote`**, JSON **`fleet-status`** (needs **`AGR_FLEET_KEY`** or **`AGR_FLEET_KEY_CONTENT`**). Optional Guardian WARN (**`FLEET_CI_POST_VERIFY_GUARDIAN_WARN=0`**). Actions: missing profile may emit **`::warning::`**. Expect **`local_health`** and **`local_mirl_http`** **200** on all five after deploy. |
| **Fleet guardian secrets verify (remote)** | `bash sovereign/scripts/fleet-guardian-secrets-verify-remote.sh` | Read-only SSH: **`fleet_guardian_secrets_dir`**, **`fleet_guardian_profile_nonempty`**, **`root_guardian_profile_nonempty`**. **`FLEET_STATUS_FORMAT=json`**. Optional **`FLEET_GUARDIAN_SECRETS_VERIFY_REQUIRE_PROFILE=1`** fails if SSH-ok host has no non-empty profile (fleet or root). |
| **Fleet vault verify (remote)** | `bash sovereign/scripts/fleet-vault-verify-remote.sh` | Exit 0 when expected dirs + `kora/README.md` exist on all five hosts. **`FLEET_STATUS_FORMAT=json`** supported. |
| **Fleet git init (destructive)** | `CONFIRM=1 bash sovereign/fleet-git-init-with-secrets-md.sh` | Each host has `/opt/agr/.git` after clone + data rsync. **GitHub:** deploy key for fleet SSH key **or** `agr fleet github read token:` in `Secrets.md` (HTTPS clone — see `lib/fleet-github-read-token-from-secrets-md.sh`). |
| **Fleet guardian secrets dir (no secrets written)** | `CONFIRM=1 bash sovereign/scripts/fleet-guardian-secrets-remote-init.sh` | Creates **`/opt/agr/.secrets/`** (0700) + README on each host; operator copies **`guardian-device-profile.json`** (0600) or uses env per **`GUARDIAN_DEVICE_BINDING.md` section 4**. |
| **Kora vault paths** | `bash sovereign/scripts/vault-kora-stagedir-init.sh` | Creates `vault/{documents,archives,github_prs}` + `vault/kora/{incoming,staged,chunks}` + **`vault/republic_builder/{inbox,approved,rejected}`** + READMEs (no corpus committed). |
| **Kora / large vault copy** | See **`MASTER_VAULT_AND_LLM_RAG.md` section 3a** — operator `rsync`, **`CONFIRM=1 bash sovereign/scripts/fleet-vault-kora-rsync.sh`** (modes: local / fanout / scp), Tower **`/vault-upload`**, object storage + pull, or handset `scp` to one node then fanout. |

### 2b. When the canonical hostname disagrees with `main`

| Symptom on `https://auroragalaxyrepublic.com` | Likely meaning | Action |
|----------------------------------------------|----------------|--------|
| **`GET /health`** **200** JSON, **`GET /api/health`** **404** JSON | Edge / worker path filter; or origin not exposing that path through the public hostname | **`fleet-pull`** on ring; fix **Cloudflare** (or tunnel) rules so **`/api/*`** reaches **uvicorn**; probes already prefer **`/health`** first. |
| **`GET /api/justice`** (etc.) **302** → **`/gate`** | Stale origin (pre‑**`8ca153d`** AuthMiddleware), **`AuthMiddleware`** / **`sovereign_tower_gate`** list skew, or edge pool | Confirm **`main`** includes **`_requires_auth` → `_is_tower1_public_path`** and shadow prefix in **`_TOWER1_SHADOW_ROUTE_API_PREFIXES`**; **`fleet-pull`** + restart; incognito re-test. |
| **`GET /api/tower`** / **`GET /api/justice`** **302** on canonical; **loopback** on OnePlus **200** JSON | Handset **`uvicorn`** checkout behind **`main`** (tunnel healthy) | **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`** §8 — **`git pull`** + restart **`uvicorn`**; optional **`TOWER1_SMOKE_MODULAR_DRIFT=0`** on probe host; **`HANDOFF_FOR_NEXT_AGENT.md`** operator cadence. |
| **`GET /api/justice`** **404** JSON on a node **public IP** | Running process **lags `main`** or wrong unit / wrong **`PYTHONPATH`** | **`fleet-status-read-only`** **`head`** vs **`origin/main`**; **`fleet-pull-with-secrets-md`**; **`systemctl restart agr-republic`**. |
| **Canonical **`GET /dl/agr-handset-secrets-md-py`** **404** but **`main`** has the route | Hostname path may hit a different pool than direct origin, or fleet not restarted | Run **`bash sovereign/scripts/tower1-origin-probe.sh`**. If **all five** public IPs also return **404** while **`/dl/ceo-os-py`** is **200**, every node is on a revision **before** that route — **`fleet-pull`** + **`systemctl restart agr-republic`** on each host. If canonical is **404** but IPs are **200**, suspect edge / pool skew. |
| **Hetzner ring powered off** | DNS / LB still aimed at old cloud IPs, or tunnel not running on OnePlus | Follow **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`**: Cloudflare → tunnel → **`uvicorn`**; then **`bash sovereign/scripts/phones-only-public-verify.sh`**. Skip **`fleet-pull`** / **`tower1-origin-probe`** until cloud returns. |
| **Canonical 5xx / timeout; origin probe all fleet IPs fail** | VMs **`off`** or networking broken; DNS still points at old cloud | **`bash sovereign/scripts/hetzner-fleet-status.sh`** — if **`status`** is **`off`**, use phones-only cutover (**`PHONES_ONLY_PUBLIC_SURFACE.md`**) or **`hetzner-fleet-poweron-all.sh`** when returning to cloud. |

## 3. Device acceptance (operator on hardware)

| Device | Action |
|--------|--------|
| **Node 6 (`iphone_17_pro`)** — iPhone 17 Pro (CEO apex handset) | After **five Hetzner** peers are green: **no Termux on iOS** — use **Safari + Tower 1** and optional **Shortcuts/SSH** per **`GUARDIAN_NODE_OS.md`** / **`PLATFORM_ITERATIVE_RUNBOOK.md`** P6. Migrate **`sync_state`** file prefixes from **`s25_ultra:`** to **`iphone_17_pro:`** when the fleet rotates evidence. If compromise suspected, follow OEM recovery guidance (out of repo). |
| **OnePlus 15 (`oneplus_15`, node 7)** | **Last** — after node 6 path is accepted. Follow **OnePlus 15 (node 7) — completion checklist** in **`GUARDIAN_NODE_OS.md`** (profile, client gate, hash allowlist, optional mirror, private MIR-L, WG IP). Fleet may use **`GUARDIAN_DEVICE_BINDING.md` section 4** for hardware recognition. |

## 4. Deferred product scope (explicit)

| Item | Status |
|------|--------|
| **Dedicated ANN index** | Not implemented; hybrid FTS + optional embeddings in `agr_vault_rag` is the supported path. |
| **Vision OCR / multimodal image embeddings** | Not implemented; V3b uses path metadata + optional **`*.ext.txt`** sidecar captions only. |

---

## 5. Recommended next actions

### 5a. Phones-only (Hetzner fleet intentionally off)

1. **`CONFIRM=1 bash sovereign/scripts/hetzner-fleet-poweroff-all.sh`** (from a trusted machine with **`HCLOUD_TOKEN`** or **`Secrets.md`**) — optional; only when cloud VMs must stop.  
2. **Cloudflare:** route **`auroragalaxyrepublic.com`** to the **OnePlus** tunnel backend; remove stale pool members pointing at dead Hetzner IPs.  
3. **On the OnePlus (Termux) or any host with HTTPS to Tower:** **`bash sovereign/scripts/phones-two-node-live-surface-bundle.sh`** — loopback sweep (**skip** with **`PHONES_BUNDLE_SKIP_LOCAL=1`** on a laptop), **`phones-only-public-verify.sh`**, then **`tower1-frozen-inventory-crawl.py`** over every GET path in **`TOWER1_FROZEN_URL_INVENTORY.md`** (header count — **119** today; regen may change). Use **`TOWER1_CRAWL_ATTEMPTS=5`** or **`6`** behind Cloudflare. Full operator plan: **`sovereign/PHONES_TWO_NODE_LIVE_SERP_FULL_SURFACE_PLAN.md`**.  
3b. **GitHub Actions:** **`.github/workflows/phones-only-public-verify.yml`** — **`workflow_dispatch`** or path-filtered **push**/**pull_request** (same live **`TOWER1_BASE`** checks from GitHub runners).  
3c. **GitHub Actions:** **`.github/workflows/phones-two-node-live-surface-bundle.yml`** — full public verify + frozen **GET** crawl (**`PHONES_BUNDLE_SKIP_LOCAL=1`** on the runner).  
4. **P4b** in **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md`** — incognito + Search Console / Bing + IndexNow where configured (**SERP and aesthetics are not provable from CI alone**).

### 5b. Five-node cloud ring (default path when Hetzner is on)

When VMs were **powered off** intentionally, **`CONFIRM=1 bash sovereign/scripts/hetzner-fleet-poweron-all.sh`** brings them back (then **`fleet-pull`** / edge repoint). Normal green path:

1. **`bash sovereign/scripts/fleet-vault-verify-remote.sh`** — confirms **`/opt/agr/vault`** tree on all **five Hetzner** peers (exit **0** = ready for corpus rsync).  
2. **`bash sovereign/fleet-status-read-only.sh`** — SSH + loopback MIR-L code.  
3. If **`git_repo=no`**: **`CONFIRM=1 bash sovereign/fleet-git-init-with-secrets-md.sh`** — requires **GitHub** to accept either the **fleet deploy key** (SSH) or **`agr fleet github read token:`** in **`Secrets.md`** (HTTPS).  
4. **`bash sovereign/fleet-pull-with-secrets-md.sh`**.  
5. **`bash sovereign/tower1-public-smoke.sh`** — Tower 1 public SEO + **`engine-runtime`** + **`citizen-engine-advice`** + chat + MIR-L + public **`/dl/*`** handset payloads + **`laws/check`** (strict MIR-L is default in CI after fleet catalog 200). Use **`TOWER1_SMOKE_STRICT_MIRL=0`** only during transitional deploys. If **`laws/check`** returns **302**, Tower has not yet deployed **`main`** with **`/api/republic/laws/check`** in **`_TOWER1_PUBLIC_POST_PATHS`** — repeat **step 4** (**`fleet-pull`**) until **200**.  
6. **`AGR_LAUNCH_READINESS_RUN_TOWER1_BASH=0 python3 sovereign/scripts/agr_autonomous_merge_gate.py --launch-readiness-tower-smoke`** — same Python follow-up as **fleet-deploy-pull** / **`tower1-public-smoke.yml`** (optional **`AGR_AUTONOMOUS_WORKER_URLS`** for multi-worker synthesis).  
7. **`bash sovereign/scripts/vault-kora-stagedir-init.sh`** where needed; rsync Kora export into **`vault/kora/incoming/`**.  
8. Append **`sovereign/AGENT_PROGRESS_GUARDIAN_NODE.md`** when a milestone closes.  
9. **Handsets:** complete **node 6** (iPhone 17 Pro / **`iphone_17_pro`** — Safari + Tower 1 + optional Shortcuts/SSH per runbook P6; or legacy Android with Termux + enroll), then **node 7** OnePlus checklist — **`GUARDIAN_NODE_OS.md`**.

---

## Related

- **`sovereign/PHONES_TWO_NODE_LIVE_SERP_FULL_SURFACE_PLAN.md`** — two-phone live + full GET surface + P4b SERP  
- **`sovereign/scripts/phones-two-node-live-surface-bundle.sh`** / **`.github/workflows/phones-two-node-live-surface-bundle.yml`** — bundled verify (loopback optional + smoke + crawl)  
- **`sovereign/scripts/workspace-autonomous-fleet-tower-verify.sh`** — optional **`WORKSPACE_AUTONOMOUS_PHONES_BUNDLE=1`** chains fleet SSH smokes + Tower + **`phones-only-public-verify`** + frozen bundle (**`SKIP_FLEET_PULL=1`** for fast re-run)  
- **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`** — handset-only public origin + verify script  
- `sovereign/GUARDIAN_NODE_OS.md`  
- `sovereign/GUARDIAN_DEVICE_BINDING.md`  
- `sovereign/tower1-public-smoke.sh`  
- `sovereign/MIR_L_DEPLOY_AND_AUDIT.md`  
- **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md`**  
- **`sovereign/TOWER_PUBLIC_EXPERIENCE_ROADMAP.md`** — public UX / gate / chat cadence (**§3** human pass; **Related** **`PLATFORM`** **§2b**)  
- **`sovereign/MASTER_VAULT_AND_LLM_RAG.md`**
- **`sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`** — phased **A–G** operator checklist (fleet + vault + handset go-live)  
- **`sovereign/scripts/print-phase-g-operator-commands.sh`** — read-only Phase **G** echo (**section 6** order; no SSH)
