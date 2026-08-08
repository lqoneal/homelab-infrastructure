"""Durable, live-projection-based lifecycle baseline reconciliation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.repository_identity import resolve as resolve_repository_identity
from scripts.lib.eos.canonical_baseline import resolve as resolve_baseline
from scripts.lib.eos.canonical_baseline import resolve_provenance_lineage


RECONCILIATION_DIRECTORY = "reconciliations"
RECEIPT_TYPE = "postpublication-lifecycle-baseline-reconciliation"


class LifecycleBaselineReconciliationError(ValueError):
    """The live lifecycle baseline cannot be reconciled safely."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_ARTIFACT_INVALID", str(error)) from error
    if not isinstance(value, dict):
        raise LifecycleBaselineReconciliationError("RECONCILIATION_ARTIFACT_INVALID", f"{path} is not an object")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise LifecycleBaselineReconciliationError("REPOSITORY_PROJECTION_UNAVAILABLE", result.stderr.strip() or "git projection failed")
    return result.stdout.strip()


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()
    except FileExistsError:
        if path.read_text(encoding="utf-8") != serialized:
            raise LifecycleBaselineReconciliationError("RECONCILIATION_IDENTITY_COLLISION", str(path))


def _current_records(runtime: Path, mission_id: str) -> list[tuple[Path, dict[str, Any]]]:
    directory = runtime / RECONCILIATION_DIRECTORY
    result: list[tuple[Path, dict[str, Any]]] = []
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("*.json")):
        value = _load(path)
        if str(value.get("mission_id", "")).upper() == mission_id:
            result.append((path, value))
    return result


def _verify_record(
    record: Mapping[str, Any],
    *,
    repository: Path,
    expected: Mapping[str, Any],
    current_published_baseline: str,
) -> dict[str, Any]:
    unsigned = {key: value for key, value in record.items() if key != "receipt_digest"}
    if record.get("receipt_digest") != _digest(unsigned):
        raise LifecycleBaselineReconciliationError("RECONCILIATION_DIGEST_MISMATCH", "reconciliation receipt digest mismatch")
    for field in ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id"):
        if record.get(field) != expected.get(field):
            raise LifecycleBaselineReconciliationError("RECONCILIATION_IDENTITY_MISMATCH", f"reconciliation {field} differs from current chain")
    identity = resolve_repository_identity(repository)
    if record.get("repository_identity") != identity:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_REPOSITORY_IDENTITY_MISMATCH", "reconciliation repository identity differs from live repository")
    head = _git(repository, "rev-parse", "HEAD")
    origin = _git(repository, "rev-parse", "origin/main")
    if record.get("current_head") != head or record.get("origin_main") != origin:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_REPOSITORY_PROJECTION_MISMATCH", "reconciliation HEAD/origin projection differs from live repository")
    if record.get("current_published_baseline") != current_published_baseline:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_BASELINE_MISMATCH", "reconciliation is not bound to current publication")
    eos = resolve_baseline(
        repository,
        Path(os.environ.get("EOS_WORKSPACE", "/data/engineering")),
        mission_provenance_baseline=str(record.get("receipt_provenance_baseline", "")),
    )
    if eos.get("result") != "PASS" or eos.get("eos_baseline") != current_published_baseline:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_EOS_PROJECTION_MISMATCH", "reconciliation EOS projection differs from live published baseline")
    lineage = resolve_provenance_lineage(repository, str(record.get("receipt_provenance_baseline", "")), current_published_baseline=current_published_baseline)
    if lineage.get("result") != "PASS" or lineage.get("baseline_relationship") not in {"IDENTICAL", "ANCESTOR"}:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_LINEAGE_INVALID", "reconciliation publication lineage is invalid")
    if record.get("publication_lineage") != lineage:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_LINEAGE_MISMATCH", "reconciliation lineage does not match live publication")
    return {"result": "PASS", "classification": "CURRENT_CANONICAL", "lineage": lineage}


