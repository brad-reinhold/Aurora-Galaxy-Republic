#!/usr/bin/env python3
"""
wave2-parity-evidence.py
------------------------
Builds a conservative Wave-2 live parity evidence artifact from existing
runtime E2E snapshots, distinguishing true endpoint failures from transport
errors in the latest captured run.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

LIVE_E2E = STATE_DIR / "runtime_e2e_live_nodes.latest.json"
PARITY_LATEST = STATE_DIR / "wave2_live_parity.latest.json"
PARITY_HISTORY = STATE_DIR / "wave2_live_parity.history.jsonl"
STALE_ARTIFACT_THRESHOLD_SECONDS = 3600


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def _error_text(entry: dict[str, Any]) -> str:
    body = entry.get("body") if isinstance(entry, dict) else {}
    if not isinstance(body, dict):
        return ""
    err = str(body.get("error", "")).strip().lower()
    return err


def _transport_signature(err: str) -> str:
    txt = str(err or "").strip().lower()
    if not txt:
        return ""
    signatures = (
        ("connection reset by peer", "connection_reset_by_peer"),
        ("connection refused", "connection_refused"),
        ("timed out", "timeout"),
        ("timeout", "timeout"),
        ("network is unreachable", "network_unreachable"),
        ("temporary failure in name resolution", "dns_resolution_failure"),
        ("name or service not known", "dns_resolution_failure"),
        ("remote end closed connection", "remote_closed_connection"),
    )
    for needle, sig in signatures:
        if needle in txt:
            return sig
    return ""


def _is_transport_error(entry: dict[str, Any]) -> bool:
    err = _error_text(entry)
    if not err:
        return False
    transport_signatures = (
        "connection reset by peer",
        "connection refused",
        "timed out",
        "timeout",
        "network is unreachable",
        "temporary failure in name resolution",
        "name or service not known",
        "remote end closed connection",
    )
    return any(sig in err for sig in transport_signatures)


def _is_guardrail_denial(entry: dict[str, Any]) -> bool:
    if not isinstance(entry, dict):
        return False
    body = entry.get("body")
    if not isinstance(body, dict):
        return False
    if str(body.get("error", "")).strip():
        return False

    blockers = body.get("blockers")
    release_blockers = body.get("release_blockers")
    if isinstance(release_blockers, list):
        return True
    if (
        body.get("ready_for_go_live_minimum") is False
        and isinstance(release_blockers, list)
    ):
        return True
    if (
        "overall" in body
        and isinstance(blockers, list)
        and isinstance(body.get("signals"), dict)
    ):
        return True
    if (
        str(body.get("result", "")).strip().upper() == "FAIL"
        and isinstance(blockers, list)
        and isinstance(body.get("checks"), dict)
    ):
        return True
    return False


def _tls_trust_diagnostics(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        rows = []
    nodes_total = 0
    nodes_with_tls_trust_issue = 0
    nodes_with_insecure_tls_success = 0
    nodes_with_strict_tls_success = 0
    verify_failed_hits = 0
    for node in rows:
        checks = node.get("results", []) if isinstance(node, dict) else []
        if not isinstance(checks, list) or not checks:
            continue
        nodes_total += 1
        trust_issue = False
        insecure_success = False
        strict_success = False
        for entry in checks:
            entry_error_text = _error_text(entry)
            if "certificate verify failed" in entry_error_text or "self-signed certificate" in entry_error_text:
                trust_issue = True
                verify_failed_hits += 1
            attempts = entry.get("attempts", []) if isinstance(entry, dict) else []
            if not isinstance(attempts, list):
                continue
            for attempt in attempts:
                if not isinstance(attempt, dict):
                    continue
                is_insecure = bool(attempt.get("insecure_tls", False))
                if bool(attempt.get("ok", False)) and not is_insecure:
                    strict_success = True
                if bool(attempt.get("ok", False)) and is_insecure:
                    insecure_success = True
                err_txt = str(attempt.get("error", "") or "").strip().lower()
                if "certificate verify failed" in err_txt or "self-signed certificate" in err_txt:
                    trust_issue = True
                    verify_failed_hits += 1
        if trust_issue:
            nodes_with_tls_trust_issue += 1
        if insecure_success:
            nodes_with_insecure_tls_success += 1
        if strict_success:
            nodes_with_strict_tls_success += 1
    all_nodes_have_tls_trust_issues = nodes_total > 0 and nodes_with_tls_trust_issue == nodes_total
    return {
        "nodes_total": nodes_total,
        "nodes_with_tls_trust_issue": nodes_with_tls_trust_issue,
        "nodes_with_insecure_tls_success": nodes_with_insecure_tls_success,
        "nodes_with_strict_tls_success": nodes_with_strict_tls_success,
        "verify_failed_hits": verify_failed_hits,
        "has_trust_chain_warnings": bool(verify_failed_hits > 0 or nodes_with_tls_trust_issue > 0),
        "all_nodes_have_tls_trust_issues": all_nodes_have_tls_trust_issues,
        "production_trust_ready": nodes_total > 0 and nodes_with_strict_tls_success == nodes_total and nodes_with_tls_trust_issue == 0,
    }


def _counter_rows(counter: Counter[str], limit: int = 20) -> list[dict[str, Any]]:
    rows = []
    for name, count in counter.most_common(max(1, limit)):
        rows.append({"name": name, "count": int(count)})
    return rows


def _artifact_age_seconds(ts: str) -> int | None:
    raw = str(ts or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
    except Exception:
        return None


def _build_remediation_targets(
    *,
    total: int,
    endpoint_failures: int,
    transport_errors: int,
    guardrail_denials: int,
    per_node: list[dict[str, Any]],
    per_check_surface: list[dict[str, Any]],
    transport_signatures: Counter[str],
    artifact_age_seconds: int | None,
    tls_trust_diagnostics: dict[str, Any],
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    active_nodes = [n for n in per_node if int(n.get("total_checks", 0)) > 0]
    all_nodes_transport_only = bool(active_nodes) and all(
        int(n.get("endpoint_failures", 0)) == 0 and int(n.get("transport_errors", 0)) > 0 for n in active_nodes
    )
    all_nodes_fully_unreachable = bool(active_nodes) and all(
        int(n.get("transport_errors", 0)) == int(n.get("total_checks", 0)) for n in active_nodes
    )

    if artifact_age_seconds is not None and artifact_age_seconds > STALE_ARTIFACT_THRESHOLD_SECONDS:
        targets.append(
            {
                "priority": "high",
                "category": "freshness",
                "scope": "evidence",
                "reason": "live_e2e_artifact_stale",
                "evidence": {
                    "artifact_age_seconds": artifact_age_seconds,
                    "stale_threshold_seconds": STALE_ARTIFACT_THRESHOLD_SECONDS,
                },
                "suggested_actions": [
                    "Re-run live node E2E sweep to refresh evidence before endpoint remediation.",
                    "Verify verification governor scheduler cadence and artifact write path.",
                ],
            }
        )

    if transport_errors > 0 and all_nodes_fully_unreachable:
        targets.append(
            {
                "priority": "critical",
                "category": "transport",
                "scope": "mesh",
                "reason": "all_nodes_fully_unreachable",
                "evidence": {"transport_errors": transport_errors, "total_checks": total},
                "suggested_actions": [
                    "Validate ingress listener health and TLS termination on each node.",
                    "Validate inter-node overlay connectivity and firewall policy alignment.",
                ],
            }
        )

    if transport_errors > 0 and transport_signatures:
        dominant_sig, dominant_count = transport_signatures.most_common(1)[0]
        targets.append(
            {
                "priority": "high",
                "category": "transport",
                "scope": "cluster",
                "reason": "dominant_transport_signature",
                "evidence": {
                    "signature": dominant_sig,
                    "count": int(dominant_count),
                    "transport_errors": transport_errors,
                },
                "suggested_actions": [
                    "Correlate service logs for the dominant signature across all affected nodes.",
                    "Apply bounded listener/process restart only after config/health verification.",
                ],
            }
        )

    if isinstance(tls_trust_diagnostics, dict) and bool(tls_trust_diagnostics.get("all_nodes_have_tls_trust_issues", False)):
        targets.append(
            {
                "priority": "high",
                "category": "tls_trust",
                "scope": "cluster",
                "reason": "tls_certificate_trust_unverified",
                "evidence": {
                    "nodes_with_tls_trust_issue": int(tls_trust_diagnostics.get("nodes_with_tls_trust_issue", 0) or 0),
                    "nodes_total": int(tls_trust_diagnostics.get("nodes_total", 0) or 0),
                    "nodes_with_insecure_tls_success": int(
                        tls_trust_diagnostics.get("nodes_with_insecure_tls_success", 0) or 0
                    ),
                    "nodes_with_strict_tls_success": int(
                        tls_trust_diagnostics.get("nodes_with_strict_tls_success", 0) or 0
                    ),
                },
                "suggested_actions": [
                    "Install trusted TLS certificates for public ingress and validate full chain presentation.",
                    "Require strict TLS success on critical probes before production promotion.",
                ],
            }
        )

    if transport_errors > 0 and endpoint_failures == 0 and all_nodes_transport_only:
        targets.append(
            {
                "priority": "high",
                "category": "triage",
                "scope": "workflow",
                "reason": "transport_only_blockage",
                "evidence": {
                    "transport_errors": transport_errors,
                    "endpoint_failures": endpoint_failures,
                },
                "suggested_actions": [
                    "Prioritize transport restoration first; defer endpoint-level debugging.",
                    "After transport recovers, re-run parity evidence to detect true endpoint regressions.",
                ],
            }
        )

    guardrail_surfaces = [row for row in per_check_surface if int(row.get("guardrail_denials", 0)) > 0]
    if guardrail_denials > 0 and endpoint_failures == 0:
        top_guardrail = guardrail_surfaces[0] if guardrail_surfaces else {}
        targets.append(
            {
                "priority": "medium",
                "category": "guardrail",
                "scope": "policy_state",
                "reason": "guardrail_denials_present",
                "evidence": {
                    "guardrail_denials": guardrail_denials,
                    "top_method": top_guardrail.get("method"),
                    "top_path": top_guardrail.get("path"),
                    "top_guardrail_denials": int(top_guardrail.get("guardrail_denials", 0) or 0),
                },
                "suggested_actions": [
                    "Inspect control-plane/governor blockers and clear policy gates before rerunning parity.",
                    "Treat these responses as fail-closed readiness denials, not transport or endpoint handler regressions.",
                ],
            }
        )

    failing_surfaces = [row for row in per_check_surface if int(row.get("endpoint_failures", 0)) > 0]
    if failing_surfaces:
        top = failing_surfaces[0]
        targets.append(
            {
                "priority": "medium",
                "category": "endpoint",
                "scope": "api_surface",
                "reason": "endpoint_regressions_detected",
                "evidence": {
                    "top_method": top.get("method"),
                    "top_path": top.get("path"),
                    "endpoint_failures": int(top.get("endpoint_failures", 0)),
                },
                "suggested_actions": [
                    "Inspect endpoint handler logs and recent deploy diff for top failing surface.",
                    "Run targeted endpoint regression tests before broad rerun.",
                ],
            }
        )
    return targets


def build_report_from_payload(payload: dict[str, Any], source_artifact: str | None = None) -> dict[str, Any]:
    nodes = payload.get("results", []) if isinstance(payload.get("results"), list) else []

    total = 0
    endpoint_failures = 0
    transport_errors = 0
    guardrail_denials = 0
    pass_count = 0
    per_node: list[dict[str, Any]] = []
    global_errors: Counter[str] = Counter()
    transport_signatures: Counter[str] = Counter()
    surface_map: dict[tuple[str, str], dict[str, Any]] = {}

    for node in nodes:
        node_name = str((node or {}).get("node", "unknown"))
        checks = node.get("results", []) if isinstance(node, dict) and isinstance(node.get("results"), list) else []
        node_total = 0
        node_pass = 0
        node_endpoint_failures = 0
        node_transport_errors = 0
        node_guardrail_denials = 0
        node_errors: Counter[str] = Counter()
        for entry in checks:
            if not isinstance(entry, dict):
                continue
            method = str(entry.get("method", "GET")).strip().upper() or "GET"
            path = str(entry.get("path", "/")).strip() or "/"
            surface = surface_map.get((method, path))
            if not surface:
                surface = {
                    "method": method,
                    "path": path,
                    "total_checks": 0,
                    "pass_count": 0,
                    "endpoint_failures": 0,
                    "transport_errors": 0,
                    "guardrail_denials": 0,
                    "failed_nodes": [],
                }
                surface_map[(method, path)] = surface
            surface["total_checks"] = int(surface.get("total_checks", 0)) + 1
            node_total += 1
            total += 1
            if bool(entry.get("ok", False)):
                node_pass += 1
                pass_count += 1
                surface["pass_count"] = int(surface.get("pass_count", 0)) + 1
                continue
            err = _error_text(entry)
            if err:
                node_errors[err] += 1
                global_errors[err] += 1
            if node_name not in surface["failed_nodes"]:
                surface["failed_nodes"].append(node_name)
            if _is_transport_error(entry):
                node_transport_errors += 1
                transport_errors += 1
                surface["transport_errors"] = int(surface.get("transport_errors", 0)) + 1
                sig = _transport_signature(err)
                if sig:
                    transport_signatures[sig] += 1
            elif _is_guardrail_denial(entry):
                node_guardrail_denials += 1
                guardrail_denials += 1
                surface["guardrail_denials"] = int(surface.get("guardrail_denials", 0)) + 1
            else:
                node_endpoint_failures += 1
                endpoint_failures += 1
                surface["endpoint_failures"] = int(surface.get("endpoint_failures", 0)) + 1
        per_node.append(
            {
                "node": node_name,
                "total_checks": node_total,
                "pass_count": node_pass,
                "endpoint_failures": node_endpoint_failures,
                "transport_errors": node_transport_errors,
                "guardrail_denials": node_guardrail_denials,
                "transport_only": node_endpoint_failures == 0 and node_transport_errors > 0,
                "fully_unreachable": node_total > 0 and node_transport_errors == node_total,
                "top_errors": _counter_rows(node_errors, limit=5),
            }
        )

    strict_all_pass = bool(total) and pass_count == total
    if strict_all_pass:
        parity_status = "pass"
    elif endpoint_failures == 0 and transport_errors > 0 and guardrail_denials == 0:
        parity_status = "transport_blocked"
    elif endpoint_failures == 0 and transport_errors == 0 and guardrail_denials > 0:
        parity_status = "guardrail_blocked"
    elif endpoint_failures == 0 and transport_errors > 0 and guardrail_denials > 0:
        parity_status = "transport_and_guardrail_blocked"
    else:
        parity_status = "failing"
    live_ts = str(payload.get("timestamp", "")).strip() if isinstance(payload, dict) else ""
    age_seconds = _artifact_age_seconds(live_ts)
    per_check_surface = sorted(
        list(surface_map.values()),
        key=lambda row: (
            -int(row.get("transport_errors", 0)),
            -int(row.get("endpoint_failures", 0)),
            -int(row.get("total_checks", 0)),
            str(row.get("method", "")),
            str(row.get("path", "")),
        ),
    )
    all_nodes = [row for row in per_node if int(row.get("total_checks", 0)) > 0]
    all_nodes_transport_only = bool(all_nodes) and all(bool(row.get("transport_only")) for row in all_nodes)
    all_nodes_fully_unreachable = bool(all_nodes) and all(bool(row.get("fully_unreachable")) for row in all_nodes)
    dominant_transport_signature = transport_signatures.most_common(1)[0][0] if transport_signatures else None
    dominant_transport_signature_count = int(transport_signatures.most_common(1)[0][1]) if transport_signatures else 0
    tls_trust = _tls_trust_diagnostics(payload if isinstance(payload, dict) else {})
    remediation_targets = _build_remediation_targets(
        total=total,
        endpoint_failures=endpoint_failures,
        transport_errors=transport_errors,
        guardrail_denials=guardrail_denials,
        per_node=per_node,
        per_check_surface=per_check_surface,
        transport_signatures=transport_signatures,
        artifact_age_seconds=age_seconds,
        tls_trust_diagnostics=tls_trust,
    )
    report = {
        "timestamp": _now(),
        "source_artifact": str(source_artifact or LIVE_E2E),
        "available": bool(total),
        "status": parity_status,
        "strict_all_pass": strict_all_pass,
        "artifact_health": {
            "live_e2e_timestamp": live_ts or None,
            "artifact_age_seconds": age_seconds,
            "stale_threshold_seconds": STALE_ARTIFACT_THRESHOLD_SECONDS,
            "is_stale": bool(age_seconds is not None and age_seconds > STALE_ARTIFACT_THRESHOLD_SECONDS),
        },
        "counts": {
            "total": total,
            "pass": pass_count,
            "endpoint_failures": endpoint_failures,
            "transport_errors": transport_errors,
            "guardrail_denials": guardrail_denials,
        },
        "per_node": per_node,
        "per_check_surface": per_check_surface,
        "error_signatures": {
            "global": _counter_rows(global_errors, limit=20),
            "transport": _counter_rows(transport_signatures, limit=10),
        },
        "transport_diagnostics": {
            "all_nodes_transport_only": all_nodes_transport_only,
            "all_nodes_fully_unreachable": all_nodes_fully_unreachable,
            "uniform_transport_signature": len(transport_signatures) == 1 if transport_signatures else False,
            "dominant_transport_signature": dominant_transport_signature,
            "dominant_transport_signature_count": dominant_transport_signature_count,
        },
        "tls_trust_diagnostics": tls_trust,
        "remediation_targets": remediation_targets,
        "policy": {
            "wave2_all_pass_requires_zero_transport_and_zero_endpoint_failures": True,
            "transport_blocked_is_not_treated_as_endpoint_regression": True,
            "guardrail_denials_are_not_treated_as_endpoint_regressions": True,
            "no_green_without_strict_all_pass": True,
            "stale_artifact_requires_refresh_before_green": True,
        },
    }
    return report


def build_report(
    live_e2e_path: Path = LIVE_E2E,
    source_artifact: str | None = None,
) -> dict[str, Any]:
    payload = _read_json(live_e2e_path, {})
    return build_report_from_payload(payload if isinstance(payload, dict) else {}, source_artifact=source_artifact or str(live_e2e_path))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Wave-2 live parity evidence artifact.")
    p.add_argument("--live-e2e", default=str(LIVE_E2E), help="Input live E2E JSON path")
    p.add_argument("--latest-out", default=str(PARITY_LATEST), help="Output latest JSON path")
    p.add_argument("--history-out", default=str(PARITY_HISTORY), help="Output history JSONL path")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    live_e2e_path = Path(str(args.live_e2e))
    latest_out = Path(str(args.latest_out))
    history_out = Path(str(args.history_out))
    report = build_report(live_e2e_path=live_e2e_path, source_artifact=str(live_e2e_path))
    _write_json(latest_out, report)
    _append_jsonl(history_out, report)
    print(json.dumps(report, indent=2))
    return 0 if report.get("strict_all_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
