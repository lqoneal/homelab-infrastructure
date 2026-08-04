"""Deterministic baseline-only admission supersession for Development execution."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.authority_resolution import digest
from scripts.lib.emp.mission_admission_runtime import AdmissionStateStore, MissionAdmissionError
from scripts.lib.emp.mission_execution_runtime import ExecutionStateStore, MissionExecutionError


class AdmissionSupersessionError(ValueError):
    """A stale admission cannot be safely superseded."""


def _authoritative_stage1_package_digest(record: Mapping[str, Any]) -> str:
    """Return the immutable package digest, checking its receipt lineage."""
    receipts = record.get("receipts") or {}
    candidates = [("transaction.package_digest", record.get("package_digest"))]
    for name in ("packaging", "registration", "dispatch"):
        receipt = receipts.get(name) or {}
        if receipt.get("package_digest") is not None:
            candidates.append((f"receipts.{name}.package_digest", receipt["package_digest"]))
    present = [(name, value) for name, value in candidates if value is not None]
    if not present:
        raise AdmissionSupersessionError("Stage 1 package digest is absent")
    expected = present[0][1]
    for name, value in present[1:]:
        if value != expected:
            raise AdmissionSupersessionError(
                f"package digest differs within Stage 1: expected={expected} observed={value} source={name}"
            )
    return expected


def _validate_lineage_package_digest(admission: Mapping[str, Any], expected: str) -> None:
    """Validate only fields that claim to bind the immutable package."""
    artifacts = admission.get("artifacts") or {}
    wop_result = artifacts.get("wop_result") or {}
    wop = wop_result.get("wop") or {}
    authority_context = artifacts.get("authority_context") or {}
    bindings = (
        ("admission.stage1_package_digest", admission.get("stage1_package_digest")),
        ("admission.package_digest", admission.get("package_digest")),
        ("admission.artifacts.wop_result.wop.package_digest", wop.get("package_digest")),
        ("admission.artifacts.authority_context.wop.package_digest", (authority_context.get("wop") or {}).get("package_digest")),
        ("admission.artifacts.authority_context.package_digest", authority_context.get("package_digest")),
    )
    present = [(name, value) for name, value in bindings if value is not None]
    if not present:
        raise AdmissionSupersessionError("admission package binding is absent")
    for name, value in present:
        if value != expected:
            raise AdmissionSupersessionError(
                f"package digest differs from Stage 1: expected={expected} observed={value} source={name}"
            )


def _authoritative_stage1_source_digest(record: Mapping[str, Any]) -> str:
    """Resolve source identity from Stage 1 receipts before generic fields."""
    receipts = record.get("receipts") or {}
    candidates = []
    validation = receipts.get("validation") or {}
    if validation.get("source_digest") is not None:
        candidates.append(("receipts.validation.source_digest", validation["source_digest"]))
    if record.get("source_digest") is not None:
        candidates.append(("transaction.source_digest", record["source_digest"]))
    if not candidates:
        raise AdmissionSupersessionError("Stage 1 source digest is absent")
    expected = candidates[0][1]
    for name, value in candidates[1:]:
        if value != expected:
            raise AdmissionSupersessionError(
                f"source digest differs within Stage 1: expected={expected} observed={value} source={name}"
            )
    return expected


def _validate_lineage_source_digest(admission: Mapping[str, Any], expected: str) -> None:
    """Validate present canonical and generic source bindings independently."""
    artifacts = admission.get("artifacts") or {}
    source_binding = artifacts.get("source_binding") or {}
    bindings = (
        ("admission.stage1_source_digest", admission.get("stage1_source_digest")),
        ("admission.artifacts.stage1_source_digest", artifacts.get("stage1_source_digest")),
        ("admission.artifacts.source_binding.source_digest", source_binding.get("source_digest")),
        ("admission.source_digest", admission.get("source_digest")),
    )
    for name, value in bindings:
        if value is not None and value != expected:
            raise AdmissionSupersessionError(
                f"source digest differs from Stage 1: expected={expected} observed={value} source={name}"
            )


def _validate_execution_source_digest(projection: Mapping[str, Any], expected: str) -> None:
    """Validate source fields on a derived or migrated execution projection."""
    for name in ("stage1_source_digest", "source_digest"):
        value = projection.get(name)
        if value is not None and value != expected:
            raise AdmissionSupersessionError(
                f"source digest differs from Stage 1: expected={expected} observed={value} source=execution.{name}"
            )


ALLOWED_TRANSITION_PATHS = (
    "scripts/zeus",
    "scripts/lib/emp/mission_execution_runtime.py",
    "scripts/lib/emp/stage1_execution_resolution.py",
    "scripts/lib/emp/admission_supersession.py",
    "scripts/tests/",
    "engineering/evidence/operation-beta/",
    "engineering/work-orders/WOP-ZEUS-STOP-DISPOSABLE-QUALIFICATION-001/",
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise AdmissionSupersessionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _git_bool(root: Path, *args: str) -> bool:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True).returncode == 0


def classify_transition(root: Path | str, admitted_baseline: str, *, published_baseline: str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    if _git(root, "status", "--porcelain"):
        raise AdmissionSupersessionError("working tree is dirty")
    current = _git(root, "rev-parse", "HEAD")
    published = published_baseline or _git(root, "rev-parse", "origin/main")
    if current != published:
        raise AdmissionSupersessionError("local and published repository states differ")
    if not _git_bool(root, "merge-base", "--is-ancestor", admitted_baseline, current):
        raise AdmissionSupersessionError("current baseline is not a descendant of admitted baseline")
    merge_base = _git(root, "merge-base", admitted_baseline, current)
    if merge_base != admitted_baseline:
        raise AdmissionSupersessionError("baseline transition is ambiguous")
    names = [item for item in _git(root, "diff", "--name-only", admitted_baseline, current).splitlines() if item]
    unauthorized = [item for item in names if not any(item == prefix or item.startswith(prefix) for prefix in ALLOWED_TRANSITION_PATHS)]
    if unauthorized:
        raise AdmissionSupersessionError("transition contains unauthorized implementation effects: " + ", ".join(unauthorized))
    commits = []
    for line in _git(root, "log", "--format=%H%x09%s", "--reverse", f"{admitted_baseline}..{current}").splitlines():
        commit, subject = line.split("\t", 1)
        commits.append({"commit": commit, "subject": subject})
    return {"admitted_baseline": admitted_baseline, "current_baseline": current,
            "published_baseline": published, "merge_base": merge_base,
            "commits": commits, "paths": names, "classification": "GOVERNED_BASELINE_RECONCILIATION"}


def _successor_id(transaction_id: str, current: str, package_digest: str | None, authority_digest: str | None) -> str:
    material = {"transaction_id": transaction_id, "current_baseline": current,
                "package_digest": package_digest, "authority_snapshot_digest": authority_digest}
    return "EMM-DEV-ADMISSION-" + hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]


def _receipt(predecessor: Mapping[str, Any], successor_id: str, transition: Mapping[str, Any]) -> dict[str, Any]:
    value = {"receipt_type": "ADMISSION_SUPERSESSION", "predecessor_admission_id": predecessor["admission_id"],
             "successor_admission_id": successor_id, "transaction_id": predecessor.get("stage1_identity") or predecessor.get("request", {}).get("submission_id"),
             "admitted_baseline": transition["admitted_baseline"], "current_baseline": transition["current_baseline"],
             "classification": transition["classification"]}
    value["receipt_id"] = "EMM-ADMISSION-SUPERSESSION-" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
    value["receipt_digest"] = digest(value)
    return value


def _atomic_json_updates(updates: Mapping[Path, Mapping[str, Any]]) -> None:
    originals = {path: path.read_bytes() if path.exists() else None for path in updates}
    temps: list[Path] = []
    installed: list[Path] = []
    try:
        for path, value in updates.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, raw = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
            temp = Path(raw); temps.append(temp)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(json.dumps(dict(value), indent=2, sort_keys=True) + "\n")
                stream.flush(); os.fsync(stream.fileno())
        for temp, path in zip(temps, updates):
            os.replace(temp, path); installed.append(path)
    except Exception as error:
        for path in installed:
            original = originals[path]
            if original is None: path.unlink(missing_ok=True)
            else: path.write_bytes(original)
        raise AdmissionSupersessionError(f"admission supersession persistence rolled back: {error}") from error
    finally:
        for temp in temps: temp.unlink(missing_ok=True)


def resolve_for_start(root: Path | str, admission_store: Path | str, execution_store: Path | str,
                      admission_id: str, *, stage1_transaction: Mapping[str, Any] | None = None,
                      published_baseline: str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    admissions = AdmissionStateStore(admission_store)
    executions = ExecutionStateStore(execution_store)
    try:
        predecessor = admissions.load(admission_id)
    except MissionAdmissionError as error:
        raise AdmissionSupersessionError(str(error)) from error
    if predecessor.get("admission_state") == "SUPERSEDED":
        successor_id = predecessor.get("superseded_by")
        if not successor_id:
            raise AdmissionSupersessionError("superseded admission has no successor")
        successor = admissions.load(successor_id)
        current = _git(root, "rev-parse", "HEAD")
        if successor.get("request", {}).get("repository_baseline") != current:
            raise AdmissionSupersessionError("successor admission baseline is stale")
        transition = classify_transition(root, predecessor.get("artifacts", {}).get("repository_baseline"),
                                         published_baseline=published_baseline)
        return {"admission_id": successor_id, "predecessor": predecessor, "successor": successor,
                "replayed": True, "transition": transition}
    admitted = predecessor.get("artifacts", {}).get("repository_baseline")
    current = _git(root, "rev-parse", "HEAD")
    if admitted == current:
        return {"admission_id": admission_id, "predecessor": predecessor, "successor": predecessor, "replayed": False}
    if not stage1_transaction:
        raise AdmissionSupersessionError("authoritative Stage 1 transaction is unavailable")
    if stage1_transaction.get("instance_id") != predecessor.get("stage1_identity") and stage1_transaction.get("instance_id") != predecessor.get("request", {}).get("submission_id"):
        raise AdmissionSupersessionError("Stage 1 transaction identity does not bind predecessor admission")
    package_digest = _authoritative_stage1_package_digest(stage1_transaction)
    _validate_lineage_package_digest(predecessor, package_digest)
    authority_digest = predecessor.get("authority_snapshot_digest") or (stage1_transaction.get("authority_snapshot") or {}).get("authority_snapshot_digest")
    if stage1_transaction.get("package_digest") and package_digest != stage1_transaction.get("package_digest"):
        raise AdmissionSupersessionError("package digest differs from Stage 1")
    transition = classify_transition(root, admitted, published_baseline=published_baseline)
    successor_id = _successor_id(stage1_transaction["instance_id"], current, package_digest, authority_digest)
    successor_path = admissions.path(successor_id)
    if successor_path.exists():
        existing = admissions.load(successor_id)
        if existing.get("supersedes") != admission_id or existing.get("request", {}).get("repository_baseline") != current:
            raise AdmissionSupersessionError("conflicting successor admission exists")
        return {"admission_id": successor_id, "predecessor": predecessor, "successor": existing, "replayed": True}
    receipt = _receipt(predecessor, successor_id, transition)
    successor = deepcopy(predecessor)
    successor["admission_id"] = successor_id
    successor["supersedes"] = admission_id
    successor["transaction_id"] = stage1_transaction["instance_id"]
    successor["supersession_receipt"] = receipt
    successor["request"]["repository_baseline"] = current
    successor["request_digest"] = digest(successor["request"])
    successor["artifacts"]["repository_baseline"] = current
    successor["artifacts"].setdefault("repository", {})["baseline_commit"] = current
    successor["package_digest"] = package_digest
    successor["stage1_package_digest"] = package_digest
    if predecessor.get("source_digest") is not None:
        successor["source_digest"] = predecessor["source_digest"]
    successor["stage1_source_digest"] = _authoritative_stage1_source_digest(stage1_transaction)
    successor["authority_snapshot_digest"] = authority_digest
    successor["artifacts"]["freshness"] = {"admitted_baseline": admitted, "current_baseline": current, "fresh": True}
    successor["admission_state"] = "ADMITTED"
    successor["status"] = "DECIDED"
    successor.pop("state_digest", None); successor["state_digest"] = digest(successor)
    predecessor_updated = deepcopy(predecessor)
    predecessor_updated["status"] = "SUPERSEDED"; predecessor_updated["admission_state"] = "SUPERSEDED"
    predecessor_updated["superseded_by"] = successor_id
    predecessor_updated["supersession_receipt"] = receipt
    predecessor_updated.pop("state_digest", None); predecessor_updated["state_digest"] = digest(predecessor_updated)
    updates: dict[Path, Mapping[str, Any]] = {admissions.path(admission_id): predecessor_updated, successor_path: successor}
    matching = []
    for path in sorted(executions.directory.glob("*.json")):
        try: value = executions.load(path.stem)
        except MissionExecutionError as error: raise AdmissionSupersessionError(str(error)) from error
        if value.get("admission_id") == admission_id: matching.append((path, value))
    if len(matching) > 1:
        raise AdmissionSupersessionError("multiple executions are bound to predecessor admission")
    if matching:
        path, execution = matching[0]
        execution["admission_id"] = successor_id; execution["repository_baseline"] = current
        execution.pop("state_digest", None); execution["state_digest"] = digest(execution)
        updates[path] = execution
    _atomic_json_updates(updates)
    return {"admission_id": successor_id, "predecessor": predecessor_updated, "successor": successor,
            "execution_rebound": bool(matching), "replayed": False, "transition": transition}


def resolve_for_resume(root: Path | str, admission_store: Path | str,
                       requested_admission_id: str, *,
                       stage1_transaction: Mapping[str, Any],
                       enforce_environment: bool = True) -> dict[str, Any]:
    """Resolve a Stage 1 admission through immutable supersession lineage.

    Resume is deliberately read-only: unlike ``resolve_for_start`` it never
    creates or rewrites an admission or execution projection.  The original
    receipt admission and every successor must bind the same transaction and
    immutable evidence before the terminal current admission is returned.
    """
    root = Path(root).resolve()
    admissions = AdmissionStateStore(admission_store)
    transaction_id = stage1_transaction.get("instance_id")
    if not transaction_id:
        raise AdmissionSupersessionError("Stage 1 transaction identity is missing")
    receipt_admission_id = (stage1_transaction.get("receipts") or {}).get("admission", {}).get("admission_id")
    if not receipt_admission_id:
        raise AdmissionSupersessionError("Stage 1 admission receipt is missing")

    try:
        predecessor = admissions.load(receipt_admission_id)
    except MissionAdmissionError as error:
        raise AdmissionSupersessionError(str(error)) from error

    current_baseline = _git(root, "rev-parse", "HEAD")
    if enforce_environment:
        published_baseline = _git(root, "rev-parse", "origin/main")
        if current_baseline != published_baseline:
            raise AdmissionSupersessionError("local and published repository states differ")
        if _git(root, "status", "--porcelain"):
            raise AdmissionSupersessionError("working tree is dirty")

    package_digest = _authoritative_stage1_package_digest(stage1_transaction)
    source_digest = _authoritative_stage1_source_digest(stage1_transaction)
    authority_digest = (stage1_transaction.get("authority_snapshot") or {}).get("authority_snapshot_digest")
    chain: list[dict[str, Any]] = []
    visited: set[str] = set()
    value = predecessor
    while True:
        admission_id = value.get("admission_id")
        if not admission_id or admission_id in visited:
            raise AdmissionSupersessionError("admission supersession lineage is circular")
        visited.add(admission_id)
        if value.get("stage1_identity") not in (None, transaction_id) and value.get("transaction_id") != transaction_id:
            raise AdmissionSupersessionError("admission lineage transaction binding differs from Stage 1")
        if value.get("transaction_id") not in (None, transaction_id) and value.get("request", {}).get("submission_id") != transaction_id:
            raise AdmissionSupersessionError("admission lineage transaction binding differs from Stage 1")
        _validate_lineage_package_digest(value, package_digest)
        _validate_lineage_source_digest(value, source_digest)
        if authority_digest is not None and value.get("authority_snapshot_digest") != authority_digest:
            raise AdmissionSupersessionError(
                f"authority snapshot digest differs from Stage 1: expected={authority_digest} "
                f"observed={value.get('authority_snapshot_digest')}"
            )
        chain.append(value)
        successor_id = value.get("superseded_by")
        if not successor_id:
            break
        matches: list[dict[str, Any]] = []
        for path in sorted(admissions.directory.glob("*.json")):
            try:
                candidate = admissions.load(path.stem)
            except MissionAdmissionError as error:
                raise AdmissionSupersessionError(str(error)) from error
            if candidate.get("supersedes") == admission_id:
                matches.append(candidate)
        if len(matches) != 1 or matches[0].get("admission_id") != successor_id:
            raise AdmissionSupersessionError("admission supersession lineage is missing or ambiguous")
        value = matches[0]

    if requested_admission_id not in visited:
        raise AdmissionSupersessionError("requested admission is unrelated to Stage 1 lineage")
    terminal = chain[-1]
    if terminal.get("admission_state") in {"SUPERSEDED", "STALE", "CANCELLED", "REJECTED"}:
        raise AdmissionSupersessionError("admission lineage has no executable terminal successor")
    if terminal.get("request", {}).get("repository_baseline") != current_baseline:
        raise AdmissionSupersessionError("successor admission baseline is stale")
    if terminal.get("artifacts", {}).get("repository_baseline") != current_baseline:
        raise AdmissionSupersessionError("successor admission artifact baseline is stale")
    return {"admission_id": terminal["admission_id"], "admission": terminal,
            "predecessor": predecessor, "lineage": chain, "replayed": len(chain) > 1}