def reconcile(repository: Path | str, runtime: Path | str, mission: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve live P2/P3/P4 projections and persist one idempotent receipt."""
    root = Path(repository).resolve()
    runtime_root = Path(runtime).resolve()
    required = ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id", "receipt_provenance_baseline")
    if any(not mission.get(field) for field in required):
        raise LifecycleBaselineReconciliationError("RECONCILIATION_INPUT_INCOMPLETE", "live lifecycle chain is incomplete")
    identity = resolve_repository_identity(root)
    head = _git(root, "rev-parse", "HEAD")
    origin = _git(root, "rev-parse", "origin/main")
    eos = resolve_baseline(
        root,
        Path(os.environ.get("EOS_WORKSPACE", "/data/engineering")),
        mission_provenance_baseline=str(mission["receipt_provenance_baseline"]),
    )
    if eos.get("result") != "PASS" or eos.get("published_head") != origin or eos.get("current_head") != head:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_PUBLICATION_NOT_VERIFIED", "live repository/EOS publication projection is not synchronized")
    lineage = resolve_provenance_lineage(
        root,
        str(mission["receipt_provenance_baseline"]),
        current_published_baseline=origin,
    )
    if lineage.get("result") != "PASS" or lineage.get("baseline_relationship") not in {"IDENTICAL", "ANCESTOR"}:
        raise LifecycleBaselineReconciliationError("RECONCILIATION_LINEAGE_INVALID", "receipt provenance is not a valid publication ancestor")

    payload = {
        "schema_version": 1,
        "receipt_type": RECEIPT_TYPE,
        "reconciliation_id": "RECONCILIATION-" + str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            _canonical({
                "repository_id": identity["repository_id"],
                "mission_id": mission["mission_id"],
                "wop_id": mission["wop_id"],
                "submission_id": mission["submission_id"],
                "admission_id": mission["admission_id"],
                "bootstrap_id": mission["bootstrap_id"],
                "receipt_provenance_baseline": mission["receipt_provenance_baseline"],
                "current_published_baseline": origin,
            }),
        )),
        "repository_identity": identity,
        "current_head": head,
        "origin_main": origin,
        "eos_published_baseline": eos.get("eos_baseline"),
        "receipt_provenance_baseline": mission["receipt_provenance_baseline"],
        "previous_published_baseline": mission["receipt_provenance_baseline"],
        "current_published_baseline": origin,
        "publication_lineage": lineage,
        "mission_id": mission["mission_id"],
        "wop_id": mission["wop_id"],
        "submission_id": mission["submission_id"],
        "admission_id": mission["admission_id"],
        "bootstrap_id": mission["bootstrap_id"],
        "submission_receipt": mission.get("submission_receipt"),
        "admission_receipt": mission.get("admission_receipt"),
        "bootstrap_receipt": mission.get("bootstrap_receipt"),
        "current_lifecycle": {
            "state": mission.get("lifecycle_state"),
            "readiness": mission.get("readiness"),
            "eligibility": mission.get("eligibility"),
            "next_authorized_action": mission.get("next_authorized_action"),
        },
        "authority": mission.get("authority"),
        "replay_contract": "DETERMINISTIC_IDEMPOTENT",
        "historical_receipts": "IMMUTABLE_AND_EXCLUDED_FROM_CURRENT_AUTHORITY",
    }
    payload["receipt_digest"] = _digest(payload)
    path = runtime_root / RECONCILIATION_DIRECTORY / f"{payload['reconciliation_id']}.json"
    existed = path.exists()
    _write_immutable(path, payload)
    verified = _verify_record(
        _load(path),
        repository=root,
        expected=mission,
        current_published_baseline=origin,
    )
    return {
        "result": "PASS",
        "reconciliation": "IDEMPOTENT" if existed else "CREATED",
        "reconciliation_id": payload["reconciliation_id"],
        "receipt_digest": payload["receipt_digest"],
        "receipt_path": str(path),
        "publication_lineage": verified["lineage"],
        "current_published_baseline": origin,
        "receipt_provenance_baseline": mission["receipt_provenance_baseline"],
    }


def reconcile_mission(repository: Path | str, runtime: Path | str, mission_id: str) -> dict[str, Any]:
    """Generate reconciliation from the canonical live mission projection."""
    from scripts.lib.emp.canonical_lifecycle_resolver import resolve as resolve_lifecycle

    root = Path(repository).resolve()
    runtime_root = Path(runtime).resolve()
    resolved = resolve_lifecycle(root, mission_id, runtime_root=runtime_root)
    if resolved.get("result") != "PASS":
        raise LifecycleBaselineReconciliationError(
            "CANONICAL_LIFECYCLE_UNRESOLVED",
            "cannot generate reconciliation from an unresolved canonical lifecycle",
        )
    admission_path = Path(resolved["admission_transaction"]["path"])
    bootstrap_path = Path(resolved["bootstrap_transaction"]["path"])
    admission = _load(admission_path)
    bootstrap = _load(bootstrap_path)
    submission = resolved.get("submission_receipt") or {}
    submission_value = _load(Path(submission["path"]))
    mission = {
        "mission_id": resolved["mission_id"],
        "wop_id": resolved["wop_id"],
        "submission_id": resolved["submission_id"],
        "admission_id": resolved["admission_id"],
        "bootstrap_id": resolved["bootstrap_id"],
        "receipt_provenance_baseline": admission["repository_baseline"],
        "submission_receipt": {"id": submission_value["submission_id"], "digest": submission_value["receipt_digest"]},
        "admission_receipt": {"id": admission["admission_id"], "digest": admission["transaction_digest"]},
        "bootstrap_receipt": {"id": bootstrap["bootstrap_id"], "digest": bootstrap["transaction_digest"]},
        "lifecycle_state": resolved.get("lifecycle_state"),
        "readiness": resolved.get("readiness"),
        "eligibility": resolved.get("eligibility"),
        "next_authorized_action": resolved.get("next_authorized_action"),
        "authority": resolved.get("authority"),
    }
    return reconcile(root, runtime_root, mission)


def verify_current(
    repository: Path | str,
    runtime: Path | str,
    *,
    expected: Mapping[str, Any],
    current_published_baseline: str,
) -> dict[str, Any]:
    """Verify the one current reconciliation receipt for a canonical chain."""
    candidates = []
    for path, record in _current_records(Path(runtime).resolve(), str(expected["mission_id"]).upper()):
        if record.get("current_published_baseline") == current_published_baseline:
            candidates.append((path, record))
    if len(candidates) != 1:
        raise LifecycleBaselineReconciliationError(
            "RECONCILIATION_CARDINALITY_INVALID",
            f"current reconciliation cardinality is {len(candidates)}",
        )
    path, record = candidates[0]
    result = _verify_record(
        record,
        repository=Path(repository).resolve(),
        expected=expected,
        current_published_baseline=current_published_baseline,
    )
    return {**result, "receipt_path": str(path), "receipt_digest": record["receipt_digest"]}
