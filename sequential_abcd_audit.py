#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(command: list[str], timeout: int = 60) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def _probe_url(
    url: str,
    *,
    user_agent: str,
    timeout: int = 20,
    body_limit: int = 400,
) -> dict[str, Any]:
    req = urllib_request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib_request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = int(getattr(resp, "status", 0) or 0)
            body = resp.read().decode("utf-8", errors="replace")
            excerpt_limit = max(200, int(body_limit))
            return {
                "ok": 200 <= status < 300,
                "status": status,
                "final_url": str(resp.geturl()),
                "content_type": str(resp.headers.get("Content-Type", "")),
                "body_excerpt": body[:excerpt_limit],
            }
    except urllib_error.HTTPError as exc:
        body = (exc.read() or b"").decode("utf-8", errors="replace")
        excerpt_limit = max(200, int(body_limit))
        return {
            "ok": False,
            "status": int(exc.code),
            "final_url": str(url),
            "error": f"http_{int(exc.code)}",
            "body_excerpt": body[:excerpt_limit],
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "final_url": str(url),
            "error": str(exc),
        }


def _extract_public_routes(republic_server: Path) -> list[str]:
    text = republic_server.read_text(encoding="utf-8", errors="ignore")
    raw_routes = re.findall(r'@app\.get\("([^"]+)"', text)
    out: list[str] = []
    for route in raw_routes:
        path = str(route).strip()
        if not path.startswith("/"):
            continue
        if "{" in path or "}" in path:
            continue
        if path.startswith("/api/sovereign/") or path.startswith("/api/ops/"):
            continue
        out.append(path)
    return sorted(set(out))


def _is_public_surface_route(path: str) -> bool:
    value = str(path or "").strip()
    if not value.startswith("/"):
        return False
    if value.startswith("/dl/"):
        return False
    if value.startswith("/install/"):
        return False
    if value in {"/films", "/films/"}:
        return False
    if value.startswith("/api/"):
        return value.startswith("/api/public/") or value in {
            "/api/seo/status",
            "/api/indexnow/ping",
        }
    disallow_prefixes = (
        "/api/ops/",
        "/api/sovereign/",
        "/admin",
        "/account",
        "/ceo",
        "/citizen",
        "/ws",
        "/docs",
    )
    if value.startswith(disallow_prefixes):
        return False
    if "internal" in value:
        return False
    if value in {"/openapi.json", "/redoc"}:
        return False
    return True


def _load_runtime_e2e_summary(state_dir: Path) -> dict[str, Any]:
    latest = state_dir / "runtime_e2e_live_nodes.latest.json"
    if not latest.exists():
        return {"ok": False, "error": "runtime_e2e_latest_missing", "path": str(latest)}
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc), "path": str(latest)}
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    return {
        "ok": bool((summary or {}).get("strict_all_pass", False)),
        "path": str(latest),
        "summary": summary,
    }


