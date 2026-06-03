#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import ssl
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request
from xml.etree import ElementTree


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_url(url: str) -> str:
    parsed = urllib_parse.urlparse(url)
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    # keep trailing slash policy stable except for root
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urllib_parse.urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "", ""))


def _is_same_domain(url: str, domain: str) -> bool:
    parsed = urllib_parse.urlparse(url)
    return parsed.netloc.lower() == domain.lower()


def _to_abs(base: str, href: str) -> str:
    joined = urllib_parse.urljoin(base, href)
    parsed = urllib_parse.urlparse(joined)
    return urllib_parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _looks_like_html_path(path: str) -> bool:
    if path == "/":
        return True
    lowered = path.lower()
    if lowered.endswith(".html") or lowered.endswith(".htm"):
        return True
    if "." in lowered.rsplit("/", 1)[-1]:
        return False
    return True


def _is_asset_path(path: str) -> bool:
    lowered = path.lower()
    return bool(
        re.search(
            r"\.(?:css|js|png|jpe?g|gif|svg|webp|avif|ico|woff2?|ttf|mp3|wav|ogg|mp4|webm|pdf|zip|txt|xml)$",
            lowered,
        )
    )


def _extract_literal_strings(source: str, symbol: str) -> list[str]:
    pattern = rf"{re.escape(symbol)}\s*=\s*(\{{.*?\}}|\(.*?\))"
    match = re.search(pattern, source, flags=re.DOTALL)
    if not match:
        return []
    block = str(match.group(1) or "")
    return [str(v).strip() for v in re.findall(r'["\']([^"\']+)["\']', block) if str(v).strip()]


def _load_gate_policy(route_source: Path) -> dict[str, Any]:
    text = route_source.read_text(encoding="utf-8", errors="ignore")
    return {
        "public_paths": set(_extract_literal_strings(text, "_TOWER1_PUBLIC_PATHS")),
        "public_prefixes": tuple(_extract_literal_strings(text, "_TOWER1_PUBLIC_PREFIXES")),
        "protected_paths": set(_extract_literal_strings(text, "_TOWER1_PROTECTED_PATHS")),
        "protected_prefixes": tuple(_extract_literal_strings(text, "_TOWER1_PROTECTED_PREFIXES")),
    }


def _is_public_scope_path(path: str, gate_policy: dict[str, Any]) -> bool:
    value = str(path or "").strip()
    if not value.startswith("/"):
        return False
    if value.startswith("/cdn-cgi/"):
        return False
    explicit_public_overrides = {
        "/install/s25",
        "/install/s25.sh",
        "/terms",
        "/terms/",
        "/privacy",
        "/privacy/",
        "/cookie-policy",
        "/cookie-policy/",
        "/dmca",
        "/dmca/",
        "/refund",
        "/refund/",
        "/data-sovereignty",
        "/data-sovereignty/",
        "/films",
        "/films/",
    }
    if value in explicit_public_overrides:
        return True
    # Auth and gate APIs are intentionally non-public for GET browsing probes.
    if value.startswith("/api/gate/") or value.startswith("/api/enter/"):
        return False
    if value in set(gate_policy.get("protected_paths", set()) or set()):
        return False
    if any(value.startswith(prefix) for prefix in tuple(gate_policy.get("protected_prefixes", tuple()) or tuple())):
        return False
    if value in set(gate_policy.get("public_paths", set()) or set()):
        return True
    if any(value.startswith(prefix) for prefix in tuple(gate_policy.get("public_prefixes", tuple()) or tuple())):
        return True
    if value.startswith("/api/"):
        return value.startswith("/api/public/") or value in {
            "/api/seo/status",
            "/api/indexnow/status",
            "/api/health",
            "/api/status",
            "/api/chat/stats",
            "/api/indexnow/status",
        }
    hard_private_prefixes = (
        "/admin",
        "/account",
        "/ceo",
        "/citizen",
        "/ws",
        "/tower2",
        "/constellation",
    )
    if value.startswith(hard_private_prefixes):
        return False
    return True


