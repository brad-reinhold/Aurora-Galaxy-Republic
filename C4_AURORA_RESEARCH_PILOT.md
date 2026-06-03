# Phase C4 pilot — `aurora_research.db` (live-state research slice)

**Chosen DB:** `aurora_server/data/aurora_research.db` — used by `/api/republic/live-state` for `research.papers` and `research.experiments` counts (`republic_os_server.py`). Distinct from `research.db` (research hub file).

**Postgres schema:** `agr_aurora_research` (basename `aurora_research` with default `AGR_PG_SCHEMA_PREFIX=agr_`).

---

## 1. Backup

```bash
cp -a /opt/agr/aurora_server/data/aurora_research.db \
  "/opt/agr/backups/aurora_research.db.bak.$(date -u +%Y%m%dT%H%M%SZ)"
```

Rollback: restore that file; no SQLite deletion in this pilot.

---

## 2. Export (generic script)

```bash
export PILOT_SQLITE_PATH=/opt/agr/aurora_server/data/aurora_research.db
export PILOT_EXPORT_LABEL=C4_aurora_research
export PILOT_EXPORT_OUT=/opt/agr/backups/c4_aurora_research_export_$(date -u +%Y%m%dT%H%M%SZ)
python3 sovereign/scripts/pilot-export-sqlite-db.py
```

(Legacy `pilot-export-research-db.py` is a thin wrapper calling the same logic; prefer **`pilot-export-sqlite-db.py`** for new pilots.)

---

## 3. Load into Postgres

Create schema **`agr_aurora_research`** and tables matching SQLite names (`research_papers`, `experiments`, … — see export manifest). Load from JSONL.

---

## 4. Dual-read counts

```bash
export PILOT_SQLITE_PATH=/opt/agr/aurora_server/data/aurora_research.db
export PILOT_PG_BASENAME=aurora_research
export AGR_PG_ENABLED=1
export AGR_PG_DSN='postgresql://...'
python3 sovereign/scripts/pilot-dual-read-sqlite-counts.py
```

---

## 5. Next wave (C4+)

Pick another `data/*.db` from `sovereign/SQLITE_DATA_LAYER_INVENTORY.md` and repeat with new `PILOT_*` env vars.

## Scripts (shared)

| Script | Role |
|--------|------|
| `sovereign/scripts/pilot-export-sqlite-db.py` | Any `PILOT_SQLITE_PATH` → JSONL + manifest |
| `sovereign/scripts/pilot-dual-read-sqlite-counts.py` | SQLite vs `agr_pg.count(PILOT_PG_BASENAME, …)` |

## Related

- `sovereign/C3_RESEARCH_DB_PILOT.md` — first pilot (`research.db`)
- `sovereign/AGR_POSTGRES_BRIDGE.md` — schema naming
