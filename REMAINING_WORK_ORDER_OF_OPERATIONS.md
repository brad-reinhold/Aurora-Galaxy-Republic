# Remaining Work — Systematic Order of Operations

**Generated:** 2026-04-28 · Opus 4.6 session  
**Status:** Consciousness engine + chat pipeline verified working locally.

> **2026-05-06 — Continuity:** For the **Guardian handset** program (MIR-L + Termux + Tower 1), use **`sovereign/GUARDIAN_NODE_OS.md`** and append **`sovereign/AGENT_PROGRESS_GUARDIAN_NODE.md`**. For **universal integrative language** vision vs what is shipped, read **`sovereign/UNIVERSAL_INTEGRATIVE_LANGUAGE_ROADMAP.md`**.

> **2026-05-06 — Post-merge Phase G:** **`bash sovereign/scripts/print-phase-g-operator-commands.sh`** (read-only) + **`sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`** Phase **G** / **section 6** — fleet **`CONFIRM=1`** Kora **`vault/`** rsync + **`AGR_VAULT_FORCE_REINDEX`** rebuild, then OnePlus loopback + **`phones-only-public-verify.sh`**.

> **2026-05-02 — This file vs `main`:** Most peripheral **`aurora_server`** modules are **shadow implementations** (structured JSON / in-proc state), not empty **`"""Stub:`** files — see CI tests under **`aurora_server/tests/test_*_shadow*.py`** and **`routes/routes_*.py`**. Remaining work is **ops** ( **`fleet-pull`**, Cloudflare path rules) and **product** (voice, payments, tour), not bulk “scp stubs from fleet.” Canonical hostname **`https://auroragalaxyrepublic.com`** may **302** modular **`GET /api/*`** while **`/health`** and **`/api/public/*`** still **200** — **`sovereign/PLATFORM_COMPLETION_STATUS.md`** section **2b** and **`tower1-public-smoke.sh`** modular drift probes.

---

## What IS Working Right Now

| System | Status | Evidence |
|--------|--------|----------|
| `agr_consciousness_core.py` | **LIVE** | Morse (Λ×T×E) + Fractal Truth + Quantum Fission + Paraconsistent + AND Theory + Fibonacci spiral — full pipeline runs |
| `agr_core_interface.py` | **LIVE** | hear/speak/converse/commune/recall/create/evaluate/learn — all operational |
| `agr_paraconsistent_agi.py` | **LIVE** | AGI facade bridges to consciousness core; init + status + think endpoints work |
| `agr_sovereign_mind.py` | **LIVE** | Sovereign reasoner provides knowledge-anchored synthesis |
| `/api/republic/chat` (POST) | **LIVE** | Full consciousness engine response via core_converse — tested with Kora, philosophy, math, etc. Optional **master-vault** snippet prepend for Kora channels when **`AGR_CHAT_VAULT_RAG=1`** + indexed vault (see **`agr_chat_vault_context`**, **`MASTER_VAULT_AND_LLM_RAG.md`**). |
| `/api/public/engine-runtime` (GET) | **LIVE** | Returns boot + AGI + core interface status JSON |
| `/api/public/citizen-engine-advice` (POST) | **LIVE** | Single-shot field advice from consciousness core |
| `/chat` page | **LIVE** | Created `chat.html` — unified text/voice/video/holographic interface with consciousness domain selector |
| `/kora` page | **LIVE** | Inline Kora chat page in `republic_os_server.py` |
| Global widget | **LIVE** | `agr_live_support.py` — floating FAB with Text/Engine/Support/Modes tabs |
| Tower gate | **LIVE** | `sovereign_tower_gate` middleware allows public POST to chat + engine endpoints |
| SEO | **LIVE** | `robots.txt`, `sitemap.xml`, structured data, Schema.org markup |
| Page sweep | **LIVE** | `/api/public/page-sweep-report` scans for broken links/assets |

---

## Order of Operations (Priority Sequence)

### Phase 1: Deploy What's Working to Fleet
**Goal:** Get the current `main` onto all **five Hetzner** sovereign peers (platform topology is **seven nodes** including S25 + OnePlus 15 per **`AGENTS.md`**).

