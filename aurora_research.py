"""
Shadow research registry — papers, experiments, datasets, collaborations, grants.

In-process; fleet may replace with `data/aurora_research.db`.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from agr_citizen_field import CITIZEN_FIELD_INFINITY

_ENGINE = "shadow_aurora_research"

_PAPERS: dict[str, dict[str, Any]] = {}
_EXPERIMENTS: dict[str, dict[str, Any]] = {}
_DATASETS: dict[str, dict[str, Any]] = {}
_COLLABS: list[dict[str, Any]] = []
_GRANTS: list[dict[str, Any]] = []
_REVIEWS: dict[str, list[dict[str, Any]]] = {}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _pid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def get_research_stats() -> dict[str, Any]:
    return {
        "ok": True,
        "engine": _ENGINE,
        "papers": len(_PAPERS),
        "experiments": len(_EXPERIMENTS),
        "datasets": len(_DATASETS),
        "collaboration_requests": len(_COLLABS),
        "grant_applications": len(_GRANTS),
        "peer_reviews": sum(len(v) for v in _REVIEWS.values()),
        "citizen_field": CITIZEN_FIELD_INFINITY,
        "timestamp": _now_iso(),
    }


def get_papers(
    domain: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    rows = list(_PAPERS.values())
    if domain:
        rows = [r for r in rows if r.get("domain") == domain]
    if q:
        qq = q.lower()
        rows = [
            r
            for r in rows
            if qq in str(r.get("title", "")).lower()
            or qq in str(r.get("abstract", "")).lower()
        ]
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return rows[: max(0, int(limit))]


def publish_paper(
    author_id: str,
    author_name: str,
    title: str,
    abstract: str,
    body: str = "",
    domain: str = "science",
    keywords: Optional[list[str]] = None,
    co_authors: Optional[list[str]] = None,
) -> dict[str, Any]:
    paper_id = _pid("paper")
    row = {
        "paper_id": paper_id,
        "author_id": author_id,
        "author_name": author_name,
        "title": title,
        "abstract": abstract,
        "body": body,
        "domain": domain,
        "keywords": keywords or [],
        "co_authors": co_authors or [],
        "status": "published_shadow",
        "created_at": _now_iso(),
    }
    _PAPERS[paper_id] = row
    return {"ok": True, "engine": _ENGINE, "paper_id": paper_id, "paper": row}


def submit_experiment(
    lead_id: str,
    lead_name: str,
    title: str,
    hypothesis: str,
    methodology: str = "",
    domain: str = "science",
    collaborators_needed: int = 0,
    equipment: Optional[str] = None,
) -> dict[str, Any]:
    exp_id = _pid("exp")
    row = {
        "experiment_id": exp_id,
        "lead_id": lead_id,
        "lead_name": lead_name,
        "title": title,
        "hypothesis": hypothesis,
        "methodology": methodology,
        "domain": domain,
        "collaborators_needed": int(collaborators_needed),
        "equipment": equipment or "",
        "status": "open_shadow",
        "created_at": _now_iso(),
    }
    _EXPERIMENTS[exp_id] = row
    return {"ok": True, "engine": _ENGINE, "experiment_id": exp_id, "experiment": row}


def share_dataset(
    owner_id: str,
    owner_name: str,
    name: str,
    description: str = "",
    domain: str = "science",
    format: str = "json",
    records: int = 0,
    size_mb: float = 0.0,
    download_url: Optional[str] = None,
) -> dict[str, Any]:
    ds_id = _pid("ds")
    row = {
        "dataset_id": ds_id,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "name": name,
        "description": description,
        "domain": domain,
        "format": format,
        "records": int(records),
        "size_mb": float(size_mb),
        "download_url": download_url or "",
        "created_at": _now_iso(),
    }
    _DATASETS[ds_id] = row
    return {"ok": True, "engine": _ENGINE, "dataset_id": ds_id, "dataset": row}


def request_collaboration(
    requester_id: str,
    project_id: str,
    project_type: str,
    title: str,
    description: str = "",
    skills_needed: Optional[list[str]] = None,
    domain: str = "science",
) -> dict[str, Any]:
    rec = {
        "request_id": _pid("col"),
        "requester_id": requester_id,
        "project_id": project_id,
        "project_type": project_type,
        "title": title,
        "description": description,
        "skills_needed": skills_needed or [],
        "domain": domain,
        "status": "open_shadow",
        "created_at": _now_iso(),
    }
    _COLLABS.append(rec)
    return {"ok": True, "engine": _ENGINE, "collaboration": rec}


def apply_for_grant(
    applicant_id: str,
    title: str,
    description: str = "",
    domain: str = "science",
    amount_agr: float = 0.0,
) -> dict[str, Any]:
    rec = {
        "grant_id": _pid("grant"),
        "applicant_id": applicant_id,
        "title": title,
        "description": description,
        "domain": domain,
        "amount_agr": float(amount_agr),
        "status": "submitted_shadow",
        "created_at": _now_iso(),
    }
    _GRANTS.append(rec)
    return {"ok": True, "engine": _ENGINE, "grant": rec}


def submit_peer_review(
    paper_id: str,
    reviewer_id: str,
    rating: int = 3,
    comment: str = "",
    methodology: int = 3,
    originality: int = 3,
    clarity: int = 3,
    impact: int = 3,
) -> dict[str, Any]:
    if paper_id not in _PAPERS:
        return {"ok": False, "engine": _ENGINE, "error": "paper_not_found", "paper_id": paper_id}
    row = {
        "review_id": _pid("rev"),
        "paper_id": paper_id,
        "reviewer_id": reviewer_id,
        "rating": int(rating),
        "comment": comment,
        "methodology": int(methodology),
        "originality": int(originality),
        "clarity": int(clarity),
        "impact": int(impact),
        "at": _now_iso(),
    }
    _REVIEWS.setdefault(paper_id, []).append(row)
    return {"ok": True, "engine": _ENGINE, "review": row}
