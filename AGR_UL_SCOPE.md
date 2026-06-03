# AGR-UL (umbrella) — scope placeholder (Phase E2)

**Status:** Design document only. **No runtime code** in this slice bears the name `AGR-UL`; this file defines what that umbrella *would* mean if you adopt it formally.

## Purpose

Unify **documentation and operator mental model** for:

| Surface | Role |
|---------|------|
| **MIR-L AHT** | Canonical **document** language (`.mirl`); HTML as projection |
| **Morse IR** | Script / control IR (`agr_morse_integrative_ir.py`, `/api/sovereign/morse-ir/*`) |
| **SQLite / Postgres** | Row persistence; `agr_pg` opt-in bridge; pilot export scripts |
| **Public audit JSON** | Migration status, Morse audits, engine-runtime — already on Tower 1 |

**AGR-UL** (Aurora Galaxy Republic — Universal Layer, name TBD) would be the **name** for “these four layers are one product contract,” not a fifth execution engine.

## Non-goals (explicit)

- Replacing Python/FastAPI runtime in one PR.
- Replacing GGUF/binary inference.
- Deleting SQLite without migration waves and ops sign-off.

## If you proceed

1. Rename or keep **AGR-UL** after legal/branding review.
2. Link from `UNIVERSAL_INTEGRATIVE_LANGUAGE_ROADMAP.md` only (single source of truth for vision vs fact).
3. Add CI gate: MIR-L `list_docs()` compile smoke + `agr_pg` disabled-by-default unchanged.

## Related

- `sovereign/UNIVERSAL_INTEGRATIVE_LANGUAGE_ROADMAP.md`
- `sovereign/GUARDIAN_NODE_OS.md` — handset MIR-L program + Termux