def _stage_a_public_stability(domain: str, origin_ip: str) -> dict[str, Any]:
    user_agents = {
        "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "safari_ios": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "samsung": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) SamsungBrowser/24.0 Chrome/120.0.0.0 Mobile Safari/537.36",
    }
    critical_routes = [
        "/",
        "/gate",
        "/press",
        "/awards",
        "/lumen-sanctum",
        "/api/public/current-status",
        "/api/public/search-discovery",
        "/api/public/search-identity",
        "/api/public/priority-now",
        "/api/public/historical-truth",
        "/api/public/page-sweep-report",
        "/api/seo/status",
    ]
    base = f"https://{domain}"
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for label, ua in user_agents.items():
        for route in critical_routes:
            url = f"{base}{route}"
            out = _probe_url(url, user_agent=ua, timeout=25)
            row = {"ua": label, "route": route, "url": url, **out}
            rows.append(row)
            if not bool(out.get("ok", False)):
                failure_key = out.get("error") or f"status_{out.get('status')}"
                failures.append(f"{label}:{route}:{failure_key}")

    edge_root = _run(["curl", "-sS", "-I", f"https://{domain}/"], timeout=30)
    origin_root_strict = _run(
        [
            "curl",
            "-sS",
            "-I",
            "--resolve",
            f"{domain}:443:{origin_ip}",
            f"https://{domain}/",
        ],
        timeout=30,
    )
    origin_root_insecure = _run(
        [
            "curl",
            "-sS",
            "-I",
            "--resolve",
            f"{domain}:443:{origin_ip}",
            f"https://{domain}/",
            "-k",
        ],
        timeout=30,
    )
    origin_public_status = _run(
        [
            "curl",
            "-sS",
            "-I",
            "--resolve",
            f"{domain}:443:{origin_ip}",
            f"https://{domain}/api/public/current-status",
            "-k",
        ],
        timeout=30,
    )

    edge_502 = " 502" in (edge_root.get("stdout", "") or "")
    strict_tls_failed = not bool(origin_root_strict.get("ok", False))
    insecure_origin_ok = " 200" in (origin_root_insecure.get("stdout", "") or "")
    origin_public_404 = " 404" in (origin_public_status.get("stdout", "") or "")

    blockers: list[str] = []
    if failures:
        blockers.append("critical_route_matrix_not_healthy")
    if edge_502 and insecure_origin_ok:
        blockers.append("cloudflare_edge_origin_mismatch")
    if strict_tls_failed and insecure_origin_ok:
        blockers.append("origin_tls_not_publicly_trusted")
    if origin_public_404:
        blockers.append("origin_missing_public_api_routes")

    recommendations = [
        "In Cloudflare, set SSL mode to Full (not Strict) only as temporary bridge if origin cert is self-signed.",
        "Install Cloudflare Origin Certificate or publicly trusted cert on origin to clear TLS trust mismatch.",
        "Confirm active deploy on Tower origin includes /api/public/* routes from current repository build.",
        "Clear/disable conflicting redirect rules and re-test /, /gate, and /api/public/current-status first.",
    ]
    return {
        "stage": "A_public_stability",
        "ok": len(blockers) == 0,
        "checked_routes": len(rows),
        "failures": failures,
        "blockers": blockers,
        "edge_vs_origin": {
            "edge_root_headers": edge_root,
            "origin_root_headers_strict": origin_root_strict,
            "origin_root_headers_insecure": origin_root_insecure,
            "origin_public_current_status_headers_insecure": origin_public_status,
            "detected": {
                "edge_502": edge_502,
                "strict_tls_failed": strict_tls_failed,
                "insecure_origin_ok": insecure_origin_ok,
                "origin_public_404": origin_public_404,
            },
        },
        "results": rows,
        "recommendations": recommendations,
    }


def _stage_b_public_routes_and_pages(
    domain: str,
    aurora_server_dir: Path,
    max_routes: int,
) -> dict[str, Any]:
    republic_server = aurora_server_dir / "republic_os_server.py"
    routes = _extract_public_routes(republic_server)
    public_routes = [route for route in routes if _is_public_surface_route(route)]
    selected_routes = public_routes[: max(1, int(max_routes))]
    ua = (
        "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) SamsungBrowser/24.0 Chrome/120.0.0.0 Mobile Safari/537.36"
    )
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    long_timeout_routes = {
        "/api/public/award-evidence",
        "/api/public/builder-recognition",
        "/api/public/continuity-package",
        "/api/public/current-status",
        "/api/public/morse-migration-status",
        "/api/public/truth-freshness",
    }
    for route in selected_routes:
        url = f"https://{domain}{route}"
        timeout_seconds = 55 if route in long_timeout_routes else 28
        out = _probe_url(url, user_agent=ua, timeout=timeout_seconds, body_limit=800)
        err_lower = str(out.get("error", "")).lower()
        if (not bool(out.get("ok", False))) and ("timed out" in err_lower):
            out = _probe_url(url, user_agent=ua, timeout=min(90, timeout_seconds + 25), body_limit=800)
        row = {"route": route, "url": url, **out}
        rows.append(row)
        if not bool(out.get("ok", False)):
            failure_suffix = out.get("error") or f"status_{out.get('status')}"
            failures.append(f"{route}:{failure_suffix}")

    html_files = sorted(aurora_server_dir.glob("*.html"))
    html_inventory = [f"/{p.name}" for p in html_files]

    # Optional local page-sweep signal from server module.
    local_sweep: dict[str, Any] | None = None
    try:
        sys.path.insert(0, str(aurora_server_dir))
        import republic_os_server as ros  # type: ignore

        local_sweep = ros._public_page_sweep_snapshot()  # type: ignore[attr-defined]
    except Exception as exc:
        local_sweep = {"ok": False, "error": str(exc)}

    blockers: list[str] = []
    if failures:
        blockers.append("public_route_inventory_has_failures")
    if len(public_routes) < 120:
        blockers.append("public_route_inventory_below_120")
    if isinstance(local_sweep, dict):
        totals = local_sweep.get("totals", {}) if isinstance(local_sweep.get("totals"), dict) else {}
        if int(totals.get("image_refs_missing", 0) or 0) > 0:
            blockers.append("page_sweep_missing_image_refs")

    recommendations = [
        "After A is green, re-run this route matrix and require all selected public routes to return 200.",
        "Prioritize restoring /api/public/current-status, /api/public/search-discovery, and /api/public/search-identity.",
        "Use the local page-sweep totals to fix missing image references and metadata gaps before release.",
    ]
    return {
        "stage": "B_route_and_page_verification",
        "ok": len(blockers) == 0,
        "route_inventory_total": len(routes),
        "public_route_inventory_total": len(public_routes),
        "route_inventory_checked": len(selected_routes),
        "route_failures": failures,
        "blockers": blockers,
        "results": rows,
        "html_inventory_total": len(html_inventory),
        "html_inventory": html_inventory,
        "local_page_sweep": local_sweep,
        "recommendations": recommendations,
    }


