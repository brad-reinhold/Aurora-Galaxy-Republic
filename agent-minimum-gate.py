#!/usr/bin/env python3
"""
agent-minimum-gate.py
---------------------
Enforces the minimum operational baseline for any agent/operator:
1) Secure fleet key resolution and file permission check.
2) Authenticated access checks to all five Hetzner nodes.
3) Guardian handset transport checks (S25 channel today; OnePlus 15 when enrolled on mesh).
4) Library of Light charter presence/integrity check.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent
_DEFAULT_NODES: list[tuple[str, str]] = [
    ("chimaera", "5.78.184.2"),
    ("yggdrasil", "128.140.45.22"),
    ("enterprise", "91.99.224.166"),
    ("prometheus", "46.62.202.166"),
    ("galactica", "178.104.31.46"),
]


def _load_fleet_public_nodes() -> list[tuple[str, str]]:
    path = _REPO_ROOT / "fleet-public-node-env.txt"
    if not path.is_file():
        return list(_DEFAULT_NODES)
    out: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        name, ip = line.split(":", 1)
        name, ip = name.strip().lower(), ip.strip()
        if name and ip:
            out.append((name, ip))
    return out if len(out) >= 1 else list(_DEFAULT_NODES)


NODES: list[tuple[str, str]] = _load_fleet_public_nodes()

CHARTER_PATH = Path("/workspace/aurora_server/data/LIBRARY_OF_LIGHT_CHARTER_20260414.json")
HEARTBEAT_CANDIDATES = [
    Path("/workspace/aurora_server/state/s25_heartbeat.last"),
    Path("/opt/agr/state/s25_heartbeat.last"),
]
ENGINE_VERIFY_LATEST = Path("/workspace/aurora_server/state/s25_engine_verify.latest.json")
ORCHESTRATOR_STATE_CANDIDATES = [
    Path("/workspace/aurora_server/state/universal_user_orchestrator.state.json"),
    Path("/opt/agr/state/universal_user_orchestrator.state.json"),
]
CONSCIOUSNESS_ENGINE_REQUIRED_FILES = [
    Path("/workspace/aurora_server/agr_consciousness_core.py"),
    Path("/workspace/aurora_server/agr_sovereign_mind.py"),
    Path("/workspace/aurora_server/agr_universal_user_orchestrator.py"),
    Path("/workspace/aurora_server/routes/routes_s25_heartbeat.py"),
]
MAX_ENGINE_VERIFY_AGE_SECONDS = 3600
MIN_ENGINE_VERIFY_SCORE = 80.0
MAX_ORCHESTRATOR_TICK_AGE_SECONDS = 600
DEFAULT_LATEST = Path("/workspace/aurora_server/state/agent_minimum_gate.latest.json")
DEFAULT_HISTORY = Path("/workspace/aurora_server/state/agent_minimum_gate.history.jsonl")


@dataclass
class GateContext:
    ssh_key_path: str | None
    ssh_key_secure: bool
    ssh_key_mode: str | None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _parse_iso(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _age_seconds_from_iso(value: Any) -> int | None:
    ts = _parse_iso(value)
    if ts is None:
        return None
    try:
        return max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
    except Exception:
        return None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def _resolve_fleet_key() -> str | None:
    cmd = (
        'source "/workspace/sovereign/lib/fleet-key.sh" '
        "&& resolve_fleet_ssh_key"
    )
    try:
        out = subprocess.run(
            ["bash", "-lc", cmd],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    key_path = out.stdout.strip()
    return key_path or None


def _key_security(path: str | None) -> tuple[bool, str | None]:
    if not path:
        return False, None
    try:
        st = os.stat(path)
    except Exception:
        return False, None
    mode = stat.S_IMODE(st.st_mode)
    secure = (mode & (stat.S_IRWXG | stat.S_IRWXO)) == 0
    return secure, oct(mode)


def _ssh_node_check(key_path: str, node: str, ip: str) -> dict[str, Any]:
    cmd = [
        "ssh",
        "-i",
        key_path,
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        f"root@{ip}",
        "hostname",
    ]
    out = None
    exc: Exception | None = None
    for attempt in range(3):
        try:
            out = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=12,
            )
            if out.returncode == 0 and out.stdout.strip():
                break
        except Exception as e:
            exc = e
        if attempt < 2:
            time.sleep(0.8)
    if out is None:
        return {
            "node": node,
            "ip": ip,
            "ok": False,
            "host": None,
            "error": str(exc) if exc else "ssh_exception",
        }
    host = out.stdout.strip()
    ok = out.returncode == 0 and bool(host)
    return {
        "node": node,
        "ip": ip,
        "ok": ok,
        "host": host if host else None,
        "error": None if ok else (out.stderr.strip() or out.stdout.strip() or "ssh_failed"),
    }


def _remote_s25_heartbeat_candidates(key_path: str | None) -> list[dict[str, Any]]:
    if not key_path:
        return []
    rows: list[dict[str, Any]] = []
    s25_nodes = [pair for pair in NODES if pair[0] == "chimaera"] or NODES
    for node, ip in s25_nodes:
        cmd = [
            "ssh",
            "-i",
            key_path,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=8",
            f"root@{ip}",
            "python3 -c \"from pathlib import Path; p=Path('/opt/agr/state/s25_heartbeat.last'); print(p.read_text(encoding='utf-8', errors='ignore').strip() if p.exists() else 'MISSING')\"",
        ]
        out = None
        exc: Exception | None = None
        for attempt in range(3):
            try:
                out = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=12,
                )
                if out.returncode == 0:
                    break
            except Exception as e:
                exc = e
            if attempt < 2:
                time.sleep(0.8)
        if out is None:
            rows.append(
                {
                    "node": node,
                    "ip": ip,
                    "source": "remote",
                    "present": False,
                    "last_epoch": None,
                    "error": str(exc) if exc else "ssh_exception",
                }
            )
            continue
        raw = (out.stdout or "").strip()
        if out.returncode != 0:
            rows.append(
                {
                    "node": node,
                    "ip": ip,
                    "source": "remote",
                    "present": False,
                    "last_epoch": None,
                    "error": (out.stderr or raw or "ssh_failed").strip(),
                }
            )
            continue
        if raw == "MISSING":
            rows.append(
                {
                    "node": node,
                    "ip": ip,
                    "source": "remote",
                    "present": False,
                    "last_epoch": None,
                    "error": "heartbeat_missing",
                }
            )
            continue
        try:
            last = int(raw)
        except Exception:
            rows.append(
                {
                    "node": node,
                    "ip": ip,
                    "source": "remote",
                    "present": True,
                    "last_epoch": None,
                    "error": "heartbeat_invalid",
                    "raw": raw,
                }
            )
            continue
        rows.append(
            {
                "node": node,
                "ip": ip,
                "source": "remote",
                "present": True,
                "last_epoch": last,
                "error": None,
            }
        )
    return rows


def _s25_channel_status(key_path: str | None) -> dict[str, Any]:
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    candidates: list[dict[str, Any]] = []
    for candidate in HEARTBEAT_CANDIDATES:
        if candidate.exists():
            raw = candidate.read_text(encoding="utf-8", errors="ignore").strip()
            try:
                last = int(raw)
                candidates.append(
                    {
                        "source": "local",
                        "node": "workspace",
                        "path": str(candidate),
                        "present": True,
                        "last_epoch": last,
                        "error": None,
                    }
                )
            except Exception:
                candidates.append(
                    {
                        "source": "local",
                        "node": "workspace",
                        "path": str(candidate),
                        "present": True,
                        "last_epoch": None,
                        "error": "heartbeat_invalid",
                        "raw": raw,
                    }
                )
    candidates.extend(_remote_s25_heartbeat_candidates(key_path))
    present = [c for c in candidates if bool(c.get("present")) and isinstance(c.get("last_epoch"), int)]
    if not present:
        return {
            "heartbeat_present": False,
            "heartbeat_file": None,
            "heartbeat_age_seconds": None,
            "ok": False,
            "reason": "heartbeat_missing_or_invalid",
            "candidates": candidates,
        }
    freshest = min(present, key=lambda c: now_epoch - int(c["last_epoch"]))
    age = max(0, now_epoch - int(freshest["last_epoch"]))
    return {
        "heartbeat_present": True,
        "heartbeat_file": freshest.get("path"),
        "heartbeat_age_seconds": age,
        "ok": age <= 3600,
        "reason": "ok" if age <= 3600 else "heartbeat_stale",
        "selected_source": freshest.get("source"),
        "selected_node": freshest.get("node"),
        "candidates": candidates,
    }


def _charter_status() -> dict[str, Any]:
    payload = _read_json(CHARTER_PATH, {})
    if not isinstance(payload, dict) or not payload:
        return {
            "path": str(CHARTER_PATH),
            "present": False,
            "valid": False,
            "missing": ["file_or_json"],
        }
    required_top = {"constitutional_minimum", "mission_statement", "infrastructure_minimum"}
    missing = [k for k in sorted(required_top) if k not in payload]
    valid = len(missing) == 0
    return {
        "path": str(CHARTER_PATH),
        "present": True,
        "valid": valid,
        "missing": missing,
        "title": payload.get("title"),
        "version": payload.get("version"),
    }


def _consciousness_engine_files_status() -> dict[str, Any]:
    rows = []
    missing: list[str] = []
    for file_path in CONSCIOUSNESS_ENGINE_REQUIRED_FILES:
        present = file_path.exists()
        rows.append({"path": str(file_path), "present": present})
        if not present:
            missing.append(str(file_path))
    return {
        "required": len(CONSCIOUSNESS_ENGINE_REQUIRED_FILES),
        "present": len(CONSCIOUSNESS_ENGINE_REQUIRED_FILES) - len(missing),
        "ok": len(missing) == 0,
        "missing": missing,
        "rows": rows,
    }


def _consciousness_engine_integration_status() -> dict[str, Any]:
    verify = _read_json(ENGINE_VERIFY_LATEST, {})
    verify_present = isinstance(verify, dict) and bool(verify)
    verify_passed = bool(verify.get("passed", False)) if verify_present else False
    try:
        verify_score = float(verify.get("score", 0.0) or 0.0) if verify_present else 0.0
    except Exception:
        verify_score = 0.0
    verify_age = _age_seconds_from_iso(verify.get("checked_at")) if verify_present else None
    if verify_age is None and ENGINE_VERIFY_LATEST.exists():
        try:
            verify_age = max(0, int(datetime.now(timezone.utc).timestamp() - ENGINE_VERIFY_LATEST.stat().st_mtime))
        except Exception:
            verify_age = None
    verify_fresh = verify_age is not None and verify_age <= MAX_ENGINE_VERIFY_AGE_SECONDS
    verify_score_ok = verify_score >= MIN_ENGINE_VERIFY_SCORE

    orch_path = next((p for p in ORCHESTRATOR_STATE_CANDIDATES if p.exists()), ORCHESTRATOR_STATE_CANDIDATES[0])
    orch = _read_json(orch_path, {})
    orch_present = isinstance(orch, dict) and bool(orch)
    orch_enabled = bool(orch.get("enabled", False)) if orch_present else False
    orch_status = str(orch.get("status", "")).strip().lower() if orch_present else ""
    orch_running = orch_status == "running"
    orch_tick_age = _age_seconds_from_iso(orch.get("last_tick_at")) if orch_present else None
    if orch_tick_age is None and Path(orch_path).exists():
        try:
            orch_tick_age = max(0, int(datetime.now(timezone.utc).timestamp() - Path(orch_path).stat().st_mtime))
        except Exception:
            orch_tick_age = None
    orch_tick_fresh = orch_tick_age is not None and orch_tick_age <= MAX_ORCHESTRATOR_TICK_AGE_SECONDS

    runtime_smoke: dict[str, Any]
    try:
        # Prefer live runtime evidence when cached verify artifacts are missing or stale.
        import sys

        workspace = Path("/workspace/aurora_server")
        if str(workspace) not in sys.path:
            sys.path.append(str(workspace))
        from agr_consciousness_core import get_consciousness_core  # type: ignore

        core = get_consciousness_core()
        thought = core.think(
            prompt="Agent minimum gate runtime smoke check.",
            citizen_id="minimum-gate",
            persona={
                "name": "Republic",
                "depth": 0.9,
                "warmth": 0.72,
                "curiosity": 0.85,
                "specialty": "governance",
            },
        )
        runtime_smoke = {
            "ok": bool(thought.get("truth_state")) and thought.get("helix_double_index") is not None,
            "truth_state": thought.get("truth_state"),
            "helix_double_index": thought.get("helix_double_index"),
            "reasoning_operator": thought.get("reasoning_operator"),
        }
    except Exception as exc:
        runtime_smoke = {"ok": False, "error": str(exc)}

    blockers: list[str] = []
    warnings: list[str] = []
    if not verify_present:
        warnings.append("engine_verify_missing")
    if verify_present and not verify_passed:
        warnings.append("engine_verify_not_passed")
    if verify_present and not verify_score_ok:
        warnings.append("engine_verify_score_below_threshold")
    if verify_present and not verify_fresh:
        warnings.append("engine_verify_stale_or_missing")
    # Allow fresh runtime smoke to satisfy integration readiness when cached verify
    # artifacts are stale/missing in this workspace.
    if not verify_present or not verify_fresh:
        if not runtime_smoke.get("ok"):
            blockers.append("engine_runtime_smoke_failed")
    if not orch_present:
        blockers.append("orchestrator_state_missing")
    if not orch_enabled:
        blockers.append("orchestrator_disabled")
    if not orch_running:
        blockers.append("orchestrator_not_running")
    if not orch_tick_fresh:
        blockers.append("orchestrator_tick_stale_or_missing")

    return {
        "ok": len(blockers) == 0,
        "blockers": blockers,
        "warnings": warnings,
        "engine_verify": {
            "path": str(ENGINE_VERIFY_LATEST),
            "present": verify_present,
            "passed": verify_passed,
            "score": round(verify_score, 2),
            "score_threshold": MIN_ENGINE_VERIFY_SCORE,
            "age_seconds": verify_age,
            "max_age_seconds": MAX_ENGINE_VERIFY_AGE_SECONDS,
        },
        "orchestrator": {
            "path": str(orch_path),
            "present": orch_present,
            "enabled": orch_enabled,
            "status": orch_status or None,
            "last_tick_age_seconds": orch_tick_age,
            "max_tick_age_seconds": MAX_ORCHESTRATOR_TICK_AGE_SECONDS,
        },
        "runtime_smoke": runtime_smoke,
    }


def build_report() -> dict[str, Any]:
    key_path = _resolve_fleet_key()
    key_secure, key_mode = _key_security(key_path)
    ctx = GateContext(ssh_key_path=key_path, ssh_key_secure=key_secure, ssh_key_mode=key_mode)

    node_rows: list[dict[str, Any]] = []
    if ctx.ssh_key_path:
        for node, ip in NODES:
            node_rows.append(_ssh_node_check(ctx.ssh_key_path, node, ip))
    else:
        for node, ip in NODES:
            node_rows.append({"node": node, "ip": ip, "ok": False, "host": None, "error": "fleet_key_unresolved"})

    nodes_ok = sum(1 for row in node_rows if bool(row.get("ok")))
    s25 = _s25_channel_status(ctx.ssh_key_path)
    charter = _charter_status()
    consciousness_files = _consciousness_engine_files_status()
    consciousness_integration = _consciousness_engine_integration_status()

    checks = {
        "fleet_key_resolved": bool(ctx.ssh_key_path),
        "fleet_key_secure_permissions": bool(ctx.ssh_key_secure),
        "all_hetzner_nodes_reachable": nodes_ok == len(NODES),
        "s25_transport_channel_fresh": bool(s25.get("ok", False)),
        "library_of_light_charter_present_and_valid": bool(charter.get("valid", False)),
        "consciousness_engine_files_totality_present": bool(consciousness_files.get("ok", False)),
        "consciousness_engine_integration_ready": bool(consciousness_integration.get("ok", False)),
    }
    minimum_pass = all(checks.values())
    return {
        "timestamp": _now(),
        "minimum_pass": minimum_pass,
        "checks": checks,
        "fleet_key": {
            "path": ctx.ssh_key_path,
            "secure_permissions": ctx.ssh_key_secure,
            "mode": ctx.ssh_key_mode,
        },
        "nodes": {
            "required": len(NODES),
            "reachable": nodes_ok,
            "rows": node_rows,
        },
        "s25_transport_channel": s25,
        "library_of_light_charter": charter,
        "consciousness_engine_files": consciousness_files,
        "consciousness_engine_integration": consciousness_integration,
        "policy": {
            "always_first_priorities": [
                "Confirm secure reachability and linkage across all five Hetzner nodes and enrolled Guardian handsets (S25, then OnePlus 15) before any other work.",
                "Confirm consciousness engine totality files and integration status before feature modifications.",
            ],
            "required_surfaces": [
                *[node for node, _ in NODES],
                "s25_ceo_node_transport_channel",
                "consciousness_engine_totality_files",
                "consciousness_engine_integration",
            ],
            "failure_mode": "fail_closed",
        },
    }


def _print_remediation_hints(report: dict[str, Any], *, file) -> None:
    """Non-JSON stderr hints when minimum_pass is false (SSH, phones-only posture, or integration)."""
    checks = report.get("checks") or {}
    hints: list[str] = []
    if not checks.get("fleet_key_resolved"):
        hints.append(
            "Fleet SSH key unresolved — see sovereign/lib/fleet-key-from-secrets-md.sh or run "
            "SKIP_AGENT_MINIMUM_GATE=1 bash sovereign/scripts/run-operator-full-verify.sh without fleet SSH."
        )
    if not checks.get("all_hetzner_nodes_reachable"):
        hints.append(
            "Not all five Hetzner nodes answered SSH — if VMs are intentionally powered off, read "
            "sovereign/PHONES_ONLY_PUBLIC_SURFACE.md §2 (post-poweroff ordered recovery) then §8; check API state with "
            "bash sovereign/scripts/hetzner-fleet-status.sh; public cutover: "
            "bash sovereign/scripts/phones-only-public-verify.sh (after tunnel). "
            "If public smoke WARNs on GET /api/tower (302) while the origin is the handset, same §8 — "
            "git pull the mirror on OnePlus + restart uvicorn (see operator-next-steps-fleet-tower.sh step 8)."
        )
    if (
        checks.get("fleet_key_resolved")
        and checks.get("all_hetzner_nodes_reachable")
        and not checks.get("consciousness_engine_integration_ready")
    ):
        ci = report.get("consciousness_engine_integration") or {}
        blockers = ci.get("blockers") or []
        btxt = ", ".join(str(b) for b in blockers) if blockers else "see JSON consciousness_engine_integration"
        hints.append(
            "SSH baseline passed, but consciousness_engine_integration_ready is false — the gate also "
            "expects fresh engine verify JSON + universal orchestrator state under aurora_server/state/ "
            f"(blockers: {btxt}). On a Cursor/git clone without those runtime files, use "
            "SKIP_AGENT_MINIMUM_GATE=1 for repo-only checks (sovereign/AGENT_MINIMUM_BASELINE.md). "
            "Hetzner peers keep separate on-disk state; SSH green does not imply this workspace has orchestrator JSON."
        )
    if hints:
        print("agent-minimum-gate: remediation hints (stderr; JSON above is the full report):", file=file)
        for h in hints:
            print("  -", h, file=file)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run minimum secure access + mission charter gate.")
    p.add_argument("--latest-out", default=str(DEFAULT_LATEST))
    p.add_argument("--history-out", default=str(DEFAULT_HISTORY))
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    latest_out = Path(str(args.latest_out))
    history_out = Path(str(args.history_out))
    report = build_report()
    _write_json(latest_out, report)
    _append_jsonl(history_out, report)
    print(json.dumps(report, indent=2))
    if not bool(report.get("minimum_pass", False)):
        _print_remediation_hints(report, file=sys.stderr)
    return 0 if bool(report.get("minimum_pass", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
