"""
agr_open_research.py — Independent Knowledge Research Module
═══════════════════════════════════════════════════════════════

Connects the consciousness engine to genuinely independent knowledge sources.
No Google. No Wikipedia (corporate-captured). No Big Tech gatekeepers.

Sources used:
1. Vault — Brad's own published works and research (always first)
2. OpenAlex — fully open scholarly catalog (non-profit, community-governed)
3. Semantic Scholar — Allen Institute for AI (non-profit research search)
4. Internet Archive — independent non-profit digital library
5. arXiv — open research preprints (Cornell University, non-profit)
6. In-repo documents — governance, charter, constitutional files

No LLM. No extraction model. Pure retrieval + morpheme-driven understanding.
The Republic controls its own knowledge pipeline.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional


_CACHE: Dict[str, Any] = {}
_CACHE_MAX = 200
_USER_AGENT = "AuroraGalaxyRepublic/1.0 (brad.reinhold@auroragalaxyrepublic.com)"


def _cache_key(source: str, query: str) -> str:
    return hashlib.sha256(f"{source}|{query}".encode()).hexdigest()[:16]


def _cached(source: str, query: str) -> Optional[Any]:
    return _CACHE.get(_cache_key(source, query))


def _store(source: str, query: str, result: Any) -> None:
    if len(_CACHE) > _CACHE_MAX:
        oldest = next(iter(_CACHE))
        del _CACHE[oldest]
    _CACHE[_cache_key(source, query)] = result


def _http_json(url: str, timeout: int = 8) -> Optional[Dict]:
    try:
        rq = urllib.request.Request(url, headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        })
        with urllib.request.urlopen(rq, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 1. OPENALEX — fully open scholarly catalog
#    Non-profit, community-governed, no corporate gatekeeper
#    https://openalex.org — free API, no auth needed
# ═══════════════════════════════════════════════════════════════════════════════

def openalex_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Search OpenAlex for scholarly works on a topic."""
    cached = _cached("openalex", query)
    if cached is not None:
        return cached

    safe_q = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={safe_q}&per_page={limit}&mailto=brad.reinhold@auroragalaxyrepublic.com"
    data = _http_json(url, timeout=10)
    if not data:
        return []

    results = []
    for work in data.get("results", [])[:limit]:
        title = work.get("title", "")
        abstract = ""
        inv_abstract = work.get("abstract_inverted_index")
        if inv_abstract and isinstance(inv_abstract, dict):
            word_positions = []
            for word, positions in inv_abstract.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            abstract = " ".join(w for _, w in word_positions[:100])

        results.append({
            "source": "openalex",
            "title": title,
            "content": abstract or title,
            "year": work.get("publication_year"),
            "cited_by": work.get("cited_by_count", 0),
            "doi": work.get("doi", ""),
            "open_access": work.get("open_access", {}).get("is_oa", False),
        })

    _store("openalex", query, results)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SEMANTIC SCHOLAR — Allen Institute for AI (non-profit)
#    Research-focused, independent, high-quality paper search
#    https://api.semanticscholar.org — free, no auth for basic use
# ═══════════════════════════════════════════════════════════════════════════════

