#!/usr/bin/env python3
"""Repository-authoritative Zeus operational runtime bootstrap."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp.orchestration import (
    MissionOrchestrator,
    OrchestrationError,
    OrchestrationStore,
    canonical_json,
    empty_orchestration_state,
)

QUALIFIED_BASELINE = "a755aeb353639550eb2ffd197e30fc03bccac90b"
RUNTIME_RELATIVE_PATH = Path(".zeus/runtime/orchestration-state.json")
EVIDENCE_RELATIVE_PATH = Path(".zeus/evidence/bootstrap-evidence.json")


def authoritative_state_path(repository_root: Path) -> Path:
    return repository_root.resolve() / RUNTIME_RELATIVE_PATH


def verify_authoritative_path(repository_root: Path) -> Path:
    path = authoritative_state_path(repository_root)
    if path.is_symlink() or (
        path.parent.exists() and path.parent.resolve() != path.parent
    ):
        raise OrchestrationError("authoritative runtime path may not use symbolic links")
    return path


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise OrchestrationError(
            f"repository verification failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bootstrap(repository_root: Path, requested_state: Path | None = None) -> dict[str, Any]:
    root = repository_root.resolve()
    discovered = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    if discovered != root:
        raise OrchestrationError("repository identity mismatch")
    expected = verify_authoritative_path(root)
    if requested_state is not None and requested_state.resolve() != expected:
        raise OrchestrationError(
            f"operational initialization is restricted to {expected}"
        )
    head = _git(root, "rev-parse", "HEAD")
    baseline_check = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", QUALIFIED_BASELINE, head],
        capture_output=True,
        check=False,
    )
    if baseline_check.returncode != 0:
        raise OrchestrationError(
            f"HEAD {head} does not contain qualified baseline {QUALIFIED_BASELINE}"
        )

    created = not expected.exists()
    store = OrchestrationStore(expected)
    if created:
        store.save(empty_orchestration_state())
        os.chmod(expected.parent, 0o700)
        os.chmod(expected, 0o600)

    first = MissionOrchestrator(store)
    first_serialized = canonical_json(first.data)
    # Exercise an atomic write and prove that the on-disk representation reloads
    # to exactly the same logical state.
    store.save(first.data)
    os.chmod(expected, 0o600)
    second = MissionOrchestrator(OrchestrationStore(expected))
    if canonical_json(second.data) != first_serialized:
        raise OrchestrationError("orchestration state deterministic reload failed")

    evidence_path = root / EVIDENCE_RELATIVE_PATH
    evidence = {
        "evidence_type": "zeus-operational-bootstrap",
        "schema_version": 1,
        "repository_root": str(root),
        "qualified_baseline": QUALIFIED_BASELINE,
        "observed_head": head,
        "state_path": str(expected),
        "state_schema_version": second.data["schema_version"],
        "state_sha256": _sha256(expected),
        "created": created,
        "checks": {
            "repository_identity": "PASS",
            "qualified_baseline": "PASS",
            "schema_validation": "PASS",
            "read_write_integrity": "PASS",
            "deterministic_reload": "PASS",
        },
        "operational_readiness": "READY",
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    OrchestrationStore(evidence_path).save(evidence)
    os.chmod(root / ".zeus", 0o700)
    os.chmod(evidence_path.parent, 0o700)
    os.chmod(evidence_path, 0o600)
    return evidence