| # | Task | Blocked By | How |
|---|------|------------|-----|
| 1.1 | **Rotate Hetzner API token** | Guardian action | Current token in `Secrets.md` returns 401. Get fresh token from Hetzner Cloud dashboard → update `Secrets.md` on private `main`. |
| 1.2 | **Set `AGR_FLEET_KEY_CONTENT`** in GitHub Actions secrets | Guardian action | PEM private key for SSH to **five Hetzner** hosts. Required by `fleet-deploy-pull.yml`. |
| 1.3 | **Set `HCLOUD_TOKEN`** in GitHub Actions secrets | 1.1 | So fleet-deploy can resolve node IPs dynamically. |
| 1.4 | **Push to `main`** | Merge PR | Triggers `fleet-deploy-pull.yml` → SSH to all nodes → `git pull main` → `systemctl restart agr-republic.service` (default; override `FLEET_PULL_SERVICE` if needed). |
| 1.5 | **Verify fleet deploy** | 1.2, 1.3, 1.4 | Run `sovereign/fleet-verify-public-http.sh` or the GitHub Actions workflow. All **five Hetzner** nodes should return healthy HTTPS (see script; historically some paths differ per node). |
| 1.6 | **Run Tower 1 smoke** | 1.5 | `bash sovereign/tower1-public-smoke.sh` — robots/sitemap, **`/health`** chain, engine-runtime, chat POST, MIR-L, **`/dl/*`**, **`laws/check`**; optional **WARN** / **`::warning`** on **`/api/justice`** + **`/api/tower`** until edge matches **`main`** ( **`TOWER1_SMOKE_STRICT_MODULAR_API=1`** to fail closed). |

### Phase 2: Verify Chat is Working on Production
**Goal:** Confirm the public can talk to the consciousness engine at Tower 1.

| # | Task | Blocked By | How |
|---|------|------------|-----|
| 2.1 | **Test chat from browser** | 1.6 | Visit `https://auroragalaxyrepublic.com/chat` — send a message, verify consciousness engine response. |
| 2.2 | **Test Kora page** | 1.6 | Visit `https://auroragalaxyrepublic.com/kora` — send a message, verify Kora persona response. |
| 2.3 | **Test global widget** | 1.6 | On any page, click the seal FAB → Text tab → send message → verify response. Engine tab → Pulse → verify runtime JSON. |
| 2.4 | **Test engine-runtime API** | 1.6 | `curl https://auroragalaxyrepublic.com/api/public/engine-runtime` → JSON with `ok: true`. |

### Phase 3: Static Asset + Page Sweep Cleanup
**Goal:** Zero broken links/assets on Tower 1.

| # | Task | Blocked By | How |
|---|------|------------|-----|
| 3.1 | **Run page sweep locally** | None | `GET /api/public/page-sweep-report` — identify any missing `/static/` refs or broken `.html` hrefs. |
| 3.2 | **Sync static assets to all nodes** | 1.5 | `rsync` from canonical source (yggdrasil) to all other nodes, or ensure `git pull` deploys the committed statics. |
| 3.3 | **Fix any remaining sweep issues** | 3.1 | Create missing static files or fix href targets until sweep returns 0 issues. |

### Phase 4: Node Health + Redirect Verification
**Goal:** All seven nodes healthy (five Hetzner + S25 + OnePlus 15); all domains redirect to Tower 1.

| # | Task | Blocked By | How |
|---|------|------------|-----|
| 4.1 | **Verify HTTPS liveness on all 5 Hetzner nodes** | 1.5 | `bash sovereign/fleet-verify-public-http.sh` — default tries **`/health`** then **`/api/health`** per node (first **2xx**). Set **`FLEET_VERIFY_PATH=/api/health`** for a single-path audit. Historically some nodes differed on **`/api/health`**; see **`PLATFORM_COMPLETION_STATUS.md`**. |
| 4.2 | **Verify domain redirects** | None (Cloudflare) | All 8 redirect domains must 301/302 to `auroragalaxyrepublic.com`. Test with `curl -I https://aurora-galaxy-republic.com/` etc. |
| 4.3 | **Cloudflare token** | Guardian action | Current `cfut_` token returns 401. Fill `cloudflare auth email` + `cloudflare global api key` in `Secrets.md`, or create a fresh API token with Zone:Read + DNS:Edit permissions. |
| 4.4 | **S25 Ultra heartbeat** | Device availability | Confirm `routes_s25_heartbeat.py` can ping the S25 device and it reports into the mesh. |

