"""
Sovereign web-research catalog — lightweight, on-disk (no external crawl by default).

Tower / fleet operators append curated rows to ``data/web_research/catalog.json``
(or use ``start_web_research`` from the CEO shell) so ``search_research`` and
``get_domain_research`` return **evidence-backed** entries instead of empty stubs.

This replaces the previous no-op stub module while full RAG / crawler pipelines
are restored from fleet (see ``REMAINING_WORK_ORDER_OF_OPERATIONS.md`` Phase 5).
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_BASE = Path(__file__).resolve().parent
_DATA_DIR = _BASE / "data" / "web_research"
_CATALOG_PATH = _DATA_DIR / "catalog.json"
_RUNS_PATH = _DATA_DIR / "runs.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_catalog() -> list[dict[str, Any]]:
    _ensure_dirs()
    if not _CATALOG_PATH.exists():
        _CATALOG_PATH.write_text("[]\n", encoding="utf-8")
        return []
    try:
        raw = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)]
    return []


def _write_catalog(rows: list[dict[str, Any]]) -> None:
    _ensure_dirs()
    _CATALOG_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _append_run(event: dict[str, Any]) -> None:
    _ensure_dirs()
    line = json.dumps(event, ensure_ascii=True) + "\n"
    with _RUNS_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def get_research_stats(*_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        rows = _read_catalog()
    domains: dict[str, int] = {}
    for row in rows:
        d = str(row.get("domain") or "").strip().lower()
        if d:
            domains[d] = domains.get(d, 0) + 1
    return {
        "ok": True,
        "catalog_path": str(_CATALOG_PATH),
        "entries": len(rows),
        "domains": domains,
        "updated_at": _now_iso(),
        "note": "Counts are from on-disk catalog only; no live crawl unless operator adds rows.",
    }


def get_domain_research(domain: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    dom = str(domain or "").strip().lower()
    with _LOCK:
        rows = _read_catalog()
    hits = [r for r in rows if str(r.get("domain", "")).strip().lower() == dom]
    return {"ok": True, "domain": dom, "count": len(hits), "items": hits}


def _tokenize(q: str) -> list[str]:
    return [t for t in re.split(r"\s+", q.strip().lower()) if t]


def search_research(query: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    q = str(query or "").strip()
    tokens = _tokenize(q)
    with _LOCK:
        rows = _read_catalog()
    if not tokens:
        return {"ok": True, "query": q, "count": len(rows), "items": rows}
    hits: list[dict[str, Any]] = []
    for row in rows:
        hay = " ".join(
            str(row.get(k, ""))
            for k in ("title", "url", "domain", "summary", "tags")
        ).lower()
        if all(t in hay for t in tokens):
            hits.append(row)
    return {"ok": True, "query": q, "count": len(hits), "items": hits}


def get_research_fact(key: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    kid = str(key or "").strip()
    with _LOCK:
        rows = _read_catalog()
    for row in rows:
        if str(row.get("id", "")).strip() == kid:
            return {"ok": True, "item": row}
    return {"ok": False, "error": "not_found", "id": kid}


def start_web_research(topic: str = "", *_a: Any, **_kw: Any) -> dict[str, Any]:
    """
    Record an operator-initiated research run (does not crawl the public web).

    ``topic`` is stored as a run log line; curated results belong in ``catalog.json``.
    """
    run_id = str(uuid.uuid4())
    payload = {
        "id": run_id,
        "topic": str(topic or "").strip(),
        "status": "logged",
        "ts": _now_iso(),
    }
    with _LOCK:
        _append_run(payload)
    return {
        "ok": True,
        "run": payload,
        "catalog_path": str(_CATALOG_PATH),
        "hint": "Append JSON objects to catalog.json or POST via future admin route.",
    }
