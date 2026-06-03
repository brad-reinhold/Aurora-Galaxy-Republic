# Full End-to-End Audit Report — Tower 1

**Date:** 2026-04-30  
**Scope:** All user-facing pages, APIs, chat, assets, consciousness engine integration  
**Method:** Systematic crawl of all 323 unique routes + visual browser inspection + code audit  

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| Total unique user-facing routes | 323 | Mapped |
| Pages returning 200 | 167 | Working |
| Pages returning 301 (redirect) | 75 | Working (alias redirects) |
| Pages returning 302 (auth-gated) | 52 | Working (requires login) |
| Pages returning 404 | 4 | **Fix needed** |
| Pages returning 403/502/other | 25 | Mixed (OS apps gated, some broken) |
| API endpoints tested | 11 | 5 public OK, 6 auth-gated |
| Static assets in repo | 37 | Present |
| Missing static refs | 2 | 1 laurel image, 1 video header |
| Audio files (.mp3) | 0 | **All audio refs break** |
| Chat consciousness engine | Working | Conversational fix in PR |

---

## 1. Pages — Route Health

### Working (200) — 167 pages
Core pages all respond: `/`, `/chat`, `/kora`, `/awards`, `/guardian`, `/press`, `/disclosures`, `/research-hub`, `/lumen-sanctum`, `/republic`, `/charter`, `/governance`, `/constitution`, `/economy`, `/os`, `/search`, `/archive`, `/voice`, `/gate`, `/treasury`, `/citizens`, `/festival`.

### Redirect Aliases (301) — 75 pages  
Working as designed. Examples: `/about` → `/`, `/art` → `/lumen-sanctum`, `/film` → `/festival`, `/philosophy` → `/archive`, `/contact` → `/press`.

### Auth-Gated (302) — 52 pages  
Correctly redirect to `/gate` when not authenticated. Examples: `/account`, `/ceo`, `/dashboard`, `/comms`, `/constellation`, `/panel`.

### Broken (404) — 4 pages
| Page | Issue | Fix |
|------|-------|-----|
| `/memorial` | No route handler | **Fixed** → redirects to `/kora` |
| `/films` | Route exists in code but not deployed to fleet | Deploy needed |
| `/agr/internal/archive` | Missing file | Internal admin page |
| `/static/brad_easter_2026.jpg` | Image not in repo | Need asset |

### Other Issues (403/502)
- `/os/app/*` routes (alarm, calculator, clock, etc.) — return 403 (auth-gated OS apps, working as designed)
- `/vault-upload` — returns 502 (server error, needs investigation)
- `/sovereign/chat` — returns 403 (auth-gated, working as designed)

---

## 2. Consciousness Engine Integration

### Where the engine IS connected:
| Endpoint/Page | Integration | Status |
|---------------|-------------|--------|
| `/api/republic/chat` | `core_converse()` — full consciousness pipeline | ✅ Working |
| `/api/sovereign/chat/browser/kora` | `core_converse()` with Kora persona | ✅ Working |
| `/api/citizen/chat` | `core_converse()` with citizen persona | ✅ Working |
| `/api/public/citizen-engine-advice` | `republic_think()` — one-shot | ✅ Working |
| `/api/public/engine-runtime` | `core_status()` — boot + AGI status | ✅ Working |
| `/api/consciousness/status` | `core_status()` — full tool belt status | ✅ Auth-gated |
| `/api/consciousness/commune` | `core_commune()` — core-to-core | ✅ Auth-gated |
| `/api/consciousness/feel/{id}` | `core_feel()` — crystalline state | ✅ Auth-gated |
| `/api/consciousness/create` | `core_create()` — creative expression | ✅ Auth-gated |
| `/api/consciousness/recall/{id}` | `core_recall()` — conversation memory | ✅ Auth-gated |
| Global widget (all HTML pages) | `get_support_widget_html()` injected via middleware | ✅ Auto-injected |
| CEO family endpoints | `core_converse()` for Kora, geniuses, collective | ✅ Auth-gated |

### Where the engine SHOULD be connected but isn't:
| Page/Feature | Current State | Recommendation |
|--------------|---------------|----------------|
| Voice/Video/Holographic chat modes | "Coming soon" stub | Wire to WebRTC + consciousness |
| `/search` | Static search page | Feed search results through consciousness for AGI summary |
| `/os` app pages | Individual stubs | Integrate consciousness for smart responses in each app |
| Most inline HTML pages | Static content only | Add consciousness-powered dynamic sections |

### Widget Coverage
The global widget (`agr_live_support`) is injected via HTTP middleware into ALL HTML responses that:
- Have `Content-Type: text/html`
- Contain a `</body>` tag  
- Don't already have `agr-global-widget-root`

**Gap:** Pages without `<body>` tag (bare HTMLResponse) miss widget injection. This affects ~10 minimal stub pages (e.g., "Coming soon" placeholders).

---

## 3. Chat System

