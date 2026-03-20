#!/usr/bin/env python3
"""
Agent-friendly wrapper for wallapop_scraper.py.
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    scraper = repo_root / "wallapop_scraper.py"
    python_bin = repo_root / "venv" / "bin" / "python"
    python = str(python_bin) if python_bin.exists() else sys.executable
    cmd = [python, str(scraper), *sys.argv[1:]]

    if "--quiet" not in cmd:
        cmd.append("--quiet")

    result = subprocess.run(cmd, cwd=repo_root)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