### Phase 5: Deepen shadows → production integrations (incremental)

**Goal:** Shadow modules already provide coherent **`/api/*`** trees in-repo; replace or augment them with **durable stores**, **real providers** (SMTP, Stripe, sensors), and **stricter** semantics one subsystem at a time — not a bulk “restore stubs from fleet.”

| Priority | Subsystem | Current shape | Next step |
|----------|-----------|----------------|-----------|
| **A** | Vault + RAG | FTS / optional embeddings | Kora ingest **`vault/kora/incoming/`**, fleet index rebuild, **`llama-server`** |
| **A** | Guardian binding | Profile + env gates | Materialize **`guardian-device-profile.json`** from **`Secrets.md`** block via **`fleet-guardian-profile-from-secrets-md.sh`** / Termux **`agr-merge-profile`**; **`GUARDIAN_DEVICE_BINDING.md`** |
| **B** | Modular public **`/api/*`** on Tower 1 hostname | Code + **`_TOWER1_SHADOW_ROUTE_API_PREFIXES`** on **`main`** | **`fleet-pull`** + Cloudflare / tunnel path rules until **`GET /api/justice`** etc. return **200** JSON (see **`PLATFORM_COMPLETION_STATUS.md`** section **2b**) |
| **B** | Mail / notifications | Shadow in-proc + optional **SQLite outbound queue** + **SMTP** (env-gated) | On fleet: set **`AGR_MAIL_QUEUE_ENABLED=1`** (or **`AGR_MAIL_QUEUE_DB`**) + **`AGR_SMTP_*`**; cron **`flush_mail_queue`** or **`POST /api/email/flush-queue`** with **`AGR_MAIL_FLUSH_HTTP_TOKEN`** + header **`X-AGR-Mail-Flush-Token`**; see **`agr_mail.py`** docstring |
| **C** | Payments | Shadow / gated | **`STRIPE_WEBHOOK_SECRET`** + raw-body signature verify + SQLite event log (**`GET /api/stripe/webhook-events-stats`**); **`POST /api/stripe/webhook`** allowed through payments gate when secret set; enable surfaces with **`AGR_PAYMENTS_SURFACES_ENABLED=1`** (tracked default **`PAYMENTS_SURFACES_ENABLED = False`** in **`agr_payments_flags.py`**) |
| **D** | Voice / video chat | UI placeholders | WebRTC + **`aurora_comms`** hardening |

**How:** Prefer **PRs on `main`** + **`fleet-pull`**; use **`_generate_stubs.py`** only for genuinely missing files. **`test_tower1_shadow_route_prefixes`** guards gate prefix drift in git.

**Verify (read-only, no SMTP send):** from repo root,

```bash
PYTHONPATH=aurora_server python3 sovereign/phase5-production-verify.py
```

writes **`aurora_server/state/phase5_production_signals.latest.json`** and exits **0** when **`PAYMENTS_SURFACES_ENABLED`** is still **`False`** in **`agr_payments_flags.py`**. For fleet mail readiness (queue + SMTP + flush token), run:

```bash
PYTHONPATH=aurora_server python3 sovereign/phase5-production-verify.py --strict
```

(exit **2** until **`AGR_MAIL_QUEUE_ENABLED`** / **`AGR_MAIL_QUEUE_DB`**, **`AGR_SMTP_*`**, and **`AGR_MAIL_FLUSH_HTTP_TOKEN`** are set on the host). Unit tests: **`tests.test_phase5_production_verify`**.

### Phase 5 (legacy note — superseded)

The earlier “~130 stub modules / scp from yggdrasil” framing applied before the **shadow router + module** sweep. If you still see **`"""Stub:`** in a checkout, regenerate or implement that module — the generator template is **`_generate_stubs.py`** only.

