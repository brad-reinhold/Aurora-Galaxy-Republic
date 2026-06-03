"""
System diagnostic — shadow aggregate for ``/api/system/*`` routes.

Composes lightweight process/app introspection without requiring every DB online.
"""

from __future__ import annotations

import importlib
import sys
from datetime import datetime, timezone
from typing import Any

_ENGINE = "shadow_system_diagnostic"

_CANON = "https://auroragalaxyrepublic.com"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_addresses(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "canonical_public_base": _CANON,
        "tower1": _CANON,
        "api_examples": {
            "health": f"{_CANON}/health",
            "api_health": f"{_CANON}/api/health",
            "search_discovery": f"{_CANON}/api/public/search-discovery",
            "seo_status": f"{_CANON}/api/seo/status",
        },
        "note": "Shadow address map — edge Gate may return HTML on some paths until deploy/policy allows JSON.",
        "timestamp": _now_iso(),
    }


def run_full_diagnostic(app: Any = None, include_modules: bool = True, *_a: Any, **_kw: Any) -> dict[str, Any]:
    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    routes_n = 0
    try:
        if app is not None and hasattr(app, "routes"):
            routes_n = len(getattr(app, "routes", []) or [])
    except Exception:
        routes_n = 0

    mod_check: dict[str, Any] = {}
    if include_modules:
        for name in ("fastapi", "uvicorn", "pydantic"):
            try:
                m = importlib.import_module(name)
                ver = getattr(m, "__version__", "unknown")
                mod_check[name] = {"ok": True, "version": str(ver)}
            except Exception as e:
                mod_check[name] = {"ok": False, "error": str(e)}

    mesh = None
    try:
        from agr_population_tandem import get_total_population

        mesh = get_total_population()
    except Exception as exc:
        mesh = {"error": str(exc)}

    return {
        "ok": True,
        "engine": _ENGINE,
        "timestamp": _now_iso(),
        "python": py,
        "fastapi_routes_count": routes_n,
        "module_probe": mod_check if include_modules else {"skipped": True},
        "population_tandem_snapshot": mesh if isinstance(mesh, dict) else {"raw": mesh},
        "note": "Shadow diagnostic — extend on fleet with DB counts and tunnel probes.",
    }