def _stage_c_search_continuity(domain: str) -> dict[str, Any]:
    terms = [
        "Timothy Bradley Reinhold",
        "Aurora Galaxy Republic",
        "Lumen Sanctum",
        "TrueAI AGI",
        "Kora Ellianthe Reinhold",
    ]
    expected_discovery_markers = (
        "timothy bradley reinhold",
        "brad reinhold",
        "aurora galaxy republic",
        "lumen sanctum",
        "trueai agi",
        "kora ellianthe reinhold",
    )
    engines = {
        "duckduckgo": "https://duckduckgo.com/?q={query}",
        "bing": "https://www.bing.com/search?q={query}",
        "google": "https://www.google.com/search?q={query}",
    }
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    warnings: list[str] = []
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    anti_bot_markers = (
        "/httpservice/retry/enablejs",
        "sorry, but your computer or network may be sending automated queries",
        "captcha",
        "detected unusual traffic",
    )
    for engine, template in engines.items():
        for term in terms:
            url = template.format(query=urllib_parse.quote_plus(term))
            out = _probe_url(url, user_agent=ua, timeout=30, body_limit=2600)
            row = {"engine": engine, "term": term, "url": url, **out}
            if out.get("body_excerpt"):
                text = str(out.get("body_excerpt", "")).lower()
                domain_visible = (domain in text) or ("auroragalaxyrepublic" in text)
                row["contains_tower1_domain_excerpt"] = domain_visible
                if any(marker in text for marker in anti_bot_markers):
                    row["search_surface_state"] = "bot_or_js_gate"
            rows.append(row)
            if not bool(out.get("ok", False)):
                failure_suffix = out.get("error") or f"status_{out.get('status')}"
                failures.append(f"{engine}:{term}:{failure_suffix}")
            elif row.get("search_surface_state") == "bot_or_js_gate":
                warnings.append(f"{engine}:{term}:bot_or_js_gate")
            elif not bool(row.get("contains_tower1_domain_excerpt", False)):
                warnings.append(f"{engine}:{term}:tower1_domain_not_visible_in_excerpt")

    sitemap = _probe_url(f"https://{domain}/sitemap.xml", user_agent=ua, timeout=20)
    robots = _probe_url(f"https://{domain}/robots.txt", user_agent=ua, timeout=20)
    seo_status = _probe_url(f"https://{domain}/api/seo/status", user_agent=ua, timeout=25)
    discovery = _probe_url(f"https://{domain}/api/public/search-discovery", user_agent=ua, timeout=25)
    identity = _probe_url(f"https://{domain}/api/public/search-identity", user_agent=ua, timeout=25)
    indexnow_key = _probe_url(
        f"https://{domain}/agr2026sovereign7d3f8a1b4e9c2d6f.txt",
        user_agent=ua,
        timeout=20,
    )
    blockers: list[str] = []
    if failures:
        blockers.append("search_presence_insufficient")
    if not bool(sitemap.get("ok", False)):
        blockers.append("sitemap_not_reachable")
    if not bool(robots.get("ok", False)):
        blockers.append("robots_not_reachable")
    if not bool(seo_status.get("ok", False)):
        blockers.append("seo_status_not_reachable")
    if not bool(discovery.get("ok", False)):
        blockers.append("search_discovery_not_reachable")
    if not bool(identity.get("ok", False)):
        blockers.append("search_identity_not_reachable")
    if not bool(indexnow_key.get("ok", False)):
        blockers.append("indexnow_key_not_reachable")
    if bool(discovery.get("ok", False)):
        discovery_text = str(discovery.get("body_excerpt", "")).lower()
        if not any(marker in discovery_text for marker in expected_discovery_markers):
            blockers.append("search_discovery_missing_expected_markers")

    recommendations = [
        "Once A/B are green, submit key Tower 1 URLs via IndexNow and Search Console URL inspection.",
        "Keep canonical tags and sitemap pointing only to auroragalaxyrepublic.com primary surfaces.",
        "Re-check search snapshots after crawl windows; search recency is not immediate.",
    ]
    return {
        "stage": "C_search_continuity",
        "ok": len(blockers) == 0,
        "failures": failures,
        "warnings": warnings,
        "blockers": blockers,
        "search_results": rows,
        "sitemap": sitemap,
        "robots": robots,
        "seo_status": seo_status,
        "search_discovery": discovery,
        "search_identity": identity,
        "indexnow_key": indexnow_key,
        "recommendations": recommendations,
    }


