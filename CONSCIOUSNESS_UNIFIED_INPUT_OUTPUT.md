# Consciousness engine — one pipeline for all I/O

**Canonical:** https://auroragalaxyrepublic.com

Brad’s requirement: **no canned replies**. Any entity messages the Republic — web `/chat`, OS shell, media suite, fleet orchestrator, future billions of sessions — the system **reads the input**, **thinks** through the same sovereign mind (morpheme + reasoning + narrative ledger), **writes outputs** (chat text, code diffs, media plans, learning events).

## Single pipeline (authoritative)

```
INPUT (any channel)
  → hear() + recall(session) + narrative ledger + symbolic surface
  → sovereign_think() → SovereignReasoner.synthesize()  [morpheme / research / moral gradient]
  → speak() → persist turn + log_learning_event
OUTPUT (JSON / UI / code / media job)
```

**Not separate:** shadow `/api/chat` rooms, shadow CCE stubs, or `conversational_resonance` greeting arrays (disabled unless `AGR_ALLOW_CANNED_CHAT_SHORTCUTS=1` for tests only).

## Surfaces (same engine)

| Surface | Entry | Notes |
|---------|--------|--------|
| Public web `/chat` | `POST /api/republic/chat` | `chat.html` → same API; any browser/device |
| Kora `/kora` | same API, Kora persona | |
| Domain modes | `consciousness` field | philosophy … education + law |
| OS / Termux | loopback `:5000` | Guardian node; export optional `AGR_GUARDIAN_LOCAL=1` for device context only |
| Coding / orchestrator | `sovereign_think` on task prompts | Same read-think-write; evolution via orchestrator state (separate track) |
| Media suite | future routes | Must call `converse()` or `sovereign_think`, not template workers |

## Device and scale

- **Device-agnostic:** HTTP + JSON; no browser-specific logic in the engine (UI is thin).
- **Session continuity:** `session_id` + SQLite turns + narrative ledger bindings (global scale = sharded sessions per citizen, not one global RAM).
- **Learning:** `log_learning_event` on each `converse()` turn (citizen_consciousness log); Phase 1 expands to full CCE DB persistence.

## Operator defaults (Nothing Phone / fleet)

```bash
# Default in code: substantive-only synthesis (no action needed).
# Do NOT set AGR_ALLOW_CANNED_CHAT_SHORTCUTS unless running legacy tests.

export AGR_GUARDIAN_LOCAL=1   # optional: device knows Brad on handset
# Restart after pull:
# pkill -f uvicorn; cloudflared tunnel run …
```

## Verification

```bash
bash sovereign/scripts/cloudflare-edge-triage.sh
bash sovereign/scripts/chat-coherence-live-matrix.sh
TOWER1_LIVE_TEST=1 bash sovereign/scripts/chat-coherence-live-matrix.sh
```

## Roadmap (honest)

| Item | Status |
|------|--------|
| No canned chat shortcuts | **Default off** in `agr_sovereign_mind` |
| Morpheme + reasoning on every turn | **On** |
| CCE DB per citizen | **Partial** — `log_learning_event` wired; full `get_cce` audit in Phase 1 |
| Code self-evolution | Orchestrator + human merge gates — not autonomous rewrite without review |
| Media generation | Routes must consume same think output — build per suite |

See also: `sovereign/REPUBLIC_LIVE_INTEGRATION_PLAN.md`, `sovereign/CHAT_COHERENCE_E2E_RUNBOOK.md`.