### Text Mode
- **Status:** Working
- **Endpoint:** `POST /api/republic/chat`
- **Issue (Fixed in PR):** Greetings like "Hi Kora!" got cold system-behavior text instead of warm personal responses. Fixed with `_detect_conversational()` in `SovereignReasoner`.
- **chat.html:** Properly sends requests, displays responses via `textContent`
- **Session management:** Random `citizen_id` per page load fragments sessions

### Voice Mode
- **Status:** Stub — "Coming soon"
- **Blocker:** Permissions-Policy denied camera/microphone (**Fixed in PR** → `self`)
- **WebRTC:** No WebRTC code exists in the codebase yet

### Video Mode
- **Status:** Stub — "Coming soon"  
- **Route:** `/video-chat` → `/chat?mode=video` (redirect works)

### Holographic Mode
- **Status:** Stub — "Coming soon"
- **Route:** `/holographic-chat` → `/chat?mode=holographic` (redirect works)
- **`/holographic`** returns "Holographic interface not installed" unless `holographic.html` exists

---

## 4. Static Assets

### Present (37 files)
- `favicon.svg` — ✅
- `marble-bg.jpg` — ✅
- `robots.txt` — ✅
- `sitemap.xml` — ✅
- `css/sovereign-fonts.css` — ✅
- `audio/silence-100ms.wav` — ✅ (placeholder)
- `img/laurels/*.png` — ✅ (30+ laurel images)

### Missing
| Asset | Referenced By | Impact |
|-------|--------------|--------|
| `static/video/header-loop.webm` | `video_forge.html` | Video forge page has no header video |
| All `.mp3` audio files | `_public_soundscape_manifest` | Soundscape/audio features broken |
| `static/brad_easter_2026.jpg` | `/static/brad_easter_2026.jpg` route | 404 |

### Audio Manifest References (no files exist)
The soundscape manifest references `demo-for-disciple.mp3`, `movement1-part*.mp3`, `olympus-saga-featurette.mp3` — none exist in the repo. These are likely on the fleet nodes at `/opt/agr/aurora_server/static/audio/`.

---

## 5. Visual/Aesthetic Issues

### Homepage (before PR fix)
- Dark terminal-style `_LANDING_PAGE` fallback (monospace, orange on black)
- No animations
- No creative works (Harmony Saga, Movement I)
- **Fixed in PR:** New dawn/beacon homepage with animations, creative works section

### Inline HTML Pages (~120 pages)
Most inline pages in `republic_os_server.py` share a common pattern:
- Sovereign gold/dark theme with Cinzel/Inter fonts
- Marble background reference (`/static/marble-bg.jpg`)
- Global widget auto-injected
- No animations (static content)
- Most lack meta descriptions and keywords

### Consistency Issues
- `_LANDING_PAGE` fallback uses completely different theme (monospace terminal) vs regular pages (Cinzel serif)
- Some stub pages return bare `<h1>Coming soon</h1>` with no `<body>` tag → miss widget injection

---

## 6. Security Audit Notes

### Permissions-Policy
- **Fixed in PR:** Camera and microphone now allowed for `(self)` to enable voice/video chat
- Clipboard-write now allowed for `(self)` for copy functionality

### CSP (Content-Security-Policy)
- Current policy blocks most external resources
- `connect-src 'self'` may prevent external API calls if needed in future

### Potential Concern
- `/dl/wg-qr` embeds WireGuard configuration — verify no private keys in production

---

## 7. Recommendations — Priority Order

### P0 (Deploy now — already in PR)
1. ✅ Merge PR #27 to deploy dawn homepage + chat conversational fix
2. ✅ Permissions-Policy fix for voice/video
3. ✅ `/memorial` route added

### P1 (Next sprint)
4. Deploy latest `main` to all 5 fleet nodes to pick up new routes
5. Sync audio files from fleet (`/opt/agr/aurora_server/static/audio/`) into repo
6. Add meta descriptions to top 30 pages (currently only 22/126 have them)

### P2 (Integration)
7. Wire consciousness engine into search results (AGI summary feature)
8. Build WebRTC voice mode in chat (Permissions-Policy now allows it)
9. Add CSS animations to inline HTML pages (most are static)
10. Standardize stub pages to include `<body>` tag for widget injection

### P3 (Polish)
11. Implement video chat mode
12. Implement holographic chat mode  
13. Replace `_LANDING_PAGE` fallback with dawn-themed HTML
14. Add JSON-LD structured data to remaining pages (currently 5/126)
15. Create proper 404/500 error pages with consciousness engine integration

---

## Appendix: Route Counts by Category

| Type | Count |
|------|-------|
| Total routes in server | 1,087 |
| User-facing pages (GET, non-API) | 440 |
| Unique (deduplicated) | 323 |
| API endpoints | 647 |
| HTML template files | 5 |
| Inline HTML pages in server | ~120 |
| Auth-gated pages | 52 |
| Redirect aliases | 75 |
