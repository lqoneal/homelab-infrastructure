"""Canonical Zeus publication transaction controller.

Publication is modeled here as a durable lifecycle transaction.  Git and EOS
are subordinate operations; the transaction record and immutable milestone
receipts are the controller's authority for replay and recovery.

The module deliberately does not start a transaction merely by importing it.
Callers must select an explicit command, and mutating commands require a
writable repository-bound Zeus runtime.  All current repository operands are
resolved through :mod:`repository_projection`.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.mission_verification_controller import verify as verify_mission
from scripts.lib.emp import publication_candidate_authority
from scripts.lib.emp import publication_cohort
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.repository_projection import project as project_repository
from scripts.lib.emp.runtime_paths import initialize_runtime, resolve_runtime
from scripts.lib.emp.publication_authority import (
    MILESTONES,
    NEXT_BY_STATE,
    active_transactions as _active_transactions,
    resolve_transaction_lineage as _resolve_transaction_lineage,
    receipt_errors as _receipt_errors,
    receipt_path as _receipt_path,
    transaction_integrity as _transaction_integrity,
)


PUBLICATION_SCHEMA = 1
TRANSACTION_DIR = "publication-transactions"
MANIFEST_DIR = "publication-manifests"
TERMINAL_STATES = {"PUBLICATION_QUALIFIED", "ABORTED", "FAILED"}
PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_./-])((?:engineering|scripts|docs|services|\.zeus)/[^\s`|,)]+)")
STAGED_TREE_DIGEST_SEMANTICS = "SHA256_CANONICAL_JSON_SORTED_PATH_INDEX_BLOB_SHA256_V1"


class PublicationTransactionError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code = code
        self.message = message
        self.next_action = next_action
        super().__init__(message)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_git(root: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _git(root: Path, *args: str) -> str:
    result = _run_git(root, *args)
    if result.returncode:
        raise PublicationTransactionError(
            "GIT_OPERATION_FAILED",
            result.stderr.strip() or "git operation failed",
        )
    return result.stdout.strip()


def _runtime(root: Path, runtime_root: Path | str | None, *, writable: bool) -> Path:
    if writable:
        return initialize_runtime(root, explicit=runtime_root)["root"]
    return resolve_runtime(root, explicit=runtime_root, require_writable=False)["root"]


def _tx_dir(runtime: Path) -> Path:
    return runtime / TRANSACTION_DIR


def _tx_path(runtime: Path, publication_id: str) -> Path:
    if not re.fullmatch(r"PUBLICATION-[0-9a-f-]+", publication_id):
        raise PublicationTransactionError("PUBLICATION_ID_INVALID", "publication identity is not canonical")
    return _tx_dir(runtime) / f"{publication_id}.json"


def _save(runtime: Path, record: Mapping[str, Any]) -> None:
    path = _tx_path(runtime, str(record["publication_id"]))
    atomic_write(path, dict(record))


def _load_transaction(runtime: Path, publication_or_mission: str) -> dict[str, Any]:
    directory = _tx_dir(runtime)
    if publication_or_mission.startswith("PUBLICATION-"):
        candidates = [directory / f"{publication_or_mission}.json"]
    else:
        lineage = _mission_lineage(runtime, publication_or_mission)
        if lineage["result"] != "PASS":
            first = lineage["errors"][0]
            raise PublicationTransactionError(first["code"], first["reason"])
        candidates = [
            directory / f"{value['publication_id']}.json"
            for value in lineage["current"]
        ]
    values = [(_safe_load(path), path) for path in candidates if path.is_file()]
    values = [(value, path) for value, path in values if value]
    if not values:
        raise PublicationTransactionError("PUBLICATION_NOT_FOUND", f"no publication transaction resolves {publication_or_mission}")
    if len(values) > 1:
        raise PublicationTransactionError("PUBLICATION_CARDINALITY_CONFLICT", "more than one current publication transaction resolves the mission")
    value, path = values[0]
    value["transaction_path"] = str(path)
    return value


def _safe_load(path: Path) -> dict[str, Any]:
    try:
        value = load_json(path)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _transaction_inventory(runtime: Path) -> tuple[list[dict[str, Any]], list[Path]]:
    """Read the immutable transaction inventory without hiding corrupt files."""
    values: list[dict[str, Any]] = []
    malformed: list[Path] = []
    for path in sorted(_tx_dir(runtime).glob("PUBLICATION-*.json")):
        value = _safe_load(path)
        if value:
            values.append(value)
        else:
            malformed.append(path)
    return values, malformed


def _mission_lineage(runtime: Path, mission_id: str) -> dict[str, Any]:
    values, malformed = _transaction_inventory(runtime)
    if malformed:
        return {
            "result": "FAIL", "current": [], "current_ids": [],
            "historical": [], "dispositions": {}, "read_only": True,
            "timestamp_ordering_used": False,
            "errors": [{
                "code": "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE",
                "reason": "; ".join(f"publication transaction is malformed: {path}" for path in malformed),
            }],
        }
    lineage = _resolve_transaction_lineage(values, mission_id=mission_id)
    if lineage["result"] == "PASS":
        # Every authoritative node participating in the immutable lineage must
        # reproduce its receipt-bound state.  Failed/aborted history is not an
        # authority edge and remains independently inspectable.
        lineage_records = [
            record for record in [*lineage["current"], *lineage["historical"]]
            if record.get("current_state") not in {"FAILED", "ABORTED"}
        ]
        for record in lineage_records:
            integrity = _transaction_integrity(runtime, record)
            if integrity["result"] != "PASS":
                lineage["result"] = "FAIL"
                lineage["current"] = []
                lineage["current_ids"] = []
                lineage["errors"].append({
                    "code": "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE",
                    "reason": f"{record.get('publication_id')}: " + "; ".join(integrity["errors"]),
                })
    return lineage


def _resolve_next_action(
    runtime: Path,
    record: Mapping[str, Any],
    *,
    authority_revalidation: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Own publication next-action resolution from persisted transaction state."""
    integrity = _transaction_integrity(runtime, record)
    if integrity["result"] != "PASS":
        return "RECOVER_PUBLICATION_TRANSACTION", integrity
    if authority_revalidation is not None and authority_revalidation.get("result") != "PASS":
        return "REPREPARE_PUBLICATION_TRANSACTION", integrity
    state = str(record.get("current_state") or "")
    if state == "FAILED":
        return "RESOLVE_PUBLICATION_BLOCKER", integrity
    if state == "ABORTED":
        return "PUBLICATION_ABORTED", integrity
    return NEXT_BY_STATE.get(state, "STOP_FAIL_CLOSED"), integrity


def _immutable_receipt(runtime: Path, record: Mapping[str, Any], milestone: str, result: str, **extra: Any) -> str:
    path = _receipt_path(runtime, str(record["publication_id"]), milestone)
    if path.is_file():
        existing = _safe_load(path)
        existing_entry = {
            "receipt_path": str(path),
            "receipt_digest": existing.get("receipt_digest"),
            "result": result,
        }
        errors = _receipt_errors(runtime, record, milestone, existing_entry)
        for key, value in extra.items():
            if existing.get(key) != value:
                errors.append(f"{milestone} receipt {key} conflicts with replay inputs")
        if errors:
            raise PublicationTransactionError("PUBLICATION_RECEIPT_CONFLICT", "; ".join(errors))
        return str(path)
    receipt = {
        "schema_version": PUBLICATION_SCHEMA,
        "receipt_type": "zeus-publication-milestone",
        "milestone": milestone,
        "result": result,
        "publication_id": record["publication_id"],
        "mission_id": record["mission_id"],
        "wop_id": record.get("wop_id"),
        "publication_cohort_id": record.get("publication_cohort_id"),
        "supersedes_publication_id": record.get("supersedes_publication_id"),
        "repository_id": record["repository_id"],
        "input_digest": record.get("candidate_digest"),
        "created_at": _now(),
        **extra,
    }
    receipt["receipt_digest"] = digest(receipt)
    atomic_write(path, receipt)
    return str(path)


