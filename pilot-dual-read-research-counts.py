#!/usr/bin/env python3
"""Legacy entrypoint — delegates to pilot-dual-read-sqlite-counts.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "sovereign" / "scripts" / "pilot-dual-read-sqlite-counts.py"


def main() -> int:
    r = subprocess.run([sys.executable, str(TARGET), *sys.argv[1:]], cwd=str(ROOT))
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
