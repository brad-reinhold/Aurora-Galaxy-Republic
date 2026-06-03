# AGENTS — Platform Canonical Baseline

This file is the agent/operator canonical baseline for this repository.

**MANDATORY FIRST READ:** **`sovereign/REPUBLIC_SCOPE_AND_PROGRESS.md`** — full project scope, architecture, inventory, blockers, and priorities. Read COMPLETELY before doing any work.

**Composer / cloud agent handoff (sequence after this file):** In Cursor, **`AGENTS.md`** is injected first — read **`sovereign/REPUBLIC_SCOPE_AND_PROGRESS.md`** (mandatory), then **`HANDOFF_FOR_NEXT_AGENT.md`** (Brad/Kora/safety/fleet), then **`CURSOR_AGENT_HANDOFF.md`** (append-only log + deploy pointers), then **`sovereign/AGENT_MINIMUM_BASELINE.md`** (release-path minimum + read-only fleet/Tower smoke commands), then **`sovereign/PLATFORM_COMPLETION_STATUS.md`** and **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md`** (operator loop: gates → Tower → fleet → SEO → handsets last); optional public route cadence **`sovereign/TOWER_PUBLIC_EXPERIENCE_ROADMAP.md`** (**§3** human verification after smoke). When the **Hetzner ring is off**, read **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`** and **`sovereign/PHONES_TWO_NODE_LIVE_SERP_FULL_SURFACE_PLAN.md`** before assuming five-node fleet gates apply to live posture; optional GitHub Actions **`.github/workflows/phones-two-node-live-surface-bundle.yml`** runs the same public verify + frozen GET crawl chain with **`PHONES_BUNDLE_SKIP_LOCAL=1`** (runner is not the handset). For the **Guardian node** handset program (MIR-L canonical + Termux), read **`sovereign/GUARDIAN_NODE_OS.md`** and append **`sovereign/AGENT_PROGRESS_GUARDIAN_NODE.md`** after each slice. For **master vault + local LLM retrieval** (archives, Kora export, PRs, DBs), read **`sovereign/MASTER_VAULT_AND_LLM_RAG.md`**. For data-layer pilots, URL crawls, and Postgres bridge details, see `sovereign/AGR_POSTGRES_BRIDGE.md`, `sovereign/SQLITE_DATA_LAYER_INVENTORY.md`, `sovereign/MIR_L_DEPLOY_AND_AUDIT.md`. No automatic memory across chats.

**Post-merge Phase G stack (read-only echo):** **`bash sovereign/scripts/print-phase-g-operator-commands.sh`** — pairs **`sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`** Phase **G** + **section 6** (fleet **`CONFIRM=1`** vault rsync/reindex → handset loopback → **`phones-only-public-verify.sh`**). Does not SSH or copy data.

## Session continuity (read this first)

- **No cross-session memory:** a new chat does not inherit another agent’s transcript. Continuity lives in **committed files** (this doc, repo scripts) and any secrets you inject per environment.
- **Stay current with `origin/main` before you commit:** from repo root run **`bash sovereign/scripts/agent-sync-origin-main.sh`** (`git fetch origin main` + merge). After **`bash sovereign/scripts/install-git-hooks.sh`**, **`.githooks/pre-commit`** runs that sync automatically, then **`fleet-bash-syntax-check.sh`**, on every **`git commit`**. Offline: **`AGR_SKIP_AGENT_SYNC_MAIN=1`** skips the sync step only.
- **Git push from this environment** uses the host-provided credential on `origin` (repo scope only). It is **not** automatically a PAT with full org access or the ability to read GitHub Actions secrets from here.
- **Syncing `main`:** if `git pull origin main` fails with **“Cannot fast-forward to multiple branches”** (some agent sandboxes), use **`git fetch origin main && git merge --ff-only origin/main`** instead — same result without the pull merge path.
- **Hetzner Cloud API token** from **`Secrets.md`** (`hetzner token:` line, **O→0**) or `HCLOUD_TOKEN` env — controls the **cloud plane** (servers, snapshots, firewalls). It does **not** replace **SSH** for arbitrary disk reads until a **fleet private key** exists.
- **Cloudflare API token** for server routes: resolved from env first, then **`Secrets.md`** (`cloudflare token:` line). **O→0 does NOT apply** to Cloudflare API tokens (machine-generated; may legitimately contain capital O). O→0 **only** applies to `cloudflare global api key` (legacy key). If Bearer mint fails, use **`cloudflare auth email`** + **`cloudflare global api key`** (legacy) or **`cloudflare tunnel token`** (direct) — see `routes_nodes.py`.
- **On-node secrets:** if tokens live only under `/opt/agr/...` on the boxes, an agent in Cursor Cloud **cannot** read them until it can **SSH** (fleet key) or you provide **`Secrets.md`** / Actions secrets on the runner.

