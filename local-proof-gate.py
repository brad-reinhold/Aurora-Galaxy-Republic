#!/usr/bin/env python3
"""
local-proof-gate.py
───────────────────
Single-command verifiable gate for sovereign runtime readiness.

Checks:
  - consciousness engine core smoke test
  - S25 heartbeat freshness
  - continuity migration readiness signals
  - cinematic UI baseline artifacts

Writes:
  - <data>/proof_gate_latest.json
  - <data>/proof_gate_latest.md
  - <data>/proof_gate_<timestamp>.json
  - <data>/proof_gate_<timestamp>.md
"""

from __future__ import annotations

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
DATA_DIR = BASE_DIR / "data"
STATE_DIR = Path("/opt/agr/state")
if not STATE_DIR.exists():
    STATE_DIR = BASE_DIR / "state"

HEARTBEAT_FILE = STATE_DIR / "s25_heartbeat.last"
MEMORY_STATE = STATE_DIR / "civilization_memory_state.json"
CONSENTS = STATE_DIR / "continuity_consents.jsonl"
SNAPSHOTS = STATE_DIR / "continuity_snapshots.jsonl"
CONSTITUTION_LOCK = STATE_DIR / "constitution_lock_manifest.json"
BASELINE_CSS = DATA_DIR / "public_aesthetic_baseline.css"
ROLLOUT_JSON = DATA_DIR / "public_cinematic_rollout.json"
MANIFEST_JSON = DATA_DIR / "public_aesthetic_manifest.json"
NODES: list[tuple[str, str]] = [
    ("chimaera", "5.78.184.2"),
    ("yggdrasil", "128.140.45.22"),
    ("enterprise", "91.99.224.166"),
    ("prometheus", "46.62.202.166"),
    ("galactica", "178.104.31.46"),
]


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


def _remote_heartbeat_candidates(key_path: str | None) -> list[dict[str, Any]]:
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


