# PostgreSQL bridge (`agr_pg`) — Phase C2

## Purpose

`/api/republic/live-state` uses `agr_pg.count(basename, table, where)` when the module imports. If Postgres returns **0** or errors, the handler **falls back to SQLite** (`republic_os_server.py`). This keeps production safe until schemas exist.

## Enable (operator)

1. Install **`psycopg2-binary`** (or `psycopg2`) in the app venv on the node.
2. Create Postgres schemas and tables mirroring the SQLite domains you want to dual-read (naming below).
3. Set environment on the service (systemd unit, `.env`, or `agr_env`):

| Variable | Required | Description |
|----------|----------|-------------|
| `AGR_PG_ENABLED` | Yes | `1`, `true`, `yes`, or `on` |
| `AGR_PG_DSN` or `DATABASE_URL` | Yes | libpq connection string, e.g. `postgresql://user:pass@host:5432/dbname` |
| `AGR_PG_SCHEMA_PREFIX` | No | Default `agr_`. Must match `^[a-z][a-z0-9_]*$` |

## Schema naming

SQLite file `data/social.db` → basename `social` → Postgres schema **`agr_social`** (with default prefix).

Tables keep **SQLite names** (e.g. `posts`, `threat_log`). Identifiers are validated; only `[a-z][a-z0-9_]{0,62}`.

## Query contract

`count(basename, table, where)` only runs SQL when **`where` is exactly `1=1`** (matches all current `live-state` callers). Any other clause returns `0` without connecting (fail-closed).

`pg_query_one` is reserved for future parameterized reads; it still returns `{}`.

## Verify

```bash
# From app host with env set:
python3 -c "import os; os.environ['AGR_PG_ENABLED']='1'; os.environ['AGR_PG_DSN']='...'; import agr_pg; print(agr_pg.pg_enabled(), agr_pg.count('social','posts','1=1'))"
```

## Related

- `sovereign/SQLITE_DATA_LAYER_INVENTORY.md` — which `.db` files exist in code
- `aurora_server/tests/test_agr_pg.py` — unit tests (mocked `psycopg2`)
- `sovereign/C3_RESEARCH_DB_PILOT.md` — **Phase C3** export + dual-read runbook for `research.db`
- `sovereign/C4_AURORA_RESEARCH_PILOT.md` — **Phase C4** wave for `aurora_research.db`
