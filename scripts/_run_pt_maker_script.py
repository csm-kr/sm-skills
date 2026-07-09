#!/usr/bin/env python3
"""Run a pt-maker bundled script from the project root."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("ERROR: missing pt-maker script name")

    script_name = sys.argv[1]
    root = Path(__file__).resolve().parents[1]
    target = root / ".codex" / "skills" / "pt-maker" / "scripts" / script_name
    if not target.is_file():
        sys.exit(f"ERROR: pt-maker script not found: {target}")

    sys.argv = [str(target), *sys.argv[2:]]
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
