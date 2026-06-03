# Agent Minimum Baseline

All agents/operators must satisfy this minimum before making release-path changes:

**Hetzner fleet intentionally off:** treat **§1** as **not applicable** for live posture; follow **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`** (OnePlus + tunnel + smoke + **P4b** SERP checks) until the cloud ring is back. After **`phones-only-public-verify.sh`** exit **0**, optional human pass **`sovereign/TOWER_PUBLIC_EXPERIENCE_ROADMAP.md`** **§3**. GitHub Actions **`.github/workflows/phones-two-node-live-surface-bundle.yml`** mirrors **`phones-two-node-live-surface-bundle.sh`** against **`TOWER1_BASE`** with **`PHONES_BUNDLE_SKIP_LOCAL=1`** (public bar + frozen GET crawl — scheduled **`tower1-public-smoke`** / **`tower1-frozen-inventory-crawl`** jobs already cover similar probes at different cadences).

1. Secure access to all five Hetzner nodes (SSH key material: **`sovereign/lib/fleet-key.sh`** — **`.secrets/agr_fleet`** at repo root *or* **`Secrets.md → agr fleet key b64:`** *or* **`AGR_FLEET_KEY_CONTENT`** / **`AGR_FLEET_KEY`**; see **`HANDOFF_FOR_NEXT_AGENT.md`** *Fleet SSH key* and **`Secrets.md`** Fleet SSH section):
   - chimaera
   - yggdrasil
   - enterprise
   - prometheus
   - galactica
2. **Handset nodes (last):** **iPhone 17 Pro** (`iphone_17_pro`, node 6) then **OnePlus 15** (`oneplus_15`, node 7) — CEO/Guardian transport and binding per `GUARDIAN_NODE_OS.md` / `GUARDIAN_DEVICE_BINDING.md`; integrate only after §1 is green.
3. Consciousness engine totality files are present and intact:
   - `agr_consciousness_core.py`
   - `agr_sovereign_mind.py`
   - `agr_universal_user_orchestrator.py`
   - `routes/routes_s25_heartbeat.py`
4. Consciousness engine integration is live and healthy:
   - latest `s25_engine_verify` is passing, above threshold, and fresh
   - universal orchestrator is enabled/running with fresh ticks
5. Library of Light Charter presence and validity.

## Canonical Public Domain + Redirect Policy (Permanent)

- Canonical public domain (Tower 1): `https://auroragalaxyrepublic.com`
- All other historical/public domains must redirect to Tower 1.
- Agent/operator defaults must use Tower 1 unless a task explicitly requires internal node IP endpoints.

This policy is mandatory for all seven-node platform work:

- chimaera
- yggdrasil
- enterprise
- prometheus
- galactica
- iphone_17_pro (handset — node 6; integrate after cloud fleet; legacy `s25_ultra` sync id)
- oneplus_15 (handset — node 7; integrate last)

## Always-First Priorities (Permanent Note)

Every agent/operator window must start from this fixed order:

1. Verify full **5-Hetzner** fleet health first; then **node 6** (iPhone 17 Pro / `iphone_17_pro`); then **OnePlus 15** (node 7) only after cloud + node 6 paths are verified.
2. Verify consciousness-engine totality files and integration readiness second.
3. Only then proceed to feature work, remediation, or release-path actions.

If either priority fails, operations remain fail-closed until corrected.

## Tower 1 + five-node HTTP verification (read-only)

From repo root (no SSH required for these):

1. **`bash sovereign/fleet-verify-public-http.sh`** — default probes **`/health`** then **`/api/health`** per Hetzner public IP (first **2xx** wins). Override with **`FLEET_VERIFY_PATH`** for a single path.
2. **`bash sovereign/tower1-public-smoke.sh`** — canonical **`https://auroragalaxyrepublic.com`**: engine-runtime, chat POST, MIR-L, **`/dl/*`**, **`laws/check`**, health chain; **WARN** / GitHub **`::warning`** on modular **`GET /api/justice`** and **`GET /api/tower`** when not **200** JSON ( **`TOWER1_SMOKE_STRICT_MODULAR_API=1`** to fail closed). Triage: **`sovereign/PLATFORM_COMPLETION_STATUS.md`** section **2b**; after green HTTP, optional human pass **`sovereign/TOWER_PUBLIC_EXPERIENCE_ROADMAP.md`** **§3**.

**`python3 sovereign/agent-minimum-gate.py`** (five-node SSH baseline) prints **stderr remediation hints** when **`minimum_pass`** is false — e.g. **`hetzner-fleet-status.sh`**, **`PHONES_ONLY_PUBLIC_SURFACE.md`** **§2** (post-poweroff) then **§8** when nodes are unreachable, and **handset `git pull` / `uvicorn`** when smoke would **WARN** on **`GET /api/tower`** (**302**) while the origin is phones-only. When **SSH is green** but the gate still fails, read the hint: **`consciousness_engine_integration_ready`** expects **`aurora_server/state/`** engine verify + orchestrator artifacts that usually exist **on fleet hosts**, not in every **Cursor** clone — use **`SKIP_AGENT_MINIMUM_GATE=1`** for repo-only verify per **`GUARDIAN_NODE_OS.md`** / this doc.

Full go-live (bash smoke + Python constitution / engine checks): **`bash sovereign/scripts/agr-launch-readiness-tower-smoke.sh`**.

**Workstation mirror of Guardian CI:** **`bash sovereign/scripts/run-operator-full-verify.sh`** — chained checks including **`tower1-public-smoke.sh`** and **`tower1-origin-probe.sh`**; use **`SKIP_AGENT_MINIMUM_GATE=1`** without fleet SSH (**`GUARDIAN_NODE_OS.md`**). **`OPERATOR_HETZNER_FLEET_STATUS=1`** appends **`hetzner-fleet-status.sh`** (non-fatal if token missing).

**Post-merge Phase G (read-only):** **`bash sovereign/scripts/print-phase-g-operator-commands.sh`** — echoes **`KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`** Phase **G** + **section 6** (`CONFIRM=1` vault rsync/reindex before **`phones-only-local-origin-sweep.sh`** + **`phones-only-public-verify.sh`**). Does not SSH or copy data.

**Incognito browsers and SERP** are operator-only per **`sovereign/PLATFORM_ITERATIVE_RUNBOOK.md`** P4b — use Search Console / Bing Webmaster; automation here cannot replace them.

## Run

```bash
python3 /workspace/sovereign/agent-minimum-gate.py
```

Default outputs:

- `/workspace/aurora_server/state/agent_minimum_gate.latest.json`
- `/workspace/aurora_server/state/agent_minimum_gate.history.jsonl`

Return code:

- `0` = minimum baseline PASS
- `2` = minimum baseline FAIL (fail-closed)