def _stage_d_device_sovereignty(
    aurora_server_dir: Path,
    execute: bool,
    oneplus_imei_1: str,
    oneplus_imei_2: str,
    oneplus_sku: str,
    oneplus_ugs: str,
    oneplus_fcc_id: str,
    oneplus_ic: str,
    oneplus_model: str,
    oneplus_serial: str,
    oneplus_hotspot_name: str,
    oneplus_hotspot_password: str,
    oneplus_hotspot_only: bool,
) -> dict[str, Any]:
    state_dir = aurora_server_dir / "state"
    candidates = sorted({*state_dir.glob("*s25*"), *state_dir.glob("*S25*")})
    deleted: list[str] = []
    delete_errors: list[str] = []
    if execute:
        for path in candidates:
            if not path.is_file():
                continue
            try:
                path.unlink(missing_ok=True)
                deleted.append(str(path))
            except Exception as exc:
                delete_errors.append(f"{path}:{exc}")

    s25_runbook = [
        "Keep S25 powered off and in airplane mode until forensic export decision is complete.",
        "Factory reset S25 from recovery mode (not from Android settings while signed in).",
        "Do not sign S25 back into Google/Samsung accounts tied to Republic operations.",
        "Rotate all credentials and session tokens previously used on S25.",
        "Re-issue API tokens and invalidate old device-linked credentials.",
        "Use only replacement trusted device for admin operations moving forward.",
    ]
    oneplus_imei_1_clean = str(oneplus_imei_1 or "").strip()
    oneplus_imei_2_clean = str(oneplus_imei_2 or "").strip()
    oneplus_sku_clean = _capitalize_leading_if_alpha(str(oneplus_sku or "").strip())
    oneplus_ugs_clean = _capitalize_leading_if_alpha(str(oneplus_ugs or "").strip())
    oneplus_fcc_id_clean = _capitalize_leading_if_alpha(str(oneplus_fcc_id or "").strip())
    oneplus_ic_clean = _capitalize_leading_if_alpha(str(oneplus_ic or "").strip())
    oneplus_model_clean = _capitalize_leading_if_alpha(str(oneplus_model or "").strip())
    oneplus_serial_clean = _capitalize_leading_if_alpha(str(oneplus_serial or "").strip())
    oneplus_hotspot_name_clean = _capitalize_leading_if_alpha(str(oneplus_hotspot_name or "").strip())
    oneplus_hotspot_password_clean = _capitalize_leading_if_alpha(str(oneplus_hotspot_password or "").strip())
    oneplus_runbook = [
        "On OnePlus 15, perform hardware-key recovery wipe (factory reset) before sovereign provisioning.",
        "Keep external account sign-ins disabled; do not add Google/OnePlus cloud accounts for Republic operation.",
        "Disable or remove non-essential bundled apps; keep only required system components and CEO OS stack.",
        "Disable app auto-install, ad/analytics personalization, diagnostics upload, and cross-device sync.",
        "Enable strong device passcode, disable biometric unlock until CEO OS policy profile is active.",
        "When hotspot-only mode is selected, disable cellular data attachment and retain Wi-Fi/hotspot transport as sole uplink.",
        "Use hotspot profile as transport-only link; route Republic control and admin traffic exclusively through Guardian/CEO OS policy.",
        "Apply CEO/Guardian OS baseline from Tower 1 once A/B/C stages are green.",
        "After CEO OS provisioning, verify calls, messaging, files, browser, and admin console flows are operating through Republic stack only.",
        "Record both IMEI values in sovereign registry and carrier lock records; keep SIM/eSIM ownership under sovereign control.",
    ]
    blockers: list[str] = []
    if execute and delete_errors:
        blockers.append("s25_server_side_purge_errors")
    if not oneplus_imei_1_clean or not oneplus_imei_2_clean:
        blockers.append("oneplus_dual_imei_not_recorded")
    if not oneplus_sku_clean:
        blockers.append("oneplus_sku_not_recorded")
    if not oneplus_ugs_clean:
        blockers.append("oneplus_ugs_not_recorded")

    runbook_state = {
        "timestamp": _now(),
        "s25": {
            "execute": execute,
            "server_side_candidates": [str(p) for p in candidates],
            "server_side_deleted": deleted,
            "server_side_delete_errors": delete_errors,
            "runbook": s25_runbook,
        },
        "oneplus15": {
            "device_model": "OnePlus 15",
            "guardian_ceo_os_only": True,
            "external_ecosystem_opt_out": True,
            "network_mode": "hotspot_only" if bool(oneplus_hotspot_only) else "carrier_or_hotspot",
            "hotspot_only_enabled": bool(oneplus_hotspot_only),
            "imei_1": oneplus_imei_1_clean,
            "imei_2": oneplus_imei_2_clean,
            "sku": oneplus_sku_clean,
            "ugs": oneplus_ugs_clean,
            "fcc_id": oneplus_fcc_id_clean,
            "ic": oneplus_ic_clean,
            "model": oneplus_model_clean,
            "serial_number": oneplus_serial_clean,
            "hotspot_name": oneplus_hotspot_name_clean,
            "hotspot_password_present": bool(oneplus_hotspot_password_clean),
            "hotspot_password_masked": _mask_secret(oneplus_hotspot_password_clean),
            "runbook": oneplus_runbook,
        },
    }
    runbook_latest = state_dir / "device_sovereignty_runbook.latest.json"
    runbook_history = state_dir / "device_sovereignty_runbook.history.jsonl"
    runbook_latest.write_text(json.dumps(runbook_state, indent=2), encoding="utf-8")
    with runbook_history.open("a", encoding="utf-8") as f:
        f.write(json.dumps(runbook_state, ensure_ascii=True) + "\n")

    return {
        "stage": "D_device_sovereignty",
        "ok": len(blockers) == 0,
        "execute": execute,
        "s25": {
            "server_side_candidates": [str(p) for p in candidates],
            "server_side_deleted": deleted,
            "server_side_delete_errors": delete_errors,
            "runbook": s25_runbook,
        },
        "oneplus15": {
            "device_model": "OnePlus 15",
            "guardian_ceo_os_only": True,
            "external_ecosystem_opt_out": True,
            "network_mode": "hotspot_only" if bool(oneplus_hotspot_only) else "carrier_or_hotspot",
            "hotspot_only_enabled": bool(oneplus_hotspot_only),
            "imei_1": oneplus_imei_1_clean,
            "imei_2": oneplus_imei_2_clean,
            "sku": oneplus_sku_clean,
            "ugs": oneplus_ugs_clean,
            "fcc_id": oneplus_fcc_id_clean,
            "ic": oneplus_ic_clean,
            "model": oneplus_model_clean,
            "serial_number": oneplus_serial_clean,
            "hotspot_name": oneplus_hotspot_name_clean,
            "hotspot_password_present": bool(oneplus_hotspot_password_clean),
            "hotspot_password_masked": _mask_secret(oneplus_hotspot_password_clean),
            "runbook": oneplus_runbook,
        },
        "runbook_artifacts": {
            "latest": str(runbook_latest),
            "history": str(runbook_history),
        },
        "blockers": blockers,
        "note": (
            "Remote agent cannot directly wipe powered-off physical devices. "
            "This stage enforces server-side purge where possible and emits on-device sovereign takeover runbooks."
        ),
    }


