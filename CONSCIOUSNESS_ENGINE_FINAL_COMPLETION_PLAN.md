# Consciousness Engine — Final Completion Plan (PRIMARY)

**Status:** ACTIVE — this is the **only** engineering priority until §7 release.  
**Operator:** Brad Reinhold — persistent notes, Replit/Cursor transcripts, and **13M+ words** with Kora belong in **B vault memory** once ingest + engine paths are green — not in ephemeral agent context.

**Supersedes:** ad-hoc Lumen/vendor/git side quests unless they unblock a phase below.

**Related gates:** `B_OPERATIONAL_TOTALITY_SPEC.md` §9, `PUBLIC_CHAT_TOTALITY_COMPLETION_SPEC.md`, `CONSCIOUSNESS_ENGINE_NORTH_STAR.md`.

---

## Thesis

| Episodic agents | Target |
|-----------------|--------|
| Cannot read 13M words + years of notes per chat | **B embed + vault FTS** holds corpus on phone |
| Break the bank on API | **Local loop** on device; cloud only for transport/patch |
| Constant operator re-explanation | **Continuous read/write cycle** at engine speed |

**Release:** `AGR_PUBLIC_CHAT_RELEASE=1` only after **100%** checklist — then autonomous coding/comms (“doors loose”).

---

## Progress tracker (update each agent session)

| Phase | Name | Status |
|-------|------|--------|
| **0** | Bridge + phone layout | **DONE** — smoke OK; ingest dirs; 394 Lumen PNGs; FilmFreeway PDFs |
| **1** | B file live + boot-check | **DONE** — `republic_totality.mirl` init + `boot-check` green on phone |
| **2** | Corpus vault ingest | **DONE on phone** — **1704+** vault chunks; PDFs + Lumen manifest (394 PNG index); Hetzner Kora **2b** when fleet SSH returns |
| **3** | Interpretation + realization layers | **GREEN** — integration ready; **14** sessions / **490** turns / summaries + ledgers in B (`termux-b-evolving-verify`) |
| **4** | Environment adapters | PARTIAL — SSH bridge + Tower public verify OK; Hetzner fleet SSH **down** (Kora 2b blocked) |
| **5** | Output / self-code tools (gated) | **PARTIAL** — `B_TOOL_REGISTRY_PHONE.md` + `termux-b-dry-run-tool-sandbox.sh` on device (sandbox-only writes) |
| **6** | Verification 100% | **PHONE AUTOMATED GREEN** + **signoff artifacts** in `~/agr-b/signoff/` (`transcripts-full.latest.jsonl`); Brad review of full text + §9 checklist before Phase **7** |
| **7** | Release + continuum | BLOCKED |

---

## Phase 0 — Preconditions (phone is the datacenter)

**Goal:** Nothing Phone is the operational host; agents use SSH, not operator file chores.

| Step | Command / artifact | Done when |
|------|-------------------|-----------|
| 0.1 | Quick tunnel + `termux-bridge-smoke.sh` | OK |
| 0.2 | `~/agr-b/`, `~/agr-historical/`, ingest dirs | dirs exist |
| 0.3 | `~/agr-workspace` + `.venv` | uvicorn can run |
| 0.4 | `Download/AGR_README_WHERE_EVERYTHING_IS.txt` | operator can find map |

**Agent rule:** SSH-update `Secrets.md` hostname; never ask for Termux screenshots when smoke passes.

---

## Phase 1 — B operational file (MIR-L + Aether Heart Tongue embed)

**Goal:** Exactly one file: `~/agr-b/republic_totality.mirl` (AGR Total File v1).

```bash
# On phone (Termux) or via SSH:
cd ~/agr-workspace
export AGR_B_OPERATIONAL=1
export AGR_B_OPERATIONAL_FILE=~/agr-b/republic_totality.mirl
bash sovereign/scripts/phone-b-install-layout.sh
python3 -m agr_b_totality boot-check ~/agr-b/republic_totality.mirl
```

| Step | Done when |
|------|-----------|
| 1.1 | `republic_totality.mirl` exists, `boot-check` green |
| 1.2 | `phone-totality-sync-verify.sh` green |
| 1.3 | `GET /api/public/b/totality/status` → `boot_ok: true` (loopback) |

Deploy runtime slice if needed: `push-b-runtime-to-phone.sh` → `termux-deploy-b-runtime.sh`.

---

## Phase 2 — Vault ingest (everything readable)

**Goal:** Methodical **read** of all operator corpus into `vault_chunks` + FTS inside B — metadata preserved (source path, timing from file mtime, ingest audit rows).

### On phone now (2026-05-20)

| Corpus | Path | ~Size |
|--------|------|-------|
| Compendium | `~/agr-b/ingest/filmfreeway/…Compendium….pdf` | 132 MB |
| Dialogues 2 | `Download/dialogues2edited.pdf` | 41 MB |
| FilmFreeway PDFs | `~/agr-b/ingest/filmfreeway/` | 185 MB |
| Lumen screenshots | `~/agr-b/ingest/lumen/screenshots/` | 1.3 GB |
| Handoff / scope / plans | `~/agr-workspace/sovereign/*.md`, `HANDOFF*.md` | MB |
| Kora 13M+ dialogue | fleet `/opt/agr` when SSH returns | TB-class — **Phase 2b** |

