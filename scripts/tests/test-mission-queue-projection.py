#!/usr/bin/env python3
"""Qualification for the authoritative, read-only mission queue projection."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.eos import mission_knowledge


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    listing = mission_knowledge.queue(ROOT, "list")
    assert listing["authoritative_source"] == mission_knowledge.PATH
    assert listing["metrics"]["submitted"] == 30
    assert listing["metrics"]["completed"] == 30
    assert listing["next_mission"] is None
    assert listing["result"] == "NO_ELIGIBLE_MISSION"

    for view in ("next", "blockers", "history"):
        projection = mission_knowledge.queue(ROOT, view)
        assert projection["entries"] == [] if view != "history" else len(projection["entries"]) == 30

    show = mission_knowledge.queue(ROOT, "show")
    assert len(show["entries"]) == 30
    assert "EMP orchestration store" in show["submission_interface"]

    print("mission queue projection tests: PASS")


if __name__ == "__main__":
    main()