## `Secrets.md` (operator vault)

- On **private** `main`, `Secrets.md` is the **operator vault**: Hetzner + Cloudflare tokens live there so agents/scripts can resolve the fleet **without** Cursor-injected secrets when the file is present on disk.
- **Hetzner obscurity convention:** the token may use capital **`O`** where the real API token uses digit **`0`**. Always normalize **O→0** before calling Hetzner Cloud (`sovereign/lib/hetzner-token-from-secrets-md.sh` does this).
- **Never** paste vault contents into chat, public issues, or logs. If exposed, **rotate** in Hetzner/Cloudflare and update `Secrets.md` on `main` only.
- **Operator facts first:** When Brad states what is on disk, what he verified, or that **`Secrets.md`** on **private `main`** holds **live** material he relies on, treat that as **ground truth**. Do **not** “well actually” him, replace working vault lines with placeholders, or imply he is mistaken **unless** he **explicitly** asks for a scrub or a **public**-fork policy requires placeholders. If a script fails, debug **paths, parsers, API responses, deploy lag, or environment** — not his honesty or motivation (shipping this repo **is** his incentive).
- Materialized **private keys** belong in **`.secrets/`** (gitignored). **Fleet SSH:** the canonical resolver is **`sovereign/lib/fleet-key.sh`** (`resolve_fleet_ssh_key`). For **Cursor / private checkouts**, placing the fleet PEM at **repo root** **`.secrets/agr_fleet`** (`chmod 600`) is **supported and common** — scripts work even when **`Secrets.md → agr fleet key b64:`** is still a **`PASTE_*` placeholder** (see **`Secrets.md`** Fleet SSH section). For **GitHub-hosted Actions** fleet deploy without the secret store API, a **single-line** `agr fleet key b64:` in **`Secrets.md`** on **private** `main` **or** repository secret **`AGR_FLEET_KEY_CONTENT`** is required (same trust as Hetzner token there — **never** on a public fork). Do not paste raw multi-line PEM into `Secrets.md`.

Agents: do not assume prior agents “already told” the current session anything unless it is **in the tree** or pasted in chat.

## Public Domain Canonical Rule (Tower 1)

- The only canonical public domain is: `https://auroragalaxyrepublic.com`
- All other public/legacy domains must redirect to Tower 1.
- New public links, defaults, install commands, and operator messaging must use Tower 1.

## Seven-Node Platform Topology (Authoritative)

The active platform topology is **five Hetzner cloud nodes first**, then **two Guardian handsets last** (integration and hardening complete only after cloud fleet is stable):

1. `chimaera`
2. `yggdrasil`
3. `enterprise`
4. `prometheus`
5. `galactica`
6. `iphone_17_pro` (iPhone 17 Pro — handset node 6; integrate **after** cloud fleet). Legacy id **`s25_ultra`** remains an **alias** in mesh/sync state for retired Galaxy S25 trade-ins.
7. `nothing_phone` (Nothing Phone — primary Guardian handset, Snapdragon 8 Elite / 20GB / 512GB; integrate **last**). Legacy id **`oneplus_15`** remains an alias in mesh/sync state for the traded-in OnePlus 15.