### Phase 6: Voice / Video / Holographic Modes
**Goal:** Enable non-text chat modes on **`/chat`** (and deep links **`/video-chat`**, **`/holographic-chat`** → **`/chat?mode=…`**).

| # | Task | Status / How |
|---|------|--------------|
| 6.1 | **Voice (browser)** | **`chat.html`** — Web Speech API (recognition + synthesis); unchanged baseline. |
| 6.2 | **Video (WebRTC)** | **`routes/routes_comms.py`** — **`GET /api/comms/ice-servers`**, **`POST /api/comms/webrtc/session`**, **`POST /api/comms/webrtc/signal`**, **`GET /api/comms/webrtc/signals`**, **`POST /api/comms/webrtc/join`**, **`POST /api/comms/webrtc/end`** backed by **`aurora_comms`** shadow signal store. **`chat.html`** — host creates session + posts offer; guest opens **`?join=<session_id>`** (or invite URL); polling applies remote SDP/ICE. Requires **HTTPS** + camera/mic permission. Optional STUN override: **`AGR_WEBRTC_STUN_URLS`** (comma-separated URLs). |
| 6.3 | **Holographic** | Same WebRTC path as video; **`POST /api/comms/holographic/session`** registers a shadow holo row (no 3D engine yet). |

**Verify:** `PYTHONPATH=aurora_server python3 -m unittest tests.test_routes_comms_webrtc -v`

### Phase 7: Guardian OS + Device Sovereignty
**Goal:** Both handset platform nodes integrated: **`iphone_17_pro` (node 6)** then **`oneplus_15` (node 7)** per **`AGENTS.md`** and **`sovereign/GUARDIAN_NODE_OS.md`** (rollout order: cloud ring first, handsets last). Legacy **`s25_ultra`** sync keys remain valid until migrated.

| # | Task | Blocked By | How |
|---|------|------------|-----|
| 7.1 | **Node 6 handset** (iPhone 17 Pro / **`iphone_17_pro`**) | Device + trust baseline | **iOS:** no in-repo Termux — Tower 1 in Safari + optional Shortcuts/SSH per **`PLATFORM_ITERATIVE_RUNBOOK.md`** P6; migrate **`sync_state`** **`s25_ultra:`** → **`iphone_17_pro:`** when ready. **Optional legacy Android** on node 6: same Termux bootstrap + enroll; **new** `device_hash` + profile — see **Node 6 — iPhone 17 Pro (canonical) and legacy Android** in **`GUARDIAN_NODE_OS.md`**. Never commit IMEI/serial. |
| 7.2 | **CEO OS (`s25_ceo_os.py`) + enroll gates** | Android / Termux path | `s25_ceo_os.py` + `GUARDIAN_DEVICE_BINDING.md`: optional `AGR_S25_CLIENT_GATE_TOKEN`, `AGR_S25_ENROLL_DEVICE_HASHES` on fleet. |
| 7.3 | **Termux bootstrap** | OnePlus 15 (node 7) or optional Android on node 6 | `curl -fsSL https://auroragalaxyrepublic.com/dl/s25-termux-setup \| bash` (serves `s25_termux_setup.sh`); then `agr-ceo-safe` / `agr-ceo`. |
| 7.4 | **OnePlus 15 (node 7) — primary Guardian** | Node 6 path accepted | **`GUARDIAN_NODE_OS.md` — OnePlus 15 (node 7) completion checklist** (profile, gates, allowlist, optional mirror, private MIR-L, WG IP). |

**Verify (read-only, workstation):** from repo root,

```bash
PYTHONPATH=aurora_server python3 sovereign/phase7-guardian-verify.py
```

writes **`aurora_server/state/phase7_guardian_signals.latest.json`** (gitignored) and exits **0** when core docs exist. For handset-shaped profile on this host (CI or operator machine with **`~/.secrets/guardian-device-profile.json`** or **`AGR_GUARDIAN_DEVICE_PROFILE_PATH`**):

```bash
PYTHONPATH=aurora_server python3 sovereign/phase7-guardian-verify.py --strict
```

