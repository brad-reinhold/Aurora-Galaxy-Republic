#!/usr/bin/env python3
"""
wave4-benchmark-proof.py
------------------------
Produce reproducible Wave-4 benchmark/proof artifacts with explicit
VERIFIED/PARTIAL/NOT VERIFIED semantics.

This script intentionally avoids overclaiming:
- render verification is based on measured static artifact generation throughput
  and remains PARTIAL for 8k/90fps runtime claims unless external runtime data exists.
- fusion/materialization claims remain NOT VERIFIED unless independent controlled
  experiment artifacts are present.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
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
    opt_base = Path("/opt/agr/aurora_server")
    if opt_base.exists():
        return opt_base
    return Path("/workspace/aurora_server")


BASE_DIR = _resolve_base_dir()
DATA_DIR = BASE_DIR / "data"
STATE_DIR = BASE_DIR / "state"
SOVEREIGN_DIR = BASE_DIR.parent / "sovereign"

ROLLOUT_JSON = DATA_DIR / "public_cinematic_rollout.json"
MANIFEST_JSON = DATA_DIR / "public_aesthetic_manifest.json"
BASELINE_CSS = DATA_DIR / "public_aesthetic_baseline.css"
PROOF_GATE_JSON = DATA_DIR / "proof_gate_latest.json"
OPS_CYCLE_JSON = STATE_DIR / "ops_verification_cycle.latest.json"
RENDER_RUNTIME_BENCH_JSON = STATE_DIR / "wave4_render_runtime_benchmark.latest.json"
FUSION_MEASUREMENT_JSON = STATE_DIR / "fusion_independent_measurement.latest.json"
FUSION_CONTAINMENT_JSON = STATE_DIR / "fusion_containment_verification.latest.json"
FUSION_SAFETY_CASE_JSON = STATE_DIR / "fusion_safety_case.latest.json"
FUSION_DUAL_CONTROL_JSON = STATE_DIR / "fusion_dual_control.latest.json"

CYCLE_MAX_AGE_SECONDS = 3600

OUT_JSON = DATA_DIR / "WAVE4_BENCHMARK_PROOF_20260414.json"
OUT_MD = DATA_DIR / "WAVE4_BENCHMARK_PROOF_20260414.md"
OUT_JSON_LATEST = DATA_DIR / "BENCHMARK_PROOF_LATEST.json"
OUT_MD_LATEST = DATA_DIR / "BENCHMARK_PROOF_LATEST.md"


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _age_seconds_from_iso(ts: Any) -> int | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None
    return max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))


def _artifact_age_seconds(report: dict[str, Any], path: Path) -> int | None:
    age_seconds = _age_seconds_from_iso(report.get("timestamp"))
    if age_seconds is not None:
        return age_seconds
    if not path.exists():
        return None
    try:
        return max(0, int(datetime.now(timezone.utc).timestamp() - path.stat().st_mtime))
    except Exception:
        return None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _runtime_render_verified(report: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    if not isinstance(report, dict) or not report:
        return False, {}
    if bool(report.get("runtime_8k_90fps_verified")):
        return True, {"source": "runtime_8k_90fps_verified"}
    width = int(report.get("width", 0) or 0)
    height = int(report.get("height", 0) or 0)
    fps = _safe_float(
        report.get("average_fps", report.get("fps", report.get("measured_fps", 0.0))),
        0.0,
    )
    resolution_text = str(report.get("resolution", "")).strip().lower()
    resolution_ok = (width >= 7680 and height >= 4320) or ("8k" in resolution_text)
    fps_ok = fps >= 90.0
    return resolution_ok and fps_ok, {
        "width": width,
        "height": height,
        "fps": round(fps, 4),
        "resolution": resolution_text or None,
        "resolution_ok": resolution_ok,
        "fps_ok": fps_ok,
    }


def _fusion_gate_pass(
    report: dict[str, Any],
    *,
    truthy_keys: tuple[str, ...],
    accepted_status: tuple[str, ...] = ("PASS", "VERIFIED", "APPROVED", "READY"),
) -> bool:
    if not isinstance(report, dict) or not report:
        return False
    for key in truthy_keys:
        if key in report:
            return bool(report.get(key))
    status = str(report.get("status", "")).strip().upper()
    result = str(report.get("result", "")).strip().upper()
    decision = str(report.get("decision", "")).strip().upper()
    if status in accepted_status or result in accepted_status or decision in accepted_status:
        return True
    if "approved" in report:
        return bool(report.get("approved"))
    if "ok" in report and isinstance(report.get("ok"), bool):
        return bool(report.get("ok"))
    return False


def _fusion_gate_component(
    *,
    name: str,
    path: Path,
    max_age_seconds: int,
    pass_keys: tuple[str, ...],
) -> dict[str, Any]:
    report = _read_json(path, {})
    present = isinstance(report, dict) and bool(report)
    age_seconds = _artifact_age_seconds(report if isinstance(report, dict) else {}, path)
    fresh = age_seconds is not None and age_seconds <= int(max_age_seconds)
    gate_pass = _fusion_gate_pass(report if isinstance(report, dict) else {}, truthy_keys=pass_keys)
    blockers: list[str] = []
    if not gate_pass:
        blockers.append(f"{name}_not_verified")
    if not fresh:
        blockers.append(f"{name}_stale_or_missing")
    return {
        "name": name,
        "path": str(path),
        "present": present,
        "max_age_seconds": int(max_age_seconds),
        "age_seconds": age_seconds,
        "fresh": fresh,
        "pass": gate_pass,
        "blockers": blockers,
        "details": report if isinstance(report, dict) else {},
    }


def _run_script(script_name: str) -> dict[str, Any]:
    script = SOVEREIGN_DIR / script_name
    if not script.exists():
        return {"ok": False, "error": "script_missing", "path": str(script)}
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "AGR_BASE_DIR": str(BASE_DIR)},
    )
    elapsed = round(time.perf_counter() - started, 3)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "seconds": elapsed,
        "path": str(script),
        "stdout_tail": proc.stdout.strip().splitlines()[-20:],
        "stderr_tail": proc.stderr.strip().splitlines()[-20:],
    }


def main() -> int:
    build_css = _run_script("build-cinematic-baseline-css.py")
    build_manifest = _run_script("build-aesthetic-manifest.py")

    rollout = _read_json(ROLLOUT_JSON, {})
    proof = _read_json(PROOF_GATE_JSON, {})
    cycle = _read_json(OPS_CYCLE_JSON, {})
    runtime_bench = _read_json(RENDER_RUNTIME_BENCH_JSON, {})

    total_pages = int((rollout or {}).get("total_pages", 0) or 0)
    rollout_ok = bool(ROLLOUT_JSON.exists() and MANIFEST_JSON.exists() and BASELINE_CSS.exists() and total_pages >= 122)
    bench_ok = bool(build_css.get("ok") and build_manifest.get("ok"))

    runtime_verified, runtime_metrics = _runtime_render_verified(runtime_bench if isinstance(runtime_bench, dict) else {})
    render_blockers: list[str] = []
    if not bench_ok:
        render_blockers.append("artifact_pipeline_benchmark_failed")
    if total_pages < 122:
        render_blockers.append("rollout_coverage_below_target_122_pages")
    if not runtime_verified:
        render_blockers.append("runtime_8k_90fps_not_verified")
    render_status = "VERIFIED" if rollout_ok and bench_ok and runtime_verified else ("PARTIAL" if rollout_ok and bench_ok else "NOT VERIFIED")

    fusion_measurement = _fusion_gate_component(
        name="independent_measurement",
        path=FUSION_MEASUREMENT_JSON,
        max_age_seconds=86400,
        pass_keys=(
            "independent_verified",
            "reproducible_effect_verified",
            "measured_net_effect_verified",
            "independent_physical_experiment_artifacts_present",
        ),
    )
    fusion_containment = _fusion_gate_component(
        name="containment_verification",
        path=FUSION_CONTAINMENT_JSON,
        max_age_seconds=86400,
        pass_keys=("containment_pass", "em_containment_pass", "fault_injection_pass", "kill_switch_verified", "passed"),
    )
    fusion_safety_case = _fusion_gate_component(
        name="safety_case_approval",
        path=FUSION_SAFETY_CASE_JSON,
        max_age_seconds=604800,
        pass_keys=("safety_case_approved", "safety_review_pass", "hazard_analysis_pass"),
    )
    fusion_dual_control = _fusion_gate_component(
        name="dual_control_authorization",
        path=FUSION_DUAL_CONTROL_JSON,
        max_age_seconds=3600,
        pass_keys=("dual_control_approved", "two_person_authorized", "authorization_active", "approved"),
    )
    fusion_components = [fusion_measurement, fusion_containment, fusion_safety_case, fusion_dual_control]
    fusion_blockers: list[str] = []
    for comp in fusion_components:
        name = str(comp.get("name", "component")).strip()
        if not bool(comp.get("pass", False)):
            fusion_blockers.append(f"fusion_reality_lock:{name}_not_verified")
        if not bool(comp.get("fresh", False)):
            fusion_blockers.append(f"fusion_reality_lock:{name}_stale_or_missing")
    dual_details = fusion_dual_control.get("details", {}) if isinstance(fusion_dual_control.get("details"), dict) else {}
    auth_count = dual_details.get("authorization_count")
    if auth_count is not None:
        try:
            if int(auth_count) < 2:
                fusion_blockers.append("fusion_reality_lock:dual_control_authorization_count_insufficient")
        except Exception:
            fusion_blockers.append("fusion_reality_lock:dual_control_authorization_count_invalid")
    fusion_ready = len(fusion_blockers) == 0
    fusion_any_evidence = any(bool(comp.get("present", False)) for comp in fusion_components)
    fusion_status = "VERIFIED" if fusion_ready else ("PARTIAL" if fusion_any_evidence else "NOT VERIFIED")

    cycle_pass = str(cycle.get("result", "")).upper() == "PASS"
    cycle_age_seconds = _artifact_age_seconds(cycle if isinstance(cycle, dict) else {}, OPS_CYCLE_JSON)
    cycle_fresh = cycle_age_seconds is not None and cycle_age_seconds <= CYCLE_MAX_AGE_SECONDS
    cycle_status = "VERIFIED" if cycle_pass and cycle_fresh else ("PARTIAL" if cycle_pass else "NOT VERIFIED")
    cycle_blockers: list[str] = []
    if not cycle_pass:
        cycle_blockers.append("verification_cycle_not_pass")
    if not cycle_fresh:
        cycle_blockers.append("verification_cycle_stale_or_missing")

    payload = {
        "timestamp": _now(),
        "wave": "wave_4_benchmark_and_proof",
        "results": {
            "render_claims": {
                "status": render_status,
                "details": {
                    "artifact_pipeline_benchmark_ok": bench_ok,
                    "rollout_pages": total_pages,
                    "target_pages_min": 122,
                    "runtime_artifact_present": isinstance(runtime_bench, dict) and bool(runtime_bench),
                    "runtime_8k_90fps_verified": runtime_verified,
                    "runtime_metrics": runtime_metrics,
                    "blockers": render_blockers,
                },
                "evidence": {
                    "build_css": build_css,
                    "build_manifest": build_manifest,
                    "rollout_json": str(ROLLOUT_JSON),
                    "manifest_json": str(MANIFEST_JSON),
                    "baseline_css": str(BASELINE_CSS),
                    "runtime_benchmark_json": str(RENDER_RUNTIME_BENCH_JSON),
                    "sha256": {
                        "rollout_json": _sha256(ROLLOUT_JSON),
                        "manifest_json": _sha256(MANIFEST_JSON),
                        "baseline_css": _sha256(BASELINE_CSS),
                        "runtime_benchmark_json": _sha256(RENDER_RUNTIME_BENCH_JSON),
                    },
                },
            },
            "fusion_claims": {
                "status": fusion_status,
                "details": {
                    "independent_physical_experiment_artifacts_present": bool(fusion_measurement.get("pass", False)),
                    "materialization_claim_verified": fusion_ready,
                    "fusion_reality_lock_ready": fusion_ready,
                    "blockers": sorted(set(fusion_blockers)),
                    "note": "Safety-first fail-closed policy: claim remains NOT VERIFIED without independent controlled measurements.",
                },
                "evidence": {
                    "components": fusion_components,
                    "policy": {
                        "require_independent_measurement": True,
                        "require_containment_verification": True,
                        "require_safety_case_approval": True,
                        "require_dual_control_authorization": True,
                        "fail_closed": True,
                    },
                },
            },
            "verification_cycle": {
                "status": cycle_status,
                "result": cycle.get("result"),
                "health_score": cycle.get("health_score"),
                "proof_gate_result": proof.get("result"),
                "age_seconds": cycle_age_seconds,
                "max_age_seconds": CYCLE_MAX_AGE_SECONDS,
                "fresh": cycle_fresh,
                "blockers": cycle_blockers,
                "evidence": {
                    "ops_cycle_json": str(OPS_CYCLE_JSON),
                    "sha256": {"ops_cycle_json": _sha256(OPS_CYCLE_JSON)},
                },
            },
        },
        "overall_wave4_status": "GREEN"
        if render_status == "VERIFIED" and fusion_status == "VERIFIED" and cycle_status == "VERIFIED"
        else ("AMBER" if cycle_status in {"VERIFIED", "PARTIAL"} or render_status == "PARTIAL" or fusion_status == "PARTIAL" else "RED"),
        "policy": {
            "no_superlative_claims_without_measurement": True,
            "fusion_claims_default_not_verified_without_independent_evidence": True,
            "fail_closed": True,
        },
        "wave4_signals": {
            "render_claims_verified": render_status == "VERIFIED",
            "fusion_claims_verified": fusion_status == "VERIFIED",
            "verification_cycle_pass": cycle_status == "VERIFIED",
            "verification_cycle_evidence_fresh": cycle_fresh,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    OUT_JSON_LATEST.write_text(json.dumps(payload, indent=2))

    lines = [
        "# Wave 4 Benchmark and Proof",
        "",
        f"- Generated: {payload['timestamp']}",
        f"- Overall Wave 4 Status: **{payload['overall_wave4_status']}**",
        "",
        "## Render Claims",
        f"- Status: **{render_status}**",
        f"- Artifact benchmark scripts succeeded: `{bench_ok}`",
        f"- Rollout pages covered: `{total_pages}` (target: `>=122`)",
        f"- Runtime 8k/90fps proof: `{'VERIFIED' if runtime_verified else 'NOT VERIFIED'}`",
        "",
        "## Fusion Claims",
        f"- Status: **{fusion_status}**",
        f"- Fusion interlock blockers: `{', '.join(sorted(set(fusion_blockers))) or 'none'}`",
        "",
        "## Verification Cycle",
        f"- Status: **{cycle_status}**",
        f"- Result: `{cycle.get('result')}`",
        f"- Health Score: `{cycle.get('health_score')}`",
        f"- Evidence age (s): `{cycle_age_seconds}` (max `{CYCLE_MAX_AGE_SECONDS}`)",
        "",
        "## Policy",
        "- Claims remain evidence-gated and fail-closed.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_MD_LATEST.write_text("\n".join(lines) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
