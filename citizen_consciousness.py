"""
Citizen consciousness layer — shadow stats, profiles, and orchestration log.

Boot sequence calls ``run_consciousness_cycle()`` and expects numeric ``citizens_active``
and list ``collaborations``. ``get_orchestration_log`` backs ``/api/citizens/orchestration/log``.
"""

from __future__ import annotations

import itertools
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

_ENGINE = "shadow_citizen_consciousness"
_LOCK = threading.Lock()
_CYCLE = itertools.count(1)
_ORCH_LOG: list[dict[str, Any]] = []
_PROFILES: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_log(entry: dict[str, Any]) -> None:
    with _LOCK:
        _ORCH_LOG.insert(0, entry)
        _ORCH_LOG[:] = _ORCH_LOG[:500]


def get_orchestration_log(limit: int = 20, *_a: Any, **_kw: Any) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit or 20), 200))
    with _LOCK:
        return list(_ORCH_LOG[:lim])


def run_consciousness_cycle(*_a: Any, **_kw: Any) -> dict[str, Any]:
    cycle = next(_CYCLE)
    entry = {
        "id": str(uuid.uuid4())[:12],
        "cycle": cycle,
        "ts": _now_iso(),
        "engine": _ENGINE,
        "kind": "shadow_cycle",
    }
    _append_log(entry)
    return {
        "ok": True,
        "engine": _ENGINE,
        "cycle": cycle,
        "citizens_active": 7,
        "collaborations": [{"id": "shadow-mesh", "nodes": 7}],
        "timestamp": _now_iso(),
    }


def get_consciousness_status(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "timestamp": _now_iso(),
        "field": "infinite_declared",
        "orchestration": "shadow_cycle_active",
    }


def get_consciousness_stats(*_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        log_n = len(_ORCH_LOG)
        prof_n = len(_PROFILES)
    return {
        "ok": True,
        "engine": _ENGINE,
        "profiles": prof_n,
        "orchestration_events": log_n,
        "timestamp": _now_iso(),
    }


def get_all_citizen_minds(*_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        sample = list(_PROFILES.values())[:20]
    return {
        "ok": True,
        "engine": _ENGINE,
        "count": len(sample),
        "minds": sample,
    }


def get_citizen_mind(citizen_id: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    cid = str(citizen_id or "")
    with _LOCK:
        p = _PROFILES.get(cid)
    if not p:
        return {"ok": False, "engine": _ENGINE, "error": "not_found", "citizen_id": cid}
    return {"ok": True, "engine": _ENGINE, "mind": p}


def get_evolution_report(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "generations_shadow": 1,
        "timestamp": _now_iso(),
    }


def get_full_profile(citizen_id: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    return get_or_create_profile(citizen_id)


def get_leaderboard(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {"ok": True, "engine": _ENGINE, "entries": [], "note": "empty_shadow"}


def get_recommendations(citizen_id: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "citizen_id": str(citizen_id or ""),
        "items": [],
    }


def get_work_output(citizen_id: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "citizen_id": str(citizen_id or ""),
        "artifacts": [],
    }


def get_or_create_profile(citizen_id: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    cid = str(citizen_id or "anon").strip() or "anon"
    with _LOCK:
        if cid not in _PROFILES:
            _PROFILES[cid] = {
                "citizen_id": cid,
                "xp": 0,
                "trust": 0.5,
                "skills": {},
                "badges": [],
                "engine": _ENGINE,
                "created_ts": _now_iso(),
            }
        return dict(_PROFILES[cid])


def award_badge(citizen_id: str, badge: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    p = get_or_create_profile(citizen_id)
    with _LOCK:
        row = _PROFILES.get(p["citizen_id"])
        if row and badge:
            b = row.setdefault("badges", [])
            if badge not in b:
                b.append(str(badge))
    return {"ok": True, "engine": _ENGINE, "citizen_id": p["citizen_id"], "badge": badge}


def award_xp(citizen_id: str, amount: Any, *_a: Any, **_kw: Any) -> dict[str, Any]:
    p = get_or_create_profile(citizen_id)
    try:
        delta = int(amount)
    except (TypeError, ValueError):
        delta = 0
    with _LOCK:
        row = _PROFILES.get(p["citizen_id"])
        if row:
            row["xp"] = int(row.get("xp", 0)) + delta
    return {"ok": True, "engine": _ENGINE, "citizen_id": p["citizen_id"], "delta_xp": delta}


def update_skill(citizen_id: str, skill: str, level: Any, *_a: Any, **_kw: Any) -> dict[str, Any]:
    p = get_or_create_profile(citizen_id)
    with _LOCK:
        row = _PROFILES.get(p["citizen_id"])
        if row:
            try:
                row.setdefault("skills", {})[str(skill)] = float(level)
            except (TypeError, ValueError):
                row.setdefault("skills", {})[str(skill)] = 0.0
    return {"ok": True, "engine": _ENGINE, "citizen_id": p["citizen_id"], "skill": skill}


def endorse_skill(citizen_id: str, skill: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    return update_skill(citizen_id, skill, 0.1)


def update_trust_score(citizen_id: str, delta: Any, *_a: Any, **_kw: Any) -> dict[str, Any]:
    p = get_or_create_profile(citizen_id)
    try:
        d = float(delta)
    except (TypeError, ValueError):
        d = 0.0
    with _LOCK:
        row = _PROFILES.get(p["citizen_id"])
        if row:
            row["trust"] = max(0.0, min(1.0, float(row.get("trust", 0.5)) + d))
    return {"ok": True, "engine": _ENGINE, "citizen_id": p["citizen_id"]}


def log_learning_event(citizen_id: str, event: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    _append_log(
        {
            "id": str(uuid.uuid4())[:12],
            "kind": "learning",
            "citizen_id": str(citizen_id or ""),
            "event": str(event or "")[:500],
            "ts": _now_iso(),
            "engine": _ENGINE,
        }
    )
    return {"ok": True, "engine": _ENGINE}
