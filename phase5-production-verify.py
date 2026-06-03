#!/usr/bin/env python3
"""
phase5-production-verify.py
-----------------------------
Read-only verification for **Phase 5** (REMAINING_WORK_ORDER_OF_OPERATIONS.md):
shadow → production integrations — mail queue / SMTP wiring and payments flags.

Does **not** send email, hit Stripe, or require fleet SSH. Imports ``agr_mail`` and
``agr_payments_flags`` from ``aurora_server`` (set ``PYTHONPATH=aurora_server`` or run
from repo root with default path injection below).

Exit codes:
  0 — baseline checks pass (and strict checks if ``--strict``).
  2 — failure (repo payments constant flipped, or strict mode unmet).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def _payments_report() -> dict[str, Any]:
    import agr_payments_flags as pf  # noqa: PLC0415

    const_on = bool(getattr(pf, "PAYMENTS_SURFACES_ENABLED", False))
    runtime_on = bool(pf.payments_surfaces_enabled_runtime())
    webhook = bool(pf.stripe_webhook_secret_configured())
    return {
        "payments_surfaces_repo_constant": const_on,
        "payments_surfaces_runtime": runtime_on,
        "stripe_webhook_secret_configured": webhook,
        "stripe_paths_blocked_when_surfaces_off": bool(pf.stripe_payments_gate_blocks("/api/stripe/webhook")),
    }


def _mail_report() -> dict[str, Any]:
    import agr_mail as mail  # noqa: PLC0415

    status = mail.get_mail_status()
    q = status.get("outbound_queue") if isinstance(status.get("outbound_queue"), dict) else {}
    return {
        "engine": status.get("engine"),
        "smtp_field": status.get("smtp"),
        "outbound_queue_enabled": bool(q.get("enabled")),
        "outbound_queue_path": q.get("path"),
        "outbound_pending": q.get("pending"),
        "flush_http_token_set": bool(os.environ.get("AGR_MAIL_FLUSH_HTTP_TOKEN", "").strip()),
    }


def build_report() -> dict[str, Any]:
    _ensure_aurora_on_path()
    return {
        "timestamp": _now(),
        "phase": "phase_5_production_integrations_verify",
        "payments": _payments_report(),
        "mail": _mail_report(),
    }


def _strict_mail_failures(report: dict[str, Any]) -> list[str]:
    bad: list[str] = []
    mail = report.get("mail") or {}
    if not bool(mail.get("outbound_queue_enabled")):
        bad.append("mail:outbound_queue_not_enabled_set_AGR_MAIL_QUEUE_ENABLED_or_AGR_MAIL_QUEUE_DB")
    if str(mail.get("smtp_field") or "") != "configured_smtp":
        bad.append("mail:smtp_not_configured_set_AGR_SMTP_HOST_and_credentials")
    if not bool(mail.get("flush_http_token_set")):
        bad.append("mail:AGR_MAIL_FLUSH_HTTP_TOKEN_unset_POST_flush_queue_will_403")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 5 production-integration read-only verify")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Require outbound mail queue + SMTP + flush HTTP token (operator fleet)",
    )
    ap.add_argument(
        "--json-out",
        type=str,
        default="",
        help="Write report JSON to this path (default: aurora_server/state/phase5_production_signals.latest.json)",
    )
    args = ap.parse_args()
    report = build_report()
    out_default = _repo_root() / "aurora_server" / "state" / "phase5_production_signals.latest.json"
    out_path = Path(args.json_out).expanduser() if args.json_out else out_default
    out_path.parent.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    pay = report.get("payments") or {}
    if bool(pay.get("payments_surfaces_repo_constant")):
        failures.append("payments:PAYMENTS_SURFACES_ENABLED_must_remain_False_on_main")

    if args.strict:
        failures.extend(_strict_mail_failures(report))

    rc = 0 if not failures else 2

    payload = {**report, "ok": rc == 0, "failures": failures}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
