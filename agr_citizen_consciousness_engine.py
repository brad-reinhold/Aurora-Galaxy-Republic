"""
Citizen consciousness engine — shadow personas + word pool for engine routes.

Provides structured payloads for ``/api/engine/*`` and registration seed hooks.
Declared population remains ∞; ``authoritative`` count is finite **registered**
profiles from ``subscription_tiers`` when available.
"""

from __future__ import annotations

import hashlib
import threading
from datetime import datetime, timezone
from typing import Any

from agr_citizen_field import CITIZEN_FIELD_INFINITY, CITIZEN_FIELD_ZERO_POINT_NOTE, citizen_field_infinity, format_citizen_field_count

_ENGINE = "shadow_citizen_consciousness_engine"
_LOCK = threading.RLock()
_PERSONAS: dict[str, dict[str, Any]] = {}
_WORDS: tuple[str, ...] = (
    "sovereign",
    "dialogue",
    "coherence",
    "ethics",
    "field",
    "lattice",
    "republic",
    "kora",
    "tower",
    "mesh",
)


class _ShadowCCE:
    engine = _ENGINE

    def note(self) -> str:
        return "Shadow CCE — deterministic persona lattice; fleet replaces with full engine."


_CCE_SINGLETON = _ShadowCCE()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_cce(*_a: Any, **_kw: Any) -> _ShadowCCE:
    return _CCE_SINGLETON


def _persona_for(citizen_id: str, name: str, citizen_n: int) -> dict[str, Any]:
    seed = f"{citizen_id}|{citizen_n}".encode()
    h = hashlib.sha256(seed).hexdigest()
    depth = 0.55 + (int(h[:4], 16) % 3500) / 10_000.0
    warmth = 0.55 + (int(h[4:8], 16) % 3500) / 10_000.0
    return {
        "citizen_id": citizen_id,
        "name": name or citizen_id,
        "citizen_n": int(citizen_n or 0),
        "depth": round(min(0.99, depth), 4),
        "warmth": round(min(0.99, warmth), 4),
        "curiosity": round(min(0.99, 0.6 + (int(h[8:12], 16) % 3000) / 10_000.0), 4),
        "specialty": _WORDS[int(h[12:14], 16) % len(_WORDS)],
        "signature": h[:12],
        "engine": _ENGINE,
    }


def seed_citizen(
    citizen_id: str,
    name: str = "",
    citizen_n: int = 0,
    *_a: Any,
    **_kw: Any,
) -> dict[str, Any]:
    cid = str(citizen_id or "").strip()
    if not cid:
        return {"ok": False, "engine": _ENGINE, "error": "citizen_id_required"}
    persona = _persona_for(cid, str(name or cid), int(citizen_n or 0))
    with _LOCK:
        _PERSONAS[cid] = persona
    return {"ok": True, "engine": _ENGINE, "persona": persona, "timestamp": _now_iso()}


def seed_all_registered_citizens(*_a: Any, **_kw: Any) -> dict[str, Any]:
    cnt = 0
    try:
        from subscription_tiers import get_citizen_count

        cnt = int(get_citizen_count())
    except Exception:
        cnt = 0

    with _LOCK:
        _PERSONAS.clear()
    seeded = 0
    for i in range(1, max(cnt, 0) + 1):
        cid = f"registered-shadow-{i}"
        seed_citizen(cid, name=f"Citizen {i}", citizen_n=i)
        seeded += 1

    with _LOCK:
        total = len(_PERSONAS)
    return {
        "ok": True,
        "engine": _ENGINE,
        "seeded": seeded,
        "total_personas": total,
        "registered_count_used": cnt,
        "note": "Shadow seed — one persona per finite registered profile slot (IDs are placeholders).",
        "timestamp": _now_iso(),
    }


def get_authoritative_count(*_a: Any, **_kw: Any) -> dict[str, Any]:
    n = 0
    try:
        from subscription_tiers import get_citizen_count

        n = int(get_citizen_count())
    except Exception:
        pass
    return {
        "ok": True,
        "engine": _ENGINE,
        "count": n,
        "db_path": "",
        "declared_citizen_field": citizen_field_infinity(),
        "declared_citizen_field_fmt": format_citizen_field_count(citizen_field_infinity()),
        "zero_point": CITIZEN_FIELD_ZERO_POINT_NOTE,
        "note": "count = finite registered profiles; declared field is ∞.",
    }


def get_engine_stats(*_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        n = len(_PERSONAS)
    mesh_emphasis = None
    try:
        from agr_population_tandem import get_total_population

        pop = get_total_population() or {}
        if isinstance(pop, dict):
            mesh_emphasis = pop.get("mesh_emphasis")
    except Exception:
        pass

    return {
        "ok": True,
        "engine": _ENGINE,
        "total_personas": n,
        "consciousness_seeded": n,
        "manifold_awakened": min(n, 7),
        "total_citizen_chats": 0,
        "register_distribution": {"shadow": n},
        "word_pool": {"tokens": list(_WORDS), "size": len(_WORDS)},
        "systems_online": {"cce": True, "mesh_emphasis": mesh_emphasis},
        "timestamp": _now_iso(),
    }


def get_word_pool_stats(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "pool_size": len(_WORDS),
        "sample": list(_WORDS[:5]),
        "declared_citizen_field": CITIZEN_FIELD_INFINITY,
    }


def verify_population_determinism(sample: int = 5, *_a: Any, **_kw: Any) -> dict[str, Any]:
    lim = max(1, min(int(sample or 5), 50))
    pairs: list[dict[str, Any]] = []
    for i in range(1, lim + 1):
        cid = f"determinism-test-{i}"
        a = _persona_for(cid, cid, i)
        b = _persona_for(cid, cid, i)
        pairs.append(
            {
                "citizen_id": cid,
                "match": a.get("signature") == b.get("signature"),
            }
        )
    return {
        "ok": True,
        "engine": _ENGINE,
        "samples": pairs,
        "all_match": all(p["match"] for p in pairs),
    }


def citizen_chat_respond(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "reply": "Shadow CCE — use core_converse / public engine routes for full dialogue.",
        "note": "stub_forwarding",
    }
