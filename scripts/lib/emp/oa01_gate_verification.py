"""Fail-closed admitted verification procedure for Progressive OA-01."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.wop_admission import verify_accepted_record
from scripts.lib.eos.mission_contract import Resolver


class OA01GateVerificationError(ValueError):
    """OA-01 cannot be represented as integrity-valid and verified."""


EVIDENCE_NAME = "VERIFICATION.json"
MARKER_NAME = "VERIFIED"
EXPECTED_REMOTE = "git@github.com:lqoneal/homelab-infrastructure.git"
VALIDATION_COMMANDS = {
    "focused_regression": [
        "python3", "-m", "unittest",
        "scripts/tests/test-zeus-oa01-verification.py",
        "scripts/tests/test-zeus-oa01-implementation.py",
        "scripts/tests/test-zeus-progressive-oa.py",
        "scripts/tests/test-zeus-stage1-runtime.py",
    ],
    "repository_health": ["scripts/engctl", "repository", "health"],
    "eos_synchronization": ["scripts/engctl", "eos", "sync-validate"],
    "registry_validation": ["scripts/engctl", "registry", "validate"],
    "full_validation": ["scripts/engctl", "validate"],
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_digest(value: dict[str, Any], omitted: str) -> str:
    material = {key: item for key, item in value.items() if key != omitted}
    return _sha256_bytes(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    )


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA01GateVerificationError(f"cannot load {path}: {error}") from error
    if not isinstance(value, dict):
        raise OA01GateVerificationError(f"{path} must contain an object")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise OA01GateVerificationError(f"cannot load {path}: {error}") from error
    if not isinstance(value, dict):
        raise OA01GateVerificationError(f"{path} must contain a mapping")
    return value


def _run(root: Path, arguments: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        arguments, cwd=root, env={**os.environ, "ZEUS_TESTING": "1"},
        text=True, capture_output=True, check=False,
    )
    return {
        "command": arguments,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "stdout_sha256": _sha256_bytes(result.stdout.encode()),
        "stderr_sha256": _sha256_bytes(result.stderr.encode()),
    }


def _git(root: Path, *arguments: str) -> str:
    result = _run(root, ["git", "-C", str(root), *arguments])
    if result["exit_code"]:
        raise OA01GateVerificationError(
            result["stderr"].strip() or f"git {' '.join(arguments)} failed"
        )
    return result["stdout"].strip()


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
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _inventory(root: Path) -> dict[str, Any]:
    raw = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    paths = []
    for record in raw.split("\0"):
        if not record:
            continue
        relative = record[3:]
        path = root / relative
        paths.append({
            "status": record[:2],
            "path": relative,
            "sha256": _sha256(path) if path.is_file() else None,
        })
    paths.sort(key=lambda item: (item["path"], item["status"]))
    return {
        "entries": paths,
        "digest": _sha256_bytes(
            json.dumps(paths, sort_keys=True, separators=(",", ":")).encode()
        ),
    }


def _without_verification_artifacts(inventory: dict[str, Any]) -> list[dict[str, str]]:
    evidence_prefix = str(progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-01/")
    return [
        item for item in inventory["entries"]
        if not item["path"].startswith(evidence_prefix)
    ]


def _bindings(root: Path) -> dict[str, Any]:
    package = root / progressive_oa.PACKAGE_PATH
    wop = _yaml(package / "immutable-wop.yaml")
    resolution = Resolver(root).resolve()
    contract = resolution.get("contract")
    if resolution.get("resolution") != "AUTHORIZED" or not isinstance(contract, dict):
        raise OA01GateVerificationError("Mission Contract is not authorized")
    contract_path = root / str(resolution.get("contract_path", ""))
    if contract.get("lifecycle") != "active":
        raise OA01GateVerificationError("Mission Contract is not active")
    expected = contract.get("repository", {})
    observed_root = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    remote = _git(root, "remote", "get-url", "origin")
    upstream = _git(root, "rev-parse", "@{upstream}")
    baseline = str(wop.get("execution_context", {}).get("qualified_baseline", ""))
    if observed_root != root:
        raise OA01GateVerificationError("unexpected repository root")
    if expected.get("identity") != root.name:
        raise OA01GateVerificationError("repository identity mismatch")
    if Path(str(expected.get("root", ""))).resolve() != root:
        raise OA01GateVerificationError("Mission Contract repository root mismatch")
    if branch != wop.get("execution_context", {}).get("branch"):
        raise OA01GateVerificationError("branch does not match admitted WOP")
    if branch != expected.get("branch"):
        raise OA01GateVerificationError("branch does not match Mission Contract")
    if remote != expected.get("remote") or remote != EXPECTED_REMOTE:
        raise OA01GateVerificationError("repository remote identity mismatch")
    if head != upstream:
        raise OA01GateVerificationError("HEAD is not synchronized with upstream")
    if len(baseline) != 40:
        raise OA01GateVerificationError("qualified baseline is malformed")
    ancestor = _run(
        root, ["git", "-C", str(root), "merge-base", "--is-ancestor", baseline, head]
    )
    if ancestor["exit_code"]:
        raise OA01GateVerificationError("qualified baseline is not an ancestor of HEAD")
    return {
        "repository_identity": root.name,
        "repository_root": str(root),
        "branch": branch,
        "head": head,
        "upstream": upstream,
        "remote": remote,
        "qualified_baseline": baseline,
        "authority_source": str(contract_path.relative_to(root)),
        "authority_digest": _sha256(contract_path),
        "mission_id": contract.get("mission_id"),
        "contract_id": contract.get("contract_id"),
        "wop_id": wop.get("wop_id"),
        "wop_digest": _sha256(package / "immutable-wop.yaml"),
    }


def _validate_state(root: Path) -> None:
    state = progressive_oa.load_state(root)
    if state.get("active_gate") != "OA-01":
        raise OA01GateVerificationError("OA-01 is not the sole active gate")
    if state.get("gates", {}).get("OA-01", {}).get("state") != (
        "AWAITING_OPERATOR_VERIFICATION"
    ):
        raise OA01GateVerificationError("OA-01 is not awaiting operator verification")
    for gate_id, gate in state["gates"].items():
        if gate_id != "OA-01" and (
            gate.get("state") != "PENDING"
            or gate.get("acceptance_receipt") is not None
        ):
            raise OA01GateVerificationError(
                f"unexpected later-gate activity: {gate_id}"
            )
    if state["gates"]["OA-01"].get("acceptance_receipt") is not None:
        raise OA01GateVerificationError("OA-01 acceptance already exists")


def _validate_implementation(root: Path) -> tuple[Path, dict[str, Any]]:
    path = (
        root / progressive_oa.PACKAGE_PATH
        / "runtime/evidence/OA-01/IMPLEMENTATION.json"
    )
    value = _json(path)
    if value.get("result") != "IMPLEMENTATION_COMPLETE":
        raise OA01GateVerificationError("implementation evidence is incomplete")
    if value.get("evidence_digest") != _canonical_digest(value, "evidence_digest"):
        raise OA01GateVerificationError("implementation evidence checksum failure")
    return path, value


def _current_material(root: Path) -> dict[str, Any]:
    package = root / progressive_oa.PACKAGE_PATH
    admission_path = package / (
        "admission/ADMISSION-f01c0c2d-8edb-5567-ad19-8d0f4344909f.json"
    )
    wop = _yaml(package / "immutable-wop.yaml")
    if not verify_accepted_record(
        admission_path, expected_repository=str(root),
        expected_wop=str(wop.get("wop_id")),
    ):
        raise OA01GateVerificationError("package admission receipt integrity failure")
    _validate_state(root)
    implementation_path, implementation = _validate_implementation(root)
    return {
        "bindings": _bindings(root),
        "package_manifest_digest": _sha256(package / "MANIFEST.sha256"),
        "admission_receipt": str(admission_path.relative_to(root)),
        "admission_digest": _sha256(admission_path),
        "implementation_evidence": str(implementation_path.relative_to(root)),
        "implementation_digest": implementation["evidence_digest"],
        "working_tree": _inventory(root),
    }


def validate_marker(root: Path | str) -> dict[str, Any]:
    """Validate the marker against current authority, evidence, and Git state."""
    repository = Path(root).resolve()
    directory = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-01"
    marker = _json(directory / MARKER_NAME)
    evidence = _json(directory / EVIDENCE_NAME)
    if evidence.get("evidence_digest") != _canonical_digest(evidence, "evidence_digest"):
        raise OA01GateVerificationError("OA-01 verification evidence integrity failure")
    if marker.get("marker_digest") != _canonical_digest(marker, "marker_digest"):
        raise OA01GateVerificationError("OA-01 marker integrity failure")
    if marker.get("evidence_digest") != evidence.get("evidence_digest"):
        raise OA01GateVerificationError("OA-01 marker evidence binding mismatch")
    current = _current_material(repository)
    expected = evidence.get("authoritative_inputs")
    # Publishing the two verification artifacts is the only allowed inventory delta.
    if not isinstance(expected, dict) or (
        {key: value for key, value in expected.items() if key != "working_tree"}
        != {key: value for key, value in current.items() if key != "working_tree"}
        or _without_verification_artifacts(expected["working_tree"])
        != _without_verification_artifacts(current["working_tree"])
    ):
        raise OA01GateVerificationError("OA-01 verification is stale")
    bindings = current["bindings"]
    required = {
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-01",
        "repository_identity": bindings["repository_identity"],
        "repository_root": bindings["repository_root"],
        "branch": bindings["branch"],
        "head": bindings["head"],
        "authority_source": bindings["authority_source"],
        "evidence_digest": evidence["evidence_digest"],
        "verification_timestamp": evidence["verification_timestamp"],
        "verification_result": "PASS",
    }
    if any(marker.get(key) != value for key, value in required.items()):
        raise OA01GateVerificationError("OA-01 marker binding mismatch")
    return marker


def verify(root: Path | str) -> dict[str, Any]:
    """Execute the admitted OA-01 verification and publish evidence atomically."""
    repository = Path(root).resolve()
    directory = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-01"
    marker_path = directory / MARKER_NAME
    evidence_path = directory / EVIDENCE_NAME
    if marker_path.is_file():
        try:
            marker = validate_marker(repository)
        except OA01GateVerificationError:
            stale_marker = _json(marker_path)
            identity = str(stale_marker.get("marker_digest", _sha256(marker_path)))
            archive = directory / "attempts" / identity
            archive.mkdir(parents=True, exist_ok=True)
            archived_marker = archive / MARKER_NAME
            archived_evidence = archive / EVIDENCE_NAME
            if archived_marker.exists() or archived_evidence.exists():
                raise OA01GateVerificationError(
                    "stale verification archive identity collision"
                )
            os.replace(marker_path, archived_marker)
            if evidence_path.is_file():
                os.replace(evidence_path, archived_evidence)
        else:
            return _result(repository, marker_path, marker["evidence_digest"], True)

    starting = _current_material(repository)
    preflight = _run(
        repository,
        [str(repository / progressive_oa.PACKAGE_PATH / "verify-package.sh")],
    )
    if preflight["exit_code"]:
        raise OA01GateVerificationError("package integrity verification failed")

    zeus = str(repository / "scripts/zeus")
    results: dict[str, Any] = {"package_integrity": preflight}
    for command in (
        ["gate", "show", "OA-01"], ["gate", "objective", "OA-01"],
        ["gate", "evidence", "OA-01"], ["mission", "show"],
        ["mission", "readiness"], ["mission", "blockers"], ["mission", "next"],
    ):
        name = "_".join(command)
        first = _run(repository, [zeus, *command])
        second = _run(repository, [zeus, *command])
        if first["exit_code"] or second["exit_code"]:
            raise OA01GateVerificationError(f"Zeus check failed: {' '.join(command)}")
        if first["stdout"] != second["stdout"]:
            raise OA01GateVerificationError(
                f"Zeus replay is nondeterministic: {' '.join(command)}"
            )
        try:
            json.loads(first["stdout"])
        except json.JSONDecodeError as error:
            raise OA01GateVerificationError(
                f"Zeus returned malformed JSON: {' '.join(command)}"
            ) from error
        results[name] = first

    negative = _run(repository, [zeus, "mission", "show", "UNKNOWN-OA01-MISSION"])
    if negative["exit_code"] == 0:
        raise OA01GateVerificationError("unknown mission selector unexpectedly succeeded")
    results["negative_unknown_mission"] = negative
    for name, arguments in VALIDATION_COMMANDS.items():
        result = _run(repository, arguments)
        results[name] = result
        if result["exit_code"]:
            raise OA01GateVerificationError(f"OA-01 check failed: {name}")

    ending = _current_material(repository)
    if _without_verification_artifacts(starting["working_tree"]) != (
        _without_verification_artifacts(ending["working_tree"])
    ):
        raise OA01GateVerificationError("unexplained working-tree mutation")
    if {
        key: value for key, value in starting.items() if key != "working_tree"
    } != {
        key: value for key, value in ending.items() if key != "working_tree"
    }:
        raise OA01GateVerificationError("authoritative inputs changed during verification")

    evidence = {
        "schema_version": 1,
        "handoff_id": "ZH-OA01-VERIFICATION-CORRECTIVE-004",
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-01",
        "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": ending,
        "commands": results,
        "assertions": {
            "positive": "PASS",
            "negative_fail_closed": "PASS",
            "replay": "PASS",
            "interruption_recovery": "PASS",
            "cumulative_regression_through": "OA-01",
            "controlled_record_reconciliation": "PASS",
            "operator_acceptance_recorded": False,
            "next_gate_enabled": False,
        },
    }
    evidence["evidence_digest"] = _canonical_digest(evidence, "evidence_digest")
    _atomic_json(evidence_path, evidence)
    if os.environ.get("ZEUS_OA01_INTERRUPT_BEFORE_MARKER") == "1":
        raise OA01GateVerificationError("verification interrupted before marker publication")
    marker = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-01",
        "repository_identity": ending["bindings"]["repository_identity"],
        "repository_root": ending["bindings"]["repository_root"],
        "branch": ending["bindings"]["branch"],
        "head": ending["bindings"]["head"],
        "authority_source": ending["bindings"]["authority_source"],
        "evidence_digest": evidence["evidence_digest"],
        "verification_timestamp": evidence["verification_timestamp"],
        "verification_result": "PASS",
    }
    marker["marker_digest"] = _canonical_digest(marker, "marker_digest")
    _atomic_json(marker_path, marker)
    validate_marker(repository)
    return _result(repository, marker_path, evidence["evidence_digest"], False)


def _result(
    root: Path, marker: Path, evidence_digest: str, replay: bool
) -> dict[str, Any]:
    return {
        "gate_id": "OA-01",
        "result": "PASS",
        "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
        "marker": str(marker.relative_to(root)),
        "evidence_digest": evidence_digest,
        "idempotent_replay": replay,
        "operator_acceptance_recorded": False,
        "next_gate_enabled": False,
    }
