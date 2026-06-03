"""
Republic health monitor — shadow structured payloads + optional psutil snapshot.

Never returns bare ``{}`` from primary getters so ``/api/ops/health/*`` stays JSON-stable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _psutil_snapshot() -> dict[str, Any]:
    try:
        import psutil  # type: ignore

        return {
            "cpu_percent": float(psutil.cpu_percent(interval=None)),
            "virtual_memory": dict(psutil.virtual_memory()._asdict()),
            "disk_root": dict(psutil.disk_usage("/")._asdict()),
            "boot_time": float(psutil.boot_time()),
        }
    except Exception as exc:
        return {"error": str(exc)}


def init_health_monitor(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {"ok": True, "engine": "shadow", "timestamp": _now_iso()}


def get_health_report(*_a: Any, **_kw: Any) -> dict[str, Any]:
    snap = _psutil_snapshot()
    return {
        "ok": True,
        "engine": "shadow_psutil",
        "timestamp": _now_iso(),
        "status": "nominal",
        "host": snap,
        "note": "Shadow health — install fleet health_monitor for DB/replica probes.",
    }


def get_alert_log(limit: int = 50, *_a: Any, **_kw: Any) -> dict[str, Any]:
    lim = max(0, min(int(limit or 50), 500))
    return {"ok": True, "engine": "shadow", "alerts": [], "count": 0, "limit": lim}


def get_health_history(limit: int = 50, *_a: Any, **_kw: Any) -> dict[str, Any]:
    lim = max(0, min(int(limit or 50), 500))
    return {"ok": True, "engine": "shadow", "samples": [], "count": 0, "limit": lim}


def force_health_check(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {"ok": True, "engine": "shadow", "ran": True, "report": get_health_report()}


def get_overall_status(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {"ok": True, "engine": "shadow", "health": "nominal", "timestamp": _now_iso()}