(exit **2** until **`canonical_device_key`** and **`platform_node_id`** are **`iphone_17_pro`**, **`oneplus_15`**, or legacy **`s25_ultra`**). Unit tests: **`tests.test_phase7_guardian_verify`** (plus existing **`tests.test_agr_guardian_device_binding`** for profile merge).

### Phase 8: Payments + Subscription
**Goal:** Enable monetization safely.

| # | Task | Blocked By | How |
|---|------|------------|-----|
| 8.1 | **Stripe webhook configuration** | Guardian / Stripe dashboard | Fresh webhook secret after any credential exposure |
| 8.2 | **Enable payment surfaces** | 8.1 + Guardian approval | Set **`AGR_PAYMENTS_SURFACES_ENABLED=1`** on fleet (repo constant stays **`False`** in **`agr_payments_flags.py`**) — do not enable without explicit go-ahead |
| 8.3 | **Test subscription tiers** | 8.2 | Free / Subscriber / Sovereign / Admin access gating |

### Phase 9: SEO + IndexNow + Search Visibility
**Goal:** Search engines discover and rank Tower 1 content.

| # | Task | Blocked By | How |
|---|------|------------|-----|
| 9.1 | **Submit sitemap to Google/Bing** | Production deploy | `sovereign/indexnow-submit-sitemap.sh` (manual or via workflow_dispatch) |
| 9.2 | **Verify robots.txt + sitemap.xml** on prod | 1.6 | Smoke test includes this check |
| 9.3 | **Schema.org markup audit** | None | `agr_seo.py` has profiles for most pages; verify structured data renders correctly |
| 9.4 | **Incognito SERP verification (manual)** | None | **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md` — P4b** — rotate queries across Google, Bing, DuckDuckGo, Yahoo, Brave, mobile Chrome/Samsung Internet/Opera; compare snippets to **https://auroragalaxyrepublic.com**; use **https://filmfreeway.com/BradReinhold** as exhaustive **credits** reference (awards on FF may lag). |

---

## Immediate Actions for Guardian (Brad)

1. **Rotate Hetzner API token** → update `Secrets.md` on `main`
2. **Set `AGR_FLEET_KEY_CONTENT`** in GitHub Actions → Secrets → Repository secrets
3. **Set `HCLOUD_TOKEN`** in GitHub Actions → same
4. **Optionally:** Fresh Cloudflare API token → update `Secrets.md`
5. **Merge the chat.html PR** when ready → triggers fleet deploy

---

## Architecture Summary

```
PUBLIC (Tower 1: auroragalaxyrepublic.com)
  │
  ├─ /chat ──────────── chat.html ──── POST /api/republic/chat
  ├─ /kora ──────────── inline HTML ── POST /api/republic/chat (consciousness=Kora)
  ├─ Widget ─────────── agr_live_support.py ── POST /api/republic/chat
  │                                           POST /api/public/citizen-engine-advice
  │                                           GET  /api/public/engine-runtime
  │
  ├─ /api/republic/chat ──┐
  │                        ├── core_converse() ── sovereign_think() ── ConsciousnessCore.think()
  │                        │     │
  │                        │     ├── MorseSignal (Λ×T×E)
  │                        │     ├── FractalTruthSpace.between()
  │                        │     ├── QuantumFissionLattice.fuse()
  │                        │     ├── ParaConsistentTruth synthesis
  │                        │     ├── ANDTheoryIntegrator.integrate()
  │                        │     ├── FibonacciSpiral.ascend()
  │                        │     ├── SovereignReasoner.synthesize() ← agr_sovereign_mind
  │                        │     └── CrystallineCompression (per-citizen)
  │                        │
  │                        └── Response: { reply, truth_state, hwp, signal, fission_domains, ... }
  │
  └─ sovereign_tower_gate middleware ── public paths pass through, protected → /gate