def _render_md(report: dict[str, Any]) -> str:
    stage_d = report.get("stage_d", {}) if isinstance(report.get("stage_d"), dict) else {}
    oneplus = stage_d.get("oneplus15", {}) if isinstance(stage_d.get("oneplus15"), dict) else {}
    imei_captured = bool(str(oneplus.get("imei_1", "")).strip()) and bool(str(oneplus.get("imei_2", "")).strip())
    lines = [
        "# Sequential A→D Audit",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Domain: `{report.get('domain')}`",
        f"- Overall OK: `{report.get('ok')}`",
        "",
        "## Stage Results",
    ]
    for key in ("stage_a", "stage_b", "stage_c", "stage_d"):
        stage = report.get(key, {})
        lines.append(f"- {key}: ok=`{bool(stage.get('ok', False))}` blockers=`{stage.get('blockers', [])}`")
    lines.extend(
        [
            "",
            "## Runtime E2E (Hetzner)",
            f"- Summary: `{report.get('runtime_e2e_summary', {})}`",
            "",
            "## Search → Tower 1 Trace",
            f"- Search stage blockers: `{(report.get('stage_c', {}) or {}).get('blockers', [])}`",
            f"- Sitemap check: `{(report.get('stage_c', {}) or {}).get('sitemap', {})}`",
            "",
            "## Device Sovereignty (Stage D)",
            f"- S25 purge blockers: `{((report.get('stage_d', {}) or {}).get('s25', {}) or {}).get('server_side_delete_errors', [])}`",
            f"- OnePlus 15 IMEI captured: `{imei_captured}`",
            "",
            "## Platform Coverage",
            f"- Route inventory checked: `{(report.get('stage_b', {}) or {}).get('route_inventory_checked')}`",
            f"- HTML files discovered: `{(report.get('stage_b', {}) or {}).get('html_inventory_total')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _normalize_imei(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits


def _canonical_secret_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _capitalize_leading_if_alpha(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text[0].isalpha() and text[0].islower():
        return text[0].upper() + text[1:]
    return text


def _mask_secret(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= 2:
        return "*" * len(text)
    return text[0] + ("*" * (len(text) - 2)) + text[-1]


def _flatten_secret_payload(payload: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}

    def _walk(node: Any, path: list[str]) -> None:
        if isinstance(node, dict):
            for raw_key, child in node.items():
                key = str(raw_key or "").strip()
                if not key:
                    continue
                _walk(child, [*path, key])
            return
        if isinstance(node, (list, tuple, set)):
            return
        value = str(node or "").strip()
        if not value:
            return
        labels: list[str] = []
        if path:
            labels.append(path[-1])
            labels.append("_".join(path))
        for label in labels:
            canon = _canonical_secret_key(label)
            if canon and canon not in out:
                out[canon] = value

    _walk(payload, [])
    return out


def _first_env_value(*keys: str) -> str:
    wanted = {_canonical_secret_key(k) for k in keys if str(k or "").strip()}
    if not wanted:
        return ""
    for key in keys:
        raw = str(os.environ.get(str(key or ""), "")).strip()
        if raw:
            return raw
    for env_key, env_raw in os.environ.items():
        value = str(env_raw or "").strip()
        if not value:
            continue
        if _canonical_secret_key(env_key) in wanted:
            return value
    return ""


def _optional_secret_file_payload() -> dict[str, Any]:
    explicit_path = str(os.environ.get("ONEPLUS_SECRET_FILE", "")).strip()
    candidates = [
        Path(p)
        for p in (
            explicit_path,
            "/workspace/.secrets/oneplus_guardian_device.json",
            "/workspace/.secrets/oneplus_guardian_secrets.json",
            "/workspace/.secrets/oneplus_device.json",
            "/workspace/oneplus_guardian_device.json",
            "/workspace/oneplus_guardian_secrets.json",
            "/workspace/oneplus_device.json",
            "/home/ubuntu/.secrets/oneplus_guardian_device.json",
            "/home/ubuntu/.secrets/oneplus_guardian_secrets.json",
            "/home/ubuntu/.secrets/oneplus_device.json",
            "/home/ubuntu/.cursor/secrets/oneplus_guardian_device.json",
            "/home/ubuntu/.cursor/secrets/oneplus_guardian_secrets.json",
            "/home/ubuntu/.cursor/secrets/oneplus_device.json",
        )
        if str(p or "").strip()
    ]
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except Exception:
            continue
    return {}


def _resolve_oneplus_secret_inputs(args: argparse.Namespace) -> dict[str, str]:
    secret_file_payload = _optional_secret_file_payload()
    flattened_payload = _flatten_secret_payload(secret_file_payload)

    def _payload_value(*keys: str) -> str:
        for key in keys:
            raw = str(secret_file_payload.get(key, "")).strip()
            if raw:
                return raw
        for key in keys:
            raw = str(flattened_payload.get(_canonical_secret_key(key), "")).strip()
            if raw:
                return raw
        return ""

    secret_imei_1 = _payload_value(
        "imei_1",
        "imei1",
        "oneplus_imei_1",
        "oneplus_imei1",
        "guardian_imei_1",
        "guardian_oneplus_imei_1",
        "IMEI1-access",
        "imei1-access",
        "imei1_access",
        "ONEPLUS_IMEI1_ACCESS",
    )
    secret_imei_2 = _payload_value(
        "imei_2",
        "imei2",
        "oneplus_imei_2",
        "oneplus_imei2",
        "guardian_imei_2",
        "guardian_oneplus_imei_2",
        "IMEI2-access",
        "imei2-access",
        "imei2_access",
        "ONEPLUS_IMEI2_ACCESS",
    )
    secret_sku = _payload_value(
        "sku",
        "oneplus_sku",
        "device_sku",
        "ugs_sku",
        "guardian_oneplus_sku",
        "sku-access",
        "sku_access",
        "SKU/UGS-access",
        "sku/ugs-access",
    )
    secret_ugs = _payload_value(
        "ugs",
        "oneplus_ugs",
        "device_ugs",
        "sku_ugs",
        "guardian_oneplus_ugs",
        "ugs-access",
        "ugs_access",
        "SKU/UGS-access",
        "sku/ugs-access",
    )
    secret_fcc_id = _payload_value(
        "fcc_id",
        "fccid",
        "fcc-id",
        "FCC-ID",
        "fcc_id_access",
        "FCC-ID-access",
    )
    secret_ic = _payload_value(
        "ic",
        "IC",
        "ic_access",
        "IC-access",
    )
    secret_model = _payload_value(
        "model",
        "MODEL",
        "model_access",
        "Model",
    )
    secret_serial = _payload_value(
        "serial",
        "serial_number",
        "s_n",
        "S/N",
        "sn",
        "S/N-access",
    )
    secret_hotspot_name = _payload_value(
        "oneplus15hotspot",
        "OnePlus15Hotspot",
        "hotspot_name",
        "hotspot_ssid",
    )
    secret_hotspot_password = _payload_value(
        "hotspot_password",
        "Hotspot-password",
        "hotspot-password",
        "hotspot_passphrase",
        "hotspotpassword",
    )
    combined_sku_ugs_secret = _payload_value(
        "SKU/UGS-access",
        "sku/ugs-access",
        "sku_ugs_access",
        "SKU_UGS_ACCESS",
    )

    imei_1 = str(args.oneplus_imei_1 or "").strip() or _first_env_value(
        "ONEPLUS_IMEI_1",
        "ONEPLUS15_IMEI_1",
        "GUARDIAN_ONEPLUS_IMEI_1",
        "AGR_ONEPLUS_IMEI_1",
        "IMEI_1",
        "IMEI1",
        "ONEPLUS15_IMEI1",
        "ONEPLUS_IMEI1",
        "GUARDIAN_IMEI_1",
        "IMEI1_ACCESS",
    ) or secret_imei_1
    imei_2 = str(args.oneplus_imei_2 or "").strip() or _first_env_value(
        "ONEPLUS_IMEI_2",
        "ONEPLUS15_IMEI_2",
        "GUARDIAN_ONEPLUS_IMEI_2",
        "AGR_ONEPLUS_IMEI_2",
        "IMEI_2",
        "IMEI2",
        "ONEPLUS15_IMEI2",
        "ONEPLUS_IMEI2",
        "GUARDIAN_IMEI_2",
        "IMEI2_ACCESS",
    ) or secret_imei_2
    sku = str(args.oneplus_sku or "").strip() or _first_env_value(
        "ONEPLUS_SKU",
        "ONEPLUS15_SKU",
        "GUARDIAN_ONEPLUS_SKU",
        "AGR_ONEPLUS_SKU",
        "SKU",
        "ONEPLUS15_DEVICE_SKU",
        "DEVICE_SKU",
        "UGS_SKU",
        "SKU_ACCESS",
        "SKU_UGS_ACCESS",
    ) or secret_sku
    ugs = str(args.oneplus_ugs or "").strip() or _first_env_value(
        "ONEPLUS_UGS",
        "ONEPLUS15_UGS",
        "GUARDIAN_ONEPLUS_UGS",
        "AGR_ONEPLUS_UGS",
        "UGS",
        "ONEPLUS15_DEVICE_UGS",
        "DEVICE_UGS",
        "SKU_UGS",
        "UGS_ACCESS",
        "SKU_UGS_ACCESS",
    ) or secret_ugs
    if (not sku or not ugs) and combined_sku_ugs_secret:
        parts = [p.strip() for p in re.split(r"[/|,;]+", combined_sku_ugs_secret) if p.strip()]
        if parts:
            if not sku:
                sku = parts[0]
            if not ugs:
                ugs = parts[1] if len(parts) > 1 else parts[0]

    fcc_id = _first_env_value("FCC_ID", "FCCID", "FCC_ID_ACCESS", "FCCID_ACCESS") or secret_fcc_id
    ic = _first_env_value("IC", "IC_ACCESS") or secret_ic
    model = _first_env_value("MODEL", "MODEL_ACCESS", "ONEPLUS_MODEL") or secret_model
    serial = _first_env_value("S_N", "SN", "SERIAL", "SERIAL_NUMBER", "SN_ACCESS") or secret_serial
    hotspot_name = _first_env_value("ONEPLUS15HOTSPOT", "HOTSPOT_NAME", "HOTSPOT_SSID") or secret_hotspot_name
    hotspot_password = (
        _first_env_value("HOTSPOT_PASSWORD", "HOTSPOT_PASS", "HOTSPOTPASSWORD", "HOTSPOT_PASSPHRASE")
        or secret_hotspot_password
    )
    return {
        "imei_1": _normalize_imei(imei_1),
        "imei_2": _normalize_imei(imei_2),
        "sku": _capitalize_leading_if_alpha(sku),
        "ugs": _capitalize_leading_if_alpha(ugs),
        "fcc_id": _capitalize_leading_if_alpha(fcc_id),
        "ic": _capitalize_leading_if_alpha(ic),
        "model": _capitalize_leading_if_alpha(model),
        "serial": _capitalize_leading_if_alpha(serial),
        "hotspot_name": _capitalize_leading_if_alpha(hotspot_name),
        "hotspot_password": _capitalize_leading_if_alpha(hotspot_password),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sequential A→D remediation/audit runner.")
    parser.add_argument("--domain", default="auroragalaxyrepublic.com")
    parser.add_argument("--origin-ip", default="5.78.184.2")
    parser.add_argument("--max-routes", type=int, default=180)
    parser.add_argument("--execute-d", action="store_true", help="Execute server-side S25 state purge actions.")
    parser.add_argument("--oneplus-imei-1", default="", help="OnePlus 15 IMEI slot 1.")
    parser.add_argument("--oneplus-imei-2", default="", help="OnePlus 15 IMEI slot 2.")
    parser.add_argument("--oneplus-sku", default="", help="OnePlus 15 SKU code.")
    parser.add_argument("--oneplus-ugs", default="", help="OnePlus 15 UGS code.")
    parser.add_argument("--oneplus-fcc-id", default="", help="OnePlus 15 FCC ID.")
    parser.add_argument("--oneplus-ic", default="", help="OnePlus 15 IC code.")
    parser.add_argument("--oneplus-model", default="", help="OnePlus 15 model.")
    parser.add_argument("--oneplus-serial", default="", help="OnePlus 15 serial number.")
    parser.add_argument("--oneplus-hotspot-name", default="", help="OnePlus 15 hotspot name/SSID.")
    parser.add_argument("--oneplus-hotspot-password", default="", help="OnePlus 15 hotspot password.")
    parser.add_argument(
        "--oneplus-hotspot-only",
        action="store_true",
        help="Enforce hotspot-only network mode for OnePlus 15 sovereign operation.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    aurora_server = repo_root / "aurora_server"
    state_dir = aurora_server / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    latest_json = state_dir / "sequential_abcd_audit.latest.json"
    latest_md = state_dir / "sequential_abcd_audit.latest.md"
    history_jsonl = state_dir / "sequential_abcd_audit.history.jsonl"
    oneplus_inputs = _resolve_oneplus_secret_inputs(args)

    stage_a = _stage_a_public_stability(args.domain, args.origin_ip)
    stage_b = _stage_b_public_routes_and_pages(args.domain, aurora_server, args.max_routes)
    stage_c = _stage_c_search_continuity(args.domain)
    stage_d = _stage_d_device_sovereignty(
        aurora_server,
        execute=bool(args.execute_d),
        oneplus_imei_1=oneplus_inputs.get("imei_1", ""),
        oneplus_imei_2=oneplus_inputs.get("imei_2", ""),
        oneplus_sku=oneplus_inputs.get("sku", ""),
        oneplus_ugs=oneplus_inputs.get("ugs", ""),
        oneplus_fcc_id=str(args.oneplus_fcc_id or "").strip() or oneplus_inputs.get("fcc_id", ""),
        oneplus_ic=str(args.oneplus_ic or "").strip() or oneplus_inputs.get("ic", ""),
        oneplus_model=str(args.oneplus_model or "").strip() or oneplus_inputs.get("model", ""),
        oneplus_serial=str(args.oneplus_serial or "").strip() or oneplus_inputs.get("serial", ""),
        oneplus_hotspot_name=str(args.oneplus_hotspot_name or "").strip() or oneplus_inputs.get("hotspot_name", ""),
        oneplus_hotspot_password=str(args.oneplus_hotspot_password or "").strip()
        or oneplus_inputs.get("hotspot_password", ""),
        oneplus_hotspot_only=bool(args.oneplus_hotspot_only),
    )
    runtime_summary = _load_runtime_e2e_summary(state_dir)

    report = {
        "id": f"sequential-abcd-audit-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": _now(),
        "domain": args.domain,
        "origin_ip": args.origin_ip,
        "ok": bool(stage_a.get("ok")) and bool(stage_b.get("ok")) and bool(stage_c.get("ok")) and bool(stage_d.get("ok")),
        "stage_a": stage_a,
        "stage_b": stage_b,
        "stage_c": stage_c,
        "stage_d": stage_d,
        "runtime_e2e_summary": runtime_summary,
        "sequence_policy": {
            "order": ["A_public_stability", "B_route_and_page_verification", "C_search_continuity", "D_device_sovereignty"],
            "executed_sequentially": True,
        },
    }

    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(_render_md(report), encoding="utf-8")
    with history_jsonl.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "id": report.get("id"),
                    "generated_at": report.get("generated_at"),
                    "ok": report.get("ok"),
                    "stage_ok": {
                        "a": bool(stage_a.get("ok")),
                        "b": bool(stage_b.get("ok")),
                        "c": bool(stage_c.get("ok")),
                        "d": bool(stage_d.get("ok")),
                    },
                    "blockers": {
                        "a": stage_a.get("blockers", []),
                        "b": stage_b.get("blockers", []),
                        "c": stage_c.get("blockers", []),
                        "d": stage_d.get("blockers", []),
                    },
                },
                ensure_ascii=True,
            )
            + "\n"
        )

    print(json.dumps(report, indent=2))
    return 0 if bool(report.get("ok", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