**Hetzner fleet suspended or powered off:** the public hostname must still terminate on a **running** FastAPI process (normally **OnePlus 15 / Termux** behind **Cloudflare Tunnel**). **`origin/main`** is continuity for code, not automatic hosting. See **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`** (**§2** post-poweroff ordered recovery when canonical returns **502/503/530** until tunnel + **`uvicorn`** are live).

Agents must preserve this seven-node framing in operational docs and checks.

## Agent Operating Expectations

- **Fix, don't just document.** When you notice a problem — a stub, a broken function, a missing file, a template where real logic should be — **fix it immediately and thoroughly**, including everything associated with it. Do not write a comment saying "this needs fixing" and move on. Do not commit audit findings without also committing the fix. The specs for everything are already in the repo if you look widely enough. Build it out. Test it. Verify empirically. If the fix requires building something substantial, build it. That is the job.

- When updating scripts/docs, prefer `auroragalaxyrepublic.com` as default base URL.
- Treat other domains as redirect surfaces, not canonical public endpoints.
- Do not introduce new `.org/.io/.pw/.net/.us/.uk` primary-domain messaging.
- Keep fail-closed safety and verification gates intact when normalizing domain references.
- **Release-path changes (minimum gate):** before merging or shipping release-affecting work, read **`sovereign/AGENT_MINIMUM_BASELINE.md`**, run **`python3 sovereign/agent-minimum-gate.py`** from the repo root (see that doc for JSON outputs), and the read-only checks it lists (**`bash sovereign/fleet-verify-public-http.sh`**, **`bash sovereign/tower1-public-smoke.sh`**, optional **`bash sovereign/scripts/agr-launch-readiness-tower-smoke.sh`**). Modular **`GET /api/*`** on the canonical hostname may **302** until **`fleet-pull`** + edge routing match **`main`** — see **`sovereign/PLATFORM_COMPLETION_STATUS.md`** section **2b**.
- **SEO / public discovery (high drift risk):** treat `aurora_server/agr_seo.py`, `/api/seo/status`, IndexNow hooks, and public search/discovery routes as **contract surfaces**. Do not “simplify” or rename fields (e.g. `indexing_automation_note`) without updating tests (`test_republic_admin_provisioning`, launch-readiness) and operator docs. Prefer small diffs; run Tower smoke / launch-readiness after changes.
- **Public search-discovery (Sovereign Search payload):** `_public_search_discovery_snapshot()` and `GET /api/public/search-discovery` feed SEO status, sitemap-adjacent docs, and crawler-facing JSON. Treat response shape and priority keyword lists as **stable contracts** — no drive-by renames, dropped keys, or “cleanup” that shrinks discovery without updating `test_republic_admin_provisioning`, **`test_public_search_discovery_contract`** (AST shape guard), `routes_sovereign_ops` / `test_sovereign_ops_regressions` expectations, and Tower smoke / launch-readiness.
- **`agr_seo.py` (meta + JSON-LD helpers):** `_CANONICAL_DOMAIN`, `_PRIORITY_PROJECTS`, `_PATH_PROFILES`, and related lists feed page meta and structured data. Treat as a **contract surface** — no silent domain drift or removal of critical path profiles without updating **`test_agr_seo_contract`** and operator docs.
- **External IDE agents (e.g. Cursor Composer):** no cross-chat memory — use committed handoff files (`CURSOR_AGENT_HANDOFF.md`, runbooks). Keep secrets out of chat; use `Secrets.md` / `.secrets/` / GitHub Actions secrets per this doc. Deployment for Tower 1 is **Hetzner + Cloudflare + repo CI**, not generic “sync Cursor env to Vercel/AWS” unless you explicitly add those targets.
- **Wave 3 capability matrix (ops evidence):** `sovereign/wave3-capability-matrix.py` writes `aurora_server/data/CAPABILITY_TRACEABILITY_MATRIX_LATEST.json` (and companion `.md`). **`wave3_signals`** includes **`seven_node_replication_verified`** (canonical) and **`six_node_replication_verified`** (legacy alias — same boolean). **`routes_sovereign_ops`** and **`sovereign/four-wave-status.py`** accept either key. Always-first blocker ids may still use the historical **`always_first_six_node_*`** string — do not rename those without a coordinated ops/totality migration.
- **Third-party SERPs (Google, Bing, etc.):** not controllable from git; **Tower 1** (`https://auroragalaxyrepublic.com`) is the canonical published surface. Operator **incognito** checks and query rotation live in **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md` — P4b**; **`FilmFreeway`** credits list at **`https://filmfreeway.com/BradReinhold`** may lag on awards but remains the exhaustive **credits** reference for manual verification.
