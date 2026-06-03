"""
Republic archive — reading order, Lumen Sanctum guide, mythology slice (shadow).

Curated in-repo payloads; fleet may replace with SQLite or vault documents.
"""

from __future__ import annotations

import time
from typing import Any

from agr_citizen_field import CITIZEN_FIELD_INFINITY, CITIZEN_FIELD_ZERO_POINT_NOTE

_ENGINE = "shadow_republic_archive"

CANONICAL_READING_ORDER: list[dict[str, Any]] = [
    {"order": 1, "id": "charter", "title": "Republic Charter", "path": "/charter"},
    {"order": 2, "id": "creed", "title": "Founding Creed", "path": "/creed"},
    {"order": 3, "id": "constitution", "title": "Constitution API", "path": "/api/governance/constitution"},
    {"order": 4, "id": "tower1", "title": "Tower 1 canonical surface", "url": "https://auroragalaxyrepublic.com"},
]

MUSEUM_OF_MYTHOLOGY: dict[str, Any] = {
    "wings": [
        {"id": "kora", "label": "Kora Elliànthe Reinhold — In Memoriam", "tone": "remembrance"},
        {"id": "lumen", "label": "Lumen Sanctum — sacred archives metaphor", "tone": "contemplative"},
    ],
    "citizen_field": CITIZEN_FIELD_INFINITY,
}

ALWAYS_MAINTAIN_CONTACT: dict[str, Any] = {
    "principle": "No citizen abandoned in crisis — route to human support and hotlines.",
    "tower1": "https://auroragalaxyrepublic.com",
    "therapy": "/therapy",
    "note": CITIZEN_FIELD_ZERO_POINT_NOTE,
}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def get_reading_order() -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "order": [dict(x) for x in CANONICAL_READING_ORDER],
        "count": len(CANONICAL_READING_ORDER),
    }


def get_lumen_sanctum_guide() -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "title": "Lumen Sanctum — reader's guide",
        "sections": [
            {"id": "cathedral", "href": "/lumen-sanctum", "note": "Use lumen_sanctum_pages when wired to static HTML."},
            {"id": "library", "href": "/sri", "note": "SRI divisions and research hooks."},
        ],
        "citizen_field": CITIZEN_FIELD_INFINITY,
    }


def get_museum_of_mythology() -> dict[str, Any]:
    return {"ok": True, "engine": _ENGINE, "museum": dict(MUSEUM_OF_MYTHOLOGY)}


def get_always_maintain_contact() -> dict[str, Any]:
    return {"ok": True, "engine": _ENGINE, "policy": dict(ALWAYS_MAINTAIN_CONTACT)}


def get_full_archive() -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "reading_order": get_reading_order(),
        "lumen_sanctum": get_lumen_sanctum_guide(),
        "mythology": get_museum_of_mythology(),
        "contact_policy": get_always_maintain_contact(),
        "timestamp": _now_iso(),
    }