def _record_milestone(runtime: Path, record: dict[str, Any], milestone: str, *, result: str = "PASS", **extra: Any) -> dict[str, Any]:
    receipts = dict(record.get("milestones") or {})
    existing = receipts.get(milestone)
    if existing:
        errors = _receipt_errors(runtime, record, milestone, existing)
        if errors or existing.get("result") != result:
            raise PublicationTransactionError("PUBLICATION_MILESTONE_CONFLICT", "; ".join(errors) or f"milestone {milestone} is not replayable")
    else:
        path = Path(_immutable_receipt(runtime, record, milestone, result, **extra))
        receipts[milestone] = {"receipt_path": str(path), "receipt_digest": _safe_load(path).get("receipt_digest"), "result": result}
    record["milestones"] = receipts
    record["current_state"] = milestone if result == "PASS" else "FAILED"
    record["completed_milestones"] = [name for name in MILESTONES if name in receipts and receipts[name].get("result") == "PASS"]
    record["pending_milestones"] = [name for name in MILESTONES if name not in record["completed_milestones"]]
    record["next_authorized_action"] = NEXT_BY_STATE.get(record["current_state"], "STOP_FAIL_CLOSED")
    record["updated_at"] = _now()
    try:
        _save(runtime, record)
    except Exception as error:
        raise PublicationTransactionError(
            "PUBLICATION_TRANSACTION_PERSISTENCE_FAILED",
            f"milestone receipt exists but authoritative transaction persistence failed: {error}",
            next_action="RECOVER_PUBLICATION_TRANSACTION",
        ) from error
    persisted = _load_transaction(runtime, str(record["publication_id"]))
    integrity = _transaction_integrity(runtime, persisted)
    if persisted.get("current_state") != milestone or integrity["result"] != "PASS":
        raise PublicationTransactionError(
            "PUBLICATION_TRANSACTION_RELOAD_FAILED",
            "; ".join(integrity["errors"]) or "persisted milestone was not reproduced by a fresh reload",
            next_action="RECOVER_PUBLICATION_TRANSACTION",
        )
    record.clear()
    record.update(persisted)
    return record


def _file_digest(root: Path, paths: list[str]) -> str:
    values = []
    for relative in sorted(paths):
        path = root / relative
        if not path.is_file():
            raise PublicationTransactionError("CANDIDATE_PATH_MISSING", relative)
        values.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return digest(values)


def _staged_paths(root: Path) -> list[str]:
    """Return the exact path set represented by the live Git index delta."""
    result = _run_git(root, "diff", "--cached", "--name-only", "-z")
    if result.returncode:
        raise PublicationTransactionError(
            "GIT_OPERATION_FAILED", result.stderr.strip() or "unable to inspect staged paths"
        )
    return sorted(value for value in result.stdout.split("\0") if value)


def _staged_file_digest(root: Path, paths: list[str]) -> str:
    """Reproduce the candidate digest from index blobs, never worktree bytes.

    The canonical representation is the sorted JSON array used by
    :func:`_file_digest`: ``[{"path": <relative>, "sha256": <blob bytes>}]``.
    Only the byte source differs: this function reads stage-zero index blobs.
    """
    values = []
    for relative in sorted(paths):
        entry = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage", "-z", "--", relative],
            capture_output=True,
            check=False,
        )
        if entry.returncode:
            raise PublicationTransactionError(
                "GIT_OPERATION_FAILED",
                os.fsdecode(entry.stderr).strip() or f"unable to inspect staged entry: {relative}",
            )
        records = [value for value in entry.stdout.split(b"\0") if value]
        if len(records) != 1 or b"\t" not in records[0]:
            raise PublicationTransactionError("STAGED_CANDIDATE_PATH_MISSING", relative)
        metadata, indexed_path = records[0].split(b"\t", 1)
        fields = metadata.split()
        if len(fields) != 3 or fields[2] != b"0" or os.fsdecode(indexed_path) != relative:
            raise PublicationTransactionError(
                "AMBIGUOUS_STAGED_ENTRY", f"stage-zero index entry is not unique: {relative}"
            )
        blob = subprocess.run(
            ["git", "-C", str(root), "cat-file", "blob", os.fsdecode(fields[1])],
            capture_output=True,
            check=False,
        )
        if blob.returncode:
            raise PublicationTransactionError(
                "GIT_OPERATION_FAILED",
                os.fsdecode(blob.stderr).strip() or f"unable to read staged blob: {relative}",
            )
        values.append({"path": relative, "sha256": hashlib.sha256(blob.stdout).hexdigest()})
    return digest(values)


