#!/usr/bin/env python3
"""
wave3-capability-matrix.py
--------------------------
Generates an evidence-backed capability matrix for Wave 3.

This does not invent proof. It marks each capability as:
  - VERIFIED
  - PARTIAL
  - NOT VERIFIED

based only on locally available artifacts.

Topology: the platform is **seven nodes** (five Hetzner + two handsets). Node 6 is **`iphone_17_pro`** (legacy **`s25_ultra`** in sync evidence still counts). **`sync_signals.observed_replication_nodes`** uses canonical node ids (**`s25_ultra:`** keys map to **`iphone_17_pro`**); raw sync_state prefixes are in **`observed_sync_state_prefixes`**. Outputs include
**`seven_node_mesh_replication_coverage`** and **`seven_node_replication_verified`**; legacy
**`six_node_*`** ids remain as stable aliases for older consumers.
"""

from __future__ import annotations

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
DATA_DIR = BASE_DIR / "data"
STATE_DIR = BASE_DIR / "state"

PROOF_GATE = DATA_DIR / "proof_gate_latest.json"
S25_E2E = STATE_DIR / "runtime_e2e_s25_full_stack.latest.json"
OPS_E2E = STATE_DIR / "runtime_e2e_sovereign_ops.latest.json"
LIVE_E2E = STATE_DIR / "runtime_e2e_live_nodes.latest.json"
CONSTITUTION_LOCK = STATE_DIR / "constitution_lock_manifest.json"
PUBLIC_TRUST_CHARTER = DATA_DIR / "PUBLIC_TRUST_CHARTER_20260413.md"
PUBLIC_ACCESS_POLICY = DATA_DIR / "PUBLIC_ACCESS_POLICY_20260413.json"
SYNC_STATE = DATA_DIR / "sync_state.json"

OUT_MD = DATA_DIR / "CAPABILITY_TRACEABILITY_MATRIX_20260414.md"
OUT_JSON = DATA_DIR / "CAPABILITY_TRACEABILITY_MATRIX_LATEST.json"


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _status(ok: bool, partial: bool = False) -> str:
    if ok:
        return "VERIFIED"
    if partial:
        return "PARTIAL"
    return "NOT VERIFIED"


def _live_e2e_summary(payload: dict[str, Any]) -> tuple[int, int]:
    rows = payload.get("results", []) if isinstance(payload.get("results"), list) else []
    total = 0
    ok = 0
    for node in rows:
        checks = node.get("results", []) if isinstance(node, dict) else []
        if not isinstance(checks, list):
            continue
        for entry in checks:
            total += 1
            if isinstance(entry, dict) and bool(entry.get("ok")):
                ok += 1
    return ok, total


def _sync_state_signals(payload: dict[str, Any]) -> dict[str, Any]:
    row = payload if isinstance(payload, dict) else {}
    files = row.get("files", {}) if isinstance(row.get("files"), dict) else {}
    local_node = str(row.get("local_node", "") or "").strip().lower()
    mirror_protocol = str(row.get("mirror_protocol", "") or "").strip().lower()
    chunk_size_mb = int(row.get("chunk_size_mb", 0) or 0)
    observed_prefixes: set[str] = set()
    for key in files.keys():
        text = str(key or "")
        if ":" not in text:
            continue
        node_name = text.split(":", 1)[0].strip().lower()
        if node_name:
            observed_prefixes.add(node_name)
    if local_node == "s25_ultra":
        local_node = "iphone_17_pro"
    expected_nodes = {
        "chimaera",
        "yggdrasil",
        "enterprise",
        "prometheus",
        "galactica",
        "iphone_17_pro",
        "oneplus_15",
    }
    expected_peers = set(expected_nodes)
    if local_node in expected_peers:
        expected_peers.remove(local_node)
    # Canonical peer labels for dashboards: legacy `s25_ultra:` file keys count as node 6 (`iphone_17_pro`).
    observed_replication_nodes: set[str] = set()
    for name in observed_prefixes:
        if name == "s25_ultra":
            observed_replication_nodes.add("iphone_17_pro")
        else:
            observed_replication_nodes.add(name)
    replication_ready = bool(expected_peers) and expected_peers.issubset(observed_replication_nodes)
    mirror_ready = mirror_protocol == "agr_mesh_v1_chunked" and chunk_size_mb >= 20
    return {
        "mirror_protocol": mirror_protocol or None,
        "chunk_size_mb": chunk_size_mb,
        "local_node": local_node or None,
        "observed_sync_state_prefixes": sorted(observed_prefixes),
        "observed_replication_nodes": sorted(observed_replication_nodes),
        "expected_replication_peers": sorted(expected_peers),
        "mirror_protocol_verified": mirror_ready,
        # Canonical seven-node platform (legacy key kept for backward compatibility).
        "seven_node_replication_verified": replication_ready,
        "six_node_replication_verified": replication_ready,
    }


