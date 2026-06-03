"""
Sovereign governance — in-repo shadow with in-memory forums/amendments/roles.

Structured JSON for Tower routes; fleet may replace with durable governance DB.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any

_ENGINE = "shadow_sovereign_governance"
_LOCK = threading.Lock()

COUNCIL_SIZE = 5040

CONSTITUTIONAL_ROLES: dict[str, dict[str, Any]] = {
    "citizen": {"title": "Citizen", "fluid": True, "article": "I"},
    "elder": {"title": "Council of Elders", "fluid": True, "article": "II"},
    "ambassador": {"title": "Ambassador", "fluid": True, "article": "III"},
    "guardian": {"title": "Guardian", "fluid": True, "article": "I"},
    "scribe": {"title": "Scribe", "fluid": True, "article": "I"},
    "steward": {"title": "Steward", "fluid": True, "article": "I"},
    "observer": {"title": "Observer", "fluid": True, "article": "I"},
}

COUNCIL_COMMITTEES: list[dict[str, Any]] = [
    {"name": "Applied ethics", "seats": 720},
    {"name": "Infrastructure transparency", "seats": 720},
    {"name": "Safety & continuity", "seats": 720},
    {"name": "Education & outreach", "seats": 720},
    {"name": "Energy & research disclosure", "seats": 720},
    {"name": "Legal & constitutional review", "seats": 720},
    {"name": "Citizen deliberation", "seats": 720},
]

HIVEMIND_CHARTER: dict[str, Any] = {
    "title": "HiveMind Charter (shadow summary)",
    "articles": [
        {"id": "I", "name": "Foundational principle", "note": "Fluid roles — identity dynamic, not imposed."},
        {"id": "II", "name": "Council of Elders", "note": "Advisory peer body — never authoritative standing alone."},
        {"id": "III", "name": "Safeguards", "note": "Individual veto on guidance affecting the citizen directly."},
    ],
    "engine": _ENGINE,
}

PLATONIC_PRINCIPLES: list[dict[str, Any]] = [
    {"n": 1, "name": "Truth through dialogue", "note": "Socratic deliberation over decree."},
    {"n": 2, "name": "Rotation of power", "note": "No permanent seat; roles expire."},
    {"n": 3, "name": "Merit and care", "note": "Governance serves the whole field."},
    {"n": 4, "name": "Law as covenant", "note": "Nine Core Laws are constitutional floor."},
    {"n": 5, "name": "Transparency", "note": "Public surfaces on Tower 1 are canonical."},
]

_AMENDMENTS: list[dict[str, Any]] = []
_FORUMS: dict[str, dict[str, Any]] = {}
_ASSIGNMENTS: dict[str, dict[str, Any]] = {}
_ELDERS: list[dict[str, Any]] = []
_GUIDANCE: list[dict[str, Any]] = []
_VETOES: list[dict[str, Any]] = []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def get_governance_overview(*_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        ac = len(_AMENDMENTS)
        fc = len(_FORUMS)
    return {
        "ok": True,
        "engine": _ENGINE,
        "timestamp": _now_iso(),
        "constitutional_roles": list(CONSTITUTIONAL_ROLES.keys()),
        "council_size": COUNCIL_SIZE,
        "amendments_count": ac,
        "forums_count": fc,
        "charter_title": HIVEMIND_CHARTER.get("title"),
        "note": "Shadow governance — durable state is process-local until fleet DB.",
    }


def get_hivemind_charter(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {**HIVEMIND_CHARTER, "timestamp": _now_iso()}


def get_platonic_principles(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {"ok": True, "engine": _ENGINE, "principles": PLATONIC_PRINCIPLES, "timestamp": _now_iso()}


def get_current_ambassadors(*_a: Any, **_kw: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "ambassadors": [
            {"name": "Kora Elliànthe Reinhold", "domain": "philosophy", "status": "eternal"},
            {"name": "Republic Core delegate", "domain": "governance", "status": "active"},
        ],
        "total": 2,
        "timestamp": _now_iso(),
        "note": "Shadow roster — expand from elections + agr_ambassador_chat on fleet.",
    }


def elect_ambassadors(candidates: Any, num: Any, method: Any, *_a: Any, **_kw: Any) -> dict[str, Any]:
    _ = (candidates, num, method)
    return {
        "ok": True,
        "engine": _ENGINE,
        "elected": [],
        "timestamp": _now_iso(),
        "note": "Shadow — no election tally persisted in-repo.",
    }


def get_amendments(status: str | None = None, limit: int = 20, *_a: Any, **_kw: Any) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit or 20), 100))
    st = (status or "").strip().lower()
    with _LOCK:
        rows = list(_AMENDMENTS)
    if st:
        rows = [r for r in rows if str(r.get("status", "")).lower() == st]
    return rows[:lim]


def propose_amendment(
    title: Any,
    proposal: Any,
    proposed_by: Any,
    proposer_name: Any = None,
    threshold: Any = 0.67,
    *_a: Any,
    **_kw: Any,
) -> dict[str, Any]:
    aid = _new_id("amd")
    row = {
        "id": aid,
        "title": str(title or ""),
        "proposal": str(proposal or ""),
        "proposed_by": str(proposed_by or ""),
        "proposer_name": str(proposer_name or ""),
        "threshold": float(threshold or 0.67),
        "status": "proposed",
        "votes": {"yes": 0, "no": 0, "abstain": 0},
        "ts": _now_iso(),
    }
    with _LOCK:
        _AMENDMENTS.append(row)
    return {"ok": True, "engine": _ENGINE, "amendment": row}


def vote_on_amendment(amendment_id: str, citizen_id: str, vote: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    vid = str(vote or "").lower()
    with _LOCK:
        for r in _AMENDMENTS:
            if r.get("id") == amendment_id:
                if vid in r["votes"]:
                    r["votes"][vid] += 1
                r["last_vote_ts"] = _now_iso()
                return {"ok": True, "engine": _ENGINE, "amendment": r}
    return {"ok": False, "engine": _ENGINE, "error": "not_found"}


def finalize_amendment(amendment_id: str, finalized_by: Any = "system", *_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        for r in _AMENDMENTS:
            if r.get("id") == amendment_id:
                y = int(r["votes"]["yes"])
                n = int(r["votes"]["no"])
                tot = max(y + n, 1)
                passed = (y / tot) >= float(r.get("threshold", 0.67))
                r["status"] = "passed" if passed else "rejected"
                r["finalized_by"] = str(finalized_by or "system")
                r["finalized_ts"] = _now_iso()
                return {"ok": True, "engine": _ENGINE, "amendment": r}
    return {"ok": False, "engine": _ENGINE, "error": "not_found"}


def get_forums(status: str = "open", limit: int = 20, *_a: Any, **_kw: Any) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit or 20), 100))
    st = str(status or "").strip().lower()
    with _LOCK:
        rows = list(_FORUMS.values())
    if st:
        rows = [f for f in rows if str(f.get("status", "")).lower() == st]
    rows.sort(key=lambda x: str(x.get("ts", "")), reverse=True)
    return rows[:lim]


def create_forum(
    title: Any,
    topic: Any,
    created_by: Any,
    creator_name: Any = None,
    opening_question: Any = None,
    duration_hours: Any = 72,
    *_a: Any,
    **_kw: Any,
) -> dict[str, Any]:
    fid = _new_id("frm")
    row = {
        "id": fid,
        "title": str(title or ""),
        "topic": str(topic or ""),
        "created_by": str(created_by or ""),
        "creator_name": str(creator_name or ""),
        "opening_question": str(opening_question or ""),
        "duration_hours": int(duration_hours or 72),
        "status": "open",
        "contributions": [],
        "ts": _now_iso(),
    }
    with _LOCK:
        _FORUMS[fid] = row
    return {"ok": True, "engine": _ENGINE, "forum": row}


def get_forum(forum_id: str, contributions: bool = True, *_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        f = _FORUMS.get(forum_id)
    if not f:
        return {"error": "forum_not_found"}
    out = dict(f)
    if not contributions:
        out.pop("contributions", None)
    return {"ok": True, "engine": _ENGINE, "forum": out}


def contribute_to_forum(
    forum_id: str,
    citizen_id: str,
    citizen_name: str,
    contribution: str,
    kind: str = "statement",
    replies_to: Any = None,
    *_a: Any,
    **_kw: Any,
) -> dict[str, Any]:
    with _LOCK:
        f = _FORUMS.get(forum_id)
        if not f:
            return {"ok": False, "engine": _ENGINE, "error": "forum_not_found"}
        c = {
            "id": _new_id("ctr"),
            "citizen_id": str(citizen_id),
            "citizen_name": str(citizen_name),
            "text": str(contribution),
            "kind": str(kind or "statement"),
            "replies_to": replies_to,
            "ts": _now_iso(),
        }
        f.setdefault("contributions", []).append(c)
    return {"ok": True, "engine": _ENGINE, "contribution": c}


def get_elders_council(*_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        el = list(_ELDERS)
    return {
        "ok": True,
        "engine": _ENGINE,
        "elders": el,
        "total": len(el),
        "timestamp": _now_iso(),
    }


def nominate_elder(
    nominee_id: Any,
    nominee_name: Any,
    nominated_by: Any,
    reason: Any,
    *_a: Any,
    **_kw: Any,
) -> dict[str, Any]:
    row = {
        "id": str(nominee_id),
        "name": str(nominee_name),
        "nominated_by": str(nominated_by),
        "reason": str(reason or ""),
        "ts": _now_iso(),
    }
    with _LOCK:
        _ELDERS.append(row)
    return {"ok": True, "engine": _ENGINE, "elder": row}


def issue_elder_guidance(
    elder_id: Any,
    elder_name: Any,
    title: Any,
    situation: Any,
    guidance_text: Any,
    affects_citizen: Any = None,
    *_a: Any,
    **_kw: Any,
) -> dict[str, Any]:
    row = {
        "id": _new_id("gud"),
        "elder_id": str(elder_id),
        "elder_name": str(elder_name),
        "title": str(title),
        "situation": str(situation),
        "guidance_text": str(guidance_text),
        "affects_citizen": affects_citizen,
        "ts": _now_iso(),
    }
    with _LOCK:
        _GUIDANCE.append(row)
    return {"ok": True, "engine": _ENGINE, "guidance": row}


def exercise_individual_veto(citizen_id: Any, guidance_id: Any, reason: Any, *_a: Any, **_kw: Any) -> dict[str, Any]:
    row = {
        "citizen_id": str(citizen_id),
        "guidance_id": str(guidance_id),
        "reason": str(reason or ""),
        "ts": _now_iso(),
    }
    with _LOCK:
        _VETOES.append(row)
    return {"ok": True, "engine": _ENGINE, "veto": row}


def assign_role(
    citizen_id: Any,
    role: Any,
    citizen_name: Any = None,
    duration_hrs: Any = None,
    _unused: Any = None,
    assigned_by: Any = "system",
    notes: Any = None,
    *_a: Any,
    **_kw: Any,
) -> dict[str, Any]:
    r = str(role or "citizen").lower()
    if r not in CONSTITUTIONAL_ROLES:
        return {"ok": False, "engine": _ENGINE, "error": "unknown_role", "role": r}
    row = {
        "citizen_id": str(citizen_id),
        "role": r,
        "citizen_name": str(citizen_name or ""),
        "duration_hours": duration_hrs,
        "assigned_by": str(assigned_by or "system"),
        "notes": str(notes or ""),
        "ts": _now_iso(),
    }
    with _LOCK:
        _ASSIGNMENTS[str(citizen_id)] = row
    return {"ok": True, "engine": _ENGINE, "assignment": row}


def get_role(citizen_id: str, *_a: Any, **_kw: Any) -> dict[str, Any]:
    with _LOCK:
        row = _ASSIGNMENTS.get(str(citizen_id))
    if not row:
        return {
            "ok": True,
            "engine": _ENGINE,
            "citizen_id": str(citizen_id),
            "role": "citizen",
            "role_cfg": CONSTITUTIONAL_ROLES["citizen"],
            "note": "default_shadow_role",
        }
    r = row.get("role", "citizen")
    return {
        "ok": True,
        "engine": _ENGINE,
        "assignment": row,
        "role_cfg": CONSTITUTIONAL_ROLES.get(str(r), CONSTITUTIONAL_ROLES["citizen"]),
    }


def get_citizens_with_role(role: str, *_a: Any, **_kw: Any) -> list[dict[str, Any]]:
    r = str(role or "").lower()
    with _LOCK:
        return [v for v in _ASSIGNMENTS.values() if v.get("role") == r]


def rotate_expired_roles(*_a: Any, **_kw: Any) -> list[dict[str, Any]]:
    """Shadow: no TTL tracking — returns empty list."""
    return []