def _assert_exact_staged_candidate(root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    """Prove that the index is exactly the frozen authorized candidate."""
    expected = sorted(record.get("candidate_paths") or [])
    actual = _staged_paths(root)
    extras = sorted(set(actual) - set(expected))
    missing = sorted(set(expected) - set(actual))
    if extras:
        raise PublicationTransactionError(
            "UNEXPECTED_STAGED_PATH", "unexpected staged paths: " + ", ".join(extras)
        )
    if missing:
        raise PublicationTransactionError(
            "STAGED_CANDIDATE_PATH_MISSING", "missing staged candidate paths: " + ", ".join(missing)
        )
    staged_digest = _staged_file_digest(root, expected)
    if staged_digest != record.get("candidate_digest"):
        raise PublicationTransactionError(
            "STAGED_CONTENT_MISMATCH",
            "staged index content does not reproduce the frozen candidate digest",
        )
    recorded_digest = record.get("staged_tree_digest")
    if recorded_digest not in (None, staged_digest):
        raise PublicationTransactionError(
            "STAGED_TREE_DIGEST_MISMATCH",
            "persisted staged_tree_digest does not reproduce the live staged index",
        )
    recorded_semantics = record.get("staged_tree_digest_semantics")
    if recorded_semantics not in (None, STAGED_TREE_DIGEST_SEMANTICS):
        raise PublicationTransactionError(
            "STAGED_TREE_DIGEST_SEMANTICS_MISMATCH",
            "persisted staged_tree_digest semantics are not canonical",
        )
    candidate_receipt = (record.get("milestones") or {}).get("CANDIDATE_STAGED")
    if candidate_receipt:
        receipt = _safe_load(Path(str(candidate_receipt.get("receipt_path") or "")))
        if receipt.get("staged_tree_digest") != staged_digest:
            raise PublicationTransactionError(
                "STAGED_TREE_DIGEST_MISMATCH",
                "CANDIDATE_STAGED receipt digest does not reproduce the live staged index",
            )
        if receipt.get("staged_tree_digest_semantics") not in (
            None, STAGED_TREE_DIGEST_SEMANTICS
        ):
            raise PublicationTransactionError(
                "STAGED_TREE_DIGEST_SEMANTICS_MISMATCH",
                "CANDIDATE_STAGED receipt digest semantics are not canonical",
            )
        if sorted(receipt.get("staged_paths") or []) != actual:
            raise PublicationTransactionError(
                "STAGED_SET_MISMATCH",
                "CANDIDATE_STAGED receipt paths do not reproduce the live staged index",
            )
    return {
        "staged_paths": actual,
        "staged_tree_digest": staged_digest,
        "staged_tree_digest_semantics": STAGED_TREE_DIGEST_SEMANTICS,
    }


def _revalidate_staged_authority(root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    try:
        staged = _assert_exact_staged_candidate(root, record)
    except PublicationTransactionError as error:
        return {
            "result": "FAIL", "read_only": True,
            "candidate_paths": sorted(record.get("candidate_paths") or []),
            "candidate_digest": record.get("candidate_digest"),
            "staged_tree_digest": record.get("staged_tree_digest"),
            "drift_inputs": [error.message],
            "blocked": [{"code": error.code, "reason": error.message}],
            "authority_recovery_action": "STOP_FAIL_CLOSED",
        }
    return {
        "result": "PASS", "read_only": True,
        "scope": "FROZEN_STAGED_INDEX",
        "candidate_paths": staged["staged_paths"],
        "candidate_digest": record.get("candidate_digest"),
        "staged_tree_digest": staged["staged_tree_digest"],
        "staged_tree_digest_semantics": staged["staged_tree_digest_semantics"],
        "drift_inputs": [], "blocked": [], "authority_recovery_action": None,
        "live_resolved_cohort_id": record.get("publication_cohort_id"),
    }


def _file_digest_at_commit(root: Path, commit_id: str, paths: list[str]) -> str:
    """Reproduce a frozen candidate digest from the publication commit tree."""
    values = []
    for relative in sorted(paths):
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit_id}:{relative}"],
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise PublicationTransactionError("CANDIDATE_PATH_MISSING", relative)
        values.append({"path": relative, "sha256": hashlib.sha256(result.stdout).hexdigest()})
    return digest(values)


def _manifest_paths(root: Path, mission_id: str, manifest: Path | str | None) -> tuple[list[str], dict[str, Any]]:
    candidates: list[Path] = []
    if manifest:
        candidates.append(Path(manifest).resolve())
    runtime_manifest = root / ".zeus" / MANIFEST_DIR / f"{mission_id}.json"
    candidates.append(runtime_manifest)
    candidates.extend(sorted((root / "engineering" / "evidence").glob("**/PUBLICATION-CANDIDATE-MANIFEST.json")))
    candidates.extend(sorted((root / "engineering" / "evidence").glob("**/PUBLICATION-CANDIDATE-MANIFEST.yaml")))
    candidates.extend(sorted((root / "engineering" / "evidence").glob("**/PUBLICATION-CANDIDATE-MANIFEST.yml")))
    candidates.extend(sorted((root / "engineering" / "evidence").glob("**/PUBLICATION-CANDIDATE-MANIFEST.md")))
    for path in candidates:
        if not path.is_file():
            continue
        try:
            if path.suffix in {".json", ".yaml", ".yml"}:
                value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if not isinstance(value, dict):
                    continue
                if value.get("mission_id") not in (None, mission_id):
                    continue
                paths = value.get("candidate_paths") or value.get("paths") or value.get("files")
                if isinstance(paths, list) and all(isinstance(item, str) for item in paths):
                    return sorted(set(paths)), {"path": str(path), "format": path.suffix[1:], "mission_id": mission_id}
            else:
                text = path.read_text(encoding="utf-8")
                if mission_id not in text and path != candidates[0]:
                    continue
                found = sorted(set(match.rstrip(".,:;") for match in PATH_PATTERN.findall(text)))
                if found:
                    return found, {"path": str(path), "format": "markdown", "mission_id": mission_id}
        except (OSError, UnicodeError, yaml.YAMLError):
            continue
    return [], {"path": None, "format": None, "mission_id": mission_id}


def _classify_paths(root: Path, projection: Mapping[str, Any], candidate_paths: list[str], authority: Mapping[str, Any]) -> dict[str, Any]:
    candidate = set(candidate_paths)
    traceability = {item.get("path"): item for item in authority.get("candidate_traceability", []) if item.get("path")}
    all_paths = set(projection.get("staged_paths", [])) | set(projection.get("unstaged_paths", [])) | set(projection.get("untracked_paths", []))
    values = []
    for path in sorted(all_paths):
        if path in candidate:
            classification, reason = "MISSION_CANDIDATE", "qualified mission/WOP publication authority"
        elif path.startswith("engineering/evidence/"):
            classification, reason = "RELATED_EVIDENCE", "evidence is preserved and not selected by dirty status"
        elif path.startswith("engineering/docs/") or path.startswith("engineering/validation/"):
            classification, reason = "RELATED_CONTROLLED_DOCUMENT", "controlled document is not selected without manifest authority"
        elif path.startswith(".zeus/"):
            classification, reason = "GENERATED_RUNTIME", "repository-local runtime/configuration is excluded from publication"
        else:
            classification, reason = "UNRELATED_DIRTY", "no authoritative candidate source resolved this path"
        values.append({"path": path, "classification": classification, "classification_authority": traceability.get(path, {}).get("sources", []), "reason": reason})
    blocked = [item for item in values if item["classification"] in {"AMBIGUOUS", "BLOCKED"}]
    selected = sorted(candidate)
    missing = sorted(path for path in selected if not (root / path).is_file())
    if missing:
        blocked.extend({"path": path, "classification": "BLOCKED", "classification_authority": traceability.get(path, {}).get("sources", []), "reason": "candidate path is missing"} for path in missing)
    return {"paths": values, "candidate_paths": selected, "blocked": blocked, "missing": missing, "already_published": authority.get("already_published", []), "excluded_paths": authority.get("excluded_paths", []), "result": "PASS" if selected and not blocked else "FAIL", "reason": "candidate authority resolved" if selected and not blocked else ("candidate path is missing" if missing else "no authoritative publication candidate resolved")}


def _revalidate_authority(root: Path, record: Mapping[str, Any], runtime: Path) -> dict[str, Any]:
    """Resolve one transaction's live authority from its persisted cohort."""
    if record.get("current_state") in {"CANDIDATE_STAGED", "STAGED_SET_VERIFIED"}:
        return _revalidate_staged_authority(root, record)
    cohort_id = record.get("publication_cohort_id")
    if not cohort_id:
        if record.get("cohort_authority_required") is False:
            live_digest = _file_digest(root, list(record.get("candidate_paths") or []))
            drift_inputs = [] if live_digest == record.get("candidate_digest") else ["candidate/path content digest"]
            return {
                "result": "PASS" if not drift_inputs else "FAIL", "cohort_id": None,
                "live_resolved_cohort_id": None, "candidate_digest": live_digest,
                "candidate_authority_digest": record.get("candidate_authority_digest"),
                "classification_digest": record.get("classification_digest"),
                "candidate_paths": sorted(record.get("candidate_paths") or []),
                "candidate_sources": record.get("candidate_sources", []), "drift_inputs": drift_inputs,
                "blocked": [], "authority_recovery_action": None,
                "read_only": True, "legacy_manifest_fallback": True,
            }
        return {
            "result": "FAIL", "cohort_id": None, "live_resolved_cohort_id": None,
            "candidate_digest": None, "candidate_authority_digest": None,
            "classification_digest": None, "candidate_paths": [], "candidate_sources": [],
            "drift_inputs": ["missing persisted publication cohort"],
            "blocked": [{"code": "PUBLICATION_COHORT_MISSING", "reason": "transaction has no persisted publication_cohort_id"}],
            "authority_recovery_action": "REPREPARE_PUBLICATION_TRANSACTION", "read_only": True,
        }
    authority = publication_candidate_authority.resolve(
        root, str(record.get("mission_id") or ""), runtime_root=runtime, cohort_id=str(cohort_id)
    )
    projection = project_repository(
        root,
        runtime_root=runtime,
        mission_id=str(record.get("mission_id") or ""),
        wop_id=str(record.get("wop_id") or ""),
        publication_id=str(record.get("publication_id") or ""),
    )
    live_paths = sorted(authority.get("candidate_paths") or [])
    live_candidate_digest = authority.get("candidate_digest")
    live_authority_digest = authority.get("candidate_authority_digest") or authority.get("classification_digest")
    drift_inputs = list(authority.get("drift_inputs") or [])
    postcommit = record.get("current_state") in {
        "COMMIT_CREATED", "REMOTE_PUBLISHED", "EOS_SYNCHRONIZED",
        "POSTPUBLICATION_VERIFIED", "PUBLICATION_QUALIFIED",
    }
    authority_structurally_valid = (
        not authority.get("blocked")
        and not authority.get("ambiguous")
        and not authority.get("missing")
        and (authority.get("cohort") or {}).get("cohort_id") == cohort_id
        and live_authority_digest == record.get("candidate_authority_digest")
    )
    if authority.get("result") != "PASS" and not (postcommit and authority_structurally_valid):
        failed_authority = dict(authority)
        authority_recovery_action = failed_authority.pop(
            "next_authorized_action", "REPREPARE_PUBLICATION_TRANSACTION"
        )
        return {
            **failed_authority, "result": "FAIL", "cohort_id": cohort_id,
            "live_resolved_cohort_id": (authority.get("cohort") or {}).get("cohort_id"),
            "candidate_authority_digest": live_authority_digest,
            "drift_inputs": sorted(set(drift_inputs or ["bound publication cohort authority"])),
            "stale_classification": True,
            "authority_recovery_action": authority_recovery_action,
        }
    if postcommit:
        frozen_paths = sorted(record.get("candidate_paths") or [])
        commit_id = str(record.get("commit_id") or "")
        try:
            commit_candidate_digest = _file_digest_at_commit(root, commit_id, frozen_paths)
        except PublicationTransactionError as error:
            drift_inputs.append(error.message)
            commit_candidate_digest = None
        if str(authority.get("wop_id") or "") != str(record.get("wop_id") or ""):
            drift_inputs.append("WOP identity")
        if projection.get("repository_id") != record.get("repository_id"):
            drift_inputs.append("repository identity")
        transition = projection.get("publication_transition") or {}
        if (projection.get("result") != "PASS" or
                transition.get("publication_id") != record.get("publication_id")):
            drift_inputs.append("authorized repository publication transition")
        if commit_candidate_digest != record.get("candidate_digest"):
            drift_inputs.append("publication commit candidate/path content digest")
        if live_authority_digest != record.get("candidate_authority_digest"):
            drift_inputs.append("candidate-authority digest")
        return {
            "result": "PASS" if not drift_inputs else "FAIL",
            "stale_classification": bool(drift_inputs),
            "cohort_id": cohort_id,
            "live_resolved_cohort_id": (authority.get("cohort") or {}).get("cohort_id"),
            "candidate_digest": commit_candidate_digest,
            "candidate_authority_digest": live_authority_digest,
            "classification_digest": record.get("classification_digest"),
            "frozen_candidate_digest": record.get("candidate_digest"),
            "frozen_candidate_authority_digest": record.get("candidate_authority_digest"),
            "frozen_classification_digest": record.get("classification_digest"),
            "candidate_paths": frozen_paths,
            "candidate_sources": authority.get("candidate_sources", []),
            "cohort": authority.get("cohort"), "authority": authority.get("authority"),
            "drift_inputs": sorted(set(drift_inputs)), "blocked": authority.get("blocked", []),
            "authority_recovery_action": "REPREPARE_PUBLICATION_TRANSACTION" if drift_inputs else None,
            "baseline_state_classification": projection.get("baseline_state_classification"),
            "read_only": True,
        }
    if str(authority.get("wop_id") or "") != str(record.get("wop_id") or ""):
        drift_inputs.append("WOP identity")
    if projection.get("repository_id") != record.get("repository_id"):
        drift_inputs.append("repository identity")
    if live_paths != sorted(record.get("candidate_paths") or []):
        drift_inputs.append("candidate path set")
    if live_candidate_digest != record.get("candidate_digest"):
        drift_inputs.append("candidate/path content digest")
    if live_authority_digest != record.get("candidate_authority_digest"):
        drift_inputs.append("candidate-authority digest")
    classification = _classify_paths(root, projection, live_paths, authority)
    live_classification_digest = digest(classification)
    # The complete dirty projection is evidence only.  Unrelated dirty or
    # newly qualified sources are not authority for this bound transaction.
    return {
        "result": "PASS" if not drift_inputs else "FAIL",
        "stale_classification": bool(drift_inputs),
        "cohort_id": cohort_id,
        "live_resolved_cohort_id": (authority.get("cohort") or {}).get("cohort_id"),
        "candidate_digest": live_candidate_digest,
        "candidate_authority_digest": live_authority_digest,
        "classification_digest": live_classification_digest,
        "frozen_candidate_digest": record.get("candidate_digest"),
        "frozen_candidate_authority_digest": record.get("candidate_authority_digest"),
        "frozen_classification_digest": record.get("classification_digest"),
        "candidate_paths": live_paths,
        "candidate_sources": authority.get("candidate_sources", []),
        "cohort": authority.get("cohort"), "authority": authority.get("authority"),
        "drift_inputs": sorted(set(drift_inputs)), "blocked": authority.get("blocked", []),
        "authority_recovery_action": "REPREPARE_PUBLICATION_TRANSACTION" if drift_inputs else None,
        "read_only": True,
    }


def inspect(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Inspect either a mission projection or a transaction-bound projection."""
    if str(publication_or_mission).startswith("PUBLICATION-"):
        repository = Path(root).resolve()
        runtime = _runtime(repository, runtime_root, writable=False)
        record = _load_transaction(runtime, publication_or_mission)
        revalidation = _revalidate_authority(repository, record, runtime)
        next_action, integrity = _resolve_next_action(runtime, record, authority_revalidation=revalidation)
        blockers = [] if revalidation.get("result") == "PASS" else [{
            "code": "STALE_CLASSIFICATION", "reason": revalidation.get("drift_inputs") or revalidation.get("blocked")
        }]
        if integrity["result"] != "PASS":
            blockers.append({"code": "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE", "reason": integrity["errors"]})
        return {**record, "result": "PASS" if revalidation.get("result") == "PASS" and integrity["result"] == "PASS" else "FAIL", "read_only": True,
                "candidate_authority_revalidation": revalidation, "blockers": blockers,
                "live_resolved_cohort_id": revalidation.get("live_resolved_cohort_id"),
                "transaction_integrity": integrity,
                "next_authorized_action": next_action}
    return _mission_inspect(root, publication_or_mission, runtime_root=runtime_root)


def _mission_inspect(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    try:
        runtime = _runtime(root, runtime_root, writable=False)
        transactions, malformed = _transaction_inventory(runtime)
    except Exception as error:
        runtime, transactions = None, []
        runtime_error = str(error)
    else:
        runtime_error = None if not malformed else "; ".join(f"malformed transaction: {path}" for path in malformed)
    existing = [value for value in transactions if value.get("mission_id") == mission_id]
    lineage = _mission_lineage(runtime, mission_id) if runtime is not None else {
        "result": "FAIL", "current": [], "dispositions": {},
        "errors": [{"code": "NO_WRITABLE_RUNTIME_ROOT", "reason": runtime_error or "runtime unavailable"}],
        "timestamp_ordering_used": False, "read_only": True,
    }
    active = list(lineage.get("current") or [])
    projection = project_repository(
        root,
        runtime_root=runtime,
        mission_id=mission_id,
        wop_id=active[0].get("wop_id") if len(active) == 1 else None,
        publication_id=active[0].get("publication_id") if len(active) == 1 else None,
    )
    authority = publication_candidate_authority.resolve(root, mission_id, runtime_root=runtime)
    active_action = None
    active_integrity = None
    if len(active) == 1 and runtime is not None:
        bound_revalidation = _revalidate_authority(root, active[0], runtime)
        active_action, active_integrity = _resolve_next_action(
            runtime, active[0], authority_revalidation=bound_revalidation
        )
    paths = authority.get("candidate_paths", [])
    value = {
        "schema_version": PUBLICATION_SCHEMA, "result": "PASS" if projection.get("result") == "PASS" and authority.get("result") == "PASS" else "FAIL", "read_only": True,
        "mission_id": mission_id, "wop_id": (active[0].get("wop_id") if active else authority.get("wop_id")), "repository": projection,
        "runtime": {"root": str(runtime) if runtime else None, "error": runtime_error},
        "candidate_sources": authority.get("candidate_sources", []), "candidate_paths": paths,
        "candidate_authority": authority,
        "publication_cohort": authority.get("cohort"),
        "transaction_integrity": active_integrity, "publication_lineage": lineage,
        "existing_transactions": existing, "publication_blockers": ([] if projection.get("result") == "PASS" else projection.get("errors", [])),
        "next_authorized_action": (
            authority.get("next_authorized_action", "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY")
            if authority.get("ambiguous")
            else active_action
            if len(active) == 1
            else "STOP_FAIL_CLOSED"
            if lineage.get("result") != "PASS"
            else "CLASSIFY_PUBLICATION_WORKTREE"
            if authority.get("result") == "PASS"
            else "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY"
        ),
    }
    return value


def classify(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None, manifest: Path | str | None = None, persist: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=persist)
    authority = publication_candidate_authority.resolve(root, mission_id, runtime_root=runtime, manifest=manifest)
    projection = project_repository(
        root,
        runtime_root=runtime,
        mission_id=mission_id,
        wop_id=authority.get("wop_id"),
    )
    paths = authority.get("candidate_paths", [])
    classification = _classify_paths(root, projection, paths, authority)
    if authority.get("result") != "PASS":
        classification["result"] = "FAIL"
        classification["reason"] = authority.get("blocked") or authority.get("ambiguous") or authority.get("missing") or "candidate authority did not resolve"
    value = {"schema_version": PUBLICATION_SCHEMA, "result": classification["result"], "read_only": not persist, "mission_id": mission_id, "wop_id": authority.get("wop_id"), "repository": projection, "candidate_authority": authority, "candidate_sources": authority.get("candidate_sources", []), "candidate_paths": paths, "classification": classification, "candidate_digest": authority.get("candidate_digest"), "classification_digest": authority.get("classification_digest"), "next_authorized_action": "PREPARE_PUBLICATION_CANDIDATE" if classification["result"] == "PASS" else authority.get("next_authorized_action", "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY")}
    if persist:
        value["classification_digest"] = digest(classification)
        atomic_write(runtime / "publication-classifications" / f"{mission_id}.json", value)
    return value


def prepare(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None, manifest: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    classified = classify(root, mission_id, runtime_root=runtime, manifest=manifest, persist=True)
    if classified["result"] != "PASS":
        raise PublicationTransactionError("CANDIDATE_AUTHORITY_UNRESOLVED", classified["classification"]["reason"], next_action="RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY")
    projection = classified["repository"]
    candidate_paths = classified["classification"]["candidate_paths"]
    candidate_digest = _file_digest(root, candidate_paths)
    wop_id = classified["candidate_authority"].get("wop_id")
    if not wop_id:
        try:
            live_mission = verify_mission(root, mission_id, runtime_root=runtime)
            if live_mission.get("result") == "PASS":
                wop_id = live_mission.get("wop_id")
        except Exception:
            # Candidate preparation remains bounded by the manifest when the
            # mission projection is unavailable; the missing WOP binding is
            # retained in the transaction and later verification fails closed.
            wop_id = None
    cohort = classified["candidate_authority"].get("cohort") or {}
    cohort_id = cohort.get("cohort_id")
    if cohort_id:
        bound = publication_candidate_authority.resolve(
            root, mission_id, runtime_root=runtime, cohort_id=cohort_id
        )
        if bound.get("result") != "PASS":
            raise PublicationTransactionError(
                "STALE_CLASSIFICATION",
                str(bound.get("blocked") or bound.get("drift_inputs") or "bound cohort authority unresolved"),
                next_action="REPREPARE_PUBLICATION_TRANSACTION",
            )
        classified["candidate_authority"] = bound
        classified["candidate_sources"] = bound.get("candidate_sources", [])
        classified["candidate_paths"] = bound.get("candidate_paths", [])
        classified["classification"]["candidate_paths"] = bound.get("candidate_paths", [])
        candidate_paths = bound.get("candidate_paths", [])
        candidate_digest = _file_digest(root, candidate_paths)
    seed = {"repository_id": projection.get("repository_id"), "mission_id": mission_id, "wop_id": wop_id, "publication_cohort_id": cohort_id, "starting_head": projection.get("head"), "candidate_digest": candidate_digest}
    publication_id = identifier("PUBLICATION", seed)
    path = _tx_path(runtime, publication_id)
    if path.is_file():
        record = load_json(path)
        if record.get("candidate_digest") != candidate_digest or record.get("candidate_authority_digest") != classified["candidate_authority"].get("classification_digest"):
            raise PublicationTransactionError("PUBLICATION_CANDIDATE_CHANGED", "existing publication identity has a different candidate or authority digest")
        lineage = _mission_lineage(runtime, mission_id)
        if lineage.get("result") != "PASS" or publication_id not in lineage.get("current_ids", []):
            error = (lineage.get("errors") or [{"code": "PUBLICATION_REPLAY_NOT_CURRENT", "reason": "replayed publication is not canonical current authority"}])[0]
            raise PublicationTransactionError(error["code"], error["reason"])
        return {**record, "result": "PASS", "replayed": True, "publication_replay": "IDEMPOTENT"}
    lineage = _mission_lineage(runtime, mission_id)
    if lineage.get("result") != "PASS":
        error = lineage["errors"][0]
        raise PublicationTransactionError(error["code"], error["reason"])
    active_prior = list(lineage.get("current") or [])
    supersedes_publication_id = active_prior[0].get("publication_id") if active_prior else None
    record: dict[str, Any] = {
        "schema_version": PUBLICATION_SCHEMA, "result": "PASS", "publication_id": publication_id, "mission_id": mission_id, "wop_id": wop_id,
        "publication_cohort_id": cohort_id, "supersedes_publication_id": supersedes_publication_id,
        "transaction_creation_authority": {
            "type": "ZEUS_PUBLICATION_PREPARE",
            "mission_id": mission_id, "wop_id": wop_id,
            "repository_id": projection.get("repository_id"),
            "candidate_authority_digest": classified["candidate_authority"].get("classification_digest"),
        },
        "supersession_lineage_authority": "IMMUTABLE_SUCCESSOR_LINK",
        "current_state_authority": "IMMUTABLE_MILESTONE_RECEIPTS",
        "repository_id": projection.get("repository_id"), "repository_root": str(root), "starting_head": projection.get("head"),
        "starting_origin": projection.get("origin_main"), "starting_eos_baseline": projection.get("eos_baseline"),
        "candidate_digest": candidate_digest, "candidate_paths": candidate_paths, "candidate_sources": classified.get("candidate_sources", []), "classification_digest": classified.get("classification_digest"), "candidate_authority_digest": classified["candidate_authority"].get("classification_digest"),
        "classification_authority": classified["candidate_authority"], "publication_cohort": cohort, "staged_tree_digest": None, "commit_id": None, "remote_ref": None,
        "cohort_authority_required": not bool(manifest),
        "published_head": None, "eos_synchronized_baseline": None, "prepublication_result": None, "postpublication_result": None,
        "qualification_result": None, "current_state": "PUBLICATION_DISCOVERED", "milestones": {}, "completed_milestones": [],
        "pending_milestones": list(MILESTONES), "blockers": [], "created_at": _now(), "updated_at": _now(),
        "next_authorized_action": NEXT_BY_STATE["PUBLICATION_DISCOVERED"],
    }
    _save(runtime, record)
    _record_milestone(runtime, record, "PUBLICATION_DISCOVERED", candidate_digest=candidate_digest)
    _record_milestone(runtime, record, "WORKTREE_CLASSIFIED", classification_digest=classified.get("classification_digest"))
    _record_milestone(runtime, record, "CANDIDATE_RESOLVED", candidate_paths=candidate_paths, candidate_digest=candidate_digest)
    _record_milestone(runtime, record, "CANDIDATE_ISOLATED", unrelated_paths=[item["path"] for item in classified["classification"]["paths"] if item["classification"] == "UNRELATED_DIRTY"])
    return record


def _require_state(record: Mapping[str, Any], allowed: set[str]) -> None:
    if record.get("current_state") not in allowed:
        raise PublicationTransactionError("PUBLICATION_TRANSITION_NOT_AUTHORIZED", f"current state {record.get('current_state')} does not authorize this transition", next_action=str(record.get("next_authorized_action")))


def verify(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None, postpublication: bool = False, run_validators: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_or_mission)
    _require_state(
        record,
        {"EOS_SYNCHRONIZED", "POSTPUBLICATION_VERIFIED"}
        if postpublication else {"CANDIDATE_ISOLATED", "PREPUBLICATION_VERIFIED"},
    )
    replayed = (
        "POSTPUBLICATION_VERIFIED" if postpublication else "PREPUBLICATION_VERIFIED"
    ) in (record.get("milestones") or {})
    projection = project_repository(
        root,
        runtime_root=runtime,
        mission_id=str(record.get("mission_id") or ""),
        wop_id=str(record.get("wop_id") or ""),
        publication_id=str(record.get("publication_id") or ""),
    )
    blockers: list[dict[str, str]] = []
    if projection.get("result") != "PASS":
        blockers.append({"code": "REPOSITORY_PROJECTION_INVALID", "reason": "; ".join(projection.get("errors", []))})
    if projection.get("repository_id") != record.get("repository_id"):
        blockers.append({"code": "REPOSITORY_IDENTITY_MISMATCH", "reason": "publication is bound to another repository"})
    if not postpublication:
        authority_revalidation = _revalidate_authority(root, record, runtime)
        if authority_revalidation.get("result") != "PASS":
            blockers.append({"code": "STALE_CLASSIFICATION", "reason": authority_revalidation.get("drift_inputs") or authority_revalidation.get("blocked")})
        if projection.get("head") != record.get("starting_head") or projection.get("origin_main") != record.get("starting_origin"):
            blockers.append({"code": "PUBLICATION_BASELINE_CHANGED", "reason": "repository projection changed after candidate freeze; reclassify/reprepare"})
        if projection.get("index_clean") is not True:
            blockers.append({"code": "UNEXPECTED_STAGED_PATH", "reason": "index is not clean before publication verification"})
        try:
            if _file_digest(root, list(record.get("candidate_paths") or [])) != record.get("candidate_digest"):
                blockers.append({"code": "CANDIDATE_DIGEST_CHANGED", "reason": "candidate content changed after preparation"})
        except PublicationTransactionError as error:
            blockers.append({"code": error.code, "reason": error.message})
        diff_check = _run_git(root, "diff", "--check")
        if diff_check.returncode:
            blockers.append({"code": "GIT_DIFF_CHECK_FAILED", "reason": diff_check.stderr.strip() or "git diff --check failed"})
        if run_validators:
            commands = (
                ([str(root / "scripts" / "validate_controlled_documents.py"), "--semantic-all", "--conformance", "--assurance"], "CONTROLLED_DOCUMENT_VALIDATION_FAILURE"),
                ([str(root / "scripts" / "engctl"), "registry", "validate"], "REGISTRY_VALIDATION_FAILURE"),
                ([str(root / "scripts" / "engctl"), "validate", "homelab"], "INTEGRATED_VALIDATION_FAILURE"),
                ([str(root / "scripts" / "zeus"), "platform", "verify", "--json"], "ZEUS_PLATFORM_VALIDATION_FAILURE"),
                ([str(root / "scripts" / "engctl"), "eos", "sync-validate", "homelab"], "REPOSITORY_EOS_VALIDATION_FAILURE"),
            )
            for command, code in commands:
                result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
                if result.returncode:
                    blockers.append({"code": code, "reason": result.stderr.strip() or result.stdout.strip() or "validator failed"})
            mission = verify_mission(root, str(record["mission_id"]), runtime_root=runtime)
            if mission.get("result") != "PASS":
                blockers.append({"code": "MISSION_NATIVE_VERIFICATION_FAILURE", "reason": "mission-native verification did not resolve the publication target"})
    result = "PASS" if not blockers else "FAIL"
    record["prepublication_result" if not postpublication else "postpublication_result"] = result
    record["blockers"] = blockers
    if result == "PASS" and not postpublication:
        record = _record_milestone(runtime, record, "PREPUBLICATION_VERIFIED", projection=projection)
    elif result == "PASS" and postpublication:
        record["published_head"] = projection.get("head")
        record = _record_milestone(runtime, record, "POSTPUBLICATION_VERIFIED", projection=projection)
    else:
        record["current_state"] = "FAILED"
        record["next_authorized_action"] = "RESOLVE_PUBLICATION_BLOCKER"
        record["updated_at"] = _now()
        try:
            _save(runtime, record)
        except Exception as error:
            raise PublicationTransactionError(
                "PUBLICATION_TRANSACTION_PERSISTENCE_FAILED",
                f"failed verification result could not be persisted: {error}",
                next_action="RECOVER_PUBLICATION_TRANSACTION",
            ) from error
    next_action, integrity = _resolve_next_action(runtime, record)
    if integrity["result"] != "PASS":
        result = "FAIL"
        blockers = [*blockers, {"code": "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE", "reason": integrity["errors"]}]
    return {
        **record,
        "result": result,
        "repository": projection,
        "read_only": False,
        "replayed": replayed and result == "PASS",
        "transaction_integrity": integrity,
        "next_authorized_action": next_action,
        "blockers": blockers,
    }


def stage(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_or_mission)
    _require_state(record, {"PREPUBLICATION_VERIFIED", "CANDIDATE_STAGED", "STAGED_SET_VERIFIED"})
    next_action, integrity = _resolve_next_action(runtime, record)
    if integrity["result"] != "PASS":
        raise PublicationTransactionError(
            "PREPUBLICATION_AUTHORITY_NOT_DURABLE"
            if record.get("current_state") == "PREPUBLICATION_VERIFIED"
            else "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE",
            "; ".join(integrity["errors"]),
            next_action="RECOVER_PUBLICATION_TRANSACTION",
        )
    if (record.get("current_state") == "PREPUBLICATION_VERIFIED"
            and next_action != "STAGE_PUBLICATION_CANDIDATE"):
        raise PublicationTransactionError(
            "PREPUBLICATION_AUTHORITY_NOT_DURABLE",
            "persisted PREPUBLICATION_VERIFIED authority is invalid",
            next_action="RECOVER_PUBLICATION_TRANSACTION",
        )
    if "CANDIDATE_STAGED" in record.get("milestones", {}) or "STAGED_SET_VERIFIED" in record.get("milestones", {}):
        _assert_exact_staged_candidate(root, record)
        return record
    before = _staged_paths(root)
    if before:
        staged = _assert_exact_staged_candidate(root, record)
    else:
        orphan_receipt = _receipt_path(runtime, str(record["publication_id"]), "CANDIDATE_STAGED")
        if record.get("staged_tree_digest") is not None or orphan_receipt.exists():
            raise PublicationTransactionError(
                "AMBIGUOUS_STAGE_RECOVERY_STATE",
                "staging persistence evidence exists but the authorized candidate is not staged",
            )
        authority_revalidation = _revalidate_authority(root, record, runtime)
        if authority_revalidation.get("result") != "PASS":
            raise PublicationTransactionError(
                "STALE_CLASSIFICATION",
                str(authority_revalidation.get("drift_inputs") or authority_revalidation.get("blocked") or "publication authority changed"),
                next_action="REPREPARE_PUBLICATION_TRANSACTION",
            )
        result = _run_git(root, "add", "--", *record["candidate_paths"])
        if result.returncode:
            raise PublicationTransactionError("EXACT_STAGING_FAILED", result.stderr.strip() or "git add failed")
        staged = _assert_exact_staged_candidate(root, record)
    record["staged_tree_digest"] = staged["staged_tree_digest"]
    record["staged_tree_digest_semantics"] = staged["staged_tree_digest_semantics"]
    return _record_milestone(
        runtime, record, "CANDIDATE_STAGED",
        staged_paths=staged["staged_paths"],
        staged_tree_digest=staged["staged_tree_digest"],
        staged_tree_digest_semantics=staged["staged_tree_digest_semantics"],
    )


def verify_staged(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Perform the explicit staged-set verification transition."""
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_or_mission)
    _require_state(record, {"CANDIDATE_STAGED", "STAGED_SET_VERIFIED"})
    integrity = _transaction_integrity(runtime, record)
    if integrity["result"] != "PASS":
        raise PublicationTransactionError(
            "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE", "; ".join(integrity["errors"]),
            next_action="RECOVER_PUBLICATION_TRANSACTION",
        )
    staged = _assert_exact_staged_candidate(root, record)
    if "STAGED_SET_VERIFIED" in record.get("milestones", {}):
        return record
    return _record_milestone(
        runtime, record, "STAGED_SET_VERIFIED",
        staged_paths=staged["staged_paths"],
        staged_tree_digest=staged["staged_tree_digest"],
        staged_tree_digest_semantics=staged["staged_tree_digest_semantics"],
    )


def commit(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_or_mission)
    if "COMMIT_CREATED" in record.get("milestones", {}):
        return record
    _require_state(record, {"STAGED_SET_VERIFIED"})
    integrity = _transaction_integrity(runtime, record)
    if integrity["result"] != "PASS":
        raise PublicationTransactionError(
            "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE", "; ".join(integrity["errors"]),
            next_action="RECOVER_PUBLICATION_TRANSACTION",
        )
    _assert_exact_staged_candidate(root, record)
    message = f"Zeus publication {record['publication_id']}"
    result = _run_git(root, "commit", "-m", message)
    if result.returncode:
        raise PublicationTransactionError("COMMIT_FAILED", result.stderr.strip() or result.stdout.strip() or "git commit failed")
    commit_id = _git(root, "rev-parse", "HEAD")
    record["commit_id"] = commit_id
    return _record_milestone(runtime, record, "COMMIT_CREATED", commit_id=commit_id, parent_id=_git(root, "rev-parse", "HEAD^") if _run_git(root, "rev-parse", "HEAD^").returncode == 0 else None)


def push(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_or_mission)
    if "REMOTE_PUBLISHED" in record.get("milestones", {}):
        return record
    _require_state(record, {"COMMIT_CREATED"})
    commit_id = _git(root, "rev-parse", "HEAD")
    if commit_id != record.get("commit_id"):
        raise PublicationTransactionError("COMMIT_IDENTITY_MISMATCH", "HEAD is not the publication commit")
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["ZEUS_PUBLICATION_AUTHORITY"] = "EXPLICIT_GOVERNED_PUBLICATION"
    result = subprocess.run(["git", "-C", str(root), "push", "origin", "HEAD:refs/heads/main"], capture_output=True, text=True, check=False, env=env)
    if result.returncode:
        raise PublicationTransactionError("PUSH_FAILED", result.stderr.strip() or result.stdout.strip() or "git push failed")
    fetched = _run_git(root, "fetch", "--prune", "origin", "main")
    if fetched.returncode:
        raise PublicationTransactionError("REMOTE_PROJECTION_FAILED", fetched.stderr.strip() or "unable to refresh origin/main after push")
    origin = _git(root, "rev-parse", "refs/remotes/origin/main")
    if origin != commit_id:
        raise PublicationTransactionError("POST_PUSH_PARITY_FAILED", "origin/main does not resolve to the publication commit")
    record["remote_ref"] = "refs/heads/main"
    record["published_head"] = origin
    return _record_milestone(runtime, record, "REMOTE_PUBLISHED", commit_id=commit_id, remote_ref=record["remote_ref"], published_head=origin)


def synchronize(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None, eos_workspace: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_or_mission)
    if "EOS_SYNCHRONIZED" in record.get("milestones", {}):
        return record
    _require_state(record, {"REMOTE_PUBLISHED"})
    command = [str(root / "scripts" / "engctl"), "eos", "synchronize", "homelab"]
    env = dict(os.environ)
    if eos_workspace:
        env["EOS_WORKSPACE"] = str(Path(eos_workspace).resolve())
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False, env=env)
    if result.returncode:
        raise PublicationTransactionError("EOS_SYNCHRONIZATION_FAILED", result.stderr.strip() or result.stdout.strip() or "EOS synchronization failed")
    projection = project_repository(
        root,
        eos_workspace,
        runtime_root=runtime,
        mission_id=str(record.get("mission_id") or ""),
        wop_id=str(record.get("wop_id") or ""),
        publication_id=str(record.get("publication_id") or ""),
    )
    if projection.get("eos_parity") is not True:
        raise PublicationTransactionError("EOS_PARITY_FAILED", "EOS does not project the published repository baseline")
    record["eos_synchronized_baseline"] = projection.get("eos_baseline")
    return _record_milestone(runtime, record, "EOS_SYNCHRONIZED", eos_baseline=projection.get("eos_baseline"))


