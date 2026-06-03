#!/usr/bin/env python3
"""
runtime-e2e-live-nodes.py
-------------------------
Refreshes runtime_e2e_live_nodes artifacts by probing core sovereign endpoints
across configured live nodes.

This script is intentionally transport-aware:
- it can try multiple transport candidates per check (e.g. https:443 then http:5000)
- it records all failed attempts for diagnostics
- it writes artifacts even when checks fail (fail-closed scoring)
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_base() -> Path:
    env_base = os.environ.get("AGR_BASE_DIR", "").strip()
    if env_base:
        p = Path(env_base)
        if p.exists():
            return p
    opt_base = Path("/opt/agr/aurora_server")
    if opt_base.exists():
        return opt_base
    return Path("/workspace/aurora_server")


BASE_DIR = _resolve_base()
STATE_DIR = Path("/opt/agr/state")
if not STATE_DIR.exists():
    STATE_DIR = BASE_DIR / "state"

LATEST_DEFAULT = STATE_DIR / "runtime_e2e_live_nodes.latest.json"
HISTORY_DEFAULT = STATE_DIR / "runtime_e2e_live_nodes.history.jsonl"

DEFAULT_NODES: list[dict[str, str]] = [
    {"node": "chimaera", "ip": "5.78.184.2"},
    {"node": "yggdrasil", "ip": "128.140.45.22"},
    {"node": "enterprise", "ip": "91.99.224.166"},
    {"node": "prometheus", "ip": "46.62.202.166"},
    {"node": "galactica", "ip": "178.104.31.46"},
]

DEFAULT_CHECKS: list[dict[str, Any]] = [
    {"method": "GET", "path": "/api/sovereign/ops/verification-governor/status"},
    {"method": "GET", "path": "/api/sovereign/ops/control-plane/invariants"},
    {"method": "POST", "path": "/api/sovereign/ops/control-plane/invariants/check", "payload": {"run_snapshot": False}},
    {"method": "GET", "path": "/api/s25/full-stack/status"},
]

PUBLIC_TOWER_CHECKS: list[dict[str, Any]] = [
    {"method": "GET", "path": "/health"},
    {"method": "GET", "path": "/api/awards/registry"},
]

DEFAULT_NODE_CHECK_PROFILE_OVERRIDES: dict[str, str] = {
    # chimaera currently serves tower/public routes while sovereign ops routes are
    # intentionally hosted on other nodes in this environment.
    "chimaera": "public_tower",
}

SLOW_PATH_TIMEOUT_OVERRIDES: dict[str, int] = {
    "/api/sovereign/ops/control-plane/invariants": 180,
    "/api/sovereign/ops/control-plane/invariants/check": 180,
    "/api/sovereign/release/go-live/check": 75,
}

RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}
RETRYABLE_ERROR_FRAGMENTS = (
    "timed out",
    "connection reset",
    "connection aborted",
    "temporary failure",
    "remote end closed",
)


def _check_profiles() -> dict[str, list[dict[str, Any]]]:
    return {
        "full_sovereign": list(DEFAULT_CHECKS),
        "public_tower": list(PUBLIC_TOWER_CHECKS),
    }


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def _parse_nodes(raw: str) -> list[dict[str, str]]:
    text = str(raw or "").strip()
    if not text:
        return list(DEFAULT_NODES)
    try:
        payload = json.loads(text)
    except Exception:
        return list(DEFAULT_NODES)
    if not isinstance(payload, list):
        return list(DEFAULT_NODES)
    rows: list[dict[str, str]] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        node = str(row.get("node") or row.get("name") or "").strip()
        ip = str(row.get("ip") or row.get("host") or "").strip()
        if node and ip:
            rows.append({"node": node, "ip": ip})
    return rows or list(DEFAULT_NODES)


def _transport_candidates(include_https_insecure_fallback: bool, include_http_80: bool) -> list[dict[str, Any]]:
    out = [
        {"scheme": "https", "port": 443, "insecure_tls": False},
    ]
    if include_https_insecure_fallback:
        out.append({"scheme": "https", "port": 443, "insecure_tls": True})
    out.append({"scheme": "http", "port": 5000, "insecure_tls": False})
    if include_http_80:
        out.append({"scheme": "http", "port": 80, "insecure_tls": False})
    return out


def _parse_node_profile_overrides(raw: str) -> dict[str, str]:
    out = dict(DEFAULT_NODE_CHECK_PROFILE_OVERRIDES)
    valid_profiles = set(_check_profiles().keys())
    text = str(raw or "").strip()
    if not text:
        return out
    try:
        payload = json.loads(text)
    except Exception:
        return out
    if not isinstance(payload, dict):
        return out
    for k, v in payload.items():
        node = str(k or "").strip().lower()
        profile = str(v or "").strip()
        if not node:
            continue
        if profile not in valid_profiles:
            continue
        out[node] = profile
    return out


def _checks_for_node(
    node: dict[str, str],
    node_profile_overrides: dict[str, str],
    check_profiles: dict[str, list[dict[str, Any]]],
) -> tuple[str, list[dict[str, Any]]]:
    node_name = str(node.get("node", "")).strip().lower()
    profile = node_profile_overrides.get(node_name, "full_sovereign")
    checks = check_profiles.get(profile, DEFAULT_CHECKS)
    return profile, list(checks)


def _url_for(ip: str, path: str, candidate: dict[str, Any]) -> str:
    scheme = str(candidate.get("scheme", "https")).strip().lower() or "https"
    port = int(candidate.get("port", 443) or 443)
    if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
        return f"{scheme}://{ip}{path}"
    return f"{scheme}://{ip}:{port}{path}"


def _decode_body(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="ignore")
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text[:12000]}


def _timeout_for_check(check: dict[str, Any], default_timeout_seconds: int) -> int:
    path = "/" + str(check.get("path", "/")).lstrip("/")
    override = int(SLOW_PATH_TIMEOUT_OVERRIDES.get(path, 0) or 0)
    return max(int(default_timeout_seconds), override) if override > 0 else int(default_timeout_seconds)


def _http_call(
    *,
    url: str,
    method: str,
    payload: dict[str, Any] | None,
    timeout_seconds: int,
    headers: dict[str, str],
    insecure_tls: bool,
) -> dict[str, Any]:
    body = None
    if payload is not None and method in {"POST", "PUT", "PATCH", "DELETE"}:
        body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(url, data=body, method=method, headers=headers)
    context = ssl._create_unverified_context() if url.startswith("https://") and insecure_tls else None
    try:
        with urllib_request.urlopen(req, timeout=timeout_seconds, context=context) as resp:  # type: ignore[arg-type]
            parsed = _decode_body(resp.read())
            status = int(getattr(resp, "status", 200) or 200)
            ok = 200 <= status < 300 and not (isinstance(parsed, dict) and parsed.get("ok") is False)
            return {"ok": ok, "status": status, "body": parsed}
    except urllib_error.HTTPError as exc:
        parsed = _decode_body(exc.read() or b"")
        return {"ok": False, "status": int(exc.code), "body": parsed}
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc


def _probe_check(
    *,
    node: dict[str, str],
    check: dict[str, Any],
    candidates: list[dict[str, Any]],
    timeout_seconds: int,
    base_headers: dict[str, str],
) -> dict[str, Any]:
    method = str(check.get("method", "GET")).strip().upper() or "GET"
    path = str(check.get("path", "/")).strip() or "/"
    payload = check.get("payload") if isinstance(check.get("payload"), dict) else None
    attempts: list[dict[str, Any]] = []
    last_error = "transport_unreachable"
    last_failure: dict[str, Any] | None = None
    max_attempts_per_candidate = 2
    retry_delay_seconds = 0.75
    for cand in candidates:
        url = _url_for(node.get("ip", ""), path, cand)
        headers = dict(base_headers)
        for attempt_idx in range(max_attempts_per_candidate):
            try:
                out = _http_call(
                    url=url,
                    method=method,
                    payload=payload,
                    timeout_seconds=timeout_seconds,
                    headers=headers,
                    insecure_tls=bool(cand.get("insecure_tls", False)),
                )
                status = out.get("status")
                ok = bool(out.get("ok", False))
                attempts.append(
                    {
                        "url": url,
                        "scheme": cand.get("scheme"),
                        "port": int(cand.get("port", 0) or 0),
                        "insecure_tls": bool(cand.get("insecure_tls", False)),
                        "status": status,
                        "ok": ok,
                        "attempt_index": attempt_idx + 1,
                        "attempts_for_candidate": max_attempts_per_candidate,
                    }
                )
                if ok:
                    return {
                        "method": method,
                        "path": path,
                        "status": status,
                        "ok": True,
                        "body": out.get("body"),
                        "transport": {
                            "url": url,
                            "scheme": cand.get("scheme"),
                            "port": int(cand.get("port", 0) or 0),
                            "insecure_tls": bool(cand.get("insecure_tls", False)),
                        },
                        "attempts": attempts,
                    }
                body = out.get("body")
                body_error = str((body or {}).get("error", "")).strip() if isinstance(body, dict) else ""
                if body_error:
                    last_error = body_error
                elif status is not None:
                    last_error = f"http_{int(status)}"
                else:
                    last_error = "http_failure"
                last_failure = {
                    "status": status,
                    "body": body,
                    "transport": {
                        "url": url,
                        "scheme": cand.get("scheme"),
                        "port": int(cand.get("port", 0) or 0),
                        "insecure_tls": bool(cand.get("insecure_tls", False)),
                    },
                }
                retryable = isinstance(status, int) and int(status) in RETRYABLE_HTTP_STATUSES
                if retryable and attempt_idx < (max_attempts_per_candidate - 1):
                    time.sleep(retry_delay_seconds)
                    continue
                break
            except Exception as exc:
                last_error = str(exc)
                attempts.append(
                    {
                        "url": url,
                        "scheme": cand.get("scheme"),
                        "port": int(cand.get("port", 0) or 0),
                        "insecure_tls": bool(cand.get("insecure_tls", False)),
                        "error": last_error,
                        "attempt_index": attempt_idx + 1,
                        "attempts_for_candidate": max_attempts_per_candidate,
                    }
                )
                retryable_error = any(fragment in last_error.lower() for fragment in RETRYABLE_ERROR_FRAGMENTS)
                if retryable_error and attempt_idx < (max_attempts_per_candidate - 1):
                    time.sleep(retry_delay_seconds)
                    continue
                break

    if last_failure is not None:
        return {
            "method": method,
            "path": path,
            "status": last_failure.get("status"),
            "ok": False,
            "body": last_failure.get("body") if last_failure.get("body") is not None else {"error": last_error},
            "transport": last_failure.get("transport"),
            "attempts": attempts,
        }

    return {
        "method": method,
        "path": path,
        "status": None,
        "ok": False,
        "body": {"error": last_error},
        "transport": None,
        "attempts": attempts,
    }


def run(
    *,
    timeout_seconds: int,
    include_https_insecure_fallback: bool,
    include_http_80: bool,
    output_latest: Path,
    output_history: Path,
) -> dict[str, Any]:
    nodes = _parse_nodes(os.environ.get("AGR_LIVE_E2E_NODES_JSON", ""))
    check_profiles = _check_profiles()
    node_profile_overrides = _parse_node_profile_overrides(os.environ.get("AGR_LIVE_E2E_NODE_CHECK_PROFILES_JSON", ""))
    token = str(os.environ.get("AGR_INTERNAL_API_TOKEN", "")).strip()
    headers = {
        "User-Agent": "AGR-Live-E2E-Runner/1.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }
    if token:
        headers["X-AGR-Internal-Token"] = token

    candidates = _transport_candidates(
        include_https_insecure_fallback=include_https_insecure_fallback,
        include_http_80=include_http_80,
    )
    node_rows: list[dict[str, Any]] = []
    total = 0
    ok_count = 0
    profile_node_counts: dict[str, int] = {}
    profile_total_checks: dict[str, int] = {}
    for node in nodes:
        profile, checks = _checks_for_node(node, node_profile_overrides, check_profiles)
        profile_node_counts[profile] = int(profile_node_counts.get(profile, 0)) + 1
        profile_total_checks[profile] = int(profile_total_checks.get(profile, 0)) + len(checks)
        row_results: list[dict[str, Any]] = []
        for check in checks:
            total += 1
            timeout_for_check = _timeout_for_check(check, timeout_seconds)
            result = _probe_check(
                node=node,
                check=check,
                candidates=candidates,
                timeout_seconds=timeout_for_check,
                base_headers=headers,
            )
            result["timeout_seconds"] = timeout_for_check
            if bool(result.get("ok", False)):
                ok_count += 1
            row_results.append(result)
        node_rows.append(
            {
                "node": node.get("node"),
                "ip": node.get("ip"),
                "check_profile": profile,
                "results": row_results,
            }
        )

    report = {
        "timestamp": _now(),
        "results": node_rows,
        "summary": {
            "nodes_total": len(nodes),
            "nodes": [str((row or {}).get("node", "")).strip() for row in nodes],
            "total_checks": total,
            "ok_checks": ok_count,
            "failed_checks": max(0, total - ok_count),
            "strict_all_pass": bool(total) and ok_count == total,
            "profile_node_counts": profile_node_counts,
            "profile_total_checks": profile_total_checks,
        },
        "transport_candidates": candidates,
        "check_profiles": {k: [dict(row) for row in v] for k, v in check_profiles.items()},
        "node_check_profile_overrides": node_profile_overrides,
    }
    output_latest.parent.mkdir(parents=True, exist_ok=True)
    output_latest.write_text(json.dumps(report, indent=2))
    _append_jsonl(output_history, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live node runtime E2E checks and write artifacts.")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument(
        "--https-insecure-fallback",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Try https with unverified TLS context after strict TLS failure.",
    )
    parser.add_argument(
        "--include-http-80",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Also probe http://<ip>:80 as a final transport fallback.",
    )
    parser.add_argument("--latest-out", default=str(LATEST_DEFAULT))
    parser.add_argument("--history-out", default=str(HISTORY_DEFAULT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = run(
        timeout_seconds=max(1, int(args.timeout_seconds or 4)),
        include_https_insecure_fallback=bool(args.https_insecure_fallback),
        include_http_80=bool(args.include_http_80),
        output_latest=Path(str(args.latest_out)),
        output_history=Path(str(args.history_out)),
    )
    print(json.dumps(report, indent=2))
    strict = bool((report.get("summary", {}) or {}).get("strict_all_pass", False))
    return 0 if strict else 2


if __name__ == "__main__":
    raise SystemExit(main())
