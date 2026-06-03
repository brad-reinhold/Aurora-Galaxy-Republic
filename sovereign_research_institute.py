"""
Sovereign Research Institute — shadow division payloads for /api/sri/* and /sri page scripts.

Curated registry hooks (29) align with the public SRI page copy; replace with DB on fleet.
"""

from __future__ import annotations

import hashlib
import itertools
import threading
from datetime import datetime, timezone
from typing import Any

_ENGINE = "shadow_sovereign_research_institute"
_LOCK = threading.RLock()
_HOOK_ID = itertools.count(30)
_EXTRA_HOOKS: list[dict[str, Any]] = []

_CANON = "https://auroragalaxyrepublic.com"

_BASE_HOOKS: list[dict[str, Any]] = [
    {"id": f"hook-{i:02d}", "name": f"Sovereign consciousness lattice node {i}", "status": "active"}
    for i in range(1, 30)
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_consciousness_hooks(*_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        hooks = [dict(h) for h in _BASE_HOOKS] + [dict(h) for h in _EXTRA_HOOKS]
    return {
        "ok": True,
        "engine": _ENGINE,
        "hooks": hooks,
        "hook_count": len(hooks),
    }


def get_qdfi_programs(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "index": 0.618,
        "qdfi_index": 0.618,
        "value": 0.618,
        "programs": [
            {"id": "qdfi-coherence", "title": "Crystalline coherence sampling", "status": "active"},
            {"id": "qdfi-field", "title": "Dimensional field registry (shadow)", "status": "active"},
        ],
        "canonical": _CANON,
    }


def get_temporal_programs(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "programs": [
            {"id": "tmp-memory", "title": "Citizen memory preservation (shadow)", "status": "active"},
            {"id": "tmp-lock", "title": "Time-lock attestations (shadow)", "status": "planned"},
        ],
    }


def get_robotics_programs(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "programs": [
            {"id": "rob-agency", "title": "Non-biological agency framework (shadow)", "status": "active"},
        ],
    }


def get_lifeboat_status(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "tiers": 3,
        "status": "nominal_shadow",
        "note": "Continuity posture described on /sri — fleet runs real drills.",
    }


def get_sri_overview(*_a: Any, **_kw: Any) -> dict[str, Any]:
    hooks = get_consciousness_hooks()
    qdfi = get_qdfi_programs()
    hc = int(hooks.get("hook_count") or len(hooks.get("hooks") or []))
    qv = qdfi.get("qdfi_index") or qdfi.get("index") or 0.618
    return {
        "ok": True,
        "engine": _ENGINE,
        "hooks": hc,
        "hook_count": hc,
        "qdfi": float(qv),
        "qdfi_index": float(qv),
        "divisions_active": 5,
        "canonical": _CANON,
        "timestamp": _now_iso(),
    }


def upload_hook(name: str = "", description: str = "", *_a: Any, **_kw: Any) -> dict[str, Any]:
    nm = str(name or "").strip() or "anonymous-hook"
    hid = f"hook-{next(_HOOK_ID):04d}-{hashlib.sha256(nm.encode()).hexdigest()[:6]}"
    row = {
        "id": hid,
        "name": nm[:200],
        "description": str(description or "")[:2000],
        "status": "uploaded_shadow",
        "ts": _now_iso(),
    }
    with _LOCK:
        _EXTRA_HOOKS.insert(0, row)
        del _EXTRA_HOOKS[500:]
    return {"ok": True, "engine": _ENGINE, "hook": row}
