#!/usr/bin/env python3
"""
runtime-transport-triage.py
---------------------------
Collects concrete transport diagnostics for known live nodes:
- DNS resolution from this executor
- TCP reachability for common ports
- TLS handshake outcomes (server certificate metadata when available)
- Minimal HTTP probe outcomes

This is diagnostics-only and does not mutate remote systems.
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

DEFAULT_NODES: list[dict[str, str]] = [
    {"name": "chimaera", "ip": "5.78.184.2"},
    {"name": "yggdrasil", "ip": "128.140.45.22"},
    {"name": "enterprise", "ip": "91.99.224.166"},
    {"name": "prometheus", "ip": "46.62.202.166"},
    {"name": "galactica", "ip": "178.104.31.46"},
]

DEFAULT_HTTP_PATHS = (
    "/api/sovereign/ops/control-plane/greenboard",
    "/api/s25/full-stack/status",
)

TLS_SELF_SIGNED_PATTERNS = (
    "self-signed certificate",
    "certificate verify failed",
)


def _tls_cert_state(tls_probe: dict[str, Any]) -> str:
    if bool(tls_probe.get("ok", False)):
        return "trusted"
    err = str(tls_probe.get("error", "")).strip().lower()
    if any(fragment in err for fragment in TLS_SELF_SIGNED_PATTERNS):
        return "self_signed_or_untrusted"
    return "unknown"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def _resolve_ips(host: str) -> list[str]:
    out: list[str] = []
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return out
    for info in infos:
        try:
            ip = str(info[4][0]).strip()
        except Exception:
            continue
        if ip and ip not in out:
            out.append(ip)
    return out


def _tcp_probe(host: str, port: int, timeout_seconds: float) -> dict[str, Any]:
    started = time.time()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_seconds):
            elapsed_ms = int((time.time() - started) * 1000)
            return {"ok": True, "elapsed_ms": elapsed_ms}
    except Exception as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return {"ok": False, "elapsed_ms": elapsed_ms, "error": str(exc)}


def _tls_probe(host: str, port: int, timeout_seconds: float) -> dict[str, Any]:
    started = time.time()
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_seconds) as raw:
            with context.wrap_socket(raw, server_hostname=host) as wrapped:
                cert = wrapped.getpeercert() or {}
                elapsed_ms = int((time.time() - started) * 1000)
                return {
                    "ok": True,
                    "elapsed_ms": elapsed_ms,
                    "version": wrapped.version(),
                    "cipher": wrapped.cipher()[0] if wrapped.cipher() else None,
                    "cert_subject": cert.get("subject"),
                    "cert_issuer": cert.get("issuer"),
                    "cert_notAfter": cert.get("notAfter"),
                }
    except Exception as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return {"ok": False, "elapsed_ms": elapsed_ms, "error": str(exc)}


def _http_probe(url: str, timeout_seconds: float, insecure_tls: bool = False) -> dict[str, Any]:
    started = time.time()
    req = urllib_request.Request(
        url,
        method="GET",
        headers={"User-Agent": "AGR-Transport-Triage/1.0", "Accept": "application/json, text/plain, */*"},
    )
    try:
        context = None
        if url.startswith("https://") and insecure_tls:
            context = ssl._create_unverified_context()  # noqa: SLF001 - intentional diagnostic fallback
        with urllib_request.urlopen(req, timeout=timeout_seconds, context=context) as resp:
            elapsed_ms = int((time.time() - started) * 1000)
            return {
                "ok": True,
                "elapsed_ms": elapsed_ms,
                "status": int(getattr(resp, "status", 200)),
                "content_type": str(resp.headers.get("Content-Type", "")),
                "insecure_tls": bool(insecure_tls),
            }
    except urllib_error.HTTPError as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "ok": False,
            "elapsed_ms": elapsed_ms,
            "status": int(exc.code),
            "error": f"http_{exc.code}",
            "insecure_tls": bool(insecure_tls),
        }
    except Exception as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "ok": False,
            "elapsed_ms": elapsed_ms,
            "error": str(exc),
            "insecure_tls": bool(insecure_tls),
        }


def _node_triage(node: dict[str, str], timeout_seconds: float) -> dict[str, Any]:
    name = str(node.get("name", "unknown"))
    ip = str(node.get("ip", "")).strip()
    resolved = _resolve_ips(ip)
    tcp_443 = _tcp_probe(ip, 443, timeout_seconds)
    tcp_5000 = _tcp_probe(ip, 5000, timeout_seconds)
    tls_443 = _tls_probe(ip, 443, timeout_seconds) if tcp_443.get("ok") else {"ok": False, "error": "tcp_443_unreachable"}

    http_rows: list[dict[str, Any]] = []
    for path in DEFAULT_HTTP_PATHS:
        path_norm = "/" + str(path or "/").lstrip("/")
        https_url = f"https://{ip}{path_norm}"
        http_url = f"http://{ip}:5000{path_norm}"
        http_rows.append({"url": https_url, **_http_probe(https_url, timeout_seconds, insecure_tls=False)})
        http_rows.append({"url": https_url, **_http_probe(https_url, timeout_seconds, insecure_tls=True)})
        http_rows.append({"url": http_url, **_http_probe(http_url, timeout_seconds, insecure_tls=False)})

    http_ok = sum(1 for row in http_rows if bool(row.get("ok")))
    tls_ok = bool(tls_443.get("ok"))
    tcp_ok = bool(tcp_443.get("ok") or tcp_5000.get("ok"))
    tls_error_text = str(tls_443.get("error", "")).strip().lower()
    tls_trust_chain_valid = tls_ok
    tls_self_signed_detected = any(fragment in tls_error_text for fragment in TLS_SELF_SIGNED_PATTERNS)
    if tls_self_signed_detected:
        tls_trust_chain_valid = False
    cert_state = _tls_cert_state(tls_443 if isinstance(tls_443, dict) else {})
    health = "reachable" if tcp_ok else "unreachable"
    if tcp_ok and not tls_ok and http_ok == 0:
        health = "tcp_only"
    if tcp_ok and (tls_ok or http_ok > 0):
        health = "service_responsive"
    return {
        "node": name,
        "ip": ip,
        "resolved_ips": resolved,
        "probes": {
            "tcp_443": tcp_443,
            "tcp_5000": tcp_5000,
            "tls_443": tls_443,
            "http": http_rows,
        },
        "summary": {
            "health": health,
            "tcp_reachable": tcp_ok,
            "tls_healthy": tls_ok,
            "tls_trust_chain_valid": tls_trust_chain_valid,
            "tls_self_signed_detected": tls_self_signed_detected,
            "tls_cert_validation": {
                "state": cert_state,
                "error": tls_443.get("error") if isinstance(tls_443, dict) else None,
            },
            "http_probe_successes": http_ok,
            "http_probe_total": len(http_rows),
        },
    }


def build_report(timeout_seconds: float = 4.0) -> dict[str, Any]:
    rows = [_node_triage(node, timeout_seconds=timeout_seconds) for node in DEFAULT_NODES]
    reachable = sum(1 for row in rows if bool((row.get("summary") or {}).get("tcp_reachable")))
    service_responsive = sum(1 for row in rows if str((row.get("summary") or {}).get("health")) == "service_responsive")
    tls_trust_chain_ok = sum(1 for row in rows if bool((row.get("summary") or {}).get("tls_trust_chain_valid")))
    tls_self_signed_nodes = [
        str(row.get("node", "unknown"))
        for row in rows
        if bool((row.get("summary") or {}).get("tls_self_signed_detected"))
    ]
    report = {
        "timestamp": _now(),
        "timeout_seconds": float(timeout_seconds),
        "nodes": rows,
        "summary": {
            "nodes_total": len(rows),
            "nodes_tcp_reachable": reachable,
            "nodes_service_responsive": service_responsive,
            "strict_all_service_responsive": bool(rows) and service_responsive == len(rows),
            "nodes_tls_trust_chain_valid": tls_trust_chain_ok,
            "strict_all_tls_trust_chain_valid": bool(rows) and tls_trust_chain_ok == len(rows),
            "tls_self_signed_nodes": tls_self_signed_nodes,
        },
    }
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Collect node-level transport triage diagnostics.")
    p.add_argument(
        "--latest-out",
        default="/workspace/aurora_server/state/runtime_transport_triage.latest.json",
        help="Output latest triage JSON path",
    )
    p.add_argument(
        "--history-out",
        default="/workspace/aurora_server/state/runtime_transport_triage.history.jsonl",
        help="Output triage history JSONL path",
    )
    p.add_argument("--timeout-seconds", type=float, default=20.0, help="Per-probe timeout")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    latest_out = Path(str(args.latest_out))
    history_out = Path(str(args.history_out))
    timeout_seconds = max(1.0, min(float(args.timeout_seconds), 20.0))
    report = build_report(timeout_seconds=timeout_seconds)
    _write_json(latest_out, report)
    _append_jsonl(history_out, report)
    print(json.dumps(report, indent=2))
    summary = report.get("summary", {})
    return 0 if bool(summary.get("strict_all_service_responsive", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
