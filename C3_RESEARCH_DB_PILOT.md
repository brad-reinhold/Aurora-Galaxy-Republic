# Phase C3 pilot — `research.db` (export, verify, dual-read)

**Why this DB:** `aurora_server/data/research.db` is referenced from `republic_os_server.py` for research flows and is **not** one of the high-churn consciousness/social stores. It is a safe first pilot for **export → verify → count parity** before any cutover.

**Cutover:** This pilot does **not** switch the app to Postgres for research. `live-state` still aggregates `aurora_research.db` for culture metrics; `research.db` is parallel research-hub storage. Full cutover would be a later PR with explicit read paths.

---

## 1. Backup (operator)

```bash
cp -a /opt/agr/aurora_server/data/research.db \
  "/opt/agr/backups/research.db.bak.$(date -u +%Y%m%dT%H%M%SZ)"
```

Rollback = restore that file and restart `agr-republic.service` if anything went wrong (nothing in this pilot mutates SQLite).

---

## 2. Export (read-only JSONL + manifest)

From a checkout with Python 3.11+:

```bash
export PILOT_SQLITE_PATH=/opt/agr/aurora_server/data/research.db
export PILOT_EXPORT_LABEL=C3_research
export PILOT_EXPORT_OUT=/opt/agr/backups/c3_research_export_$(date -u +%Y%m%dT%H%M%SZ)
python3 sovereign/scripts/pilot-export-sqlite-db.py
```

(Legacy: `pilot-export-research-db.py` delegates to the same exporter.)

Output: `manifest.json` + one `.jsonl` per table under `PILOT_EXPORT_OUT`. Paths are gitignored under `sovereign/state/` if you use the default (dev only).

---

## 3. Load into Postgres (operator)

1. Create schema **`agr_research`** (see `sovereign/AGR_POSTGRES_BRIDGE.md` — basename `research` from `research.db`).
2. For each table in SQLite, create the same table name in Postgres with compatible types, then load from JSONL (use `COPY`, `psql \copy`, or a one-off loader). **Do not** drop SQLite until counts match and ops sign off.

---

## 4. Dual-read count verification

```bash
export PILOT_SQLITE_PATH=/opt/agr/aurora_server/data/research.db
export PILOT_PG_BASENAME=research
export AGR_PG_ENABLED=1
export AGR_PG_DSN='postgresql://...'
python3 sovereign/scripts/pilot-dual-read-sqlite-counts.py
```

(Legacy: `pilot-dual-read-research-counts.py` delegates here; omit `PILOT_PG_BASENAME` only when using `RESEARCH_DB_PATH` alone — basename defaults to file stem `research`.)

- Exit **0** = every table: `agr_pg.count("research", table, "1=1")` equals SQLite `COUNT(*)`.
- `AGR_PILOT_PG_STRICT=0` (or legacy `AGR_C3_PG_STRICT=0`) — still fails on numeric mismatch; only use if you need to log partial progress (tables with data in SQLite but empty PG still fail in strict mode).

Uses the same **`agr_pg`** rules as `/api/republic/live-state` (identifier-safe, `WHERE 1=1` only).

---

## 5. Next (C4 / waves)

Repeat for another domain (e.g. read-mostly slice of `aurora_research.db` tables) after this pilot is green on staging + one production node.

## Scripts

| Script | Role |
|--------|------|
| `sovereign/scripts/pilot-export-sqlite-db.py` | **Canonical** — any `PILOT_SQLITE_PATH` → JSONL + `manifest.json` |
| `sovereign/scripts/pilot-dual-read-sqlite-counts.py` | **Canonical** — SQLite vs `agr_pg` for `PILOT_PG_BASENAME` |
| `pilot-export-research-db.py` / `pilot-dual-read-research-counts.py` | Wrappers for C3 defaults |