def qualify(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_or_mission)
    if "PUBLICATION_QUALIFIED" in record.get("milestones", {}):
        return record
    _require_state(record, {"POSTPUBLICATION_VERIFIED"})
    if record.get("blockers"):
        raise PublicationTransactionError("PUBLICATION_BLOCKED", "publication has unresolved blockers")
    record["qualification_result"] = "PASS"
    return _record_milestone(runtime, record, "PUBLICATION_QUALIFIED", qualification="PASS")


def status(root: Path | str, publication_or_mission: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=False)
    mission_scoped = not str(publication_or_mission).startswith("PUBLICATION-")
    record = _load_transaction(runtime, publication_or_mission)
    # Mission lookup answers which durable transaction is current.  Candidate
    # content revalidation belongs to direct transaction status and the
    # prepublication verification gate; otherwise engineering a corrective to
    # the resolver would itself make current-transaction lookup impossible.
    revalidation = (
        {"result": "PASS", "read_only": True, "scope": "CURRENT_TRANSACTION_RESOLUTION",
         "live_resolved_cohort_id": record.get("publication_cohort_id")}
        if mission_scoped else _revalidate_authority(root, record, runtime)
    )
    next_action, integrity = _resolve_next_action(runtime, record, authority_revalidation=revalidation)
    blockers = [] if revalidation.get("result") == "PASS" else [{
        "code": "STALE_CLASSIFICATION", "reason": revalidation.get("drift_inputs") or revalidation.get("blocked")
    }]
    if integrity["result"] != "PASS":
        blockers.append({"code": "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE", "reason": integrity["errors"]})
    lineage = _mission_lineage(runtime, str(record.get("mission_id") or ""))
    disposition = lineage.get("dispositions", {}).get(record.get("publication_id"), "UNRESOLVED")
    predecessor_ids: list[str] = []
    inventory, _ = _transaction_inventory(runtime)
    by_id = {value.get("publication_id"): value for value in inventory}
    cursor = record
    seen: set[str] = set()
    while cursor.get("supersedes_publication_id"):
        predecessor = str(cursor.get("supersedes_publication_id"))
        if predecessor in seen:
            break
        seen.add(predecessor)
        predecessor_ids.append(predecessor)
        cursor = by_id.get(predecessor) or {}
    return {
        **record, "result": "PASS" if revalidation.get("result") == "PASS" and integrity["result"] == "PASS" else "FAIL", "read_only": True,
        "candidate_count": len(record.get("candidate_paths") or []),
        "candidate_authority_revalidation": revalidation,
        "transaction_integrity": integrity,
        "blockers": blockers,
        "live_resolved_cohort_id": revalidation.get("live_resolved_cohort_id"),
        "publication_disposition": disposition,
        "current_publication": disposition in {"CURRENT", "CURRENT_QUALIFIED"},
        "supersession_lineage": predecessor_ids,
        "publication_lineage": lineage,
        "next_authorized_action": next_action,
    }


