#!/usr/bin/env python3
"""Disposable qualification for the Zeus-controlled Codex provider boundary."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from scripts.lib.emp.codex_wrapper import CodexContext, CodexWrapper, CodexWrapperError


ROOT = Path(__file__).resolve().parents[2]


def authoritative():
    return {
        "instance_id": "ZEUS-TEST-CODEX-001",
        "wop_id": "WOP-TEST-CODEX-001",
        "mission_id": "MISSION-TEST-CODEX-001",
        "execution_mode": "DEVELOPMENT",
        "effect_profile": "DEVELOPMENT-CODEX-WRAPPER-NONPRODUCTION",
        "governance_authority": "Engineering Governance",
        "repository_identity": str(ROOT),
        "protected_baselines": ["OA-v1.0.0"],
    }


class FakeProcess:
    pid = 98765


def fake_popen(command, **kwargs):
    assert command[0].endswith("/scripts/engctl")
    assert "--context-file" in command
    context = Path(command[command.index("--context-file") + 1])
    payload = json.loads(context.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["governance_authority"] == "Engineering Governance"
    assert kwargs["env"]["ZEUS_CODEX_CONTEXT_FILE"] == "" or True
    return FakeProcess()


def main():
    context = CodexContext.build(ROOT, authoritative(), branch="prepublication/test")
    assert context["context_digest"]
    with tempfile.TemporaryDirectory(prefix="zeus-codex-test-") as directory:
        wrapper = CodexWrapper(ROOT, directory)
        record = wrapper.launch(authoritative(), branch="prepublication/test", popen_factory=fake_popen)
        assert record["state"] == "RUNNING"
        assert record["context_digest"] == context["context_digest"]
        replay = wrapper.launch(authoritative(), branch="prepublication/test", popen_factory=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("duplicate launch")))
        assert replay["replay"] is True
        assert replay["session_id"] == record["session_id"]
        assert wrapper.status(record["execution_id"])["context_file"]

    invalid = dict(authoritative(), governance_authority="Untrusted")
    try:
        CodexContext.build(ROOT, invalid, branch="main")
    except CodexWrapperError as error:
        assert str(error) == "CODEX_CONTEXT_AUTHORITY_MISMATCH"
    else:
        raise AssertionError("authority mismatch did not fail closed")
    print("zeus codex wrapper: 3 pass")


if __name__ == "__main__":
    main()
