#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "zeus-publication-boundary-guard"


def run(*args, **env):
    merged = None
    if env:
        merged = {**__import__("os").environ, **env}
    return subprocess.run([sys.executable, str(GUARD), "--repository", str(ROOT), *args], text=True, capture_output=True, env=merged)


def main():
    checks = []
    # The current candidate branch is safe for commit.
    checks.append(run("--operation", "commit", "--target-ref", "refs/heads/prepublication/test").returncode == 0)
    # A clean candidate tree may push only to its explicit candidate ref.
    checks.append(run("--operation", "push", "--target-ref", "refs/heads/prepublication/test").returncode == 0)
    # main publication is fail-closed unless the governed workflow supplies authority.
    checks.append(run("--operation", "push", "--target-ref", "refs/heads/main").returncode != 0)
    checks.append(run("--operation", "push", "--target-ref", "refs/heads/main", ZEUS_PUBLICATION_AUTHORITY="EXPLICIT_GOVERNED_PUBLICATION").returncode != 0)
    assert all(checks), checks
    print("publication boundary guard: 4 assertions passed")


if __name__ == "__main__":
    main()