def mission_projection(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Expose publication state as a subordinate mission-native projection."""
    try:
        value = inspect(root, mission_id, runtime_root=runtime_root)
        lineage = value.get("publication_lineage") or {}
        existing = list(lineage.get("current") or [])
        if lineage.get("result") != "PASS":
            return {
                "result": "FAIL", "publication_required": True,
                "publication_id": None, "publication_state": "UNRESOLVED",
                "publication_blockers": lineage.get("errors") or [{"code": "PUBLICATION_CARDINALITY_CONFLICT", "reason": "current publication transaction lineage is unresolved"}],
                "candidate_digest": None, "published_head": None,
                "eos_synchronized_baseline": None, "postpublication_result": None,
                "qualification_result": None, "next_authorized_action": "STOP_FAIL_CLOSED", "read_only": True,
            }
        if existing:
            record = existing[0]
            if value.get("result") != "PASS" and (
                value.get("candidate_authority", {}).get("ambiguous")
            ):
                return {
                    "result": "FAIL", "publication_required": True,
                    "publication_id": record.get("publication_id"), "publication_state": "AUTHORITY_UNRESOLVED",
                    "publication_cohort_id": record.get("publication_cohort_id"),
                    "publication_blockers": value.get("candidate_authority", {}).get("ambiguous")
                    or value.get("candidate_authority", {}).get("blocked")
                    or [{"code": "CANDIDATE_AUTHORITY_UNRESOLVED", "reason": "current publication candidate authority did not resolve"}],
                    "candidate_digest": record.get("candidate_digest"),
                    "published_head": record.get("published_head"),
                    "eos_synchronized_baseline": record.get("eos_synchronized_baseline"),
                    "postpublication_result": record.get("postpublication_result"),
                    "qualification_result": record.get("qualification_result"),
                    "next_authorized_action": value.get("next_authorized_action", "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY"),
                    "read_only": True,
                }
            projected = status(root, str(record.get("publication_id")), runtime_root=runtime_root)
            return {
                "result": projected.get("result", "FAIL"), "publication_required": True,
                "publication_id": projected.get("publication_id"), "publication_state": projected.get("current_state"),
                "publication_cohort_id": projected.get("publication_cohort_id"),
                "publication_blockers": projected.get("blockers", []), "candidate_digest": projected.get("candidate_digest"),
                "prepublication_result": projected.get("prepublication_result"),
                "completed_milestones": projected.get("completed_milestones", []),
                "pending_milestones": projected.get("pending_milestones", []),
                "transaction_integrity": projected.get("transaction_integrity"),
                "published_head": projected.get("published_head"), "eos_synchronized_baseline": projected.get("eos_synchronized_baseline"),
                "postpublication_result": projected.get("postpublication_result"), "qualification_result": projected.get("qualification_result"),
                "next_authorized_action": projected.get("next_authorized_action"), "read_only": True,
            }
        return {
            "result": value.get("result", "FAIL"), "publication_required": True, "publication_id": None,
            "publication_cohort_id": None,
            "publication_state": "NOT_STARTED", "publication_blockers": value.get("publication_blockers", []),
            "candidate_digest": None, "published_head": None, "eos_synchronized_baseline": None,
            "postpublication_result": "NOT_STARTED", "qualification_result": "NOT_STARTED",
            "next_authorized_action": value.get("next_authorized_action", "INSPECT_PUBLICATION_CANDIDATE"), "read_only": True,
        }
    except Exception as error:
        return {"result": "FAIL", "publication_required": True, "publication_state": "UNRESOLVED", "publication_blockers": [{"code": "PUBLICATION_PROJECTION_FAILED", "message": str(error)}], "next_authorized_action": "STOP_FAIL_CLOSED", "read_only": True}


def resume(root: Path | str, publication_id: str, *, runtime_root: Path | str | None = None, approve: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=False)
    record = _load_transaction(runtime, publication_id)
    revalidation = None
    if record.get("current_state") in {"CANDIDATE_ISOLATED", "PREPUBLICATION_VERIFIED"}:
        revalidation = _revalidate_authority(root, record, runtime)
        if revalidation.get("result") != "PASS":
            return {**record, "result": "FAIL", "read_only": True,
                    "candidate_authority_revalidation": revalidation,
                    "blockers": [{"code": "STALE_CLASSIFICATION", "reason": revalidation.get("drift_inputs") or revalidation.get("blocked")}],
                    "next_authorized_action": "REPREPARE_PUBLICATION_TRANSACTION"}
    action, integrity = _resolve_next_action(runtime, record, authority_revalidation=revalidation)
    if integrity["result"] != "PASS":
        return {**record, "result": "FAIL", "read_only": True,
                "transaction_integrity": integrity,
                "blockers": [{"code": "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE", "reason": integrity["errors"]}],
                "next_authorized_action": action}
    if not approve:
        return {**record, "result": "READY_FOR_REVIEW", "read_only": True, "next_authorized_action": action}
    if action == "STAGE_PUBLICATION_CANDIDATE": return stage(root, publication_id, runtime_root=runtime)
    if action == "VERIFY_STAGED_SET": return verify_staged(root, publication_id, runtime_root=runtime)
    if action == "COMMIT_PUBLICATION": return commit(root, publication_id, runtime_root=runtime)
    if action == "PUSH_PUBLICATION": return push(root, publication_id, runtime_root=runtime)
    if action == "SYNCHRONIZE_EOS": return synchronize(root, publication_id, runtime_root=runtime)
    if action == "VERIFY_POSTPUBLICATION_STATE": return verify(root, publication_id, runtime_root=runtime, postpublication=True)
    if action == "QUALIFY_PUBLICATION": return qualify(root, publication_id, runtime_root=runtime)
    return {**record, "result": "PASS", "read_only": True, "next_authorized_action": action}


def abort(root: Path | str, publication_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    runtime = _runtime(root, runtime_root, writable=True)
    record = _load_transaction(runtime, publication_id)
    if record.get("current_state") in {"REMOTE_PUBLISHED", "EOS_SYNCHRONIZED", "POSTPUBLICATION_VERIFIED", "PUBLICATION_QUALIFIED"}:
        raise PublicationTransactionError("PUBLICATION_ALREADY_PUBLISHED", "published history cannot be rewritten by abort")
    if record.get("current_state") in {"CANDIDATE_STAGED", "STAGED_SET_VERIFIED"}:
        restored = _run_git(root, "restore", "--staged", "--", *record.get("candidate_paths", []))
        if restored.returncode:
            raise PublicationTransactionError("ABORT_UNSTAGE_FAILED", restored.stderr.strip() or "unable to unstage the frozen candidate")
    record["current_state"] = "ABORTED"
    record["next_authorized_action"] = "PUBLICATION_ABORTED"
    record["updated_at"] = _now()
    receipt = Path(_immutable_receipt(runtime, record, "PUBLICATION_ABORTED", "PASS", abort_reason="operator abort; no history rewrite"))
    record["abort_receipt"] = {"receipt_path": str(receipt), "receipt_digest": _safe_load(receipt).get("receipt_digest")}
    _save(runtime, record)
    return record


def run(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None, manifest: Path | str | None = None, approve: bool = False, run_validators: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    if not approve:
        return {"result": "READY_FOR_REVIEW", "read_only": True, "mission_id": mission_id, "inspection": inspect(root, mission_id, runtime_root=runtime_root), "next_authorized_action": "APPROVE_PUBLICATION"}
    record = prepare(root, mission_id, runtime_root=runtime_root, manifest=manifest)
    verified = verify(root, record["publication_id"], runtime_root=runtime_root, run_validators=run_validators)
    if verified.get("result") != "PASS": return verified
    record = stage(root, record["publication_id"], runtime_root=runtime_root)
    record = verify_staged(root, record["publication_id"], runtime_root=runtime_root)
    record = commit(root, record["publication_id"], runtime_root=runtime_root)
    record = push(root, record["publication_id"], runtime_root=runtime_root)
    record = synchronize(root, record["publication_id"], runtime_root=runtime_root)
    record = verify(root, record["publication_id"], runtime_root=runtime_root, postpublication=True)
    return qualify(root, record["publication_id"], runtime_root=runtime_root)


def render(value: Mapping[str, Any]) -> str:
    repository = value.get("repository") or {}
    return "\n".join((
        "Zeus Publication Transaction", "============================", f"Result       : {value.get('result', 'PASS')}",
        f"Publication   : {value.get('publication_id', 'UNRESOLVED')}", f"Mission       : {value.get('mission_id', 'UNRESOLVED')}",
        f"State         : {value.get('current_state', value.get('publication_state', 'UNRESOLVED'))}",
        f"HEAD          : {repository.get('head', value.get('published_head', 'UNRESOLVED'))}",
        f"Candidate     : {len(value.get('candidate_paths') or value.get('candidate_paths', []))}",
        f"Blockers      : {', '.join(item.get('code', 'UNKNOWN') for item in value.get('blockers', [])) or 'NONE'}",
        f"Next action   : {value.get('next_authorized_action', 'UNRESOLVED')}",
        f"Read-only     : {'YES' if value.get('read_only') else 'NO'}",
    ))
