"""Transactional adoption of legacy and canonical Zeus runtime state."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.emp.runtime_paths import runtime_identity
from scripts.lib.emp.submission_boundary import mission_view as p2_mission_view


class RuntimeAdoptionError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: list[dict[str, str]] | None = None):
        self.diagnostics = diagnostics or []
        super().__init__(message)


def _digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _inventory(root: Path) -> dict[str, Any]:
    return {"files": sum(1 for p in root.rglob("*") if p.is_file()), "digest": _digest_tree(root)}


def _baselines(repository: Path) -> dict[str, str]:
    values = {}
    for tag in ("OA-v1.0.0", "OB-PLAN-v1.0.0"):
        import subprocess
        result = subprocess.run(["git", "-C", str(repository), "rev-parse", f"refs/tags/{tag}"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeAdoptionError(f"protected baseline tag unavailable: {tag}")
        values[tag] = result.stdout.strip()
    return values


def _verify(source: Path, repository: Path, destination: Path) -> dict[str, Any]:
    if not source.is_dir():
        raise RuntimeAdoptionError("legacy runtime source is not a directory")
    if source.resolve() == repository.resolve() or repository.resolve() in source.resolve().parents:
        raise RuntimeAdoptionError("runtime source is inside the repository")
    if not os.access(source, os.R_OK | os.X_OK) or not os.access(source.parent, os.W_OK | os.X_OK):
        raise RuntimeAdoptionError("legacy runtime is not safely readable/writable")
    evidence = source / "evidence" / "bootstrap-evidence.json"
    if not evidence.is_file():
        raise RuntimeAdoptionError("LEGACY_RUNTIME_REQUIRES_ADOPTION: bootstrap evidence is missing")
    try:
        bootstrap = json.loads(evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeAdoptionError(f"bootstrap evidence is invalid: {error}") from error
    if bootstrap.get("repository_root") != str(repository.resolve()):
        raise RuntimeAdoptionError("legacy runtime repository root does not match this repository")
    if bootstrap.get("schema_version") != 1:
        raise RuntimeAdoptionError("legacy runtime schema is incompatible")
    required_state = (source / "orchestration-state.json", source / "stage1", source / "stage1" / "eens")
    if any(not path.exists() for path in required_state):
        raise RuntimeAdoptionError("legacy runtime history or EENS evidence is incomplete")
    identity = runtime_identity(repository)
    destination_existing = destination.exists()
    if destination_existing and not destination.is_dir():
        raise RuntimeAdoptionError("canonical runtime destination is not a directory")
    marker = destination / "runtime-identity.json"
    if marker.is_file():
        try:
            value = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeAdoptionError(f"canonical runtime identity is invalid: {error}") from error
        if value.get("repository_fingerprint") != identity["repository_fingerprint"]:
            raise RuntimeAdoptionError("canonical runtime belongs to another repository")
    baselines = _baselines(repository)
    declared_baselines = bootstrap.get("protected_baselines")
    if isinstance(declared_baselines, dict):
        for tag, expected in baselines.items():
            if declared_baselines.get(tag) not in (None, expected):
                raise RuntimeAdoptionError(f"protected baseline mismatch: {tag}")
    source_inventory = _inventory(source)
    adoption_id = hashlib.sha256((str(source.resolve()) + source_inventory["digest"] + identity["repository_fingerprint"]).encode()).hexdigest()[:24]
    return {"identity": identity, "baselines": baselines, "source_inventory": source_inventory,
            "destination_inventory": _inventory(destination) if destination_existing else None,
            "adoption_id": adoption_id, "source": str(source.resolve()), "destination": str(destination.resolve()),
            "bootstrap": bootstrap}


def _canonical_submission_records(root: Path) -> list[tuple[Path, dict[str, Any], Path]]:
    """Return the P2 receipt/request pairs eligible for durable adoption."""
    receipts = sorted((root / "submissions" / "receipts").glob("*.json"))
    if not receipts:
        raise RuntimeAdoptionError(
            "CANONICAL_SUBMISSION_REQUIRES_RECEIPTS: no P2 submission receipts found"
        )
    records: list[tuple[Path, dict[str, Any], Path]] = []
    for receipt_path in receipts:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise RuntimeAdoptionError(
                f"canonical submission receipt is unreadable: {receipt_path}: {error}"
            ) from error
        if not isinstance(receipt, dict) or receipt.get("receipt_type") != "submission":
            raise RuntimeAdoptionError(
                f"canonical submission receipt is invalid: {receipt_path}"
            )
        request_path = root / "submissions" / "requests" / f"{receipt.get('admission_request_id')}.json"
        if not request_path.is_file():
            raise RuntimeAdoptionError(
                f"canonical submission request is missing: {request_path}"
            )
        records.append((receipt_path, receipt, request_path))
    return records


def _verify_canonical_submissions(source: Path, repository: Path, destination: Path) -> dict[str, Any]:
    """Validate a temporary P2 transaction without adopting unrelated files."""
    if not source.is_dir():
        raise RuntimeAdoptionError("canonical runtime source is not a directory")
    if source.resolve() == repository.resolve() or repository.resolve() in source.resolve().parents:
        raise RuntimeAdoptionError("runtime source is inside the repository")
    if not os.access(source, os.R_OK | os.X_OK):
        raise RuntimeAdoptionError("canonical runtime is not safely readable")
    identity = runtime_identity(repository)
    marker_path = source / "runtime-identity.json"
    if not marker_path.is_file():
        raise RuntimeAdoptionError("canonical runtime repository binding is missing")
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeAdoptionError(f"canonical runtime identity is invalid: {error}") from error
    if any(marker.get(field) != identity[field] for field in ("repository", "repository_identity", "repository_fingerprint", "repository_id")):
        raise RuntimeAdoptionError("canonical runtime belongs to another repository")

    records = _canonical_submission_records(source)
    missions: dict[str, str] = {}
    selected: list[dict[str, Any]] = []
    for receipt_path, receipt, request_path in records:
        mission = str(receipt.get("mission_id", "")).upper()
        if not mission:
            raise RuntimeAdoptionError(f"canonical submission mission identity is missing: {receipt_path}")
        if mission in missions and missions[mission] != str(receipt.get("submission_id")):
            raise RuntimeAdoptionError(
                f"multiple competing canonical receipts for mission: {mission}"
            )
        missions[mission] = str(receipt.get("submission_id"))
        projected = p2_mission_view(source / "submissions", mission, "snapshot")
        if projected.get("result") != "PASS":
            raise RuntimeAdoptionError(
                f"canonical submission cannot be adopted for {mission}: "
                f"{projected.get('result', 'FAIL')}"
            )
        repository_identity = receipt.get("repository_identity")
        if not isinstance(repository_identity, dict):
            raise RuntimeAdoptionError(f"canonical submission repository identity is missing: {receipt_path}")
        expected_repository_fields = {
            "canonical_repository_identity": identity["repository"],
            "repository_identity": identity["repository_identity"],
            "repository_fingerprint": identity["repository_fingerprint"],
            "repository_id": identity["repository_id"],
        }
        if any(repository_identity.get(field) != expected for field, expected in expected_repository_fields.items()):
            raise RuntimeAdoptionError(f"canonical submission repository identity mismatch: {receipt_path}")
        selected.extend([
            {"relative_path": str(receipt_path.relative_to(source)), "digest": hashlib.sha256(receipt_path.read_bytes()).hexdigest()},
            {"relative_path": str(request_path.relative_to(source)), "digest": hashlib.sha256(request_path.read_bytes()).hexdigest()},
        ])

    # A canonical adoption identity is derived from content and repository
    # identity, never from the temporary directory name.
    adoption_payload = {
        "repository_fingerprint": identity["repository_fingerprint"],
        "records": sorted(selected, key=lambda item: item["relative_path"]),
    }
    adoption_id = hashlib.sha256(
        json.dumps(adoption_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    if destination.exists() and not destination.is_dir():
        raise RuntimeAdoptionError("canonical runtime destination is not a directory")
    destination_marker = destination / "runtime-identity.json"
    if destination_marker.is_file():
        try:
            value = json.loads(destination_marker.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise RuntimeAdoptionError(f"canonical runtime identity is invalid: {error}") from error
        if value.get("repository_fingerprint") != identity["repository_fingerprint"]:
            raise RuntimeAdoptionError("canonical runtime belongs to another repository")

    # Existing current P2 records are immutable.  A same-identity byte match
    # is replay; a different receipt for the same mission is a hard conflict.
    for receipt_path, receipt, request_path in records:
        mission = str(receipt.get("mission_id", "")).upper()
        existing = []
        if destination.exists():
            for candidate in sorted((destination / "submissions" / "receipts").glob("*.json")):
                try:
                    value = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    continue
                if str(value.get("mission_id", "")).upper() == mission:
                    existing.append(candidate)
        if len(existing) > 1:
            raise RuntimeAdoptionError(f"canonical runtime has multiple receipts for mission: {mission}")
        if existing and existing[0].read_bytes() != receipt_path.read_bytes():
            raise RuntimeAdoptionError(f"canonical runtime has a conflicting receipt for mission: {mission}")

    source_inventory = _inventory(source)
    return {
        "identity": identity,
        "source": str(source.resolve()),
        "destination": str(destination.resolve()),
        "source_inventory": source_inventory,
        "adoption_id": adoption_id,
        "records": selected,
        "missions": sorted(missions),
        "submission_ids": sorted(missions.values()),
    }


def _adopt_canonical_submissions(repository: Path, source_path: Path, destination: Path, *, dry_run: bool) -> dict[str, Any]:
    report = _verify_canonical_submissions(source_path, repository, destination)
    lock_parent = destination.parent
    lock_parent.mkdir(parents=True, exist_ok=True)
    lock_path = lock_parent / ".zeus-runtime-adoption.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeAdoptionError("another runtime adoption is active") from error
        manifest = {
            "schema_version": 1,
            "adoption_type": "CANONICAL_P2_SUBMISSION",
            "adoption_id": report["adoption_id"],
            "repository": report["identity"],
            "source": report["source"],
            "destination": report["destination"],
            "source_inventory": report["source_inventory"],
            "missions": report["missions"],
            "submission_ids": report["submission_ids"],
            "records": report["records"],
        }
        manifest_path = destination / "canonical-submission-adoption.json"
        if manifest_path.is_file():
            try:
                existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise RuntimeAdoptionError(f"canonical adoption manifest is invalid: {error}") from error
            # The temporary source path is transaction metadata, not part of
            # canonical identity.  Replaying from an equivalent temporary
            # directory must therefore compare the content-bound fields only.
            comparable_existing = dict(existing_manifest)
            comparable_manifest = dict(manifest)
            comparable_existing.pop("source", None)
            comparable_manifest.pop("source", None)
            comparable_existing.pop("source_inventory", None)
            comparable_manifest.pop("source_inventory", None)
            if comparable_existing != comparable_manifest:
                raise RuntimeAdoptionError("canonical runtime has a different canonical adoption identity")
            report.update({"result": "PASS", "action": "ALREADY_ADOPTED", "dry_run": dry_run, "manifest": str(manifest_path)})
            return report
        if dry_run:
            report.update({"result": "PASS", "action": "ADOPT_CANONICAL_SUBMISSION", "dry_run": True, "manifest": str(manifest_path)})
            return report

        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".zeus-runtime-adopt-", dir=str(destination.parent)))
        staged = staging / destination.name
        backup = destination.parent / f".zeus-runtime-backup-{report['adoption_id']}"
        try:
            if destination.exists():
                shutil.copytree(destination, staged, ignore=shutil.ignore_patterns("*.lock"))
            else:
                staged.mkdir(parents=True)
            for record in report["records"]:
                relative = Path(record["relative_path"])
                source_file = source_path / relative
                target = staged / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.read_bytes() != source_file.read_bytes():
                    raise RuntimeAdoptionError(f"canonical runtime conflict: {relative}")
                if not target.exists():
                    shutil.copy2(source_file, target)
            marker_payload = {**report["identity"], "runtime_root": str(destination)}
            (staged / "runtime-identity.json").write_text(json.dumps(marker_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (staged / "canonical-submission-adoption.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if destination.exists():
                os.replace(destination, backup)
            os.replace(staged, destination)
            shutil.rmtree(backup, ignore_errors=True)
            staging.rmdir()
        except Exception:
            if not destination.exists() and backup.exists():
                os.replace(backup, destination)
            shutil.rmtree(staging, ignore_errors=True)
            raise
        report.update({"result": "PASS", "action": "ADOPTED_CANONICAL_SUBMISSION", "dry_run": False, "manifest": str(manifest_path)})
        return report


def adopt(repository: Path | str, *, source: Path | str | None = None, dry_run: bool = False) -> dict[str, Any]:
    repository = Path(repository).resolve()
    identity = runtime_identity(repository)
    destination = Path.home() / ".local" / "state" / "zeus-runtime" / identity["repository_id"]
    source_path = Path(source).expanduser().resolve() if source else Path.home() / ".local" / "state" / "zeus-runtime" / repository.name
    if (source_path / "submissions" / "receipts").is_dir():
        return _adopt_canonical_submissions(repository, source_path, destination, dry_run=dry_run)
    report = _verify(source_path, repository, destination)
    lock_parent = source_path.parent
    lock_parent.mkdir(parents=True, exist_ok=True)
    temporary_lock = tempfile.NamedTemporaryFile(prefix="zeus-runtime-adopt-lock-", delete=False)
    lock_path = Path(temporary_lock.name) if dry_run else lock_parent / ".zeus-runtime-adoption.lock"
    temporary_lock.close()
    if not dry_run:
        lock_path.unlink(missing_ok=True)
    try:
        lock = lock_path.open("a+")
    except OSError as error:
        raise RuntimeAdoptionError(f"cannot create runtime adoption lock: {error}") from error
    try:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeAdoptionError("another runtime adoption is active") from error
        binding = {"schema_version": 1, "repository_root": str(repository), "repository_identity": "homelab", "repository_fingerprint": identity["repository_fingerprint"], "runtime_identity": identity["repository_id"], "runtime_root": str(destination), "protected_baselines": report["baselines"], "adopted_from": str(source_path), "adoption_id": report["adoption_id"]}
        report["binding"] = binding
        report["action"] = "ALREADY_ADOPTED" if (destination / "runtime-binding.yaml").is_file() else "MIGRATED"
        if dry_run:
            report["result"] = "PASS"; report["dry_run"] = True; return report
        if (destination / "runtime-binding.yaml").is_file():
            existing = yaml.safe_load((destination / "runtime-binding.yaml").read_text(encoding="utf-8")) or {}
            if existing.get("adoption_id") != binding["adoption_id"]:
                raise RuntimeAdoptionError("canonical runtime has a different adoption identity")
            report["result"] = "PASS"; report["dry_run"] = False; return report
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".zeus-runtime-adopt-", dir=str(destination.parent)))
        backup = destination.parent / f".zeus-runtime-backup-{report['adoption_id']}"
        try:
            shutil.copytree(source_path, staging / destination.name)
            staged = staging / destination.name
            if destination.exists():
                for item in destination.iterdir():
                    target = staged / item.name
                    if item.name in {"operator-interface-state.json", "operator-interface-state.json.lock"}:
                        continue
                    if target.exists() and item.is_file() and target.read_bytes() != item.read_bytes():
                        raise RuntimeAdoptionError(f"canonical runtime conflict: {item.name}")
                    if not target.exists():
                        shutil.copy2(item, target) if item.is_file() else shutil.copytree(item, target)
            marker_payload = {**identity, "runtime_root": str(destination)}
            (staged / "runtime-identity.json").write_text(json.dumps(marker_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (staged / "runtime-binding.yaml").write_text(yaml.safe_dump(binding, sort_keys=False), encoding="utf-8")
            checkpoint = {"adoption_id": report["adoption_id"], "source": report["source"], "destination": report["destination"], "source_inventory": report["source_inventory"], "created_at": datetime.now(timezone.utc).isoformat()}
            (staged / "adoption-checkpoint.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if destination.exists(): os.replace(destination, backup)
            os.replace(staged, destination)
            shutil.rmtree(backup, ignore_errors=True); staging.rmdir()
        except Exception:
            if not destination.exists() and backup.exists(): os.replace(backup, destination)
            shutil.rmtree(staging, ignore_errors=True); raise
        report["result"] = "PASS"; report["dry_run"] = False; return report
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN); lock.close()
        if dry_run: lock_path.unlink(missing_ok=True)
