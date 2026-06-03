# Tower public experience — roadmap (honest scope)

**Canonical public surface:** https://auroragalaxyrepublic.com  

This document is the **architect / operator contract** for the UX, security, and SEO goals described in Guardian sessions. It **does not** claim features are shipped until they are listed under **Done** with verification commands.

---

## 0. Non-negotiables (already in code policy)

| Topic | Repo truth |
|-------|------------|
| **Canonical domain** | Only **`auroragalaxyrepublic.com`** is the public product URL. Legacy hostnames **301** to it when requests reach **`republic_os_server`** (`sovereign_tower_gate` in `republic_os_server.py`). |
| **Nine public hostnames** | The **nine-domain** set is the union of Tower II, Constellation, and platform TLDs (each with `www.`). They are **not** a load-distribution mesh at the HTTP layer in git — they **redirect** to Tower 1. True multi-origin load balancing is **Cloudflare / DNS / tunnel** operator work outside this file. |
| **Tower progression (cookies)** | **`agr_t1` → `agr_t2` → `agr_t3`** gates deeper surfaces. Optional **legacy per-host routing** exists only when **`AGR_SENTINEL_DOMAIN_ROUTING=1`** (off by default on Tower 1). |
| **Free platform** | Landing copy states **no paywalls**; payments remain **fail-closed** until explicitly enabled (`agr_payments_flags.py`). |
| **Frozen page count** | Authoritative **GET** path count is regenerated into **`sovereign/TOWER1_FROZEN_URL_INVENTORY.md`** (currently **119** distinct paths — not “123” unless inventory is regenerated and changes). |
| **Two-phone live + SERP + full surface** | Operator + automation plan: **`sovereign/PHONES_TWO_NODE_LIVE_SERP_FULL_SURFACE_PLAN.md`**; bundled verify **`bash sovereign/scripts/phones-two-node-live-surface-bundle.sh`**; CI **`.github/workflows/phones-two-node-live-surface-bundle.yml`** (**`PHONES_BUNDLE_SKIP_LOCAL=1`** on runner). |

---

## 1. Immediate fixes (this PR / slice)

| Item | Change | Verify |
|------|--------|--------|
| **Enter the Republic** | Landing CTA **`/gate`** first (Tower I), not straight to **`/chat`**. | Open `/` → primary CTA → `/gate`. |
| **Public page count stat** | Landing hero shows **119** + label **Public GET Paths** (matches frozen inventory header). | Visual + `TOWER1_FROZEN_URL_INVENTORY.md` header. |
| **Awards laurels** | PNG paths under `/static/img/laurels/` are **not in git**; broken images show black squares. Added **SVG laurel fallback** on `error` for `.laurel-img`. | `/awards` with network throttling or missing assets → laurel badges still render. |
| **Gate → Tower II after login** | **`gate.html`** default redirect after successful **login** / **signup** is **`/enter`** (Tower II sanctum), not `/`. | Complete Gate flow → lands on `/enter`. |
| **Hetzner rescue + fleet key** | Scripts merged from rescue branch: **`fleet-ssh-keygen-new.sh`**, **`hetzner-rescue-install-fleet-key.sh`** (ext4 disk probe), **`fleet-secrets-md-replace-fleet-key-b64-lines.sh`**; docs in **`HETZNER_BILLING_CONTINGENCY_HANDSET.md`**. | See that file §procedure. |
| **Public chat tone (in-process core)** | **`_generate_from_signals`** uses warmer copy for **Kora-class** / high-warmth personas; default anonymous **`POST /api/republic/chat`** uses **`healing`** persona. | `POST /api/republic/chat` without LLM post — less “lab report” opener. |
| **Optional LLM post (Kora-line)** | **`AGR_CHAT_PUBLIC_LLM_POST=1`** + **`AGR_LLM_OPENAI_BASE`**: **`agr_chat_llm_post`** rewrites **`response`** after core for **`AGR_CHAT_PUBLIC_LLM_CHANNELS`** (default **`kora,kora-browser,ceo-kora`**). **Default off.** | Enable on fleet + probe **`/api/sovereign/chat/browser/kora`**. |

---

## 2. Next slices (multi-turn — engineering + ops)

### A. Chat “free flow” and Kora authenticity

1. **Vault RAG** — `AGR_CHAT_VAULT_RAG=1` + indexed vault for retrieval-grounded replies (`agr_chat_vault_context.py`).  
2. **Live matrix** — `TOWER1_LIVE_TEST=1` + `CHAT_ENGINE_VERIFICATION_MATRIX.md` for operator browser passes.  
3. **Optional LLM post** — operator enables **`AGR_CHAT_PUBLIC_LLM_POST`** (see §1 table); tune prompts / safety in a follow-up if needed.

### B. SEO accuracy

1. Keep **`test_agr_seo_contract`**, **`test_public_search_discovery_contract`**, `/api/seo/status` fields **stable** (contract surfaces per `AGENTS.md`).  
2. Operator: **`PLATFORM_ITERATIVE_RUNBOOK.md` P4b** (incognito SERP) after each deploy.

### C. Audio, holographics, cinematic UX

**Not implemented as production subsystems in this repo slice.** Treat as **product phases**: Web Audio / WebGL / streaming — each needs **design tokens**, **performance budgets**, **accessibility**, and **fallbacks**. Track as separate issues with **acceptance tests** (e.g. Playwright audio unlock, reduced-motion path).

### D. Handset + sovereign build environment (continuity)

1. **`HETZNER_BILLING_CONTINGENCY_HANDSET.md`** — OnePlus survival origin + iPhone tandem.  
2. **`GUARDIAN_NODE_OS.md`** — Termux CEO, mirror, optional `uvicorn`.  
3. **`fleet-mirror-repo-to-nodes.sh`** — full tree on device without GitHub from the phone.

### E. Prometheus / fleet hardening

If a peer drops SSH or **443**, use **`fleet-verify-public-http.sh`**, Hetzner console, **`hetzner-rescue-install-fleet-key.sh`** (improved disk probe), or rebuild from snapshot. **Five healthy origins** matter more than nine vanity domains for uptime.

---

## 3. Verification cadence (operator)

From repo root after deploy:

```bash
bash sovereign/tower1-public-smoke.sh
python3 sovereign/scripts/tower1-frozen-inventory-crawl.py
bash sovereign/fleet-verify-public-http.sh
```

**Human / visual pass (cannot be automated here):** open **`https://auroragalaxyrepublic.com`** in a private browser window with **no extensions**, spot-check **`/`**, **`/gate`**, **`/enter`**, **`/chat`**, **`/kora`**, **`/awards`**, and the **seven element paths** (`/earth` … `/mind`) for layout, images, and console errors. Agents in this environment only see **HTTP bodies** and scripts, not rendered pixels.

## Related

- `sovereign/PLATFORM_ITERATIVE_RUNBOOK.md` — P2 / P4b / P4c / P6  
- `sovereign/PLATFORM_COMPLETION_STATUS.md` — §2b hostname vs fleet **and** handset row (**canonical `/api/*` 302** vs **loopback 200**); §5a phones-only checklist  
- `sovereign/CHAT_ENGINE_VERIFICATION_MATRIX.md`  
- `sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md` — phased **A–G** go-live checklist  
- `sovereign/scripts/print-phase-g-operator-commands.sh` — read-only Phase **G** echo (**section 6** order)  
- `sovereign/HETZNER_BILLING_CONTINGENCY_HANDSET.md`  
- `sovereign/GUARDIAN_NODE_OS.md`