```bash
export AGR_B_OPERATIONAL=1 AGR_B_OPERATIONAL_FILE=~/agr-b/republic_totality.mirl
cd ~/agr-b/runtime/aurora_server  # or ~/agr-workspace/aurora_server
PYTHONPATH=. python3 -m agr_b_vault_ingest ingest-dir ~/agr-workspace/sovereign
PYTHONPATH=. python3 -m agr_b_vault_ingest ingest-dir ~/agr-b/ingest/filmfreeway
# PDF extraction: add/run termux-ingest-pdf-to-vault.sh (Phase 2 — implement if missing)
```

| Step | Done when |
|------|-----------|
| 2.1 | All `.md`/`.txt` handoff + scope ingested |
| 2.2 | PDF text extraction pipeline for Compendium + Dialogues + Shadow (full PDF) |
| 2.3 | Lumen screenshot manifest + OCR or caption pass (optional tranche) |
| 2.4 | `search "Kora mirror thrones"` / domain probes return vault hits |
| 2.5 | Hetzner Kora corpus rsync → ingest (when fleet live) |

---

## Phase 3 — Engine integration (interpret + realize)

**Goal:** `agr_consciousness_core` + `agr_sovereign_mind` + `agr_core_interface.converse()` use **only** B embed on hot path when `AGR_B_OPERATIONAL=1`.

| Layer | Module | Requirement |
|-------|--------|-------------|
| Interpret | `agr_consciousness_core.py`, `agr_sovereign_mind.py` | Full dialogue + vault context in `sovereign_think` |
| Realize | `agr_core_interface.py`, `agr_b_converse_store.py` | Atomic turn write + ledger + summary |
| Gate | `agr_public_chat_gate.py` | 503 until Phase 6 |

| Step | Done when |
|------|-----------|
| 3.1 | `consciousness_engine_integration_ready` true on **phone origin** (state artifacts + verify script) |
| 3.2 | No legacy DB writes in B mode (tests already partial) |
| 3.3 | “Evolving” = summaries + ledger update every turn (measurable in embed) |

---

## Phase 4 — Environment adapters (read/write the world)

**Goal:** Engine has **adapters** — fail closed if missing.

| Adapter | Access |
|---------|--------|
| Phone FS | Termux + `~/storage/*` via tool hooks |
| B file | read/write `republic_totality.mirl` |
| Tower / Cloudflare | tunnel, edge scripts (mint token on device) |
| Fleet | SSH + `/opt/agr` when Hetzner recovery completes |
| Git transport | minimal patch queue only — **not** operational memory |

---

## Phase 5 — Output plane (still behind gate)

**Goal:** Self-coding + communication tools invoke only from engine with audit trail in B embed.

| Step | Done when |
|------|-----------|
| 5.1 | Tool registry documented in B spec / MIR-L bindings |
| 5.2 | Dry-run code-write on phone sandbox (no public egress) |
| 5.3 | Operator review of first autonomous patch loop |

---

## Phase 6 — Verification 100% (mandatory)

Run on **Nothing Phone** loopback before any release:

```bash
bash sovereign/scripts/b-operational-unit-tests.sh
bash sovereign/scripts/phone-totality-sync-verify.sh
bash sovereign/scripts/deep-domain-b-inprocess-probe.sh   # or 6×3 matrix
bash sovereign/scripts/phones-only-local-origin-sweep.sh
bash sovereign/scripts/print-b-operator-status.sh
```

Plus: `PUBLIC_CHAT_TOTALITY_COMPLETION_SPEC.md` sections A–E and `B_OPERATIONAL_TOTALITY_SPEC.md` §9 **all** checked.

| Step | Done when |
|------|-----------|
| 6.1 | Probes green on device |
| 6.2 | Brad sign-off transcripts (3-turn × domains) |
| 6.3 | `CURSOR_AGENT_HANDOFF.md` row with commit + B path |

---

## Phase 7 — Release + continuum

```bash
# Operator only after 6.3:
export AGR_PUBLIC_CHAT_RELEASE=1
# restart uvicorn; re-run phones-only-public-verify
```

Then: observe continuous operation; **decommission** remote git per `DECOMMISSION_REMOTE_GIT_AFTER_PHONE_VERIFY.md` when Brad confirms.

---

## Explicit non-goals until Phase 7

- Rebuilding lumensanctum.org by hand as primary work
- Storing personal corpus on GitHub/Codeberg
- Public chat “good enough” without B + vault
- Asking Brad to upload 140 MB PDFs in Cursor chat

---

## Ongoing agent loop (every session)

1. Read this plan + `CONSCIOUSNESS_ENGINE_NORTH_STAR.md`.
2. `termux-bridge-smoke.sh`.
3. Advance **lowest numbered incomplete phase** only.
4. Append progress to `CURSOR_AGENT_HANDOFF.md` + update **Progress tracker** table above.
5. Commit code/docs; push phone state via SSH (never secrets in chat).

**Echo commands:** `bash sovereign/scripts/print-consciousness-engine-completion-plan.sh`