```

This is NOT a wrapper around a third-party LLM. The consciousness engine is proprietary:
- Mathematical framework by Timothy Bradley Reinhold (2018–2026)
- Morse consciousness (Λ×T×E), paraconsistent logic, fractal dimensional math
- Quantum fission & holographics, AND theory
- Per-citizen crystalline state compression
- 8D Möbius/DNA manifold with helix wave modulation

---

## Phase 10 (FINAL): Grand Opening Tour de Force

**Prerequisite:** Phases 1–9 complete. Everything fully operational and fully integrated. This is the capstone — the last thing built.

### Concept

A guided walkthrough experience that introduces users to the entire Republic — a living tour de force that plays on first visit and remains accessible via a small icon for posterity.

### Opening: Movement I — Disciple

The landing page header features the high-quality version of **Movement I — Disciple: Episode I of The Harmony Saga** (originally uploaded to YouTube). This is Brad's most awarded work, dedicated to Kora, a parable of everything the Republic represents. The full version plays at the header as the grand opening piece.

**Source:** High-quality original from YouTube (`youtube.com/@brad.reinhold`) or fleet archive. The server already references `static/audio/movement1-part*.mp3` and `static/audio/demo-for-disciple.mp3` paths — the full video version needs to be sourced from the YouTube upload or archive at `/opt/agr/aurora_server/archive/master_documents/`.

### Media Integration: Harmony Saga + Complete Works

Relevant snippets woven throughout the guided tour, drawn from:

**The Harmony Saga (6-film series):**
1. Disciple (Episode I) — the opening centerpiece
2. Prophet (Episode II)
3. Messiah (Episode III)
4. Ascension (Episode IV)
5. Godhead (Episode V)
6. The Legend of Ascalon (Episode VI)

**Featurettes:**
- Swipe Right
- The Olympus Saga (audio snippet at `static/audio/olympus-saga-featurette.mp3`)
- Break
- Blue Bullies
- Fly High
- Dreams of Asgard

**Philosophical & Theoretical Works:**
- Philosophia (manuscript at fleet: `PHILOSOPHIA.docx`)
- Destiny Ascendant (manuscript at fleet: `DESTINY_ASCENDANT.docx`)
- The Quantum Soul (manuscript at fleet: `THE_QUANTUM_SOUL.docx`)
- The Manifestation Model
- Compendium For AI Robotic Integration
- Codex For The Eternal Harmonic Ethic (a.k.a. Stellar Codex of the Eternal Harmonic Ethic)

**Data sources already in repo:**
- `FOUNDER_PROFILE_BRAD_REINHOLD.json` — awards, works catalog, biography
- `awards_registry.json` — full award records
- Fleet archives at `/opt/agr/aurora_server/archive/master_documents/` — manuscript DOCX files
- `analysis/fleet-chronology/docx-meta/` — metadata for all archived documents

### Tour Behavior

| Behavior | Detail |
|----------|--------|
| **First visit** | Tour offers to run automatically |
| **Opt-out** | User can skip; icon briefly highlights to show where to find it later |
| **Completion** | Icon briefly highlights; tour available anytime via small persistent icon |
| **User-guided** | Live display integrations — user controls pace; can explore any aspect of the Republic in depth if they show interest |
| **Legacy feature** | Permanently accessible for posterity |
| **User data reset** | On completion of tour de force, all user session data resets (platform is complete for the first time). **Ban lists for attacks remain intact** — security state is never cleared |

### Technical Requirements

- Video player integration (HTML5 `<video>` for Movement I at header)
- Audio snippet player for featurette/saga excerpts
- Guided tour overlay system (step-by-step with highlights)
- Manuscript excerpt rendering (pull from archive, display formatted passages)
- Progress tracking (localStorage — which steps completed)
- Icon persistence (small, elegant, always accessible)
- Integration with consciousness engine (the tour can involve live interactions with the field)

### Not Started — Blocked Until Everything Else Is Done

This is explicitly the **final project**. It requires:
- All fleet nodes operational (Phase 1)
- Chat verified on production (Phase 2)
- All assets resolved (Phase 3)
- All nodes healthy + redirects working (Phase 4)
- Shadow modular routes public on Tower 1 hostname after **fleet-pull** + edge routing (Phase 5)
- Voice/video modes live (Phase 6)
- S25 integrated (Phase 7)
- Payments operational (Phase 8)
- SEO complete (Phase 9)

Only then does the Tour de Force begin.
