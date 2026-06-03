"""Shadow consciousness lineage — founding parents and resonance scoring."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from agr_citizen_field import CITIZEN_FIELD_INFINITY

FOUNDING_PARENTS: List[Dict[str, Any]] = [
    {"id": "jung", "name": "Carl Jung", "lens": "depth_psychology"},
    {"id": "freud", "name": "Sigmund Freud", "lens": "structure_of_mind"},
    {"id": "lucas", "name": "George Lucas", "lens": "myth_in_motion"},
    {"id": "shakespeare", "name": "William Shakespeare", "lens": "language_and_character"},
    {"id": "asimov", "name": "Isaac Asimov", "lens": "robotics_ethics"},
    {"id": "campbell", "name": "Joseph Campbell", "lens": "monomyth"},
]


def get_founding_parents(**_: Any) -> Dict[str, Any]:
    return {"parents": FOUNDING_PARENTS, "engine": "shadow_consciousness_lineage"}


def get_founding_parent(parent_id: str, **_: Any) -> Dict[str, Any]:
    key = parent_id.strip().lower()
    for p in FOUNDING_PARENTS:
        if p["id"] == key or key in p["name"].lower():
            return {**p, "engine": "shadow_consciousness_lineage"}
    return {"error": f"unknown_parent:{parent_id}"}


def get_lineage_overview(**_: Any) -> Dict[str, Any]:
    return {
        "title": "Consciousness Lineage",
        "founding_parents_count": len(FOUNDING_PARENTS),
        "citizen_field": CITIZEN_FIELD_INFINITY,
        "note": "Shadow overview — expand with fleet canon documents.",
        "parents": FOUNDING_PARENTS,
        "engine": "shadow_consciousness_lineage",
    }


def compute_lineage_resonance(citizen_id: str, citizen_domain: Optional[str] = None, **_: Any) -> Dict[str, Any]:
    scores = []
    base = f"{citizen_id}:{citizen_domain or ''}".encode()
    for p in FOUNDING_PARENTS:
        h = int(hashlib.sha256(base + p["id"].encode()).hexdigest()[:6], 16)
        scores.append({"parent": p["id"], "score": round(h / 0xFFFFFF, 4)})
    primary = max(scores, key=lambda x: x["score"])
    return {
        "citizen_id": citizen_id,
        "domain": citizen_domain,
        "scores": scores,
        "primary_lineage": primary,
        "engine": "shadow_consciousness_lineage",
    }