def _continuity_memory_threshold() -> int:
    memory_state = _read_json(MEMORY_STATE, {})
    signatures = memory_state.get("signatures", {}) if isinstance(memory_state, dict) else {}
    estimated = len(signatures) if isinstance(signatures, dict) else 0
    if estimated <= 0:
        return 80
    return max(80, min(250, int(estimated * 0.6)))


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _read_jsonl(path: Path, limit: int = 5000) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines()[-max(1, min(limit, 50000)):]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _engine_check() -> dict[str, Any]:
    try:
        sys.path.append(str(BASE_DIR))
        from agr_consciousness_core import get_consciousness_core  # type: ignore

        core = get_consciousness_core()
        thought = core.think(
            prompt="Proof gate smoke: recursive semantic helix-wave check.",
            citizen_id="republic",
            persona={"name": "Republic", "depth": 0.9, "warmth": 0.72, "curiosity": 0.85, "specialty": "governance"},
        )
        ok = bool(thought.get("truth_state")) and thought.get("helix_double_index") is not None
        return {
            "ok": ok,
            "truth_state": thought.get("truth_state"),
            "helix_double_index": thought.get("helix_double_index"),
            "helix_pair_energy": thought.get("helix_pair_energy"),
            "reasoning_operator": thought.get("reasoning_operator"),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _s25_check() -> dict[str, Any]:
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    candidates: list[dict[str, Any]] = []
    if HEARTBEAT_FILE.exists():
        raw = HEARTBEAT_FILE.read_text(encoding="utf-8", errors="ignore").strip()
        try:
            ts = int(raw)
            candidates.append(
                {
                    "source": "local",
                    "node": "workspace",
                    "path": str(HEARTBEAT_FILE),
                    "present": True,
                    "last_epoch": ts,
                    "error": None,
                }
            )
        except Exception:
            candidates.append(
                {
                    "source": "local",
                    "node": "workspace",
                    "path": str(HEARTBEAT_FILE),
                    "present": True,
                    "last_epoch": None,
                    "error": "heartbeat_invalid",
                    "raw": raw,
                }
            )
    key_path = _resolve_fleet_key()
    candidates.extend(_remote_heartbeat_candidates(key_path))
    valid = [c for c in candidates if bool(c.get("present")) and isinstance(c.get("last_epoch"), int)]
    if not valid:
        return {
            "ok": False,
            "present": False,
            "age_seconds": None,
            "selected_source": None,
            "selected_node": None,
            "reason": "heartbeat_missing_or_invalid",
            "candidates": candidates,
        }
    freshest = min(valid, key=lambda c: now_epoch - int(c["last_epoch"]))
    age = max(0, now_epoch - int(freshest["last_epoch"]))
    return {
        "ok": bool(age <= 600),
        "present": True,
        "age_seconds": age,
        "selected_source": freshest.get("source"),
        "selected_node": freshest.get("node"),
        "reason": "ok" if age <= 600 else "heartbeat_stale",
        "candidates": candidates,
    }


def _continuity_check(s25_transport: dict[str, Any] | None = None) -> dict[str, Any]:
    memory_state = _read_json(MEMORY_STATE, {})
    tracked_files = int(memory_state.get("tracked_files", 0) or 0)
    memory_threshold = _continuity_memory_threshold()
    consent_count = len(_read_jsonl(CONSENTS, 5000))
    snapshot_count = len(_read_jsonl(SNAPSHOTS, 5000))
    constitution_locked = CONSTITUTION_LOCK.exists()

    score = 0
    blockers: list[str] = []
    if constitution_locked:
        score += 20
    else:
        blockers.append("constitution_not_locked")
    if tracked_files >= memory_threshold:
        score += 25
    else:
        blockers.append("memory_ingest_low_or_missing")
    if consent_count >= 1:
        score += 20
    else:
        blockers.append("continuity_consent_missing")
    if snapshot_count >= 2:
        score += 20
    else:
        blockers.append("insufficient_continuity_snapshots")
    s25_ok = bool((s25_transport or {}).get("ok", False))
    s25_age = (s25_transport or {}).get("age_seconds")
    if s25_ok and isinstance(s25_age, int) and s25_age <= 600:
        score += 15
    else:
        blockers.append("s25_heartbeat_stale_or_missing")

    status = "ready" if score >= 80 and "s25_heartbeat_stale_or_missing" not in blockers else (
        "partial" if score >= 45 else "not_ready"
    )
    return {
        "ok": status in {"partial", "ready"},
        "score": score,
        "status": status,
        "blockers": blockers,
        "signals": {
            "constitution_locked": constitution_locked,
            "memory_tracked_files": tracked_files,
            "memory_threshold_min_files": memory_threshold,
            "consent_count": consent_count,
            "snapshot_count": snapshot_count,
        },
    }


def _visual_check() -> dict[str, Any]:
    ok = BASELINE_CSS.exists() and ROLLOUT_JSON.exists() and MANIFEST_JSON.exists()
    return {
        "ok": ok,
        "baseline_css_present": BASELINE_CSS.exists(),
        "rollout_json_present": ROLLOUT_JSON.exists(),
        "manifest_json_present": MANIFEST_JSON.exists(),
    }


def _write_reports(payload: dict[str, Any]) -> dict[str, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_json = DATA_DIR / "proof_gate_latest.json"
    latest_md = DATA_DIR / "proof_gate_latest.md"
    hist_json = DATA_DIR / f"proof_gate_{ts}.json"
    hist_md = DATA_DIR / f"proof_gate_{ts}.md"

    latest_json.write_text(json.dumps(payload, indent=2))
    hist_json.write_text(json.dumps(payload, indent=2))

    lines = [
        "# Sovereign Local Proof Gate",
        "",
        f"- Generated: {payload['timestamp']}",
        f"- Result: **{payload['result']}**",
        "",
        "## Checks",
    ]
    for key, val in payload["checks"].items():
        lines.append(f"- {key}: {'PASS' if val.get('ok') else 'FAIL'}")
        if val.get("blockers"):
            lines.append(f"  - blockers: {', '.join(val['blockers'])}")
        if val.get("error"):
            lines.append(f"  - error: {val['error']}")
    latest_md.write_text("\n".join(lines) + "\n")
    hist_md.write_text("\n".join(lines) + "\n")
    return {
        "latest_json": str(latest_json),
        "latest_md": str(latest_md),
        "history_json": str(hist_json),
        "history_md": str(hist_md),
    }


def main() -> int:
    s25_transport = _s25_check()
    checks = {
        "engine_core": _engine_check(),
        "s25_transport": s25_transport,
        "continuity_migration": _continuity_check(s25_transport=s25_transport),
        "visual_baseline": _visual_check(),
    }
    critical = [name for name in ("engine_core", "s25_transport", "visual_baseline") if not checks[name].get("ok")]
    result = "PASS" if not critical else "FAIL"
    payload = {
        "timestamp": _now(),
        "base_dir": str(BASE_DIR),
        "state_dir": str(STATE_DIR),
        "result": result,
        "critical_failures": critical,
        "checks": checks,
    }
    payload["artifacts"] = _write_reports(payload)
    print(json.dumps(payload, indent=2))
    return 0 if result == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