def main() -> int:
    proof = _read_json(PROOF_GATE, {})
    s25 = _read_json(S25_E2E, {})
    ops = _read_json(OPS_E2E, {})
    live = _read_json(LIVE_E2E, {})
    sync_state = _read_json(SYNC_STATE, {})
    live_ok, live_total = _live_e2e_summary(live if isinstance(live, dict) else {})
    sync_signals = _sync_state_signals(sync_state if isinstance(sync_state, dict) else {})

    proof_pass = str(proof.get("result", "")).upper() == "PASS"
    continuity_ready = str(((proof.get("checks", {}) or {}).get("continuity_migration", {}) or {}).get("status", "")).lower() == "ready"
    s25_ops_ready = bool(((s25.get("status", {}) or {}).get("ops_control_plane_ready")))
    constitution_locked = CONSTITUTION_LOCK.exists()
    public_policy_present = PUBLIC_ACCESS_POLICY.exists() and PUBLIC_TRUST_CHARTER.exists()

    matrix = [
        {
            "capability": "control_plane_reliability",
            "status": _status(proof_pass and bool(ops)),
            "evidence": [
                str(PROOF_GATE),
                str(OPS_E2E),
            ],
            "note": "Requires proof gate PASS and ops E2E artifact presence.",
        },
        {
            "capability": "s25_visibility_and_ops_surface",
            "status": _status(s25_ops_ready, partial=bool(s25)),
            "evidence": [
                str(S25_E2E),
            ],
            "note": "S25 E2E present; verified only when ops_control_plane_ready is true.",
        },
        {
            "capability": "live_node_parity_transport",
            "status": _status(live_total > 0 and live_ok == live_total, partial=live_total > 0),
            "evidence": [
                str(LIVE_E2E),
            ],
            "note": f"Observed {live_ok}/{live_total} passing live node checks.",
        },
        {
            "capability": "constitutional_integrity_lock",
            "status": _status(constitution_locked, partial=False),
            "evidence": [
                str(CONSTITUTION_LOCK),
            ],
            "note": "Manifest lock presence indicates constitutional lock materialized.",
        },
        {
            "capability": "public_policy_and_trust_transparency",
            "status": _status(public_policy_present),
            "evidence": [
                str(PUBLIC_ACCESS_POLICY),
                str(PUBLIC_TRUST_CHARTER),
            ],
            "note": "Public policy + trust charter artifacts present.",
        },
        {
            "capability": "continuity_protocol_readiness",
            "status": _status(continuity_ready, partial=proof_pass),
            "evidence": [
                str(PROOF_GATE),
            ],
            "note": "Continuity is partial unless proof continuity_migration status is ready.",
        },
        {
            "capability": "sovereign_mirror_protocol",
            "status": _status(
                bool(sync_signals.get("mirror_protocol_verified", False)),
                partial=bool(sync_signals.get("mirror_protocol")),
            ),
            "evidence": [
                str(SYNC_STATE),
            ],
            "note": (
                "Requires agr_mesh_v1_chunked with >=20MB chunk policy; "
                f"observed protocol={sync_signals.get('mirror_protocol')}, "
                f"chunk_size_mb={sync_signals.get('chunk_size_mb')}."
            ),
        },
        {
            "capability": "seven_node_mesh_replication_coverage",
            "status": _status(
                bool(sync_signals.get("seven_node_replication_verified", False)),
                partial=len(sync_signals.get("observed_replication_nodes", [])) > 0,
            ),
            "evidence": [
                str(SYNC_STATE),
            ],
            "note": (
                "Requires sync evidence to all peer nodes for current local node "
                "(seven-node platform: five Hetzner + two handsets). "
                f"Observed peers={len(sync_signals.get('observed_replication_nodes', []))}/"
                f"{len(sync_signals.get('expected_replication_peers', []))}."
            ),
        },
        {
            "capability": "six_node_mesh_replication_coverage",
            "status": _status(
                bool(sync_signals.get("six_node_replication_verified", False)),
                partial=len(sync_signals.get("observed_replication_nodes", [])) > 0,
            ),
            "evidence": [
                str(SYNC_STATE),
            ],
            "note": (
                "Deprecated capability id (same evidence as seven_node_mesh_replication_coverage); "
                "kept so older dashboards keep working."
            ),
        },
    ]

    verified = sum(1 for row in matrix if row["status"] == "VERIFIED")
    partial = sum(1 for row in matrix if row["status"] == "PARTIAL")
    not_verified = sum(1 for row in matrix if row["status"] == "NOT VERIFIED")

    wave3_signals = {
        "control_plane_reliability_verified": proof_pass and bool(ops),
        "s25_visibility_verified": s25_ops_ready,
        "big_tech_surface_verified": bool(ops) and bool(s25) and live_total > 0 and live_ok == live_total,
        "constitutional_integrity_verified": constitution_locked and public_policy_present,
        "mirror_protocol_verified": bool(sync_signals.get("mirror_protocol_verified", False)),
        "seven_node_replication_verified": bool(sync_signals.get("seven_node_replication_verified", False)),
        "six_node_replication_verified": bool(sync_signals.get("six_node_replication_verified", False)),
    }

    payload = {
        "timestamp": _now(),
        "base_dir": str(BASE_DIR),
        "matrix": matrix,
        "wave3_signals": wave3_signals,
        "sync_signals": sync_signals,
        "summary": {
            "verified": verified,
            "partial": partial,
            "not_verified": not_verified,
            "total": len(matrix),
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2))

    lines = [
        "# Wave 3 Capability Matrix (Evidence-Backed)",
        "",
        f"- Generated: {payload['timestamp']}",
        f"- Verified: {verified}/{len(matrix)}",
        "",
        "| Capability | Status | Evidence | Note |",
        "|---|---|---|---|",
    ]
    for row in matrix:
        evidence = ", ".join(row["evidence"])
        lines.append(f"| {row['capability']} | {row['status']} | `{evidence}` | {row['note']} |")
    OUT_MD.write_text("\n".join(lines) + "\n")

    if os.environ.get("WAVE3_CAPABILITY_MATRIX_QUIET", "").strip().lower() not in ("1", "true", "yes"):
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