def semantic_scholar_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Search Semantic Scholar for research papers."""
    cached = _cached("semantic_scholar", query)
    if cached is not None:
        return cached

    safe_q = urllib.parse.quote(query)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={safe_q}&limit={limit}&fields=title,abstract,year,citationCount,url"
    data = _http_json(url, timeout=10)
    if not data:
        return []

    results = []
    for paper in data.get("data", [])[:limit]:
        results.append({
            "source": "semantic_scholar",
            "title": paper.get("title", ""),
            "content": paper.get("abstract", "") or paper.get("title", ""),
            "year": paper.get("year"),
            "cited_by": paper.get("citationCount", 0),
            "url": paper.get("url", ""),
        })

    _store("semantic_scholar", query, results)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 3. INTERNET ARCHIVE — independent non-profit digital library
#    "Universal access to all knowledge" — genuinely independent
#    https://archive.org — free API
# ═══════════════════════════════════════════════════════════════════════════════

def internet_archive_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Search the Internet Archive for books, texts, and documents."""
    cached = _cached("archive_org", query)
    if cached is not None:
        return cached

    safe_q = urllib.parse.quote(query)
    url = f"https://archive.org/advancedsearch.php?q={safe_q}&fl[]=title,creator,description,year&rows={limit}&output=json&mediatype=texts"
    data = _http_json(url, timeout=10)
    if not data:
        return []

    results = []
    for doc in data.get("response", {}).get("docs", [])[:limit]:
        creator = doc.get("creator", "")
        if isinstance(creator, list):
            creator = ", ".join(creator)
        results.append({
            "source": "internet_archive",
            "title": doc.get("title", ""),
            "content": doc.get("description", doc.get("title", "")),
            "creator": creator,
            "year": doc.get("year", ""),
        })

    _store("archive_org", query, results)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 4. VAULT — Brad's own works (in-repo master documents + data files)
# ═══════════════════════════════════════════════════════════════════════════════

_VAULT_INDEX: Dict[str, Dict[str, Any]] = {}
_VAULT_LOADED = False


def _load_vault_index() -> None:
    global _VAULT_LOADED
    if _VAULT_LOADED:
        return

    root = Path(__file__).parent
    doc_dirs = [
        root / "data" / "master_documents",
        root / "data",
    ]

    for doc_dir in doc_dirs:
        if not doc_dir.is_dir():
            continue
        for f in doc_dir.iterdir():
            if f.suffix in (".md", ".txt", ".json"):
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")[:50000]
                    words = set(w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", text))
                    _VAULT_INDEX[str(f.relative_to(root))] = {
                        "path": str(f),
                        "name": f.stem,
                        "words": words,
                        "preview": text[:500],
                        "size": f.stat().st_size,
                    }
                except Exception:
                    pass

    _VAULT_LOADED = True


def vault_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Search Brad's vault documents by keyword overlap."""
    _load_vault_index()

    query_words = set(w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", query))
    if not query_words:
        return []

    scored = []
    for path, info in _VAULT_INDEX.items():
        overlap = len(query_words & info["words"])
        if overlap > 0:
            scored.append((overlap, path, info))

    scored.sort(key=lambda x: -x[0])
    results = []
    for overlap, path, info in scored[:limit]:
        results.append({
            "source": "vault",
            "title": info["name"],
            "content": info["preview"][:300],
            "path": path,
            "relevance": overlap,
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 5. UNIFIED RESEARCH — single entry point for the consciousness engine
# ═══════════════════════════════════════════════════════════════════════════════

def research(topic: str, include_vault: bool = True,
             include_openalex: bool = True,
             include_semantic_scholar: bool = True,
             include_archive: bool = True) -> Dict[str, Any]:
    """Research a topic across all independent sources.

    Vault (Brad's work) always comes first. External sources are
    genuinely independent — non-profits, universities, public institutions.
    No Google. No Wikipedia. No corporate gatekeepers.
    """
    findings = []
    sources_checked = []

    if include_vault:
        sources_checked.append("vault")
        for vr in vault_search(topic, limit=2):
            findings.append(vr)

    if include_openalex:
        sources_checked.append("openalex")
        for ar in openalex_search(topic, limit=2):
            findings.append(ar)

    if include_semantic_scholar:
        sources_checked.append("semantic_scholar")
        for sr in semantic_scholar_search(topic, limit=2):
            findings.append(sr)

    if include_archive:
        sources_checked.append("internet_archive")
        for ir in internet_archive_search(topic, limit=1):
            findings.append(ir)

    return {
        "topic": topic,
        "findings": findings,
        "sources_checked": sources_checked,
        "finding_count": len(findings),
    }
