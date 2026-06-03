#!/usr/bin/env python3
"""
autonomous-build-remediate-loop.py
----------------------------------
Continuously executes concrete project build/remediation actions, then verifies.

This is intentionally NOT a "health-check only" loop:
- runs mutating remediation/build scripts each cycle
- records what artifacts changed (hash/mtime/size)
- appends cycle evidence to history JSONL
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
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
REPO_DIR = BASE_DIR.parent
SOVEREIGN_DIR = REPO_DIR / "sovereign"
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

LATEST_OUT = STATE_DIR / "autonomous_build_loop.latest.json"
HISTORY_OUT = STATE_DIR / "autonomous_build_loop.history.jsonl"
STATUS_OUT = STATE_DIR / "autonomous_build_loop.status.json"
PROGRESS_OUT = STATE_DIR / "autonomous_build_loop.progress.jsonl"
TEN_SHELL_REPORT_OUT = STATE_DIR / "autonomous_build_loop.progress_10.latest.json"

ARTIFACTS_TO_TRACK: tuple[Path, ...] = (
    BASE_DIR / "data" / "public_aesthetic_baseline.css",
    BASE_DIR / "data" / "public_aesthetic_manifest.json",
    BASE_DIR / "data" / "public_aesthetic_manifest.md",
    BASE_DIR / "data" / "public_cinematic_rollout.json",
    BASE_DIR / "data" / "BENCHMARK_PROOF_LATEST.json",
    BASE_DIR / "data" / "BENCHMARK_PROOF_LATEST.md",
    BASE_DIR / "data" / "proof_gate_latest.json",
    BASE_DIR / "data" / "proof_gate_latest.md",
    BASE_DIR / "state" / "wave1_remediation.latest.json",
)


@dataclass(frozen=True)
class StepSpec:
    name: str
    script: str
    kind: str
    required: bool


STEPS: tuple[StepSpec, ...] = (
    StepSpec("wave1_remediate", "wave1-remediate.py", "build_remediate", True),
    StepSpec("build_cinematic_baseline_css", "build-cinematic-baseline-css.py", "build_remediate", True),
    StepSpec("build_aesthetic_manifest", "build-aesthetic-manifest.py", "build_remediate", True),
    StepSpec("systemic_integration_ledger", "systemic-integration-ledger.py", "build_remediate", True),
    StepSpec("wave4_benchmark_proof", "wave4-benchmark-proof.py", "build_remediate", True),
    StepSpec("agent_minimum_gate", "agent-minimum-gate.py", "verify", False),
    StepSpec("local_proof_gate", "local-proof-gate.py", "verify", False),
    StepSpec("runtime_e2e_live_nodes", "runtime-e2e-live-nodes.py", "verify", False),
)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _fingerprint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "size": None, "mtime": None, "sha256": None}
    st = path.stat()
    return {
        "exists": True,
        "size": int(st.st_size),
        "mtime": int(st.st_mtime),
        "sha256": _sha256(path),
    }


def _snapshot_artifacts() -> dict[str, dict[str, Any]]:
    return {str(p): _fingerprint(p) for p in ARTIFACTS_TO_TRACK}


def _diff_artifacts(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    changed: list[dict[str, Any]] = []
    keys = sorted(set(before.keys()) | set(after.keys()))
    for key in keys:
        b = before.get(key, {"exists": False, "size": None, "mtime": None, "sha256": None})
        a = after.get(key, {"exists": False, "size": None, "mtime": None, "sha256": None})
        if b != a:
            changed.append({"path": key, "before": b, "after": a})
    return changed


def _update_status(payload: dict[str, Any]) -> None:
    out = {"updated_at": _now_iso(), **payload}
    _write_json(STATUS_OUT, out)


def _progress_event(payload: dict[str, Any]) -> None:
    _append_jsonl(PROGRESS_OUT, {"timestamp": _now_iso(), **payload})


def _write_ten_shell_report(payload: dict[str, Any]) -> None:
    _write_json(TEN_SHELL_REPORT_OUT, payload)


def _run_step(step: StepSpec, timeout_seconds: int, *, cycle_id: str, step_index: int, total_steps: int) -> dict[str, Any]:
    script_path = SOVEREIGN_DIR / step.script
    if not script_path.exists():
        return {
            "name": step.name,
            "kind": step.kind,
            "required": step.required,
            "ok": False,
            "error": "script_missing",
            "script": str(script_path),
            "returncode": None,
            "seconds": 0.0,
            "stdout_tail": [],
            "stderr_tail": [],
        }

    started = time.perf_counter()
    timeout_seconds = max(10, int(timeout_seconds))
    proc = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "AGR_BASE_DIR": str(BASE_DIR)},
    )
    timed_out = False
    while True:
        rc = proc.poll()
        elapsed = round(time.perf_counter() - started, 3)
        _update_status(
            {
                "running": True,
                "cycle_id": cycle_id,
                "phase": "step_running",
                "step": step.name,
                "step_index": step_index,
                "total_steps": total_steps,
                "step_elapsed_seconds": elapsed,
                "step_timeout_seconds": timeout_seconds,
            }
        )
        _progress_event(
            {
                "event": "step_heartbeat",
                "cycle_id": cycle_id,
                "step": step.name,
                "step_index": step_index,
                "total_steps": total_steps,
                "elapsed_seconds": elapsed,
            }
        )
        if rc is not None:
            break
        if elapsed >= timeout_seconds:
            timed_out = True
            try:
                proc.kill()
            except Exception:
                pass
            break
        time.sleep(1)
    stdout, stderr = proc.communicate()
    returncode = int(proc.returncode if proc.returncode is not None else -1)
    if timed_out:
        returncode = 124
    elapsed = round(time.perf_counter() - started, 3)
    return {
        "name": step.name,
        "kind": step.kind,
        "required": step.required,
        "ok": returncode == 0,
        "script": str(script_path),
        "returncode": returncode,
        "seconds": elapsed,
        "timed_out": timed_out,
        "stdout_tail": (stdout or "").strip().splitlines()[-25:],
        "stderr_tail": (stderr or "").strip().splitlines()[-25:],
    }


def run_cycle(timeout_seconds: int) -> dict[str, Any]:
    cycle_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    started_at = _now_iso()
    t0 = time.perf_counter()
    _update_status({"running": True, "cycle_id": cycle_id, "phase": "cycle_start"})
    _progress_event({"event": "cycle_start", "cycle_id": cycle_id})
    before = _snapshot_artifacts()

    steps: list[dict[str, Any]] = []
    hard_failures: list[str] = []
    total_steps = len(STEPS)
    for step_index, step in enumerate(STEPS, start=1):
        try:
            _update_status(
                {
                    "running": True,
                    "cycle_id": cycle_id,
                    "phase": "step_start",
                    "step": step.name,
                    "step_index": step_index,
                    "total_steps": total_steps,
                }
            )
            _progress_event(
                {
                    "event": "step_start",
                    "cycle_id": cycle_id,
                    "step": step.name,
                    "step_index": step_index,
                    "total_steps": total_steps,
                }
            )
            out = _run_step(
                step,
                timeout_seconds=timeout_seconds,
                cycle_id=cycle_id,
                step_index=step_index,
                total_steps=total_steps,
            )
        except Exception as exc:
            out = {
                "name": step.name,
                "kind": step.kind,
                "required": step.required,
                "ok": False,
                "error": str(exc),
                "script": str(SOVEREIGN_DIR / step.script),
                "returncode": None,
                "seconds": 0.0,
                "stdout_tail": [],
                "stderr_tail": [],
            }
        steps.append(out)
        _progress_event(
            {
                "event": "step_complete",
                "cycle_id": cycle_id,
                "step": step.name,
                "step_index": step_index,
                "total_steps": total_steps,
                "ok": bool(out.get("ok", False)),
                "returncode": out.get("returncode"),
                "seconds": out.get("seconds"),
            }
        )
        if step.required and not bool(out.get("ok", False)):
            hard_failures.append(step.name)

    after = _snapshot_artifacts()
    changed = _diff_artifacts(before, after)
    elapsed = round(time.perf_counter() - t0, 3)

    report = {
        "cycle_id": cycle_id,
        "timestamp": _now_iso(),
        "started_at": started_at,
        "ended_at": _now_iso(),
        "duration_seconds": elapsed,
        "ok": len(hard_failures) == 0,
        "hard_failures": hard_failures,
        "steps": steps,
        "mutation": {
            "changed_files_count": len(changed),
            "changed_files": changed,
            "mutation_observed": len(changed) > 0,
        },
        "policy": {
            "mode": "build_remediate_then_verify",
            "health_check_only": False,
            "autonomous": True,
        },
    }
    _write_json(LATEST_OUT, report)
    _append_jsonl(HISTORY_OUT, report)
    _update_status(
        {
            "running": True,
            "cycle_id": cycle_id,
            "phase": "cycle_complete",
            "ok": bool(report.get("ok", False)),
            "duration_seconds": report.get("duration_seconds"),
            "hard_failures": report.get("hard_failures", []),
            "mutations": ((report.get("mutation") or {}).get("changed_files_count")),
        }
    )
    _progress_event(
        {
            "event": "cycle_complete",
            "cycle_id": cycle_id,
            "ok": bool(report.get("ok", False)),
            "duration_seconds": report.get("duration_seconds"),
            "mutations": ((report.get("mutation") or {}).get("changed_files_count")),
        }
    )
    return report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Autonomous build/remediate loop runner")
    p.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    p.add_argument("--interval-seconds", type=int, default=0, help="Delay between cycles when not --once")
    p.add_argument("--timeout-seconds", type=int, default=300, help="Per-step timeout")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    interval_seconds = max(0, int(args.interval_seconds or 0))
    timeout_seconds = max(10, int(args.timeout_seconds or 300))
    cycles_completed = 0
    steps_completed_total = 0
    next_steps_report_mark = 10

    if args.once:
        report = run_cycle(timeout_seconds=timeout_seconds)
        print(json.dumps(report, indent=2))
        return 0 if bool(report.get("ok", False)) else 2

    while True:
        report = run_cycle(timeout_seconds=timeout_seconds)
        cycles_completed += 1
        steps_completed_total += len(report.get("steps", []))
        while steps_completed_total >= next_steps_report_mark:
            checkpoint = {
                "timestamp": _now_iso(),
                "type": "progress_every_10_steps",
                "steps_completed_total": steps_completed_total,
                "cycles_completed": cycles_completed,
                "next_report_at_steps": next_steps_report_mark + 10,
                "latest_cycle_id": report.get("cycle_id"),
                "latest_cycle_ok": bool(report.get("ok", False)),
                "latest_mutations": ((report.get("mutation") or {}).get("changed_files_count")),
                "latest_hard_failures": report.get("hard_failures", []),
            }
            _write_ten_shell_report(checkpoint)
            _progress_event({"event": "progress_every_10_steps", **checkpoint})
            print(
                f"[autonomous-build-loop:progress] steps={steps_completed_total} "
                f"cycles={cycles_completed} "
                f"ok={checkpoint['latest_cycle_ok']} "
                f"mutations={checkpoint['latest_mutations']}"
            )
            next_steps_report_mark += 10
        print(
            f"[autonomous-build-loop] {report.get('timestamp')} "
            f"ok={report.get('ok')} "
            f"mutations={((report.get('mutation') or {}).get('changed_files_count'))}"
        )
        if interval_seconds > 0:
            sleep_started = time.time()
            while True:
                elapsed = int(time.time() - sleep_started)
                if elapsed >= interval_seconds:
                    break
                _update_status(
                    {
                        "running": True,
                        "phase": "between_cycles_wait",
                        "next_cycle_in_seconds": max(0, interval_seconds - elapsed),
                    }
                )
                time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())

