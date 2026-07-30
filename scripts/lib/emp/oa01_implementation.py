"""Fail-closed implementation completion assessment for Progressive OA-01."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa


class OA01ImplementationError(ValueError):
    """OA-01 implementation cannot transition to operator verification."""


COMMANDS = (
    "list", "show", "state", "readiness", "eligibility",
    "blockers", "authority", "contract", "next",
)


def _run(root: Path, arguments: list[str], *, environment=None) -> dict[str, Any]:
    result = subprocess.run(
        arguments,
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": arguments,
        "exit_code": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}."
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _evidence_digest(value: dict[str, Any]) -> str:
    material = {key: item for key, item in value.items() if key != "evidence_digest"}
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def qualify(root: Path | str) -> dict[str, Any]:
    """Prove existing OA-01 behavior and persist implementation evidence."""
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-01":
        raise OA01ImplementationError("OA-01 is not the sole active gate")
    gate = state["gates"]["OA-01"]
    if gate["state"] == "AWAITING_OPERATOR_VERIFICATION":
        evidence_path = (
            repository / progressive_oa.PACKAGE_PATH
            / "runtime/evidence/OA-01/IMPLEMENTATION.json"
        )
        if not evidence_path.is_file():
            raise OA01ImplementationError(
                "OA-01 state lacks implementation evidence"
            )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if evidence.get("evidence_digest") != _evidence_digest(evidence):
            raise OA01ImplementationError("OA-01 implementation evidence is invalid")
        return {**progressive_oa.next_action(repository), "implementation": evidence}
    if gate["state"] != "IMPLEMENTATION_REQUIRED":
        raise OA01ImplementationError(
            f"OA-01 implementation cannot resume from {gate['state']}"
        )

    environment = {**os.environ, "ZEUS_TESTING": "1"}
    zeus = str(repository / "scripts/zeus")
    command_evidence: dict[str, Any] = {}
    projection_digest = None
    for action in COMMANDS:
        first = _run(repository, [zeus, "mission", action], environment=environment)
        second = _run(repository, [zeus, "mission", action], environment=environment)
        if first["exit_code"] or second["exit_code"]:
            raise OA01ImplementationError(f"zeus mission {action} failed")
        if first["stdout"] != second["stdout"]:
            raise OA01ImplementationError(
                f"zeus mission {action} is nondeterministic"
            )
        try:
            value = json.loads(first["stdout"])
        except json.JSONDecodeError as error:
            raise OA01ImplementationError(
                f"zeus mission {action} returned invalid JSON"
            ) from error
        command_evidence[action] = {
            key: first[key]
            for key in ("command", "exit_code", "stdout_sha256", "stderr_sha256")
        }
        if action == "show":
            projection_digest = value.get("projection_digest")
            required = {
                "current_mission", "mission_contract", "governance_state",
                "execution_state", "eligibility", "readiness", "blockers",
                "required_approvals", "next_authorized_action", "authority_source",
            }
            if required - set(value):
                raise OA01ImplementationError(
                    "mission projection is incomplete"
                )
            if value["governance_state"] != "AUTHORIZED":
                raise OA01ImplementationError("Mission Contract is not authorized")
            if value["progressive_wop"]["active_gate"] != "OA-01":
                raise OA01ImplementationError("OA-01 is not observable as active")

    checks = {
        "focused_tests": [
            "python3", "-m", "unittest",
            "scripts/tests/test-zeus-oa01-verification.py",
            "scripts/tests/test-zeus-progressive-oa.py",
            "scripts/tests/test-zeus-stage1-runtime.py",
        ],
        "package_integrity": [
            str(
                repository / progressive_oa.PACKAGE_PATH / "verify-package.sh"
            )
        ],
        "repository_health": ["scripts/engctl", "repository", "health"],
        "eos_synchronization": ["scripts/engctl", "eos", "sync-validate"],
        "work_registry": ["scripts/engctl", "registry", "validate"],
    }
    check_evidence = {}
    for name, arguments in checks.items():
        result = _run(repository, arguments, environment=environment)
        check_evidence[name] = {
            key: result[key]
            for key in ("command", "exit_code", "stdout_sha256", "stderr_sha256")
        }
        if result["exit_code"]:
            raise OA01ImplementationError(f"OA-01 check failed: {name}")

    evidence = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-01",
        "result": "IMPLEMENTATION_COMPLETE",
        "projection_digest": projection_digest,
        "commands": command_evidence,
        "checks": check_evidence,
        "authority_boundary": (
            "Implementation evidence does not verify or accept OA-01 and "
            "does not authorize OA-02."
        ),
    }
    evidence["evidence_digest"] = _evidence_digest(evidence)
    evidence_path = (
        repository / progressive_oa.PACKAGE_PATH
        / "runtime/evidence/OA-01/IMPLEMENTATION.json"
    )
    _atomic_json(evidence_path, evidence)

    current = progressive_oa.load_state(repository)
    if (
        current.get("active_gate") != "OA-01"
        or current["gates"]["OA-01"]["state"] != "IMPLEMENTATION_REQUIRED"
    ):
        raise OA01ImplementationError(
            "OA-01 runtime changed during implementation assessment"
        )
    current["gates"]["OA-01"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    current["status"] = "ACTIVE"
    progressive_oa._write_state(repository, current)
    return {**progressive_oa.next_action(repository), "implementation": evidence}
