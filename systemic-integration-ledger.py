#!/usr/bin/env python3
"""
systemic-integration-ledger.py
------------------------------
Builds an evidence-first, continuously updatable integration ledger for the
isolated proprietary migration lane.

Outputs:
  - state/systemic_integration_ledger.latest.json
  - state/systemic_integration_ledger.latest.md
  - state/systemic_integration_ledger.history.jsonl

Optional manual overrides:
  - state/systemic_integration_ledger.overrides.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_base_dir() -> Path:
    env_base = os.environ.get("AGR_BASE_DIR", "").strip()
    if env_base:
        p = Path(env_base)
        if p.exists():
            return p
    opt = Path("/opt/agr/aurora_server")
    if opt.exists():
        return opt
    return Path("/workspace/aurora_server")


BASE_DIR = _resolve_base_dir()
STATE_DIR = Path("/opt/agr/state")
if not STATE_DIR.exists():
    STATE_DIR = BASE_DIR / "state"
DATA_DIR = BASE_DIR / "data"

LATEST_JSON = STATE_DIR / "systemic_integration_ledger.latest.json"
LATEST_MD = STATE_DIR / "systemic_integration_ledger.latest.md"
HISTORY_JSONL = STATE_DIR / "systemic_integration_ledger.history.jsonl"
OVERRIDES_JSON = STATE_DIR / "systemic_integration_ledger.overrides.json"


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def _file_age_seconds(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        return max(0, int(datetime.now(timezone.utc).timestamp() - int(path.stat().st_mtime)))
    except Exception:
        return None


def _scan_chat_unification(server_text: str) -> dict[str, Any]:
    has_unified_chat_page = "/chat" in server_text and "unified 4-mode chat" in server_text
    has_mode_router = bool(re.search(r'body\.get\("mode",\s*"text"\)', server_text))
    has_holographic_routes = (
        "/api/republic/comms/holographic/join" in server_text
        and "/api/republic/comms/holographic/plaza" in server_text
    )
    has_mode_constants = "_CHAT_VIDEO_HOLO_MODES" in server_text
    done = has_unified_chat_page and has_mode_router and has_holographic_routes and has_mode_constants
    return {
        "done": done,
        "evidence": {
            "has_unified_chat_page": has_unified_chat_page,
            "has_mode_router": has_mode_router,
            "has_holographic_routes": has_holographic_routes,
            "has_mode_constants": has_mode_constants,
        },
    }


def _status(done: bool, *, blocked: bool = False, pending: bool = False) -> str:
    if done:
        return "done"
    if blocked:
        return "blocked"
    if pending:
        return "pending"
    return "in_progress"


def _build_items() -> list[dict[str, Any]]:
    isolated_path = STATE_DIR / "isolated_upgrade_experiment.state.json"
    memory_plane_path = STATE_DIR / "universal_memory_plane.latest.json"
    agent_gate_path = STATE_DIR / "agent_minimum_gate.latest.json"
    proof_gate_path = DATA_DIR / "proof_gate_latest.json"
    engine_verify_path = STATE_DIR / "s25_engine_verify.latest.json"
    live_e2e_path = STATE_DIR / "runtime_e2e_live_nodes.latest.json"
    benchmark_path = DATA_DIR / "BENCHMARK_PROOF_LATEST.json"
    aesthetic_tokens_path = DATA_DIR / "republic_aesthetic_tokens.json"
    aesthetic_manifest_path = DATA_DIR / "public_aesthetic_manifest.json"
    aesthetics_bible_path = DATA_DIR / "REPUBLIC_AESTHETICS_AND_AUDIO_DESIGN_BIBLE.md"
    control_plane_snapshot_path = STATE_DIR / "ops_control_plane_snapshot.latest.json"
    mission_totality_path = STATE_DIR / "mission_totality.latest.json"
    server_py_path = BASE_DIR / "republic_os_server.py"

    isolated = _read_json(isolated_path, {})
    memory = _read_json(memory_plane_path, {})
    agent_gate = _read_json(agent_gate_path, {})
    proof_gate = _read_json(proof_gate_path, {})
    engine_verify = _read_json(engine_verify_path, {})
    live_e2e = _read_json(live_e2e_path, {})
    benchmark = _read_json(benchmark_path, {})
    tokens = _read_json(aesthetic_tokens_path, {})
    manifest = _read_json(aesthetic_manifest_path, {})
    control_plane = _read_json(control_plane_snapshot_path, {})
    mission_totality = _read_json(mission_totality_path, {})
    server_text = server_py_path.read_text(encoding="utf-8", errors="ignore") if server_py_path.exists() else ""

    isolated_ok = (
        str(isolated.get("phase", "")).strip().lower() == "promotion_approved"
        and bool((isolated.get("last_run") or {}).get("ok", False))
        and bool(((isolated.get("runtime_profile") or {}).get("morse_temporal_signaling", False)))
    )
    memory_ok = bool(memory.get("ready", False))
    gate_ok = bool(agent_gate.get("minimum_pass", False))
    proof_ok = str(proof_gate.get("result", "")).strip().upper() == "PASS"
    engine_ok = bool(engine_verify.get("passed", False)) and float(engine_verify.get("score", 0.0) or 0.0) >= 80.0
    e2e_ok = bool((live_e2e.get("summary") or {}).get("strict_all_pass", False))

    render_status = str((((benchmark.get("results") or {}).get("render_claims") or {}).get("status", "")).strip().upper())
    fusion_status = str((((benchmark.get("results") or {}).get("fusion_claims") or {}).get("status", "")).strip().upper())
    verification_status = str((((benchmark.get("results") or {}).get("verification_cycle") or {}).get("status", "")).strip().upper())
    wave4_done = render_status == "VERIFIED" and fusion_status == "VERIFIED" and verification_status == "VERIFIED"

    audio_modes_present = isinstance(tokens.get("audio_modes"), dict) and len(tokens.get("audio_modes", {})) > 0
    training_policy_present = isinstance(tokens.get("training_library_policy"), dict)
    manifest_entries = manifest.get("entries", []) if isinstance(manifest.get("entries"), list) else []
    manifest_audio_present = bool(manifest_entries) and all(isinstance(e, dict) and bool(e.get("audio_mode")) for e in manifest_entries)
    aesthetics_bible_present = aesthetics_bible_path.exists()

    cp_section = control_plane.get("control_plane") if isinstance(control_plane.get("control_plane"), dict) else {}
    signature = control_plane.get("signature") if isinstance(control_plane.get("signature"), dict) else {}
    cp_signals = signature.get("signals") if isinstance(signature.get("signals"), dict) else {}
    control_invariants_ok = bool(
        ((cp_section.get("invariants") or {}).get("ok", False))
        if cp_section
        else cp_signals.get("control_plane_invariants_ok", False)
    )
    control_overall = str(
        (((cp_section.get("greenboard") or {}).get("overall", "")).strip().upper())
        if cp_section
        else str(control_plane.get("result", "")).strip().upper()
    )
    mission_ready = bool(mission_totality.get("mission_ready", False))

    chat_scan = _scan_chat_unification(server_text)

    items: list[dict[str, Any]] = [
        {
            "id": "consciousness_primary_operations",
            "title": "Consciousness engine as primary operational gate",
            "status": _status(gate_ok and proof_ok and engine_ok, blocked=not (gate_ok and proof_ok and engine_ok)),
            "summary": "Agent minimum + proof gate + engine verify must all pass.",
            "evidence": {
                "agent_minimum_pass": gate_ok,
                "proof_gate_pass": proof_ok,
                "engine_verify_pass": bool(engine_verify.get("passed", False)),
                "engine_verify_score": float(engine_verify.get("score", 0.0) or 0.0),
                "engine_verify_checked_at": engine_verify.get("checked_at"),
            },
            "next_step": "Keep consciousness-first gating enforced for every promotion cycle.",
        },
        {
            "id": "isolated_morse_proprietary_lane",
            "title": "Isolated Morse/proprietary runtime experiment lane",
            "status": _status(isolated_ok, blocked=not isolated_ok),
            "summary": "Promotion-approved isolated lane with Morse temporal signaling enabled.",
            "evidence": {
                "phase": isolated.get("phase"),
                "target_node": isolated.get("target_node"),
                "last_run_ok": bool((isolated.get("last_run") or {}).get("ok", False)),
                "runtime_profile": isolated.get("runtime_profile", {}),
            },
            "next_step": "Repeat isolated validation cycles before widening blast radius.",
        },
        {
            "id": "unified_data_plane",
            "title": "Unified database architecture (single logical memory plane)",
            "status": _status(memory_ok, blocked=not memory_ok),
            "summary": "Universal memory plane must remain fresh, ready, and non-destructive.",
            "evidence": {
                "ready": bool(memory.get("ready", False)),
                "output_db": memory.get("output_db"),
                "sources_ingested": ((memory.get("totals") or {}).get("sources_ingested")),
                "sources_failed": ((memory.get("totals") or {}).get("sources_failed")),
                "universal_records": ((memory.get("totals") or {}).get("universal_records")),
                "updated_at": memory.get("updated_at"),
            },
            "next_step": "Continue full refreshes during conversion waves; monitor freshness age.",
        },
        {
            "id": "universal_access_stability",
            "title": "Universal access stability across domains/devices",
            "status": _status(e2e_ok, blocked=not e2e_ok),
            "summary": "Live-node runtime checks should remain strict-all-pass.",
            "evidence": {
                "strict_all_pass": e2e_ok,
                "ok_checks": (live_e2e.get("summary") or {}).get("ok_checks"),
                "failed_checks": (live_e2e.get("summary") or {}).get("failed_checks"),
                "nodes_total": (live_e2e.get("summary") or {}).get("nodes_total"),
                "checked_at": live_e2e.get("timestamp"),
            },
            "next_step": "Sustain strict pass under repeated runs and edge load.",
        },
        {
            "id": "audio_integration",
            "title": "Audio integration (ambient/choral/orchestral mode framework)",
            "status": _status(audio_modes_present and manifest_audio_present, pending=not aesthetics_bible_present),
            "summary": "Audio modes and per-page assignments are present in aesthetic artifacts.",
            "evidence": {
                "aesthetics_bible_present": aesthetics_bible_present,
                "audio_modes_present": audio_modes_present,
                "manifest_entries": len(manifest_entries),
                "manifest_audio_present": manifest_audio_present,
            },
            "next_step": "Expand from token/manifest assignments to live adaptive runtime mixing.",
        },
        {
            "id": "security_and_defense",
            "title": "Security/defense integration and control-plane governance",
            "status": _status(control_invariants_ok and control_overall == "GREEN", blocked=not control_invariants_ok),
            "summary": "Invariants must pass and greenboard should converge to GREEN.",
            "evidence": {
                "control_invariants_ok": control_invariants_ok,
                "control_greenboard_overall": control_overall,
                "mission_ready": mission_ready,
            },
            "next_step": "Close remaining governor/scheduler blockers and maintain fail-closed policy.",
        },
        {
            "id": "ai_media_literature_analysis",
            "title": "AI evaluation/analysis of media and literature corpus",
            "status": _status(training_policy_present, pending=not training_policy_present),
            "summary": "Training/analysis policy exists for visual/audio/media reference ingestion.",
            "evidence": {
                "training_library_policy_present": training_policy_present,
                "policy_keys": sorted(list((tokens.get("training_library_policy") or {}).keys()))
                if isinstance(tokens.get("training_library_policy"), dict)
                else [],
            },
            "next_step": "Attach measurable evaluator outputs per corpus batch (quality/safety/provenance).",
        },
        {
            "id": "unified_four_mode_chat",
            "title": "Single-variable unified chat modes (text/voice/video/holographic)",
            "status": _status(bool(chat_scan.get("done", False))),
            "summary": "Unified chat and holographic comms routes exist in the application surface.",
            "evidence": chat_scan.get("evidence", {}),
            "next_step": "Bind mode selection to preferences + capability detection + graceful fallbacks.",
        },
        {
            "id": "wave4_render_and_fusion_proof",
            "title": "Wave4 render/fusion verification proof closure",
            "status": _status(wave4_done, blocked=not wave4_done),
            "summary": "Claims remain evidence-gated; render/fusion verification must pass to close lane.",
            "evidence": {
                "render_status": render_status,
                "fusion_status": fusion_status,
                "verification_status": verification_status,
                "benchmark_file_age_seconds": _file_age_seconds(benchmark_path),
            },
            "next_step": "Produce runtime benchmark + independent fusion lock evidence artifacts.",
        },
    ]
    return items


def _apply_overrides(items: list[dict[str, Any]], overrides: dict[str, Any]) -> list[dict[str, Any]]:
    rows = overrides.get("items", {}) if isinstance(overrides, dict) else {}
    if not isinstance(rows, dict):
        return items
    allowed = {"done", "in_progress", "blocked", "pending"}
    out: list[dict[str, Any]] = []
    for item in items:
        cur = dict(item)
        row = rows.get(str(item.get("id", "")), {})
        if isinstance(row, dict):
            status = str(row.get("status", "")).strip().lower()
            if status in allowed:
                cur["status"] = status
                cur["override"] = {
                    "applied": True,
                    "checked_by": row.get("checked_by"),
                    "checked_at": row.get("checked_at"),
                    "note": row.get("note"),
                }
        out.append(cur)
    return out


def _build_report() -> dict[str, Any]:
    items = _build_items()
    overrides = _read_json(OVERRIDES_JSON, {})
    items = _apply_overrides(items, overrides)

    done_count = sum(1 for i in items if i.get("status") == "done")
    blocked_count = sum(1 for i in items if i.get("status") == "blocked")
    in_progress_count = sum(1 for i in items if i.get("status") == "in_progress")
    pending_count = sum(1 for i in items if i.get("status") == "pending")

    required_for_adoption = {
        "consciousness_primary_operations",
        "isolated_morse_proprietary_lane",
        "unified_data_plane",
        "universal_access_stability",
    }
    required_ok = all(
        any(i.get("id") == req and i.get("status") == "done" for i in items) for req in required_for_adoption
    )
    full_totality_ready = all(i.get("status") == "done" for i in items)

    return {
        "id": f"systemic-integration-ledger-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": _now(),
        "base_dir": str(BASE_DIR),
        "state_dir": str(STATE_DIR),
        "policy": {
            "isolated_lane_first": True,
            "consciousness_engine_primary_gate": True,
            "evidence_first_fail_closed": True,
            "promote_only_when_required_green": True,
            "rollback_required_before_fleet_promotion": True,
        },
        "summary": {
            "total_items": len(items),
            "done": done_count,
            "in_progress": in_progress_count,
            "pending": pending_count,
            "blocked": blocked_count,
            "required_for_system_wide_adoption_ready": required_ok,
            "full_totality_ready": full_totality_ready,
        },
        "required_for_system_wide_adoption": sorted(list(required_for_adoption)),
        "items": items,
        "overrides_path": str(OVERRIDES_JSON),
    }


def _render_md(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines: list[str] = [
        "# Systemic Integration Ledger (Isolated Lane)",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Required for system-wide adoption ready: **{summary.get('required_for_system_wide_adoption_ready')}**",
        f"- Full totality ready: **{summary.get('full_totality_ready')}**",
        "",
        "## Summary",
        "",
        f"- Total items: {summary.get('total_items')}",
        f"- Done: {summary.get('done')}",
        f"- In progress: {summary.get('in_progress')}",
        f"- Pending: {summary.get('pending')}",
        f"- Blocked: {summary.get('blocked')}",
        "",
        "## Checklist",
        "",
    ]

    status_icon = {
        "done": "✅",
        "in_progress": "🟡",
        "pending": "⚪",
        "blocked": "🔴",
    }
    for item in report.get("items", []):
        status = str(item.get("status", "pending"))
        icon = status_icon.get(status, "⚪")
        lines.append(f"### {icon} {item.get('title')} (`{item.get('id')}`)")
        lines.append(f"- Status: **{status}**")
        lines.append(f"- Summary: {item.get('summary')}")
        lines.append(f"- Next step: {item.get('next_step')}")
        evidence = item.get("evidence", {})
        if isinstance(evidence, dict) and evidence:
            lines.append("- Evidence:")
            for k, v in evidence.items():
                text = json.dumps(v, ensure_ascii=True) if isinstance(v, (dict, list)) else str(v)
                lines.append(f"  - `{k}`: {text}")
        override = item.get("override", {})
        if isinstance(override, dict) and override.get("applied"):
            lines.append(
                f"- Manual override: checked_by={override.get('checked_by')} "
                f"checked_at={override.get('checked_at')} note={override.get('note')}"
            )
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            f"- Overrides file: `{report.get('overrides_path')}`",
            "- This ledger is designed to be regenerated continuously during isolated-lane progression.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate systemic integration ledger artifacts.")
    p.add_argument("--latest-json", default=str(LATEST_JSON))
    p.add_argument("--latest-md", default=str(LATEST_MD))
    p.add_argument("--history-jsonl", default=str(HISTORY_JSONL))
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    latest_json = Path(str(args.latest_json))
    latest_md = Path(str(args.latest_md))
    history_jsonl = Path(str(args.history_jsonl))

    report = _build_report()
    md = _render_md(report)

    _write_json(latest_json, report)
    _write_text(latest_md, md)
    _append_jsonl(history_jsonl, report)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