def _is_navigational_html_path(path: str, gate_policy: dict[str, Any]) -> bool:
    value = str(path or "").strip()
    if not _looks_like_html_path(value):
        return False
    if not _is_public_scope_path(value, gate_policy):
        return False
    # Keep graph-focused on human-browsable pages (Tower 1 web surfaces).
    if value.startswith("/api/"):
        return False
    # Install/device scripts are downloadable utilities, not page-hub nodes.
    if value.startswith("/install/"):
        return False
    if value.startswith("/dl/"):
        return False
    return True


@dataclass
class FetchResult:
    ok: bool
    status: int | None
    final_url: str
    content_type: str
    body: str
    error: str | None = None


def _is_cloudflare_challenge(*, status: int | None, body: str) -> bool:
    if int(status or 0) != 403:
        return False
    text = str(body or "").lower()
    markers = (
        "attention required",
        "just a moment",
        "/cdn-cgi/challenge-platform",
        "cloudflare",
        "ray id:",
    )
    return any(marker in text for marker in markers)


def _fetch(url: str, *, timeout: int, ua: str) -> FetchResult:
    req = urllib_request.Request(
        url,
        headers={
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    ctx = ssl.create_default_context()
    attempts = 3
    for idx in range(attempts):
        try:
            with urllib_request.urlopen(req, timeout=timeout, context=ctx) as resp:
                status = int(getattr(resp, "status", 0) or 0)
                ctype = str(resp.headers.get("Content-Type", ""))
                body = resp.read().decode("utf-8", errors="replace")
                return FetchResult(
                    ok=200 <= status < 400,
                    status=status,
                    final_url=str(resp.geturl()),
                    content_type=ctype,
                    body=body,
                )
        except urllib_error.HTTPError as exc:
            body = (exc.read() or b"").decode("utf-8", errors="replace")
            status = int(exc.code)
            # Retry common edge throttles/challenge responses once or twice.
            if idx < attempts - 1 and (status in {403, 429, 503, 520, 522}):
                time.sleep(0.35 * (idx + 1))
                continue
            return FetchResult(
                ok=False,
                status=status,
                final_url=url,
                content_type=str(exc.headers.get("Content-Type", "")) if exc.headers else "",
                body=body,
                error=f"http_{status}",
            )
        except Exception as exc:
            if idx < attempts - 1:
                time.sleep(0.25 * (idx + 1))
                continue
            return FetchResult(
                ok=False,
                status=None,
                final_url=url,
                content_type="",
                body="",
                error=str(exc),
            )
    return FetchResult(ok=False, status=None, final_url=url, content_type="", body="", error="fetch_retry_exhausted")


def _fetch_api_endpoint(url: str, *, timeout: int, ua: str) -> FetchResult:
    """
    API-aware fetch: retries GET first, and for known auth/gate action APIs
    retries as POST with a minimal JSON body so method-only mismatches
    do not appear as false broken-route signals.
    """
    out = _fetch(url, timeout=timeout, ua=ua)
    path = urllib_parse.urlparse(url).path or "/"
    post_paths = {
        "/api/gate/login",
        "/api/gate/signup",
        "/api/gate/logout",
        "/api/enter/verify",
    }
    if path not in post_paths:
        return out
    if bool(out.ok):
        return out
    if int(out.status or 0) not in {403, 404, 405}:
        return out
    body_bytes = b"{}"
    req = urllib_request.Request(
        url,
        data=body_bytes,
        method="POST",
        headers={
            "User-Agent": ua,
            "Accept": "application/json,*/*;q=0.8",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib_request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = int(getattr(resp, "status", 0) or 0)
            ctype = str(resp.headers.get("Content-Type", ""))
            body = resp.read().decode("utf-8", errors="replace")
            return FetchResult(
                ok=200 <= status < 400,
                status=status,
                final_url=str(resp.geturl()),
                content_type=ctype,
                body=body,
            )
    except urllib_error.HTTPError as exc:
        body = (exc.read() or b"").decode("utf-8", errors="replace")
        return FetchResult(
            ok=False,
            status=int(exc.code),
            final_url=url,
            content_type=str(exc.headers.get("Content-Type", "")) if exc.headers else "",
            body=body,
            error=f"http_{int(exc.code)}",
        )
    except Exception as exc:
        return FetchResult(
            ok=False,
            status=None,
            final_url=url,
            content_type="",
            body="",
            error=str(exc),
        )


class _HTMLLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.assets: list[str] = []
        self.has_title = False
        self.has_h1 = False
        self.has_description = False
        self._in_title = False
        self._in_h1 = False
        self._title_text = ""
        self._h1_text = ""

    @property
    def title_text(self) -> str:
        return self._title_text.strip()

    @property
    def h1_text(self) -> str:
        return self._h1_text.strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()
        if t == "a":
            href = attrs_map.get("href", "").strip()
            if href:
                self.links.append(href)
        elif t == "form":
            action = attrs_map.get("action", "").strip()
            if action:
                self.links.append(action)
        elif t in {"img", "script", "source"}:
            src = attrs_map.get("src", "").strip()
            if src:
                self.assets.append(src)
        elif t == "link":
            href = attrs_map.get("href", "").strip()
            rel = attrs_map.get("rel", "").strip().lower()
            rel_tokens = {tok for tok in rel.split() if tok}
            asset_rels = {
                "stylesheet",
                "icon",
                "preload",
                "prefetch",
                "modulepreload",
                "mask-icon",
                "apple-touch-icon",
            }
            if href:
                if rel_tokens & asset_rels or _is_asset_path(urllib_parse.urlparse(href).path or ""):
                    self.assets.append(href)
                else:
                    self.links.append(href)
        if t == "title":
            self._in_title = True
            self.has_title = True
        if t == "h1":
            self._in_h1 = True
            self.has_h1 = True
        if t == "meta":
            name = attrs_map.get("name", "").strip().lower()
            if name == "description" and attrs_map.get("content", "").strip():
                self.has_description = True

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "title":
            self._in_title = False
        if t == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_text += data
        if self._in_h1:
            self._h1_text += data


def _sitemap_urls(domain: str, timeout: int, ua: str) -> tuple[list[str], dict[str, Any]]:
    url = f"https://{domain}/sitemap.xml"
    out = _fetch(url, timeout=timeout, ua=ua)
    if not out.ok or not out.body:
        return [], {"ok": False, "url": url, "status": out.status, "error": out.error}
    try:
        root = ElementTree.fromstring(out.body)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [el.text.strip() for el in root.findall(".//sm:url/sm:loc", ns) if el.text]
        locs = [v for v in locs if _is_same_domain(v, domain)]
        normalized = sorted({_canonical_url(v) for v in locs})
        return normalized, {"ok": True, "url": url, "status": out.status, "count": len(normalized)}
    except Exception as exc:
        return [], {"ok": False, "url": url, "status": out.status, "error": str(exc)}


def _seed_urls(domain: str, route_source: Path, sitemap: list[str], gate_policy: dict[str, Any]) -> list[str]:
    seeds: set[str] = {
        f"https://{domain}/",
        f"https://{domain}/gate",
        f"https://{domain}/press",
        f"https://{domain}/awards",
        f"https://{domain}/lumen-sanctum",
        f"https://{domain}/chat",
        f"https://{domain}/citizens",
        f"https://{domain}/contact",
        f"https://{domain}/team",
        f"https://{domain}/mission",
        f"https://{domain}/world",
        f"https://{domain}/join",
        f"https://{domain}/founder",
        f"https://{domain}/disclosures",
        f"https://{domain}/justice",
        f"https://{domain}/faq",
        f"https://{domain}/media",
        f"https://{domain}/laws",
        f"https://{domain}/science",
        f"https://{domain}/security",
        f"https://{domain}/projects",
        f"https://{domain}/accountability",
        f"https://{domain}/api/indexnow/status",
    }
    for path in sorted(set(gate_policy.get("public_paths", set()) or set())):
        value = str(path or "").strip()
        if value.startswith("/"):
            seeds.add(f"https://{domain}{value}")
    seeds.update(sitemap)
    normalized: set[str] = set()
    for value in seeds:
        canon = _canonical_url(value)
        path = urllib_parse.urlparse(canon).path or "/"
        if not _is_public_scope_path(path, gate_policy):
            continue
        normalized.add(canon)
    return sorted(normalized)


def _public_page_sweep_summary(domain: str, timeout: int, ua: str) -> dict[str, Any]:
    out = _fetch(f"https://{domain}/api/public/page-sweep-report", timeout=timeout, ua=ua)
    if not out.ok or not out.body:
        return {"ok": False, "status": out.status, "error": out.error}
    try:
        payload = json.loads(out.body)
        sweep = payload.get("sweep", {}) if isinstance(payload, dict) else {}
        totals = sweep.get("totals", {}) if isinstance(sweep, dict) else {}
        return {
            "ok": True,
            "status": out.status,
            "pages_total": int(totals.get("pages_total", 0) or 0),
            "missing_image_refs": int(totals.get("image_refs_missing", 0) or 0),
            "pages_with_title": int(totals.get("pages_with_title", 0) or 0),
            "pages_with_description_meta": int(totals.get("pages_with_description_meta", 0) or 0),
        }
    except Exception as exc:
        return {"ok": False, "status": out.status, "error": str(exc)}


def _md(report: dict[str, Any]) -> str:
    totals = report.get("totals", {}) if isinstance(report.get("totals"), dict) else {}
    lines = [
        "# Full Network Surface Audit",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Domain: `{report.get('domain')}`",
        f"- Overall OK: `{report.get('ok')}`",
        "",
        "## Totals",
        f"- Seed URLs: `{totals.get('seed_urls_total')}`",
        f"- Crawled pages: `{totals.get('crawled_pages_total')}`",
        f"- HTML pages: `{totals.get('html_pages_total')}`",
        f"- Internal link edges: `{totals.get('internal_link_edges_total')}`",
        f"- Broken pages (public-strict): `{totals.get('broken_pages_total')}`",
        f"- Broken pages (raw crawl): `{totals.get('raw_broken_pages_total')}`",
        f"- Broken internal links (public-strict): `{totals.get('broken_internal_links_total')}`",
        f"- Broken internal links (raw crawl): `{totals.get('raw_broken_internal_links_total')}`",
        f"- Dead-end HTML pages (public-strict): `{totals.get('dead_end_html_pages_total')}`",
        f"- Dead-end HTML pages (raw crawl): `{totals.get('raw_dead_end_html_pages_total')}`",
        f"- Orphan HTML pages (public-strict): `{totals.get('orphan_html_pages_total')}`",
        f"- Orphan HTML pages (raw crawl): `{totals.get('raw_orphan_html_pages_total')}`",
        f"- HTML missing title (public-strict): `{totals.get('missing_title_total')}`",
        f"- HTML missing title (raw crawl): `{totals.get('raw_missing_title_total')}`",
        f"- HTML missing description (public-strict): `{totals.get('missing_description_total')}`",
        f"- HTML missing description (raw crawl): `{totals.get('raw_missing_description_total')}`",
        f"- Broken assets (public-strict): `{totals.get('broken_assets_total')}`",
        f"- Broken assets (raw crawl): `{totals.get('raw_broken_assets_total')}`",
        "",
        "## Blockers",
        *(f"- `{b}`" for b in report.get("blockers", [])),
        "",
    ]
    return "\n".join(lines) + "\n"


def run_audit(
    *,
    domain: str,
    max_pages: int,
    timeout: int,
    route_source: Path,
    state_dir: Path,
) -> dict[str, Any]:
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    gate_policy = _load_gate_policy(route_source)
    sitemap_urls, sitemap_status = _sitemap_urls(domain, timeout, ua)
    seed_urls = _seed_urls(domain, route_source, sitemap_urls, gate_policy)
    page_sweep = _public_page_sweep_summary(domain, timeout, ua)
    sitemap_paths = {urllib_parse.urlparse(u).path or "/" for u in sitemap_urls}
    explicit_public_paths = set(gate_policy.get("public_paths", set()) or set())
    explicit_public_prefixes = tuple(gate_policy.get("public_prefixes", tuple()) or tuple())
    always_verify_paths = {
        "/",
        "/gate",
        "/press",
        "/awards",
        "/lumen-sanctum",
        "/chat",
        "/citizens",
        "/api/public/current-status",
        "/api/public/page-sweep-report",
        "/api/public/search-discovery",
        "/api/public/search-identity",
        "/api/seo/status",
    }

    def _in_verification_scope(path: str) -> bool:
        p = str(path or "").strip()
        if p.startswith("/api/gate/") or p.startswith("/api/enter/"):
            return False
        if p in always_verify_paths:
            return True
        if p in explicit_public_paths:
            return True
        if any(p.startswith(prefix) for prefix in explicit_public_prefixes):
            return True
        if p in sitemap_paths:
            return True
        return False

    queue: deque[str] = deque(seed_urls)
    seen: set[str] = set()
    page_results: dict[str, dict[str, Any]] = {}
    page_edges: dict[str, set[str]] = {}
    in_degree: dict[str, int] = {}
    asset_refs: set[str] = set()

    while queue and len(seen) < max(1, int(max_pages)):
        url = _canonical_url(queue.popleft())
        if url in seen:
            continue
        seen.add(url)

        url_path = urllib_parse.urlparse(url).path or "/"
        if url_path.startswith("/api/"):
            fetched = _fetch_api_endpoint(url, timeout=timeout, ua=ua)
        else:
            fetched = _fetch(url, timeout=timeout, ua=ua)
        final = _canonical_url(fetched.final_url) if fetched.final_url else url
        row: dict[str, Any] = {
            "url": url,
            "status": fetched.status,
            "ok": bool(fetched.ok),
            "final_url": final,
            "content_type": fetched.content_type,
            "error": fetched.error,
            "is_html": "text/html" in fetched.content_type.lower(),
        }
        edges: set[str] = set()
        if row["is_html"] and fetched.body:
            parser = _HTMLLinkParser()
            try:
                parser.feed(fetched.body)
            except Exception:
                pass

            row["has_title"] = bool(parser.has_title and parser.title_text)
            row["has_h1"] = bool(parser.has_h1 and parser.h1_text)
            row["has_description_meta"] = bool(parser.has_description)
            row["title"] = parser.title_text[:220]
            row["h1"] = parser.h1_text[:220]

            for raw_link in parser.links:
                raw = str(raw_link).strip()
                if not raw or raw.startswith("#") or raw.startswith("mailto:") or raw.startswith("tel:") or raw.startswith("javascript:"):
                    continue
                abs_url = _to_abs(url, raw)
                if not _is_same_domain(abs_url, domain):
                    continue
                canonical = _canonical_url(abs_url)
                path = urllib_parse.urlparse(canonical).path or "/"
                if not _is_public_scope_path(path, gate_policy):
                    continue
                if not _in_verification_scope(path):
                    continue
                if _is_asset_path(path):
                    asset_refs.add(canonical)
                    continue
                if _looks_like_html_path(path):
                    edges.add(canonical)
                    in_degree[canonical] = in_degree.get(canonical, 0) + 1
                    if canonical not in seen and canonical not in queue:
                        queue.append(canonical)
                else:
                    # Keep API/non-HTML links in edges for broken-link checks.
                    edges.add(canonical)
                    in_degree[canonical] = in_degree.get(canonical, 0) + 1
                    if canonical not in seen and canonical not in queue:
                        queue.append(canonical)

            for raw_asset in parser.assets:
                raw = str(raw_asset).strip()
                if not raw or raw.startswith("data:") or raw.startswith("javascript:"):
                    continue
                abs_url = _to_abs(url, raw)
                if _is_same_domain(abs_url, domain):
                    asset_refs.add(_canonical_url(abs_url))

        page_results[url] = row
        page_edges[url] = edges

    # Probe assets once.
    assets: dict[str, dict[str, Any]] = {}
    for asset in sorted(asset_refs):
        out = _fetch(asset, timeout=timeout, ua=ua)
        assets[asset] = {
            "url": asset,
            "status": out.status,
            "ok": bool(out.ok),
            "content_type": out.content_type,
            "error": out.error,
        }

    # Analyze graph and status.
    raw_broken_pages: list[str] = []
    raw_html_pages: list[str] = []
    raw_missing_title: list[str] = []
    raw_missing_description: list[str] = []
    raw_dead_end_html: list[str] = []
    raw_broken_internal_links: list[str] = []
    raw_orphan_html: list[str] = []
    raw_edges_total = 0

    for src, row in page_results.items():
        status = int(row.get("status", 0) or 0) if row.get("status") is not None else 0
        if status >= 400 or not bool(row.get("ok", False)):
            raw_broken_pages.append(src)
        if bool(row.get("is_html", False)):
            raw_html_pages.append(src)
            if not bool(row.get("has_title", False)):
                raw_missing_title.append(src)
            if not bool(row.get("has_description_meta", False)):
                raw_missing_description.append(src)

    for src, links in page_edges.items():
        raw_edges_total += len(links)
        src_is_html = bool((page_results.get(src) or {}).get("is_html", False))
        if src_is_html:
            src_row = page_results.get(src, {})
            src_status = int(src_row.get("status", 0) or 0) if src_row.get("status") is not None else 0
            src_final_url = str(src_row.get("final_url", "") or "").strip()
            src_is_redirect = 300 <= src_status < 400 or (
                bool(src_final_url) and _canonical_url(src_final_url) != _canonical_url(src)
            )
            if src_is_redirect:
                continue
            outgoing_html = 0
            for dst in links:
                dst_path = urllib_parse.urlparse(dst).path or "/"
                if _looks_like_html_path(dst_path) and not dst_path.startswith("/api/"):
                    outgoing_html += 1
            if outgoing_html == 0:
                raw_dead_end_html.append(src)
        for dst in links:
            dst_row = page_results.get(dst)
            if dst_row is None:
                dst_path = urllib_parse.urlparse(dst).path or "/"
                if dst_path.startswith("/api/"):
                    out = _fetch_api_endpoint(dst, timeout=timeout, ua=ua)
                else:
                    out = _fetch(dst, timeout=timeout, ua=ua)
                dst_row = {
                    "status": out.status,
                    "ok": bool(out.ok),
                }
                page_results[dst] = dst_row
            status = int(dst_row.get("status", 0) or 0) if dst_row.get("status") is not None else 0
            if status >= 400 or not bool(dst_row.get("ok", False)):
                raw_broken_internal_links.append(f"{src} -> {dst}")

    for page in raw_html_pages:
        if page in {f"https://{domain}/", f"https://{domain}/gate"}:
            continue
        if in_degree.get(page, 0) == 0:
            raw_orphan_html.append(page)

    raw_broken_assets = [u for u, row in assets.items() if not bool(row.get("ok", False))]

    broken_pages: list[str] = []
    html_pages: list[str] = []
    missing_title: list[str] = []
    missing_description: list[str] = []
    dead_end_html: list[str] = []
    broken_internal_links: list[str] = []
    edges_total = 0

    for src, row in page_results.items():
        src_path = urllib_parse.urlparse(src).path or "/"
        if not _is_public_scope_path(src_path, gate_policy):
            continue
        if not _in_verification_scope(src_path):
            continue
        status = int(row.get("status", 0) or 0) if row.get("status") is not None else 0
        final_url = str(row.get("final_url", "") or "").strip()
        is_redirect = 300 <= status < 400 or (bool(final_url) and _canonical_url(final_url) != _canonical_url(src))
        if status >= 400 or not bool(row.get("ok", False)):
            broken_pages.append(src)
        if bool(row.get("is_html", False)):
            html_pages.append(src)
            # Redirect aliases and utility switchboard pages are excluded from metadata blockers.
            metadata_exclusions = {"/login", "/projects"}
            if not is_redirect and status < 400 and src_path not in metadata_exclusions:
                if not bool(row.get("has_title", False)):
                    missing_title.append(src)
                if not bool(row.get("has_description_meta", False)):
                    missing_description.append(src)

    for src, links in page_edges.items():
        src_path = urllib_parse.urlparse(src).path or "/"
        if not _is_public_scope_path(src_path, gate_policy):
            continue
        if not _in_verification_scope(src_path):
            continue
        edges_total += len(links)
        src_is_html = bool((page_results.get(src) or {}).get("is_html", False))
        if src_is_html:
            src_row = page_results.get(src, {})
            src_status = int(src_row.get("status", 0) or 0) if src_row.get("status") is not None else 0
            src_final_url = str(src_row.get("final_url", "") or "").strip()
            src_is_redirect = 300 <= src_status < 400 or (
                bool(src_final_url) and _canonical_url(src_final_url) != _canonical_url(src)
            )
            if src_is_redirect:
                continue
            outgoing_html = 0
            for dst in links:
                dst_path = urllib_parse.urlparse(dst).path or "/"
                if (
                    _looks_like_html_path(dst_path)
                    and not dst_path.startswith("/api/")
                    and _is_public_scope_path(dst_path, gate_policy)
                    and _in_verification_scope(dst_path)
                ):
                    outgoing_html += 1
            if outgoing_html == 0:
                dead_end_html.append(src)
        for dst in links:
            dst_path = urllib_parse.urlparse(dst).path or "/"
            if not _is_public_scope_path(dst_path, gate_policy):
                continue
            if not _in_verification_scope(dst_path):
                continue
            dst_row = page_results.get(dst)
            if dst_row is None:
                # if not crawled due cap, one quick fetch
                if dst_path.startswith("/api/"):
                    out = _fetch_api_endpoint(dst, timeout=timeout, ua=ua)
                else:
                    out = _fetch(dst, timeout=timeout, ua=ua)
                dst_row = {
                    "status": out.status,
                    "ok": bool(out.ok),
                }
                page_results[dst] = dst_row
            status = int(dst_row.get("status", 0) or 0) if dst_row.get("status") is not None else 0
            if status >= 400 or not bool(dst_row.get("ok", False)):
                broken_internal_links.append(f"{src} -> {dst}")

    # Filter out known intentional utility/switchboard surfaces from dead-end accounting.
    dead_end_exclusions = {
        "/login",
        "/projects",
        "/faq",
        "/justice",
        "/museum",
        "/museum/mythology",
    }
    dead_end_html = [
        page
        for page in dead_end_html
        if (urllib_parse.urlparse(page).path or "/") not in dead_end_exclusions
    ]

    orphan_exclusions = {
        "/login",
        "/projects",
    }
    orphan_html: list[str] = []
    for page in html_pages:
        page_path = urllib_parse.urlparse(page).path or "/"
        if not _is_public_scope_path(page_path, gate_policy):
            continue
        if not _in_verification_scope(page_path):
            continue
        if page in {f"https://{domain}/", f"https://{domain}/gate"}:
            continue
        if page_path in orphan_exclusions:
            continue
        row = page_results.get(page, {})
        status = int(row.get("status", 0) or 0) if row.get("status") is not None else 0
        final_url = str(row.get("final_url", "") or "").strip()
        is_redirect = 300 <= status < 400 or (bool(final_url) and _canonical_url(final_url) != _canonical_url(page))
        if is_redirect:
            continue
        if in_degree.get(page, 0) == 0:
            orphan_html.append(page)

    broken_assets = []
    for u, row in assets.items():
        path = urllib_parse.urlparse(u).path or "/"
        if not _is_public_scope_path(path, gate_policy):
            continue
        if not bool(row.get("ok", False)):
            broken_assets.append(u)

    # Chat/user interaction quality probes.
    chat_paths = [
        "/chat",
        "/api/chat/stats",
        "/api/public/current-status",
        "/api/public/consciousness-morse-audit",
        "/api/republic/comms/channels",
    ]
    chat_checks: list[dict[str, Any]] = []
    chat_failures: list[str] = []
    for path in chat_paths:
        url = f"https://{domain}{path}"
        out = _fetch(url, timeout=timeout, ua=ua)
        ok = bool(out.ok) and (out.status is not None and int(out.status) < 400)
        chat_checks.append({"path": path, "url": url, "status": out.status, "ok": ok, "error": out.error})
        if not ok:
            chat_failures.append(path)

    blockers: list[str] = []
    if broken_pages:
        blockers.append("broken_pages_present")
    if broken_internal_links:
        blockers.append("broken_internal_links_present")
    if dead_end_html:
        blockers.append("dead_end_html_pages_present")
    if orphan_html:
        blockers.append("orphan_html_pages_present")
    if missing_title:
        blockers.append("html_pages_missing_title")
    if missing_description:
        blockers.append("html_pages_missing_description")
    if broken_assets:
        blockers.append("broken_assets_present")
    if chat_failures:
        blockers.append("chat_or_citizen_surface_failures")

    payload = {
        "id": f"full-network-surface-audit-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": _now(),
        "domain": domain,
        "ok": len(blockers) == 0,
        "blockers": sorted(set(blockers)),
        "sitemap": sitemap_status,
        "public_page_sweep": page_sweep,
        "totals": {
            "seed_urls_total": len(seed_urls),
            "sitemap_urls_total": len(sitemap_urls),
            "crawled_pages_total": len(page_results),
            "public_page_sweep_total": int(page_sweep.get("pages_total", 0) or 0),
            "html_pages_total": len(html_pages),
            "internal_link_edges_total": edges_total,
            "broken_pages_total": len(broken_pages),
            "broken_internal_links_total": len(broken_internal_links),
            "dead_end_html_pages_total": len(dead_end_html),
            "orphan_html_pages_total": len(orphan_html),
            "missing_title_total": len(missing_title),
            "missing_description_total": len(missing_description),
            "assets_checked_total": len(assets),
            "broken_assets_total": len(broken_assets),
            "raw_html_pages_total": len(raw_html_pages),
            "raw_internal_link_edges_total": raw_edges_total,
            "raw_broken_pages_total": len(raw_broken_pages),
            "raw_broken_internal_links_total": len(raw_broken_internal_links),
            "raw_dead_end_html_pages_total": len(raw_dead_end_html),
            "raw_orphan_html_pages_total": len(raw_orphan_html),
            "raw_missing_title_total": len(raw_missing_title),
            "raw_missing_description_total": len(raw_missing_description),
            "raw_broken_assets_total": len(raw_broken_assets),
            "chat_checks_total": len(chat_checks),
            "chat_failures_total": len(chat_failures),
        },
        "chat_user_experience_checks": {
            "ok": len(chat_failures) == 0,
            "failures": chat_failures,
            "results": chat_checks,
        },
        "samples": {
            "broken_pages": broken_pages[:80],
            "broken_internal_links": broken_internal_links[:120],
            "dead_end_html_pages": dead_end_html[:120],
            "orphan_html_pages": orphan_html[:120],
            "missing_title_pages": missing_title[:120],
            "missing_description_pages": missing_description[:120],
            "broken_assets": broken_assets[:120],
            "raw_broken_pages": raw_broken_pages[:120],
            "raw_broken_internal_links": raw_broken_internal_links[:160],
            "raw_dead_end_html_pages": raw_dead_end_html[:120],
            "raw_orphan_html_pages": raw_orphan_html[:120],
            "raw_missing_title_pages": raw_missing_title[:120],
            "raw_missing_description_pages": raw_missing_description[:120],
            "raw_broken_assets": raw_broken_assets[:120],
        },
        "paths": {
            "latest_json": str(state_dir / "full_network_surface_audit.latest.json"),
            "latest_md": str(state_dir / "full_network_surface_audit.latest.md"),
            "history_jsonl": str(state_dir / "full_network_surface_audit.history.jsonl"),
        },
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deep public link/page network audit for Tower 1 surfaces.")
    parser.add_argument("--domain", default="auroragalaxyrepublic.com")
    parser.add_argument("--max-pages", type=int, default=900)
    parser.add_argument("--timeout-seconds", type=int, default=25)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    route_source = repo_root / "aurora_server" / "republic_os_server.py"
    state_dir = repo_root / "aurora_server" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    report = run_audit(
        domain=str(args.domain).strip(),
        max_pages=int(args.max_pages),
        timeout=int(args.timeout_seconds),
        route_source=route_source,
        state_dir=state_dir,
    )

    latest_json = state_dir / "full_network_surface_audit.latest.json"
    latest_md = state_dir / "full_network_surface_audit.latest.md"
    history = state_dir / "full_network_surface_audit.history.jsonl"

    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(_md(report), encoding="utf-8")
    with history.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "id": report.get("id"),
                    "generated_at": report.get("generated_at"),
                    "ok": report.get("ok"),
                    "blockers": report.get("blockers", []),
                    "totals": report.get("totals", {}),
                },
                ensure_ascii=True,
            )
            + "\n"
        )

    print(json.dumps(report, indent=2))
    return 0 if bool(report.get("ok", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
