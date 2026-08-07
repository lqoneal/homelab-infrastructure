#!/usr/bin/env python3
"""Zeus Stage 1 package validation, mission admission, and staging."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import subprocess
import tarfile
import tempfile
import uuid
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

import yaml

from scripts.lib.eos.mission_contract import Resolver


class Stage1Error(ValueError):
    """A Stage 1 submission cannot be admitted safely."""

    def __init__(self, message: str, *, evidence: Mapping[str, Any] | None = None):
        self.evidence = dict(evidence or {})
        super().__init__(message)


AUTHORITY_FAILURE = "AUTHORITY_CHAIN_INTEGRITY_FAILURE"
RECOVERY_SCHEMA_VERSION = 3
HYDRATION_SCHEMA_VERSION = 1
BASELINE_CLASSIFICATIONS = {
    "EXACT_SUBMISSION_BASELINE",
    "AUTHORIZED_PUBLICATION_SUCCESSOR",
    "AUTHORIZED_RECOVERY_BASELINE",
    "UNCOMMITTED_WORKING_TREE_DRIFT",
    "UNRELATED_REPOSITORY_HISTORY",
    "REWOUND_REPOSITORY_HISTORY",
    "AMBIGUOUS_PUBLICATION_TRANSITION",
    "PROTECTED_BASELINE_MUTATION",
    "REPOSITORY_IDENTITY_MISMATCH",
}


ACTIVE_STATES = {"VALIDATING", "ADMITTED", "STAGED", "VALIDATED", "PACKAGED", "REGISTERED", "AUTHORIZED", "AWAITING_EXECUTION_DISPATCH", "DISPATCHED", "EXECUTING", "QUALIFYING", "QUALIFIED", "PUBLICATION_READY", "PUBLISHED", "SYNCHRONIZING", "SYNCHRONIZED", "CLOSING", "INTERRUPTED", "BLOCKED"}
MISSION_STATES = ("VALIDATING", "REJECTED", "ADMITTED", "STAGED", "VALIDATED", "PACKAGED", "REGISTERED", "AUTHORIZED", "AWAITING_EXECUTION_DISPATCH", "DISPATCHED", "EXECUTING", "QUALIFYING", "QUALIFIED", "PUBLICATION_READY", "PUBLISHED", "SYNCHRONIZING", "SYNCHRONIZED", "CLOSING", "INTERRUPTED", "BLOCKED", "CLOSED")
MISSION_CONTRACT_FIELDS = (
    "mission_id",
    "wop_id",
    "objective",
    "scope",
    "dependencies",
    "priority",
    "candidate_state",
)
REQUIRED_COMPONENTS = {
    "bootstrap": ("bootstrap.md", "bootstrap.yaml", "bootstrap.yml"),
    "roadmap": ("roadmap.md", "roadmap.yaml", "roadmap.yml"),
    "mission_metadata": ("mission.yaml", "mission.yml", "mission.json"),
    "gate_definitions": ("gates.yaml", "gates.yml", "gates.json"),
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _dispatch_receipt_valid(receipt: Mapping[str, Any], record: Mapping[str, Any]) -> tuple[bool, str]:
    """Validate the minimum receipt chain before exposing DISPATCHED."""
    required = (
        "receipt_id", "receipt_digest", "wop_id", "instance_id", "package_digest",
        "repository", "provider_id", "agent_id", "qualification_id", "registry_digest",
        "selection", "dispatch_plan_digest", "authority_snapshot_digest",
    )
    missing = [field for field in required if not receipt.get(field)]
    if missing:
        return False, "missing dispatch receipt fields: " + ", ".join(missing)
    supplied_digest = receipt.get("receipt_digest")
    digest_body = dict(receipt)
    digest_body.pop("receipt_digest", None)
    if supplied_digest != _digest(digest_body):
        return False, "dispatch receipt digest mismatch"
    if receipt.get("wop_id") != record.get("wop_id") or receipt.get("instance_id") != record.get("instance_id"):
        return False, "dispatch receipt transaction identity mismatch"
    if receipt.get("package_digest") != record.get("package_digest"):
        return False, "dispatch receipt package identity mismatch"
    selection = (record.get("receipts") or {}).get("provider_selection")
    selection_fields = ("receipt_id", "receipt_digest", "transaction_id", "wop_id",
                        "agent_id", "provider_id", "selection_policy", "registry_digest",
                        "authority_snapshot_digest")
    if not isinstance(selection, Mapping) or any(not selection.get(field) for field in selection_fields):
        return False, "provider-selection receipt is incomplete"
    selection_unsigned = dict(selection)
    selection_digest = selection_unsigned.pop("receipt_digest", None)
    if not selection_digest or selection_digest != _digest(selection_unsigned):
        return False, "provider-selection receipt digest mismatch"
    if selection.get("transaction_id") != record.get("instance_id"):
        return False, "provider-selection transaction identity mismatch"
    if selection.get("agent_id") != receipt.get("agent_id") or selection.get("provider_id") != receipt.get("provider_id"):
        return False, "provider-selection binding mismatch"
    snapshot = record.get("authority_snapshot") or {}
    if receipt.get("authority_snapshot_digest") != snapshot.get("authority_snapshot_digest"):
        return False, "dispatch receipt authority snapshot mismatch"
    return True, "PASS"


def _authority_snapshot(record: Mapping[str, Any], captured_at: str) -> dict[str, Any]:
    """Derive the immutable redispatch binding from the existing transaction."""
    snapshot = {
        "authority_snapshot_id": "ZEUS-AUTHORITY-SNAPSHOT-" + _digest({
            "instance_id": record["instance_id"], "wop_id": record["wop_id"],
            "package_digest": record.get("package_digest"),
            "repository_baseline": record.get("repository_baseline"),
            "captured_at": captured_at,
        })[:24],
        "authority_schema_version": 1,
        "wop_id": record["wop_id"],
        "package_digest": record.get("package_digest"),
        "repository": record.get("repository"),
        "repository_baseline": record.get("repository_baseline"),
        "captured_at": captured_at,
        "protected_baselines": record.get("protected_baselines", {}),
        "execution_mode": record.get("execution_mode"),
        "effect_profile": record.get("effect_profile"),
        "governance_authority": (record.get("authorization") or {}).get("authority"),
        "publication_authority": "Engineering Governance",
        "approval_state": (record.get("authorization") or {}).get("decision"),
        "provider_qualification_required": True,
        "permitted_effects": [record.get("effect_profile")],
        "prohibited_effects": ["PRODUCTION", "EOS_PUBLICATION", "UNAUTHORIZED_SCOPE_EXPANSION"],
        "resolution": "AUTHORIZED",
    }
    snapshot["authority_snapshot_digest"] = _digest(snapshot)
    return snapshot


def _utc(value: datetime | None = None) -> str:
    moment = value or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        raise Stage1Error("submission timestamp must include a timezone")
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
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


class Stage1Store:
    """Integrity-protected, process-restart-safe mission state."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def _path(self, instance_id: str) -> Path:
        return self.directory / "missions" / f"{instance_id}.json"

    def save(self, value: Mapping[str, Any]) -> dict[str, Any]:
        record = deepcopy(dict(value))
        record.pop("state_digest", None)
        record["state_digest"] = _digest(record)
        _atomic_json(self._path(str(record["instance_id"])), record)
        return record

    def load_path(self, path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise Stage1Error(f"invalid runtime state {path}: {error}") from error
        supplied = value.pop("state_digest", None)
        if supplied != _digest(value):
            raise Stage1Error(f"runtime state digest mismatch: {path.name}")
        for field in ("instance_id", "mission_id", "wop_id"):
            if not isinstance(value.get(field), str) or not value[field]:
                raise Stage1Error(
                    f"runtime state missing valid {field}: {path.name}"
                )
        if value["instance_id"] != path.stem:
            raise Stage1Error(
                f"runtime state instance/path mismatch: {path.name}"
            )
        if value.get("state") not in MISSION_STATES:
            raise Stage1Error(
                f"runtime state lifecycle value invalid: {path.name}"
            )
        if value.get("lifecycle_integrity") == "RECEIPT_BACKED_V1":
            receipts = value.get("receipts")
            if not isinstance(receipts, Mapping):
                raise Stage1Error(f"receipt-backed runtime state has no receipt map: {path.name}")
            receipt_phases = {
                "validation": "VALIDATED", "packaging": "PACKAGED",
                "registration": "REGISTERED", "authorization": "AUTHORIZED",
                "admission": "ADMITTED", "dispatch": "DISPATCHED",
                "execution": "EXECUTING", "independent_verification": "QUALIFIED",
                "publication": "PUBLISHED", "synchronization": "SYNCHRONIZED",
                "closeout": "CLOSED",
            }
            expected = [phase for key, phase in receipt_phases.items() if key in receipts]
            legacy_projection = int(value.get("schema_version", 1)) < RECOVERY_SCHEMA_VERSION
            if value.get("phases") != expected and not legacy_projection:
                raise Stage1Error(f"receipt-backed lifecycle phases do not match receipts: {path.name}")
            if value.get("state") in {"EXECUTING", "QUALIFIED", "PUBLICATION_READY", "PUBLISHED", "SYNCHRONIZED", "CLOSED"}:
                required = {
                    "EXECUTING": ("dispatch", "execution"),
                    "QUALIFIED": ("dispatch", "execution", "independent_verification"),
                    "PUBLICATION_READY": ("dispatch", "execution", "independent_verification", "publication"),
                    "PUBLISHED": ("dispatch", "execution", "independent_verification", "publication"),
                    "SYNCHRONIZED": ("dispatch", "execution", "independent_verification", "publication", "synchronization"),
                    "CLOSED": ("dispatch", "execution", "independent_verification", "publication", "synchronization", "closeout"),
                }[value["state"]]
                missing = [key for key in required if key not in receipts]
                if missing:
                    raise Stage1Error(f"receipt-backed lifecycle state lacks receipts: {path.name}: {','.join(missing)}")
                required_fields = {
                    "dispatch": ("agent_id",),
                    "execution": ("execution_id", "launch_acknowledgment"),
                    "independent_verification": ("result",),
                    "publication": ("publication_id",),
                    "synchronization": ("eos_checkpoint",),
                    "closeout": ("closeout_report_digest",),
                }
                for key, fields in required_fields.items():
                    if key in receipts and any(not receipts[key].get(field) for field in fields):
                        raise Stage1Error(f"receipt-backed {key} receipt is incomplete: {path.name}")
        value["state_digest"] = supplied
        return value

    def all(self) -> list[dict[str, Any]]:
        return [self.load_path(path) for path in sorted((self.directory / "missions").glob("*.json"))]

    def find(self, identifier: str) -> dict[str, Any]:
        matches = [
            item for item in self.all()
            if identifier in {item["instance_id"], item["mission_id"], item["wop_id"]}
        ]
        if len(matches) != 1:
            raise Stage1Error(
                f"mission identifier resolved {len(matches)} records: {identifier}"
            )
        return matches[0]


class EensPublisher:
    """Durable append-only Stage 1 projection with idempotent event identities."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def publish(self, event_type: str, mission: Mapping[str, Any], at: str) -> dict[str, Any]:
        material = {
            "event_type": event_type,
            "instance_id": mission["instance_id"],
            "mission_id": mission["mission_id"],
            "state": mission["state"],
            "timestamp": at,
            "wop_id": mission["wop_id"],
        }
        event_id = "EENS-" + str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(material, sort_keys=True)))
        path = self.directory / f"{event_id}.json"
        event = {"schema_version": 1, "event_id": event_id, **material}
        event["event_digest"] = _digest(event)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != event:
                raise Stage1Error(f"EENS event identity collision: {event_id}")
            return existing
        _atomic_json(path, event)
        return event


@contextmanager
def _package_root(source: Path) -> Iterator[Path]:
    if source.is_dir():
        yield source.resolve()
        return
    if not source.is_file() or not (
        source.name.endswith(".tar.gz") or source.name.endswith(".tgz")
    ):
        raise Stage1Error("WOP source must be a directory or .tar.gz archive")
    with tempfile.TemporaryDirectory(prefix="zeus-stage1-") as temporary:
        destination = Path(temporary)
        try:
            with tarfile.open(source, "r:gz") as archive:
                members = archive.getmembers()
                for member in members:
                    target = (destination / member.name).resolve()
                    if destination.resolve() not in (target, *target.parents):
                        raise Stage1Error(f"unsafe archive member: {member.name}")
                    if member.issym() or member.islnk():
                        raise Stage1Error(f"archive links are prohibited: {member.name}")
                archive.extractall(destination, filter="data")
        except (tarfile.TarError, OSError) as error:
            raise Stage1Error(f"invalid WOP archive: {error}") from error
        children = [path for path in destination.iterdir()]
        root = children[0] if len(children) == 1 and children[0].is_dir() else destination
        yield root


def _first(root: Path, names: tuple[str, ...]) -> Path | None:
    matches = [root / name for name in names if (root / name).is_file()]
    return matches[0] if matches else None


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise Stage1Error(f"invalid {path.name}: {error}") from error
    if not isinstance(value, Mapping):
        raise Stage1Error(f"{path.name} must contain an object")
    return dict(value)


def validate_package(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    failures: list[dict[str, str]] = []
    components: dict[str, str] = {}
    for component, names in REQUIRED_COMPONENTS.items():
        path = _first(root, names)
        if path is None:
            failures.append({"component": component, "error": "missing"})
        else:
            components[component] = str(path.relative_to(root))

    manifests = sorted(
        path for path in (root / "manifests").glob("*")
        if path.is_file() and path.suffix in {".yaml", ".yml", ".json"}
    )
    if not manifests:
        manifest = _first(root, ("manifest.yaml", "manifest.yml", "manifest.json"))
        manifests = [manifest] if manifest else []
    if not manifests:
        failures.append({"component": "manifests", "error": "missing"})
    else:
        components["manifests"] = ",".join(str(path.relative_to(root)) for path in manifests)

    metadata_path = _first(root, REQUIRED_COMPONENTS["mission_metadata"])
    metadata: dict[str, Any] = {}
    if metadata_path:
        try:
            metadata = _load_mapping(metadata_path)
        except Stage1Error as error:
            failures.append({"component": "mission_metadata", "error": str(error)})
        for field in ("mission_id", "wop_id", "objective", "scope"):
            if not metadata.get(field):
                failures.append({"component": "mission_metadata", "error": f"{field} is required"})
        dependencies = metadata.get("dependencies")
        if not isinstance(dependencies, list) or any(
            not isinstance(item, str) or not item for item in dependencies
        ):
            failures.append(
                {
                    "component": "mission_metadata",
                    "error": "dependencies must be a list of non-empty identities",
                }
            )
        priority = metadata.get("priority")
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 0:
            failures.append(
                {
                    "component": "mission_metadata",
                    "error": "priority must be a non-negative integer",
                }
            )
        if metadata.get("candidate_state") != "CANDIDATE":
            failures.append(
                {
                    "component": "mission_metadata",
                    "error": "candidate_state must be CANDIDATE",
                }
            )

    required_files = metadata.get("required_execution_files", [])
    if not isinstance(required_files, list) or not required_files:
        failures.append({"component": "required_execution_files", "error": "non-empty list is required"})
    else:
        for relative in required_files:
            candidate = (root / str(relative)).resolve()
            if root.resolve() not in (candidate, *candidate.parents) or not candidate.is_file():
                failures.append({"component": "required_execution_files", "error": f"missing or unsafe: {relative}"})

    integrity = root / "SHA256SUMS"
    integrity_checks: list[dict[str, str]] = []
    if integrity.exists():
        for number, line in enumerate(integrity.read_text().splitlines(), 1):
            match = re.fullmatch(r"([0-9a-fA-F]{64})\s+(?:\*)?(.+)", line.strip())
            if not match:
                failures.append({"component": "integrity", "error": f"invalid SHA256SUMS line {number}"})
                continue
            candidate = (root / match.group(2)).resolve()
            if root.resolve() not in (candidate, *candidate.parents) or not candidate.is_file():
                failures.append({"component": "integrity", "error": f"unresolved path: {match.group(2)}"})
                continue
            actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
            result = "PASS" if actual.lower() == match.group(1).lower() else "FAIL"
            integrity_checks.append({"path": match.group(2), "result": result})
            if result == "FAIL":
                failures.append({"component": "integrity", "error": f"digest mismatch: {match.group(2)}"})
    evidence = {
        "components": components,
        "integrity": integrity_checks if integrity.exists() else "NOT_PRESENT",
        "result": "FAIL" if failures else "PASS",
        "failures": failures,
    }
    if failures:
        raise Stage1Error("package validation failed", evidence=evidence)
    return metadata, evidence


class Stage1Runtime:
    def __init__(
        self,
        repository: Path | str,
        state_directory: Path | str,
        *,
        resolver_factory: Callable[[Path], Any] = Resolver,
        operator_resolver: Callable[[], str] = getpass.getuser,
        execution_executor: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    ):
        self.repository = Path(repository).resolve()
        self.store = Stage1Store(state_directory)
        self.events = EensPublisher(Path(state_directory) / "eens")
        self.resolver_factory = resolver_factory
        self.operator_resolver = operator_resolver
        self.execution_executor = execution_executor

    def submit(self, source: Path | str, *, at: datetime | None = None) -> dict[str, Any]:
        timestamp = _utc(at)
        source_path = Path(source).resolve()
        with _package_root(source_path) as root:
            provisional = self._provisional(source_path, root, timestamp)
            self.events.publish("mission.submitted", provisional, timestamp)
            self.events.publish("mission.validating", provisional, timestamp)
            try:
                metadata, package_evidence = validate_package(root)
                provisional.update(
                    mission_id=str(metadata["mission_id"]), wop_id=str(metadata["wop_id"])
                )
                package_digest = self._tree_digest(root)
                instance_id = "ZEUS-MISSION-" + str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"{metadata['mission_id']}:{metadata['wop_id']}:{package_digest}")
                )
                staging_contract = {
                    "mission_id": str(metadata["mission_id"]),
                    "wop_id": str(metadata["wop_id"]),
                    "objective": metadata["objective"],
                    "scope": metadata["scope"],
                    "dependencies": sorted(set(metadata["dependencies"])),
                    "priority": metadata["priority"],
                    "state": metadata["candidate_state"],
                }
                provisional.update(
                    instance_id=instance_id,
                    package_digest=package_digest,
                    staging_contract=staging_contract,
                    staging_contract_digest=_digest(staging_contract),
                )
                replay = self._existing(provisional)
                if replay:
                    replay["idempotent_replay"] = True
                    return replay
                authority = self.resolver_factory(self.repository).resolve(str(metadata["mission_id"]))
                if authority.get("resolution") != "AUTHORIZED":
                    raise Stage1Error(
                        f"Mission Contract authorization failed: {authority.get('resolution')}",
                        evidence={"mission_contract": authority},
                    )
                repository_evidence = self._repository_evidence(authority["contract"])
                evidence = {
                    "package_validation": package_evidence,
                    "mission_contract": authority,
                    "repository_verification": repository_evidence,
                }
                provisional.update(
                    contract_id=authority["contract"]["contract_id"],
                    validation_evidence=evidence,
                    state="ADMITTED",
                    updated_at=timestamp,
                )
                self.store.save(provisional)
                self.events.publish("mission.admitted", provisional, timestamp)
                provisional["state"] = "STAGED"
                provisional["updated_at"] = timestamp
                record = self.store.save(provisional)
                self.events.publish("mission.staged", record, timestamp)
                record["idempotent_replay"] = False
                return record
            except Stage1Error as error:
                provisional.update(
                    state="REJECTED",
                    updated_at=timestamp,
                    validation_evidence=error.evidence,
                    rejection_reason=str(error),
                )
                record = self.store.save(provisional)
                self.events.publish("mission.rejected", record, timestamp)
                raise Stage1Error(str(error), evidence=record) from error

    def submit_development(self, source: Path | str, *, at: datetime | None = None,
                           interrupt_after: str | None = None,
                           packaging: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Submit a bounded Development Mode WOP.

        Development submissions are the manual-governance recovery path.  The
        package itself must explicitly opt in; validation is completed before
        the first state write, and the resulting lifecycle is persisted in the
        existing Stage 1 store so replay/resume remains idempotent.
        """
        timestamp = _utc(at)
        source_path = Path(source).resolve()
        with _package_root(source_path) as root:
            metadata, package_evidence = validate_package(root)
            if metadata.get("execution_mode") != "DEVELOPMENT":
                raise Stage1Error("development submission requires execution_mode=DEVELOPMENT",
                                  evidence={"reason_code": "DEVELOPMENT_MODE_REQUIRED"})
            # The canonical Zeus submission operation is the governance
            # submission act. Legacy governance_authority metadata remains
            # accepted, but is not a second authority assertion.
            declared_authority = {
                "authority": metadata.get("authority"),
                "execution_authority": metadata.get("execution_authority"),
                "publication_authority": metadata.get("publication_authority"),
            }
            conflicts = [key for key, value in declared_authority.items()
                         if value and value != "Engineering Governance"]
            if conflicts:
                raise Stage1Error(
                    "authority chain sources disagree: " + ", ".join(conflicts),
                    evidence={"reason_code": "AUTHORITY_CHAIN_INTEGRITY_FAILURE", "conflicts": conflicts},
                )
            effect_profile = str(metadata.get("effect_profile") or "").upper()
            if not effect_profile or effect_profile == "PRODUCTION" or effect_profile.startswith("PRODUCTION-"):
                raise Stage1Error("development WOP requires a non-production effect profile",
                                  evidence={"reason_code": "EFFECT_PROFILE_INVALID"})
            if metadata.get("development_operator") not in {None, self.operator_resolver(), "loneal"}:
                raise Stage1Error("development operator is not authorized",
                                  evidence={"reason_code": "UNAUTHORIZED_OPERATOR"})
            try:
                from scripts.lib.emp.repository_identity import resolve_declared
                resolved_identity = resolve_declared(metadata.get("repository_identity"), self.repository)
            except (ValueError, OSError) as error:
                raise Stage1Error(
                    f"development WOP repository identity mismatch: {error}",
                    evidence={"reason_code": "REPOSITORY_IDENTITY_MISMATCH"},
                ) from error
            expected = resolved_identity["canonical_repository_identity"]
            baseline = subprocess.run(["git", "-C", str(self.repository), "rev-parse", "HEAD"],
                                      text=True, capture_output=True, check=False).stdout.strip()
            if not baseline:
                raise Stage1Error("unable to resolve repository baseline",
                                  evidence={"reason_code": "BASELINE_UNRESOLVED"})
            protected = {}
            for tag in ("OA-v1.0.0", "OB-PLAN-v1.0.0"):
                result = subprocess.run(["git", "-C", str(self.repository), "rev-parse", tag],
                                        text=True, capture_output=True, check=False)
                if result.returncode:
                    raise Stage1Error(f"protected baseline is unavailable: {tag}",
                                      evidence={"reason_code": "PROTECTED_BASELINE_UNAVAILABLE", "tag": tag})
                protected[tag] = result.stdout.strip()
            package_digest = self._tree_digest(root)
            # Target-mission metadata is a derived linkage, never a replacement
            # for the immutable Stage 1 transaction or its package digest.
            from scripts.lib.emp.canonical_mission_lifecycle import derive_linkage
            canonical_linkage = derive_linkage(
                metadata, source_path, package_digest=package_digest
            )
            manifest_path = root / "manifests/immutable-manifest.yaml"
            try:
                manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as error:
                raise Stage1Error(f"immutable manifest is invalid: {error}",
                                  evidence={"reason_code": "IMMUTABLE_MANIFEST_INVALID"}) from error
            if not isinstance(manifest, Mapping) or manifest.get("wop_id") != metadata["wop_id"]:
                raise Stage1Error("immutable manifest and WOP identity mismatch",
                                  evidence={"reason_code": "IMMUTABLE_MANIFEST_MISMATCH"})
            instance_id = "ZEUS-DEVELOPMENT-" + str(uuid.uuid5(
                uuid.NAMESPACE_URL, f"{metadata['mission_id']}:{metadata['wop_id']}:{package_digest}"))
            existing = next((item for item in self.store.all()
                             if item.get("instance_id") == instance_id), None)
            prior = [item for item in self.store.all()
                     if item.get("wop_id") == str(metadata["wop_id"])
                     and item.get("package_digest") != package_digest
                     and item.get("state") not in {"REJECTED", "BLOCKED"}]
            if prior:
                raise Stage1Error(
                    "source changed after an accepted package; explicit supersession is required",
                    evidence={"reason_code": "SOURCE_CHANGED_REQUIRES_SUPERSESSION",
                              "prior_instances": [item["instance_id"] for item in prior]})
            if existing:
                if existing.get("package_digest") != package_digest:
                    raise Stage1Error("development submission identity collision")
                if canonical_linkage and not existing.get("canonical_mission_linkage"):
                    existing["canonical_mission_linkage"] = canonical_linkage
                if existing.get("state") != "CLOSED":
                    existing = self._resume_development(existing, baseline, protected, timestamp,
                                                        interrupt_after=interrupt_after)
                existing = self._reconcile_runtime_after_dispatch(existing, timestamp)
                existing["idempotent_replay"] = True
                return existing
            operator = self.operator_resolver()
            record = {
                "schema_version": 2, "lifecycle_integrity": "RECEIPT_BACKED_V1", "instance_id": instance_id,
                "mission_id": str(metadata["mission_id"]), "wop_id": str(metadata["wop_id"]),
                "submitted_at": timestamp, "updated_at": timestamp, "operator": operator,
                "repository": expected, "source": str(source_path), "state": "VALIDATED",
                "package": str(source_path), "packaging": dict(packaging or {"packaged": False}),
                "execution_mode": "DEVELOPMENT", "package_digest": package_digest,
                "source_digest": str(metadata.get("source_document_digest") or package_digest),
                "effect_profile": metadata["effect_profile"],
                "repository_baseline": baseline, "submission_baseline": baseline,
                "submission_branch": subprocess.run(["git", "-C", str(self.repository), "branch", "--show-current"],
                                                     text=True, capture_output=True, check=False).stdout.strip(),
                "protected_baselines": protected,
                "validation_evidence": package_evidence,
                "registration": {"registration_id": "EMM-DEV-" + package_digest[:24],
                                  "owner": "Engineering Governance", "status": "GENERATED"},
                "provenance": {"repository": expected, "baseline": baseline,
                               "package_digest": package_digest, "generated_at": timestamp,
                               "operator": operator},
                "authorization": {"mode": "MANUAL_GOVERNANCE_DEVELOPMENT",
                                   "authority": "Engineering Governance",
                                   "decision": "SUBMISSION_AUTHORITY_ONLY"},
                "failure_injection": {
                    "publication": bool(metadata.get("simulate_publication_failure")),
                    "synchronization": bool(metadata.get("simulate_synchronization_failure")),
                },
                "canonical_mission_linkage": canonical_linkage,
                "phases": [], "receipts": {}, "evidence": [], "failure": None,
            }
            # Freeze the complete authority chain before provider selection.
            # Providers consume this snapshot; they never become an authority
            # source and cannot silently re-resolve mutable metadata.
            snapshot = {
                "authority_snapshot_id": "ZEUS-AUTHORITY-SNAPSHOT-" + _digest({
                    "instance_id": instance_id, "wop_id": str(metadata["wop_id"]),
                    "package_digest": package_digest, "baseline": baseline,
                })[:24],
                "authority_schema_version": 1,
                "mission_contract": {
                    "locator": record.get("contract_id"),
                    "digest": _digest(record.get("validation_evidence", {}).get("mission_contract", {})),
                },
                "wop_id": str(metadata["wop_id"]),
                "package_digest": package_digest,
                "repository": expected,
                "repository_fingerprint": resolved_identity.get("repository_fingerprint"),
                "protected_baselines": protected,
                "execution_mode": "DEVELOPMENT",
                "effect_profile": metadata["effect_profile"],
                "governance_authority": "Engineering Governance",
                "wop_authority": "Engineering Governance",
                "transaction_profile": metadata.get("engineering_transaction_profile") or metadata.get("transaction_profile") or "SPEC-0008:DEVELOPMENT",
                "approval_state": "SUBMISSION_AUTHORITY_ONLY",
                "publication_authority": "Engineering Governance",
                "provider_qualification_required": True,
                "permitted_effects": [metadata["effect_profile"]],
                "prohibited_effects": ["PRODUCTION", "EOS_PUBLICATION", "UNAUTHORIZED_SCOPE_EXPANSION"],
                "resolution": "AUTHORIZED",
            }
            snapshot["authority_snapshot_digest"] = _digest(snapshot)
            record["authority_snapshot"] = snapshot
            record["receipts"] = self._development_receipts(
                record, metadata, package_digest, package_source=source_path,
                package_evidence=package_evidence, packaging=packaging,
                timestamp=timestamp,
            )
            record = self._resume_development(record, baseline, protected, timestamp,
                                              interrupt_after=interrupt_after)
            record = self._reconcile_runtime_after_dispatch(record, timestamp)
            record["idempotent_replay"] = False
            return record

    def _reconcile_runtime_after_dispatch(self, record: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
        """Seal dispatched Stage 1 state with its canonical runtime projections.

        Stage 1 receipts remain immutable authority.  Admission and execution
        files are derived projections and are installed by the shared atomic
        reconciler.  A submission is not allowed to return ``DISPATCHED``
        until both projections and the reconciliation receipt verify.  If the
        projection transaction cannot complete, persist a durable blocked
        checkpoint so the existing transaction can be resumed without
        resubmission.
        """
        value = deepcopy(dict(record))
        if "dispatch" not in (value.get("receipts") or {}):
            return value
        try:
            from scripts.lib.emp.runtime_reconciliation import reconcile

            runtime_root = self.store.directory.resolve().parent
            reconciliation = reconcile(
                self.repository,
                self.store.directory,
                runtime_root / "mission-admissions",
                runtime_root / "mission-executions",
                command="submit",
                execution_id=value["instance_id"],
                require_lineage_environment=False,
            )
        except (OSError, ValueError) as error:
            value["state"] = "BLOCKED"
            value["pending_phase"] = "EXECUTION_PERSISTED"
            value["next_action"] = "Resume the existing transaction to reconcile admission and execution projections"
            value["failure"] = {
                "classification": "RUNTIME_PROJECTION_PERSISTENCE_FAILURE",
                "message": str(error),
                "transaction_id": value["instance_id"],
            }
            value.setdefault("evidence", []).append({
                "type": "lifecycle-reconciliation-failure",
                "classification": "RUNTIME_PROJECTION_PERSISTENCE_FAILURE",
                "message": str(error),
                "transaction_id": value["instance_id"],
                "timestamp": timestamp,
            })
            value["updated_at"] = timestamp
            return self.store.save(value)

        value["runtime_reconciliation"] = {
            "reconciliation_id": reconciliation["reconciliation"]["reconciliation_id"],
            "classification": reconciliation["reconciliation"]["classification"],
            "admission_id": reconciliation["admission_id"],
            "execution_id": reconciliation["execution_id"],
            "receipt_path": reconciliation["reconciliation"]["receipt_path"],
        }
        value["runtime_projection_state"] = "VERIFIED"
        value["updated_at"] = timestamp
        return self.store.save(value)

    def _resume_development(self, record: dict[str, Any], baseline: str,
                            protected: Mapping[str, str], timestamp: str,
                            *, interrupt_after: str | None = None,
                            repository_transition: Mapping[str, Any] | None = None) -> dict[str, Any]:
        current = subprocess.run(["git", "-C", str(self.repository), "rev-parse", "HEAD"],
                                 text=True, capture_output=True, check=False).stdout.strip()
        expected = str((repository_transition or {}).get("recovery_baseline") or baseline)
        if current != expected:
            raise Stage1Error("repository drift detected during development submission",
                              evidence={"reason_code": "REPOSITORY_DRIFT", "expected": expected, "observed": current})
        for tag, value in protected.items():
            observed = subprocess.run(["git", "-C", str(self.repository), "rev-parse", tag],
                                      text=True, capture_output=True, check=False).stdout.strip()
            if observed != value:
                raise Stage1Error("protected baseline changed during development submission",
                                  evidence={"reason_code": "PROTECTED_BASELINE_MUTATION", "tag": tag})
        receipts = record.setdefault("receipts", {})
        if "dispatch" in receipts:
            valid, reason = _dispatch_receipt_valid(receipts["dispatch"], record)
            if not valid:
                return self.reconcile_invalid_dispatch(record, reason=reason, timestamp=timestamp)
        phase_receipts = (
            ("VALIDATED", "validation"), ("PACKAGED", "packaging"),
            ("REGISTERED", "registration"), ("AUTHORIZED", "authorization"),
            ("ADMITTED", "admission"), ("DISPATCHED", "dispatch"),
            ("EXECUTING", "execution"), ("QUALIFIED", "independent_verification"),
            ("PUBLICATION_READY", "publication"), ("PUBLISHED", "publication"),
            ("SYNCHRONIZED", "synchronization"), ("CLOSED", "closeout"),
        )
        completed = [phase for phase, receipt_key in phase_receipts if receipt_key in receipts]
        record["phases"] = completed
        if self.execution_executor is None and "dispatch" not in receipts:
            if (record.get("state") == "AWAITING_EXECUTION_DISPATCH"
                    and record.get("pending_phase") == "DISPATCHED"
                    and record.get("next_action") == "Dispatch to a qualified Development execution agent"):
                return self.store.load_path(self.store._path(record["instance_id"]))
            record["state"] = "AWAITING_EXECUTION_DISPATCH"
            record["next_action"] = "Dispatch to a qualified Development execution agent"
            record["pending_phase"] = "DISPATCHED"
            record["updated_at"] = timestamp
            self.store.save(record)
            return self.store.load_path(self.store._path(record["instance_id"]))
        # The execution boundary is deliberately explicit. A caller must
        # provide a qualified executor that returns receipt-bound results;
        # package creation never implies dispatch or execution.
        if "dispatch" not in receipts:
            # A recovered transaction must receive a fresh immutable binding
            # before any provider is consulted for redispatch.
            if not record.get("authority_snapshot"):
                record["authority_snapshot"] = _authority_snapshot(record, timestamp)
            result = self.execution_executor(record)
            if not isinstance(result, Mapping) or not result.get("dispatch_receipt"):
                record["state"] = "AWAITING_EXECUTION_DISPATCH"
                record["next_action"] = "Dispatch to a qualified Development execution agent"
                record["pending_phase"] = "DISPATCHED"
                record["updated_at"] = timestamp
                self.store.save(record)
                return self.store.load_path(self.store._path(record["instance_id"]))
            dispatch = dict(result["dispatch_receipt"])
            selection = (result.get("receipts") or {}).get("provider_selection")
            selection_required = ("receipt_id", "receipt_digest", "transaction_id", "wop_id",
                                  "agent_id", "provider_id", "selection_policy", "registry_digest",
                                  "authority_snapshot_digest")
            if not isinstance(selection, Mapping) or any(not selection.get(field) for field in selection_required):
                record["state"] = "AWAITING_EXECUTION_DISPATCH"
                record["next_action"] = "Dispatch blocked: incomplete provider-selection receipt"
                record["pending_phase"] = "DISPATCHED"
                record["updated_at"] = timestamp
                self.store.save(record)
                return self.store.load_path(self.store._path(record["instance_id"]))
            candidate = deepcopy(record)
            candidate.setdefault("receipts", {})["provider_selection"] = dict(selection)
            valid, reason = _dispatch_receipt_valid(dispatch, candidate)
            if not valid:
                record["state"] = "AWAITING_EXECUTION_DISPATCH"
                record["next_action"] = "Dispatch blocked: " + reason
                record["pending_phase"] = "DISPATCHED"
                record["updated_at"] = timestamp
                self.store.save(record)
                return self.store.load_path(self.store._path(record["instance_id"]))
            receipts["dispatch"] = dispatch
            receipts.update({key: dict(value) for key, value in result.get("receipts", {}).items()})
        record["phases"] = [phase for phase, receipt_key in phase_receipts if receipt_key in receipts]
        record["state"] = record["phases"][-1] if record["phases"] else "VALIDATED"
        if "execution" not in receipts and "dispatch" in receipts:
            record["next_action"] = "Await provider launch acknowledgment before EXECUTING"
        else:
            record["next_action"] = "Continue from the first lifecycle phase without a receipt"
        record["updated_at"] = timestamp
        self.store.save(record)
        return self.store.load_path(self.store._path(record["instance_id"]))

    def reconcile_invalid_dispatch(self, record: Mapping[str, Any], *, reason: str,
                                   timestamp: str) -> dict[str, Any]:
        """Idempotently demote an invalid dispatch while preserving evidence."""
        value = deepcopy(dict(record))
        dispatch = deepcopy((value.get("receipts") or {}).get("dispatch"))
        if not dispatch:
            return self.store.load_path(self.store._path(value["instance_id"]))
        invalid_digest = _digest(dispatch)
        evidence = value.setdefault("evidence", [])
        existing = next((item for item in evidence
                         if item.get("type") == "invalid-dispatch-reconciliation"
                         and item.get("invalid_dispatch_digest") == invalid_digest), None)
        if existing:
            return self.store.load_path(self.store._path(value["instance_id"]))
        recovery = {
            "schema_version": 1,
            "receipt_type": "invalid-dispatch-reconciliation",
            "transaction_id": value["instance_id"],
            "wop_id": value["wop_id"],
            "invalid_dispatch_digest": invalid_digest,
            "reason": reason,
            "action": "ROLLBACK_TO_AWAITING_EXECUTION_DISPATCH",
            "execution_performed": False,
        }
        recovery["receipt_id"] = "ZEUS-RECEIPT-RECONCILIATION-" + _digest(recovery)[:24]
        recovery["receipt_digest"] = _digest(recovery)
        evidence.append({"type": "receiptless-dispatch-recovery",
                         "reconciliation_type": "invalid-dispatch-reconciliation",
                         "historical_dispatch": dispatch,
                         "invalid_dispatch_digest": invalid_digest,
                         "recovery_receipt": recovery,
                         "reason": reason,
                         "recovery": recovery["action"]})
        value.setdefault("receipts", {}).pop("dispatch", None)
        # A stale or absent binding cannot authorize a later dispatch.  The
        # next canonical resume must freeze a fresh snapshot first.
        value.pop("authority_snapshot", None)
        value["source_digest"] = ((value.get("receipts", {}).get("validation") or {}).get("source_digest")
                                   or value.get("source_digest"))
        value["phases"] = [phase for phase, receipt_key in (
            ("VALIDATED", "validation"), ("PACKAGED", "packaging"),
            ("REGISTERED", "registration"), ("AUTHORIZED", "authorization"),
            ("ADMITTED", "admission"),
        ) if receipt_key in value["receipts"]]
        value["state"] = "AWAITING_EXECUTION_DISPATCH"
        value["pending_phase"] = "DISPATCHED"
        value["next_action"] = "Create a new authority snapshot before receipt-backed redispatch"
        value["updated_at"] = timestamp
        saved = self.store.save(value)
        self.events.publish("mission.invalid-dispatch-reconciled", saved, timestamp)
        return self.store.load_path(self.store._path(saved["instance_id"]))

    def _development_receipts(self, record: Mapping[str, Any], metadata: Mapping[str, Any],
                              package_digest: str, *, package_source: Path,
                              package_evidence: Mapping[str, Any],
                              packaging: Mapping[str, Any] | None, timestamp: str) -> dict[str, Any]:
        """Create only receipts proven by source/package acceptance."""
        def receipt(kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
            value = {"schema_version": 1, "receipt_type": kind, **dict(payload), "timestamp": timestamp,
                     "authority_snapshot_digest": (record.get("authority_snapshot") or {}).get("authority_snapshot_digest")}
            value["receipt_id"] = f"ZEUS-RECEIPT-{kind.upper()}-{_digest(value)[:24]}"
            value["receipt_digest"] = _digest(value)
            return value
        source_digest = str(metadata.get("source_document_digest") or
                            (hashlib.sha256(package_source.read_bytes()).hexdigest()
                             if package_source.is_file() else self._tree_digest(package_source)))
        return {
            "validation": receipt("validation", {"source": str(package_source), "source_digest": source_digest, "validator": "stage1.validate_package", "result": package_evidence.get("result", "PASS"), "failures": package_evidence.get("failures", [])}),
            "packaging": receipt("packaging", {"package": record.get("package"), "package_digest": package_digest, "source_digest": source_digest, "transactional_promotion": bool((packaging or {}).get("packaged", False))}),
            "registration": receipt("registration", {"registration_id": record["registration"]["registration_id"], "wop_id": record["wop_id"], "package_digest": package_digest, "repository_baseline": record["repository_baseline"]}),
            "authorization": receipt("authorization", {"authority": "Engineering Governance", "decision": record["authorization"]["decision"], "effect_profile": record["effect_profile"], "repository": record["repository"], "protected_baselines": record["protected_baselines"]}),
            "admission": receipt("admission", {"admission_id": f"EMM-DEV-ADMISSION-{package_digest[:24]}", "wop_id": record["wop_id"], "execution_mode": "DEVELOPMENT", "executor_requirements": ["qualified Development execution agent"], "effect_profile": record["effect_profile"]}),
        }

    def status(self) -> dict[str, Any]:
        missions = self.store.all()
        counts = {
            state: sum(item["state"] == state for item in missions)
            for state in MISSION_STATES
        }
        if sum(counts.values()) != len(missions):
            raise Stage1Error("mission state counts do not reconcile")
        return {"schema_version": 1, "mission_count": len(missions), "states": counts}

    def list(self) -> list[dict[str, Any]]:
        return [item for item in self.store.all() if item["state"] == "STAGED"]

    def show(self, identifier: str) -> dict[str, Any]:
        return self.store.find(identifier)

    def resolve_transaction(self, identifier: str) -> dict[str, Any]:
        """Resolve every supported Development transaction identity."""
        value = str(identifier)
        matches = []
        for item in self.store.all():
            identities = {
                item.get("instance_id"), item.get("mission_id"), item.get("wop_id"),
                item.get("package_digest"), item.get("source_digest"),
                (item.get("registration") or {}).get("registration_id"),
            }
            if value in identities:
                matches.append(item)
        if len(matches) != 1:
            raise Stage1Error(f"development transaction identifier resolved {len(matches)} records: {identifier}")
        return matches[0]

    def transaction_view(self, identifier: str) -> dict[str, Any]:
        record = self.resolve_transaction(identifier)
        receipts = record.get("receipts") or {}
        dispatch = receipts.get("dispatch")
        dispatch_valid = False
        dispatch_reason = "DISPATCH_RECEIPT_ABSENT"
        if dispatch:
            dispatch_valid, dispatch_reason = _dispatch_receipt_valid(dispatch, record)
        blocked = bool(dispatch and not dispatch_valid)
        readiness = self._canonical_resume_readiness(record, dispatch_valid=dispatch_valid)
        snapshot = record.get("authority_snapshot") or {}
        current_phase = (record.get("phases") or [None])[-1]
        receipt_verification = {
            key: {"result": "PASS", "receipt_id": value.get("receipt_id")}
            for key, value in receipts.items() if isinstance(value, Mapping)
        }
        return {
            "result": "BLOCKED" if blocked else "PASS",
            "mission_id": record.get("mission_id"),
            "wop_id": record.get("wop_id"),
            "transaction_id": record.get("instance_id"),
            "registration_id": (record.get("registration") or {}).get("registration_id"),
            "package_digest": record.get("package_digest"),
            "source_digest": (receipts.get("validation") or {}).get("source_digest"),
            "state": record.get("state"),
            "repository": record.get("repository"),
            "protected_baselines": record.get("protected_baselines", {}),
            "authority_snapshot_digest": (record.get("authority_snapshot") or {}).get("authority_snapshot_digest"),
            "authority_identity": snapshot.get("authority_snapshot_id"),
            "runtime_identity": {"instance_id": record.get("instance_id"),
                                 "schema_version": record.get("schema_version"),
                                 "state_digest": record.get("state_digest")},
            "repository_transition": record.get("repository_transition") or {
                "submission_baseline": record.get("submission_baseline") or record.get("repository_baseline"),
                "current_head": None,
                "classification": "UNRESOLVED",
                "recovery_baseline_bound": bool(record.get("recovery_baseline_binding")),
            },
            "lifecycle": {"current_phase": current_phase, "next_phase": record.get("pending_phase")},
            "receipt_verification": receipt_verification,
            "authority_verification": {"result": "PASS" if snapshot else "PENDING",
                                        "authority_snapshot_digest": snapshot.get("authority_snapshot_digest")},
            "dispatch_readiness": "READY" if dispatch_valid else "PENDING",
            "execution_readiness": "READY" if "execution" in receipts else "AWAITING_LAUNCH_ACKNOWLEDGEMENT",
            "provider": (dispatch or {}).get("provider_id"),
            "agent": (dispatch or {}).get("agent_id"),
            "receipts": {key: value.get("receipt_id") for key, value in receipts.items() if isinstance(value, Mapping)},
            "dispatch_receipt_valid": dispatch_valid,
            "dispatch_receipt_diagnostic": dispatch_reason,
            "blocker": None if not blocked else "RECEIPT_INTEGRITY_FAILURE",
            "readiness": readiness["readiness"],
            "readiness_diagnostic": readiness.get("diagnostic"),
            "next_action": readiness["next_action"],
        }

    def _canonical_resume_readiness(self, record: Mapping[str, Any], *,
                                    dispatch_valid: bool) -> dict[str, Any]:
        """Project whether canonical resume may perform internal recovery work.

        This is strictly read-only.  The authority and repository checks are
        shared with recovery, while authority snapshots, provider selection,
        and dispatch receipts remain resume-owned lifecycle outputs.  Their
        absence is therefore not a prerequisite failure for an admitted,
        recoverable transaction.
        """
        next_action = "scripts/zeus resume " + str(record.get("mission_id") or record.get("instance_id"))
        if record.get("state") != "AWAITING_EXECUTION_DISPATCH":
            return {"readiness": "NO_GO", "next_action": record.get("next_action") or next_action,
                    "diagnostic": "MISSION_NOT_AWAITING_EXECUTION_DISPATCH"}
        if (record.get("receipts") or {}).get("dispatch") is not None and not dispatch_valid:
            return {"readiness": "NO_GO", "next_action": next_action,
                    "diagnostic": "RECEIPT_CORRUPTION"}
        baseline = str(record.get("repository_baseline") or "")
        try:
            verification = self._verify_recovery(
                record, baseline, record.get("protected_baselines") or {},
                allow_pending_dispatch=True,
            )
        except Stage1Error as error:
            return {"readiness": "NO_GO", "next_action": record.get("next_action") or next_action,
                    "diagnostic": error.evidence.get("reason_code") or str(error)}
        if verification.get("receipt_chain", {}).get("result") == "FAIL":
            return {"readiness": "NO_GO", "next_action": next_action,
                    "diagnostic": "RECEIPT_CHAIN_INTEGRITY_FAILURE"}
        return {"readiness": "GO_FOR_CANONICAL_RESUME", "next_action": next_action,
                "diagnostic": "INTERNAL_RESUME_ARTIFACTS_DEFERRED_TO_CANONICAL_RESUME"}

    def resume_transaction(self, identifier: str | None = None, *, at: datetime | None = None) -> dict[str, Any]:
        """Canonical recovery entry point for one existing transaction.

        Recovery is deliberately separate from submission: it may migrate and
        reconcile the existing record, but it never derives a replacement
        transaction or a synthetic lifecycle receipt.
        """
        candidates = [item for item in self.store.all() if item.get("state") not in {"CLOSED", "REJECTED"}]
        if identifier:
            record = self.resolve_transaction(identifier)
        elif len(candidates) == 1:
            record = candidates[0]
        elif not candidates:
            raise Stage1Error("no resumable Development transaction exists")
        else:
            raise Stage1Error("multiple resumable Development transactions exist; provide an identifier")
        record = self._hydrate_transaction(record)
        baseline = str(record.get("repository_baseline") or "")
        protected = record.get("protected_baselines") or {}
        timestamp = _utc(at)
        verification = self._verify_recovery(record, baseline, protected)
        record = self._bind_recovery_baseline(record, verification["repository_transition"], timestamp)
        record = self._migrate_runtime(record, verification)
        # A verified dispatch is already authoritative.  Do not rewrite its
        # timestamp, provider binding, or receipt identities on replay.
        if verification["dispatch"]["result"] == "PASS":
            result = self.store.load_path(self.store._path(record["instance_id"]))
            result["recovery"] = verification
            result["idempotent_recovery"] = True
            return result
        prior_digest = record.get("state_digest")
        result = self._resume_development(record, baseline, protected, timestamp,
                                           repository_transition=verification["repository_transition"])
        result["recovery"] = self._verify_recovery(result, baseline, protected, allow_pending_dispatch=True)
        result["idempotent_recovery"] = prior_digest == result.get("state_digest")
        return result

    def _hydrate_transaction(self, record: Mapping[str, Any]) -> dict[str, Any]:
        """Rebuild only derived projection fields from authoritative evidence.

        Hydration never creates a receipt, authority snapshot, provider binding,
        execution identity, or lifecycle phase. Missing values remain explicitly
        unresolved and are handled by the normal fail-closed recovery checks.
        """
        value = deepcopy(dict(record))
        receipts = value.get("receipts")
        if not isinstance(receipts, Mapping):
            raise Stage1Error("runtime hydration requires an authoritative receipt map",
                              evidence={"reason_code": "MISSING_RECEIPT"})
        changed: list[str] = []
        unresolved: list[dict[str, str]] = []

        def derive(field: str, candidate: Any, source: str) -> None:
            if candidate in (None, "", {}):
                unresolved.append({"field": field, "classification": "HISTORICAL_EVIDENCE_UNAVAILABLE",
                                   "source": source})
                return
            current = value.get(field)
            if current not in (None, "", {}):
                if current != candidate:
                    raise Stage1Error(f"hydration found conflicting {field}", evidence={
                        "reason_code": AUTHORITY_FAILURE,
                        "classification": "CONFLICTING_AUTHORITATIVE_VALUES",
                        "field": field, "stored": current, "derived": candidate,
                    })
                return
            value[field] = candidate
            changed.append(field)

        validation = receipts.get("validation") if isinstance(receipts.get("validation"), Mapping) else {}
        packaging = receipts.get("packaging") if isinstance(receipts.get("packaging"), Mapping) else {}
        registration = receipts.get("registration") if isinstance(receipts.get("registration"), Mapping) else {}
        dispatch = receipts.get("dispatch") if isinstance(receipts.get("dispatch"), Mapping) else {}
        derive("source", validation.get("source"), "receipts.validation.source")
        derive("source_digest", validation.get("source_digest"), "receipts.validation.source_digest")
        derive("package", packaging.get("package"), "receipts.packaging.package")
        derive("package_digest", packaging.get("package_digest") or registration.get("package_digest"),
               "receipts.packaging.package_digest")
        registration_id = registration.get("registration_id")
        if registration_id:
            current_registration = value.get("registration")
            if not isinstance(current_registration, Mapping):
                value["registration"] = {"registration_id": registration_id}
                changed.append("registration")
            elif current_registration.get("registration_id") not in (None, registration_id):
                raise Stage1Error("hydration found conflicting registration identity", evidence={
                    "reason_code": AUTHORITY_FAILURE,
                    "classification": "CONFLICTING_AUTHORITATIVE_VALUES",
                    "field": "registration.registration_id",
                })
        dispatch_fields = ("provider_id", "agent_id", "qualification_id", "registry_digest")
        for field in dispatch_fields:
            if not dispatch.get(field):
                unresolved.append({"field": field, "classification": "HISTORICAL_EVIDENCE_UNAVAILABLE",
                                   "source": f"receipts.dispatch.{field}"})
        if not value.get("authority_snapshot"):
            unresolved.append({"field": "authority_snapshot", "classification": "HISTORICAL_EVIDENCE_UNAVAILABLE",
                               "source": "runtime.authority_snapshot"})

        phase_receipts = (
            ("VALIDATED", "validation"), ("PACKAGED", "packaging"),
            ("REGISTERED", "registration"), ("AUTHORIZED", "authorization"),
            ("ADMITTED", "admission"), ("DISPATCHED", "dispatch"),
            ("EXECUTING", "execution"), ("QUALIFIED", "independent_verification"),
            ("PUBLISHED", "publication"), ("SYNCHRONIZED", "synchronization"),
            ("CLOSED", "closeout"),
        )
        projected_phases = [phase for phase, key in phase_receipts if key in receipts]
        if value.get("phases") != projected_phases:
            value["phases"] = projected_phases
            changed.append("phases")
        if value.get("lifecycle_integrity") != "RECEIPT_BACKED_V1":
            value["lifecycle_integrity"] = "RECEIPT_BACKED_V1"
            changed.append("lifecycle_integrity")
        if not value.get("pending_phase") and projected_phases:
            value["pending_phase"] = "DISPATCHED" if "DISPATCHED" not in projected_phases else "EXECUTING"
            changed.append("pending_phase")
        if not value.get("next_action"):
            value["next_action"] = (
                "Recover receipt-backed dispatch through the canonical Zeus transaction resume"
                if "dispatch" in receipts else
                "Dispatch to a qualified Development execution agent"
            )
            changed.append("next_action")

        value["hydration"] = {
            "schema_version": HYDRATION_SCHEMA_VERSION,
            "result": "PASS" if not unresolved else "PASS_WITH_UNRESOLVED_HISTORICAL_FIELDS",
            "derived_fields": sorted(set(changed)),
            "unresolved": unresolved,
            "receipt_ids": sorted(
                receipt.get("receipt_id") for receipt in receipts.values()
                if isinstance(receipt, Mapping) and receipt.get("receipt_id")
            ),
        }
        if changed or record.get("hydration") != value["hydration"]:
            value = self.store.save(value)
        return value

    def _verify_recovery(self, record: Mapping[str, Any], baseline: str,
                         protected: Mapping[str, str], *, allow_pending_dispatch: bool = False) -> dict[str, Any]:
        """Verify the authoritative inputs consumed by canonical recovery."""
        def fail(code: str, detail: str, **extra: Any) -> None:
            raise Stage1Error(detail, evidence={"reason_code": code, **extra})

        if record.get("repository") != str(self.repository):
            fail("REPOSITORY_MISMATCH", "transaction repository identity mismatch",
                 expected=str(self.repository), observed=record.get("repository"))
        transition = self._resolve_baseline_transition(record, baseline, fail)
        repository_status = "PASS" if transition["classification"] == "EXACT_SUBMISSION_BASELINE" else "STALE_RUNTIME_RECONCILED"
        for tag, expected in protected.items():
            actual = subprocess.run(["git", "-C", str(self.repository), "rev-parse", tag],
                                    text=True, capture_output=True, check=False).stdout.strip()
            if actual != expected:
                fail("PROTECTED_BASELINE_MUTATION", f"protected baseline mismatch: {tag}",
                     classification="PROTECTED_BASELINE_MUTATION", tag=tag,
                     expected=expected, observed=actual)

        receipts = record.get("receipts")
        if not isinstance(receipts, Mapping):
            fail("MISSING_RECEIPT", "receipt chain is unavailable")
        ordered = ("validation", "packaging", "registration", "authorization", "admission")
        receipt_report: dict[str, Any] = {}
        previous = None
        for key in ordered:
            receipt = receipts.get(key)
            if not isinstance(receipt, Mapping):
                fail("MISSING_RECEIPT", f"missing receipt: {key}", phase=key)
            supplied = receipt.get("receipt_digest")
            unsigned = dict(receipt)
            unsigned.pop("receipt_digest", None)
            if not supplied or supplied != _digest(unsigned):
                fail("INVALID_RECEIPT", f"invalid receipt: {key}", phase=key)
            if key in {"validation", "packaging"} and receipt.get("package_digest") not in {None, record.get("package_digest")}:
                fail("PACKAGE_DIGEST_MISMATCH", f"package digest mismatch: {key}", phase=key)
            if key in {"validation", "packaging"}:
                source_digest = receipt.get("source_digest")
                if not source_digest or source_digest != record.get("source_digest"):
                    fail("SOURCE_DIGEST_MISMATCH", f"source digest mismatch: {key}", phase=key)
            # Admission receipts retain the snapshot that existed when they
            # were issued.  After invalid-dispatch reconciliation a fresh
            # snapshot is intentionally bound only to the redispatch; the
            # historical pre-dispatch receipts remain immutable evidence.
            receipt_report[key] = {"result": "PASS", "receipt_id": receipt.get("receipt_id")}
            previous = key

        source = record.get("source")
        if source and Path(str(source)).is_dir():
            actual_package_digest = self._tree_digest(Path(str(source)))
            if actual_package_digest != record.get("package_digest"):
                fail("PACKAGE_DIGEST_MISMATCH", "source package digest mismatch",
                     expected=record.get("package_digest"), observed=actual_package_digest)

        dispatch = receipts.get("dispatch")
        dispatch_valid = False
        dispatch_reason = "DISPATCH_RECEIPT_ABSENT"
        if isinstance(dispatch, Mapping):
            dispatch_valid, dispatch_reason = _dispatch_receipt_valid(dispatch, record)

        snapshot = record.get("authority_snapshot")
        if snapshot:
            unsigned = dict(snapshot)
            supplied = unsigned.pop("authority_snapshot_digest", None)
            if not supplied or supplied != _digest(unsigned):
                fail(AUTHORITY_FAILURE, "authority snapshot digest mismatch")
            bindings = {"wop_id": record.get("wop_id"), "package_digest": record.get("package_digest"),
                        "repository": record.get("repository"), "protected_baselines": protected}
            if any(snapshot.get(key) != value for key, value in bindings.items()):
                fail(AUTHORITY_FAILURE, "authority snapshot binding mismatch")
            authority = {"result": "PASS", "authority_snapshot_digest": supplied}
        elif dispatch is not None and dispatch_valid:
            fail(AUTHORITY_FAILURE, "dispatched transaction has no authority snapshot")
        else:
            authority = {"result": "PENDING", "authority_snapshot_digest": None,
                         "diagnostic": "HISTORICAL_EVIDENCE_UNAVAILABLE" if dispatch is not None else None}

        if dispatch is not None:
            if not dispatch_valid:
                if not allow_pending_dispatch:
                    return {"result": "RECONCILE", "receipt_chain": receipt_report,
                            "authority": authority, "dispatch": {"result": "FAIL", "diagnostic": dispatch_reason},
                            "hydration": record.get("hydration"),
                            "repository_transition": transition}
                return {"result": "RECONCILE", "receipt_chain": receipt_report,
                        "authority": authority, "dispatch": {"result": "FAIL", "diagnostic": dispatch_reason},
                        "hydration": record.get("hydration"),
                        "repository_transition": transition}
            dispatch_report = {"result": "PASS", "receipt_id": dispatch.get("receipt_id"),
                               "provider_id": dispatch.get("provider_id"), "agent_id": dispatch.get("agent_id")}
        else:
            dispatch_report = {"result": "PENDING", "diagnostic": "DISPATCH_RECEIPT_ABSENT"}
        return {"result": "PASS", "repository": {"result": repository_status,
                                                       "baseline": baseline,
                                                       "current_head": transition["current_head"]},
                "repository_transition": transition,
                "runtime": {"result": "PASS", "schema_version": record.get("schema_version")},
                "package": {"result": "PASS", "package_digest": record.get("package_digest")},
                "receipt_chain": receipt_report, "authority": authority, "dispatch": dispatch_report,
                "lifecycle": {"state": record.get("state"), "phase": (record.get("phases") or [None])[-1],
                               "next_phase": record.get("pending_phase")}}

    def _resolve_baseline_transition(self, record: Mapping[str, Any], baseline: str,
                                     fail: Callable[..., None]) -> dict[str, Any]:
        """Classify the repository transition before lifecycle verification."""
        if not baseline:
            fail("REPOSITORY_MISMATCH", "repository baseline is unavailable", expected=baseline)
        current = subprocess.run(["git", "-C", str(self.repository), "rev-parse", "HEAD"],
                                 text=True, capture_output=True, check=False).stdout.strip()
        status = subprocess.run(["git", "-C", str(self.repository), "status", "--porcelain",
                                 "--untracked-files=all"], text=True, capture_output=True, check=False)
        branch = subprocess.run(["git", "-C", str(self.repository), "branch", "--show-current"],
                                text=True, capture_output=True, check=False).stdout.strip()
        origin = subprocess.run(["git", "-C", str(self.repository), "rev-parse", "origin/main"],
                                text=True, capture_output=True, check=False).stdout.strip()
        if status.returncode or status.stdout:
            fail("UNCOMMITTED_WORKING_TREE_DRIFT", "repository working tree is not clean",
                 classification="UNCOMMITTED_WORKING_TREE_DRIFT", changes=status.stdout.splitlines())
        if current == baseline:
            submission_branch = record.get("submission_branch")
            if submission_branch and branch != submission_branch:
                fail("UNCOMMITTED_WORKING_TREE_DRIFT", "repository branch differs from submission branch",
                     classification="UNCOMMITTED_WORKING_TREE_DRIFT", expected_branch=submission_branch,
                     observed_branch=branch)
            classification = "EXACT_SUBMISSION_BASELINE"
            transition = {"transition_type": classification, "from_baseline": baseline,
                          "to_baseline": current, "recovery_baseline": current,
                          "current_head": current, "branch": branch, "ancestry_verified": True,
                          "publication_verified": False, "eos_synchronized": False,
                          "platform_validated": False}
            transition["transition_digest"] = _digest(transition)
            return {"classification": classification, **transition}
        if branch != "main" or not origin or current != origin:
            fail("UNCOMMITTED_WORKING_TREE_DRIFT", "repository is not the synchronized main baseline",
                 classification="UNCOMMITTED_WORKING_TREE_DRIFT", branch=branch,
                 current_head=current, origin_main=origin)
        baseline_ancestor = subprocess.run(
            ["git", "-C", str(self.repository), "merge-base", "--is-ancestor", baseline, current],
            capture_output=True, check=False,
        ).returncode == 0
        if not baseline_ancestor:
            current_ancestor = subprocess.run(
                ["git", "-C", str(self.repository), "merge-base", "--is-ancestor", current, baseline],
                capture_output=True, check=False,
            ).returncode == 0
            classification = "REWOUND_REPOSITORY_HISTORY" if current_ancestor else "UNRELATED_REPOSITORY_HISTORY"
            fail(classification, "repository baseline transition is not an authorized descendant",
                 classification=classification, expected=baseline, observed=current)

        binding = record.get("recovery_baseline_binding") or {}
        if binding and binding.get("recovery_baseline") == current:
            classification = "AUTHORIZED_RECOVERY_BASELINE"
            transition = dict(binding)
            transition.update(classification=classification, current_head=current, ancestry_verified=True)
            return transition

        receipt_path = record.get("publication_receipt_path")
        if not receipt_path:
            receipt_path = self.repository / "engineering/evidence/operation-beta/wop-zdcl-02-publication-aware-baseline-transition-and-canonical-resume-001/PUBLICATION-RECEIPT.json"
        path = Path(str(receipt_path))
        if not path.is_absolute():
            path = self.repository / path
        try:
            publication = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            fail("AMBIGUOUS_PUBLICATION_TRANSITION", "publication authority receipt is unavailable",
                 classification="AMBIGUOUS_PUBLICATION_TRANSITION", path=str(path))
        supplied = publication.get("receipt_digest")
        unsigned = dict(publication)
        unsigned.pop("receipt_digest", None)
        if not supplied or supplied != _digest(unsigned):
            fail("AMBIGUOUS_PUBLICATION_TRANSITION", "publication receipt digest is invalid",
                 classification="AMBIGUOUS_PUBLICATION_TRANSITION")
        publication_baseline = str(publication.get("resulting_main") or "")
        if not publication_baseline:
            fail("AMBIGUOUS_PUBLICATION_TRANSITION", "publication receipt has no resulting publication baseline",
                 classification="AMBIGUOUS_PUBLICATION_TRANSITION")
        published_ancestor = subprocess.run(
            ["git", "-C", str(self.repository), "merge-base", "--is-ancestor", publication_baseline, current],
            capture_output=True, check=False,
        ).returncode == 0
        if not published_ancestor:
            fail("AMBIGUOUS_PUBLICATION_TRANSITION", "current main is not a descendant of the published baseline",
                 classification="AMBIGUOUS_PUBLICATION_TRANSITION", expected=publication_baseline,
                 observed=current)
        continuation_paths = []
        if publication_baseline != current:
            diff = subprocess.run(
                ["git", "-C", str(self.repository), "diff", "--name-only", publication_baseline, current],
                text=True, capture_output=True, check=False,
            )
            continuation_paths = [line for line in diff.stdout.splitlines() if line]
            allowed_prefixes = ("docs/", "engineering/docs/", "engineering/evidence/")
            unauthorized = [path for path in continuation_paths
                            if not path.startswith(allowed_prefixes)]
            if diff.returncode or unauthorized:
                fail("AMBIGUOUS_PUBLICATION_TRANSITION",
                     "publication receipt does not authorize intervening repository changes",
                     classification="AMBIGUOUS_PUBLICATION_TRANSITION",
                     publication_baseline=publication_baseline, current_head=current,
                     unauthorized_paths=unauthorized)
        required = {
            "repository_identity": "git@github.com:lqoneal/homelab-infrastructure",
            "source_branch": "recovery/zdcl02-canonical-transaction-hydration",
            "source_commit": "1d14d59baef2be5dcecce0f550a997b474491402",
            "target_branch": "main",
            "resulting_main": publication_baseline,
            "pr_number": 52,
            "merge_disposition": "MERGED",
        }
        if any(publication.get(key) != value for key, value in required.items()):
            fail("AMBIGUOUS_PUBLICATION_TRANSITION", "publication receipt does not bind current publication",
                 classification="AMBIGUOUS_PUBLICATION_TRANSITION", expected=required, observed=publication)
        if not all(publication.get(key) is True for key in ("ancestry_verified", "eos_synchronized", "platform_validated", "protected_baselines_verified")):
            fail("AMBIGUOUS_PUBLICATION_TRANSITION", "publication receipt lacks required validation",
                 classification="AMBIGUOUS_PUBLICATION_TRANSITION")
        transition = {
            "transition_type": "AUTHORIZED_PUBLICATION_SUCCESSOR",
            "from_baseline": baseline,
            "to_baseline": current,
            "recovery_baseline": current,
            "repository": str(self.repository),
            "repository_identity": publication["repository_identity"],
            "ancestry_verified": True,
            "publication_verified": True,
            "eos_synchronized": True,
            "platform_validated": True,
            "publication_receipt_id": publication.get("publication_receipt_id"),
            "publication_receipt_digest": supplied,
            "publication_baseline": publication_baseline,
            "post_publication_descendant_verified": publication_baseline != current,
            "post_publication_paths": continuation_paths,
            "current_head": current,
        }
        transition["transition_digest"] = _digest(transition)
        return {"classification": transition["transition_type"], **transition}

    def _bind_recovery_baseline(self, record: Mapping[str, Any], transition: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
        value = deepcopy(dict(record))
        existing = value.get("recovery_baseline_binding")
        if existing and existing.get("transition_digest") != transition.get("transition_digest"):
            raise Stage1Error("recovery baseline binding conflicts with existing provenance",
                              evidence={"reason_code": AUTHORITY_FAILURE})
        if transition.get("classification") in {"AUTHORIZED_PUBLICATION_SUCCESSOR", "AUTHORIZED_RECOVERY_BASELINE"}:
            binding = dict(transition)
            binding["verified_at"] = (existing or {}).get("verified_at", timestamp)
            value["submission_baseline"] = value.get("submission_baseline") or value.get("repository_baseline")
            value["recovery_baseline"] = transition.get("recovery_baseline")
            value["recovery_baseline_binding"] = binding
        value["repository_transition"] = dict(transition)
        if value != record:
            return self.store.save(value)
        return self.store.load_path(self.store._path(value["instance_id"]))

    def _migrate_runtime(self, record: Mapping[str, Any], verification: Mapping[str, Any]) -> dict[str, Any]:
        """Upgrade pre-recovery records without changing transaction identity."""
        value = deepcopy(dict(record))
        if int(value.get("schema_version", 1)) < RECOVERY_SCHEMA_VERSION:
            value["schema_version"] = RECOVERY_SCHEMA_VERSION
            value["runtime_migration"] = {"from": record.get("schema_version", 1), "to": RECOVERY_SCHEMA_VERSION,
                                           "migration": "CANONICAL_TRANSACTION_RECOVERY_V1"}
            value["recovery_verification"] = deepcopy(dict(verification))
            return self.store.save(value)
        return value

    def _provisional(self, source: Path, root: Path, timestamp: str) -> dict[str, Any]:
        token = hashlib.sha256(f"{source}:{timestamp}".encode()).hexdigest()[:24]
        return {
            "schema_version": 1,
            "instance_id": f"ZEUS-SUBMISSION-{token}",
            "mission_id": "UNRESOLVED",
            "wop_id": "UNRESOLVED",
            "contract_id": None,
            "submitted_at": timestamp,
            "updated_at": timestamp,
            "operator": self.operator_resolver(),
            "repository": str(self.repository),
            "source": str(source),
            "state": "VALIDATING",
            "validation_evidence": {},
        }

    def _existing(self, candidate: Mapping[str, Any]) -> dict[str, Any] | None:
        for item in self.store.all():
            if item["instance_id"] == candidate["instance_id"]:
                if item["package_digest"] != candidate["package_digest"]:
                    raise Stage1Error("mission instance identity collision")
                return item
            if item["mission_id"] == candidate["mission_id"] and item["state"] in ACTIVE_STATES:
                raise Stage1Error(
                    f"mission already has an active admission: {item['instance_id']}",
                    evidence={"existing_instance": item["instance_id"]},
                )
        return None

    def _repository_evidence(self, contract: Mapping[str, Any]) -> dict[str, Any]:
        def git(*arguments: str) -> str:
            result = subprocess.run(
                ["git", "-C", str(self.repository), *arguments],
                text=True, capture_output=True, check=False,
            )
            if result.returncode:
                raise Stage1Error(result.stderr.strip() or "repository verification failed")
            return result.stdout.strip()
        observed_root = Path(git("rev-parse", "--show-toplevel")).resolve()
        observed = {
            "identity": self.repository.name,
            "root": str(observed_root),
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "working_tree": "CLEAN" if not git("status", "--porcelain=v1") else "MODIFIED",
            "baseline_provenance": str(contract["repository"]["baseline"]),
        }
        expected = contract["repository"]
        failures = []
        if observed_root != self.repository or Path(expected["root"]).resolve() != self.repository:
            failures.append("REPOSITORY_ROOT_MISMATCH")
        if expected["identity"] != observed["identity"]:
            failures.append("REPOSITORY_IDENTITY_MISMATCH")
        if expected["branch"] != observed["branch"]:
            failures.append("BRANCH_MISMATCH")
        ancestor = subprocess.run(
            ["git", "-C", str(self.repository), "merge-base", "--is-ancestor", str(expected["baseline"]), "HEAD"],
            capture_output=True,
        ).returncode == 0
        if not ancestor:
            failures.append("BASELINE_MISMATCH")
        if observed["working_tree"] == "MODIFIED" and contract["dirty_tree"]["policy"] == "CLEAN_REQUIRED":
            failures.append("WORKING_TREE_NOT_CLEAN")
        observed["result"] = "FAIL" if failures else "PASS"
        observed["failures"] = failures
        if failures:
            raise Stage1Error("repository verification failed", evidence={"repository_verification": observed})
        return observed

    @staticmethod
    def _tree_digest(root: Path) -> str:
        entries = [
            (str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest())
            for path in sorted(root.rglob("*")) if path.is_file()
        ]
        return _digest(entries)
