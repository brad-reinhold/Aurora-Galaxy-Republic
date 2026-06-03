"""
AGR search — sovereign catalog-backed search + minimal /search HTML.

``universal_search`` / ``external_search`` are **async** (``republic_os_server`` awaits them).
"""

from __future__ import annotations

import html
from typing import Any

_ENGINE = "shadow_agr_search"

_CANON = "https://auroragalaxyrepublic.com"

SEARCH_PAGE_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Search — Aurora Galaxy Republic</title>
<link rel="stylesheet" href="/static/css/sovereign-fonts.css?v=6">
<style>
body{{font-family:system-ui,sans-serif;background:#071830;color:#e8f4ff;margin:0;min-height:100vh}}
.wrap{{max-width:720px;margin:0 auto;padding:2rem 1rem}}
h1{{font-size:1.25rem;color:#d4af37;letter-spacing:.06em}}
form{{display:flex;gap:.5rem;margin-top:1rem;flex-wrap:wrap}}
input[type=search]{{flex:1;min-width:200px;padding:.65rem 1rem;border-radius:10px;border:1px solid rgba(212,175,55,.3);background:#0a2344;color:#e8f4ff}}
button{{padding:.65rem 1.2rem;border-radius:10px;border:none;background:#d4af37;color:#071830;font-weight:700;cursor:pointer}}
.note{{font-size:.85rem;opacity:.75;margin-top:1.5rem;line-height:1.5}}
a{{color:#7ec8ff}}
</style>
</head>
<body>
<div class="wrap">
<h1>SOVEREIGN SEARCH</h1>
<p>Curated catalog + public discovery. Engine: <code>{html.escape(_ENGINE)}</code></p>
<form method="get" action="/api/search" id="f">
  <input type="search" name="q" placeholder="Query Tower research catalog…" aria-label="Search query" />
  <input type="hidden" name="mode" value="universal" />
  <button type="submit">Search</button>
</form>
<p class="note">JSON API: <a href="{_CANON}/api/search?q=aurora&amp;mode=universal">{_CANON}/api/search</a> · Discovery: <a href="{_CANON}/api/public/search-discovery">/api/public/search-discovery</a></p>
</div>
</body>
</html>"""


def _hits_to_results(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or row.get("id") or "Result")
        url = str(row.get("url") or _CANON)
        summary = str(row.get("summary") or "")
        out.append(
            {
                "title": title,
                "url": url,
                "snippet": summary[:400],
                "source": "inhouse_catalog",
                "domain": str(row.get("domain") or ""),
            }
        )
    return out


def inhouse_search(query: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    try:
        from agr_web_research import search_research

        bag = search_research(str(query or ""))
        items = bag.get("items") if isinstance(bag, dict) else []
        if not isinstance(items, list):
            items = []
    except Exception as exc:
        return {
            "ok": False,
            "engine": _ENGINE,
            "error": str(exc),
            "results": [],
            "total": 0,
        }
    results = _hits_to_results(items)
    return {"ok": True, "engine": _ENGINE, "results": results, "total": len(results)}


async def external_search(query: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    """No live crawl from repo checkout — returns honest empty external slice."""
    _ = query
    return {
        "ok": True,
        "engine": _ENGINE,
        "results": [],
        "total": 0,
        "note": "external_shadow_no_crawl",
    }


async def universal_search(query: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    local = inhouse_search(query)
    ext = await external_search(query)
    merged = list(local.get("results") or []) + list(ext.get("results") or [])
    return {
        "ok": True,
        "engine": _ENGINE,
        "results": merged,
        "total": len(merged),
        "inhouse_total": int(local.get("total") or 0),
        "external_total": int(ext.get("total") or 0),
    }


def paginate(raw: Any, page: int = 1, per_page: int = 10, *_a: Any, **_kw: Any) -> dict[str, Any]:
    pg = max(1, int(page or 1))
    pp = max(1, min(int(per_page or 10), 50))
    items: list[Any] = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = list(raw.get("results") or raw.get("items") or [])
    total = len(items)
    pages = (total + pp - 1) // pp if total else 0
    start = (pg - 1) * pp
    chunk = items[start : start + pp]
    return {
        "results": chunk,
        "total": total,
        "page": pg,
        "pages": pages,
        "per_page": pp,
        "has_prev": pg > 1,
        "has_next": pages > 0 and pg < pages,
    }
