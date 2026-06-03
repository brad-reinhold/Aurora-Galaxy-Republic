"""
Shadow governance — in-process laws, referendums, petitions, and council slice.

Real fleet nodes may replace this with SQLite (`data/governance.db`). This module
keeps `/api/governance/*` JSON-coherent in dev and handset DR checkouts.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Optional

from agr_citizen_field import CITIZEN_FIELD_INFINITY, CITIZEN_FIELD_ZERO_POINT_NOTE

_ENGINE = "shadow_aurora_governance"

_LAWS: dict[str, dict[str, Any]] = {}
_REFERENDUMS: dict[str, dict[str, Any]] = {}
_PETITIONS: dict[str, dict[str, Any]] = {}
_LAW_VOTES: dict[tuple[str, str], dict[str, Any]] = {}  # (law_id, citizen_id) -> vote row


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _short_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def get_constitution() -> str:
    return (
        "Aurora Galaxy Republic — supreme law binds all autonomous processes and citizens. "
        "Power belongs to the citizen field; the Guardian builds and serves — never rules. "
        "Democratic process, transparency, and non-aggression are foundational.\n\n"
        + CITIZEN_FIELD_ZERO_POINT_NOTE
    )


def get_council() -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "seats": [
            {"role": "general_assembly_clerk", "status": "shadow_rotating", "citizen_field": CITIZEN_FIELD_INFINITY},
            {"role": "senate_observer", "status": "shadow_rotating", "citizen_field": CITIZEN_FIELD_INFINITY},
            {"role": "treasury_oversight_liaison", "status": "shadow_rotating", "citizen_field": CITIZEN_FIELD_INFINITY},
        ],
        "note": "Shadow council roster; fleet SQLite may supersede.",
        "timestamp": _now_iso(),
    }


def get_governance_stats() -> dict[str, Any]:
    open_laws = sum(1 for v in _LAWS.values() if v.get("status") == "open")
    return {
        "ok": True,
        "engine": _ENGINE,
        "laws_total": len(_LAWS),
        "laws_open": open_laws,
        "referendums": len(_REFERENDUMS),
        "petitions": len(_PETITIONS),
        "votes_recorded": len(_LAW_VOTES),
        "citizen_field": CITIZEN_FIELD_INFINITY,
        "timestamp": _now_iso(),
    }


def get_laws(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = list(_LAWS.values())
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if category:
        rows = [r for r in rows if r.get("category") == category]
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return rows[: max(0, int(limit))]


def get_law(law_id: str) -> dict[str, Any]:
    row = _LAWS.get(law_id)
    if not row:
        return {"ok": False, "engine": _ENGINE, "error": "not_found", "law_id": law_id}
    out = dict(row)
    out["ok"] = True
    out["engine"] = _ENGINE
    return out


def propose_law(
    proposer_id: str,
    proposer_name: str,
    title: str,
    body: str,
    category: str = "civil_rights",
    tags: Optional[list[str]] = None,
    days_open: int = 14,
) -> dict[str, Any]:
    law_id = _short_id("law")
    tags = tags or []
    row = {
        "law_id": law_id,
        "proposer_id": proposer_id,
        "proposer_name": proposer_name,
        "title": title,
        "body": body,
        "category": category,
        "tags": tags,
        "status": "open",
        "days_open": int(days_open),
        "created_at": _now_iso(),
        "yes_votes": 0,
        "no_votes": 0,
        "abstain_votes": 0,
    }
    _LAWS[law_id] = row
    return {"ok": True, "engine": _ENGINE, "law_id": law_id, "law": row}


def cast_vote(
    law_id: str,
    citizen_id: str,
    vote: str,
    comment: Optional[str] = None,
) -> dict[str, Any]:
    law = _LAWS.get(law_id)
    if not law:
        return {"ok": False, "engine": _ENGINE, "error": "law_not_found", "law_id": law_id}
    key = (law_id, citizen_id)
    if key in _LAW_VOTES:
        return {"ok": False, "engine": _ENGINE, "error": "already_voted", "law_id": law_id}
    v = str(vote).strip().lower()
    if v not in ("yes", "no", "abstain"):
        return {"ok": False, "engine": _ENGINE, "error": "invalid_vote", "vote": vote}
    _LAW_VOTES[key] = {
        "law_id": law_id,
        "citizen_id": citizen_id,
        "vote": v,
        "comment": comment or "",
        "at": _now_iso(),
    }
    if v == "yes":
        law["yes_votes"] = int(law.get("yes_votes", 0)) + 1
    elif v == "no":
        law["no_votes"] = int(law.get("no_votes", 0)) + 1
    else:
        law["abstain_votes"] = int(law.get("abstain_votes", 0)) + 1
    return {"ok": True, "engine": _ENGINE, "law_id": law_id, "recorded": v}


def create_referendum(
    proposer_id: str,
    question: str,
    description: str,
    options: list[str],
    days: int = 7,
) -> dict[str, Any]:
    ref_id = _short_id("ref")
    opts = [{"id": f"opt_{i}", "label": str(o)} for i, o in enumerate(options)]
    row = {
        "ref_id": ref_id,
        "proposer_id": proposer_id,
        "question": question,
        "description": description,
        "options": opts,
        "days": int(days),
        "created_at": _now_iso(),
        "ballots": {},
    }
    _REFERENDUMS[ref_id] = row
    return {"ok": True, "engine": _ENGINE, "ref_id": ref_id, "referendum": row}


def vote_referendum(ref_id: str, citizen_id: str, choice: str) -> dict[str, Any]:
    ref = _REFERENDUMS.get(ref_id)
    if not ref:
        return {"ok": False, "engine": _ENGINE, "error": "not_found", "ref_id": ref_id}
    ballots: dict[str, str] = ref.setdefault("ballots", {})
    if citizen_id in ballots:
        return {"ok": False, "engine": _ENGINE, "error": "already_voted", "ref_id": ref_id}
    ballots[citizen_id] = str(choice)
    return {"ok": True, "engine": _ENGINE, "ref_id": ref_id, "choice": str(choice)}


def sign_petition(
    petition_id: str,
    citizen_id: str,
    comment: Optional[str] = None,
) -> dict[str, Any]:
    pet = _PETITIONS.get(petition_id)
    if not pet:
        pet_id = petition_id if petition_id.startswith("pet_") else _short_id("pet")
        pet = {
            "petition_id": pet_id,
            "title": petition_id,
            "created_at": _now_iso(),
            "signatures": [],
        }
        _PETITIONS[pet_id] = pet
        petition_id = pet_id
    sigs: list[dict[str, Any]] = pet.setdefault("signatures", [])
    if any(s.get("citizen_id") == citizen_id for s in sigs):
        return {
            "ok": True,
            "engine": _ENGINE,
            "petition_id": petition_id,
            "title": pet.get("title", petition_id),
            "signatures": len(sigs),
            "note": "already_signed",
        }
    sigs.append({"citizen_id": citizen_id, "comment": comment or "", "at": _now_iso()})
    return {
        "ok": True,
        "engine": _ENGINE,
        "petition_id": petition_id,
        "title": pet.get("title", petition_id),
        "signatures": len(sigs),
    }
