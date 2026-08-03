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


ACTIVE_STATES = {"VALIDATING", "ADMITTED", "STAGED", "VALIDATED", "AUTHORIZED", "EXECUTING", "QUALIFIED", "PUBLICATION_PREPARED", "SYNCHRONIZED", "INTERRUPTED", "BLOCKED"}
MISSION_STATES = ("VALIDATING", "REJECTED", "ADMITTED", "STAGED", "VALIDATED", "AUTHORIZED", "EXECUTING", "QUALIFIED", "PUBLICATION_PREPARED", "SYNCHRONIZED", "INTERRUPTED", "BLOCKED", "CLOSED")
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
    ):
        self.repository = Path(repository).resolve()
        self.store = Stage1Store(state_directory)
        self.events = EensPublisher(Path(state_directory) / "eens")
        self.resolver_factory = resolver_factory
        self.operator_resolver = operator_resolver

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
            if metadata.get("governance_authority") != "Engineering Governance":
                raise Stage1Error("development submission requires Engineering Governance authority",
                                  evidence={"reason_code": "GOVERNANCE_AUTHORITY_REQUIRED"})
            effect_profile = str(metadata.get("effect_profile") or "").upper()
            if not effect_profile or effect_profile == "PRODUCTION" or effect_profile.startswith("PRODUCTION-"):
                raise Stage1Error("development WOP requires a non-production effect profile",
                                  evidence={"reason_code": "EFFECT_PROFILE_INVALID"})
            if metadata.get("development_operator") not in {None, self.operator_resolver(), "loneal"}:
                raise Stage1Error("development operator is not authorized",
                                  evidence={"reason_code": "UNAUTHORIZED_OPERATOR"})
            expected = str(self.repository)
            if metadata.get("repository_identity") not in {None, expected}:
                raise Stage1Error("development WOP repository identity mismatch",
                                  evidence={"reason_code": "REPOSITORY_IDENTITY_MISMATCH"})
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
                     and item.get("state") in {"CLOSED", "PUBLICATION_PREPARED", "SYNCHRONIZED"}]
            if prior:
                raise Stage1Error(
                    "source changed after an accepted package; explicit supersession is required",
                    evidence={"reason_code": "SOURCE_CHANGED_REQUIRES_SUPERSESSION",
                              "prior_instances": [item["instance_id"] for item in prior]})
            if existing:
                if existing.get("package_digest") != package_digest:
                    raise Stage1Error("development submission identity collision")
                if existing.get("state") != "CLOSED":
                    existing = self._resume_development(existing, baseline, protected, timestamp,
                                                        interrupt_after=interrupt_after)
                existing["idempotent_replay"] = True
                return existing
            operator = self.operator_resolver()
            record = {
                "schema_version": 1, "instance_id": instance_id,
                "mission_id": str(metadata["mission_id"]), "wop_id": str(metadata["wop_id"]),
                "submitted_at": timestamp, "updated_at": timestamp, "operator": operator,
                "repository": expected, "source": str(source_path), "state": "VALIDATED",
                "package": str(source_path), "packaging": dict(packaging or {"packaged": False}),
                "execution_mode": "DEVELOPMENT", "package_digest": package_digest,
                "effect_profile": metadata["effect_profile"],
                "repository_baseline": baseline, "protected_baselines": protected,
                "validation_evidence": package_evidence,
                "registration": {"registration_id": "EMM-DEV-" + package_digest[:24],
                                  "owner": "Engineering Governance", "status": "GENERATED"},
                "provenance": {"repository": expected, "baseline": baseline,
                               "package_digest": package_digest, "generated_at": timestamp,
                               "operator": operator},
                "authorization": {"mode": "MANUAL_GOVERNANCE_DEVELOPMENT",
                                   "authority": "Engineering Governance",
                                   "decision": "SUBMISSION_CONSTITUTES_EXECUTION_AUTHORITY"},
                "failure_injection": {
                    "publication": bool(metadata.get("simulate_publication_failure")),
                    "synchronization": bool(metadata.get("simulate_synchronization_failure")),
                },
                "phases": [], "evidence": [], "failure": None,
            }
            record = self._resume_development(record, baseline, protected, timestamp,
                                              interrupt_after=interrupt_after)
            record["idempotent_replay"] = False
            return record

    def _resume_development(self, record: dict[str, Any], baseline: str,
                            protected: Mapping[str, str], timestamp: str,
                            *, interrupt_after: str | None = None) -> dict[str, Any]:
        phases = ("VALIDATED", "AUTHORIZED", "ADMITTED", "EXECUTING", "QUALIFIED",
                  "PUBLICATION_PREPARED", "SYNCHRONIZED", "CLOSED")
        completed = list(record.get("phases", []))
        for phase in phases:
            if phase in completed:
                continue
            injected = record.get("failure_injection", {})
            if phase == "PUBLICATION_PREPARED" and injected.get("publication"):
                record["state"] = "BLOCKED"
                record["failure"] = {"reason_code": "PUBLICATION_FAILURE", "phase": phase}
                record["updated_at"] = timestamp
                self.store.save(record)
                return self.store.load_path(self.store._path(record["instance_id"]))
            if phase == "SYNCHRONIZED" and injected.get("synchronization"):
                record["state"] = "BLOCKED"
                record["failure"] = {"reason_code": "SYNCHRONIZATION_FAILURE", "phase": phase}
                record["updated_at"] = timestamp
                self.store.save(record)
                return self.store.load_path(self.store._path(record["instance_id"]))
            current = subprocess.run(["git", "-C", str(self.repository), "rev-parse", "HEAD"],
                                     text=True, capture_output=True, check=False).stdout.strip()
            if current != baseline:
                raise Stage1Error("repository drift detected during development submission",
                                  evidence={"reason_code": "REPOSITORY_DRIFT", "expected": baseline, "observed": current})
            for tag, value in protected.items():
                observed = subprocess.run(["git", "-C", str(self.repository), "rev-parse", tag],
                                          text=True, capture_output=True, check=False).stdout.strip()
                if observed != value:
                    raise Stage1Error("protected baseline changed during development submission",
                                      evidence={"reason_code": "PROTECTED_BASELINE_MUTATION", "tag": tag})
            completed.append(phase)
            record["phases"] = completed
            record["state"] = phase
            record["updated_at"] = timestamp
            self.store.save(record)
            if interrupt_after == phase:
                record["state"] = "INTERRUPTED"
                record["interrupted_at"] = timestamp
                self.store.save(record)
                return self.store.load_path(self.store._path(record["instance_id"]))
        return self.store.load_path(self.store._path(record["instance_id"]))

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
