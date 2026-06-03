#!/usr/bin/env python3
"""
phase7-guardian-verify.py
-------------------------
Read-only verification for **Phase 7** (REMAINING_WORK_ORDER_OF_OPERATIONS.md):
Guardian OS + device sovereignty — profile resolution, canonical handset identity,
and platform node id alignment with **AGENTS.md** seven-node topology.

Does **not** SSH to devices or read **Secrets.md**. Imports
``agr_guardian_device_binding`` with ``PYTHONPATH=aurora_server``.

Exit codes:
  0 — baseline OK (and strict checks if ``--strict``).
  2 — strict mode failure or invariant violation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ALLOWED_PLATFORM_NODES = frozenset({"iphone_17_pro", "oneplus_15", "s25_ultra"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_aurora_on_path() -> None:
    root = _repo_root()
    aurora = root / "aurora_server"
    p = str(aurora.resolve())
    if p not in sys.path:
        sys.path.insert(0, p)


def _doc_signals() -> dict[str, Any]:
    root = _repo_root()
    agents = (root / "AGENTS.md").is_file()
    gnos = (root / "sovereign" / "GUARDIAN_NODE_OS.md").is_file()
    gbind = (root / "sovereign" / "GUARDIAN_DEVICE_BINDING.md").is_file()
    return {
        "agents_md_present": agents,
        "guardian_node_os_md_present": gnos,
        "guardian_device_binding_md_present": gbind,
        "seven_node_docs_ok": bool(agents and gnos and gbind),
    }


def _profile_signals() -> dict[str, Any]:
    import agr_guardian_device_binding as gdb  # noqa: PLC0415

    path = gdb._default_profile_path()  # type: ignore[attr-defined]
    path_s = str(path) if path else ""
    prof = gdb.load_guardian_device_profile()
    canon = str(prof.get("canonical_device_key") or "").strip()
    node = str(prof.get("platform_node_id") or "").strip().lower()
    wg = str(prof.get("wg_ip") or "").strip()
    return {
        "profile_path": path_s or None,
        "profile_resolved": bool(path and Path(path).is_file()),
        "canonical_device_key_set": bool(canon),
        "platform_node_id": node or None,
        "wg_ip_set": bool(wg),
        "platform_node_allowed": (node in _ALLOWED_PLATFORM_NODES) if node else False,
    }


def build_report() -> dict[str, Any]:
    _ensure_aurora_on_path()
    docs = _doc_signals()
    prof = _profile_signals()
    return {
        "timestamp": _now(),
        "phase": "phase_7_guardian_device_sovereignty_verify",
        "docs": docs,
        "profile": prof,
    }


def _strict_failures(report: dict[str, Any]) -> list[str]:
    bad: list[str] = []
    docs = report.get("docs") or {}
    if not docs.get("seven_node_docs_ok"):
        bad.append("docs:missing_AGENTS_or_GUARDIAN_NODE_OS_or_GUARDIAN_DEVICE_BINDING")
    prof = report.get("profile") or {}
    if not prof.get("profile_resolved"):
        bad.append("profile:no_guardian_device_profile_file_set_AGR_GUARDIAN_DEVICE_PROFILE_PATH_or_fleet_default")
    if not prof.get("canonical_device_key_set"):
        bad.append("profile:canonical_device_key_required_in_JSON_per_GUARDIAN_DEVICE_BINDING")
    pid = prof.get("platform_node_id")
    if not pid:
        bad.append("profile:platform_node_id_missing_set_in_guardian_device_profile_json")
    elif not prof.get("platform_node_allowed"):
        bad.append(f"profile:platform_node_id_invalid:{pid}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 7 Guardian handset sovereignty read-only verify")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Require Guardian profile file + canonical_device_key + platform_node_id (handset)",
    )
    ap.add_argument(
        "--json-out",
        type=str,
        default="",
        help="Write report JSON (default: aurora_server/state/phase7_guardian_signals.latest.json)",
    )
    args = ap.parse_args()
    report = build_report()
    out_default = _repo_root() / "aurora_server" / "state" / "phase7_guardian_signals.latest.json"
    out_path = Path(args.json_out).expanduser() if args.json_out else out_default
    out_path.parent.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    if args.strict:
        failures.extend(_strict_failures(report))

    rc = 0 if not failures else 2
    payload = {**report, "ok": rc == 0, "failures": failures}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
