#!/usr/bin/env python3
"""Load, validate, discover, and render EMP Work Registry context."""

from __future__ import annotations

import argparse
import copy
import fcntl
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml
from yaml.constructor import ConstructorError


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = ROOT / "engineering/registry/work-registry.yaml"
DEFAULT_SCHEMA = ROOT / "engineering/registry/work-registry.schema.yaml"


class RegistryError(ValueError):
    """Raised when the registry cannot be loaded or validated."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


class NoAliasSafeDumper(yaml.SafeDumper):
    """Safe YAML dumper that never emits anchors or aliases."""

    def ignore_aliases(self, data):
        return True


def construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def configured_path(variable: str, default: Path) -> Path:
    return Path(os.environ.get(variable, str(default))).expanduser().resolve()


def load_mapping(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise RegistryError(f"{label} not found: {path}")
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError) as error:
        raise RegistryError(f"invalid {label}: {error}") from error
    if not isinstance(data, dict):
        raise RegistryError(f"{label} root must be a mapping")
    return data


def parse_yaml_value(value: str) -> Any:
    try:
        return yaml.load(value, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise RegistryError(f"invalid YAML value: {error}") from error


def normalized_collection(value: str) -> str:
    aliases = {
        "portfolio": "portfolios",
        "project": "projects",
        "mission": "missions",
        "phase": "phases",
        "sprint": "sprints",
        "work": "work_items",
        "work-item": "work_items",
        "work_item": "work_items",
        "queue": "queues",
        "milestone": "milestones",
        "deferral": "deferrals",
        "dependency": "dependencies",
    }
    return aliases.get(value, value)


def timestamp() -> str:
    """Return the attributable UTC timestamp used by registry mutations."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def serializable_date() -> str:
    return date.today().isoformat()


class WorkRegistry:
    def __init__(self, registry_path: Path, schema_path: Path) -> None:
        self.registry_path = registry_path
        self.schema_path = schema_path
        self.data = load_mapping(registry_path, "registry")
        self.schema = load_mapping(schema_path, "registry schema")
        self.objects: dict[str, dict[str, Any]] = {}
        self.collections: dict[str, list[dict[str, Any]]] = {}

    def validate(self) -> list[str]:
        errors: list[str] = []
        schema_types = self.schema.get("entity_types")
        root_schema = self.schema.get("root")
        if self.schema.get("schema_version") != 1 or not isinstance(schema_types, dict):
            errors.append("schema must declare schema_version 1 and entity_types")
            return errors
        if not isinstance(root_schema, dict):
            errors.append("schema root definition is missing")
            return errors

        for key in root_schema.get("required", []):
            if key not in self.data:
                errors.append(f"registry missing root field: {key}")

        if self.data.get("schema_version") != self.schema.get("registry_schema_version"):
            errors.append("registry schema_version does not match schema")
        if self.data.get("serialization") != self.schema.get("serialization"):
            errors.append("registry serialization does not match schema")
        if not isinstance(self.data.get("revision"), int) or self.data.get("revision", 0) < 1:
            errors.append("registry revision must be a positive integer")
        mutation_history = self.data.get("mutation_history", [])
        if not isinstance(mutation_history, list):
            errors.append("registry mutation_history must be a list when present")
        elif self.data.get("revision", 0) > 1:
            previous_revision = 1
            for entry in mutation_history:
                if not isinstance(entry, dict):
                    errors.append("registry mutation_history entry must be a mapping")
                    continue
                for field in ("revision", "previous_revision", "at", "actor", "action", "reason"):
                    if field not in entry or entry.get(field) in (None, ""):
                        errors.append(f"registry mutation_history entry missing {field}")
                if entry.get("previous_revision") != previous_revision:
                    errors.append("registry mutation_history revisions are not contiguous")
                previous_revision = entry.get("revision")
            if not mutation_history or mutation_history[-1].get("revision") != self.data.get("revision"):
                errors.append("registry mutation_history does not end at current revision")

        authority = self.data.get("authority_boundary")
        expected_authority = self.schema.get("authority_boundary")
        if authority != expected_authority:
            errors.append("registry authority_boundary does not match the required separation model")

        entities = self.data.get("entities")
        if not isinstance(entities, dict):
            errors.append("registry entities must be a mapping")
            return errors

        self.objects = {}
        self.collections = {}
        common_required = self.schema.get("common_required", [])
        for collection, definition in schema_types.items():
            items = entities.get(collection)
            if not isinstance(items, list):
                errors.append(f"entity collection must be a list: {collection}")
                continue
            self.collections[collection] = items
            required = list(common_required) + list(definition.get("required", []))
            allowed_states = set(definition.get("management_states", []))
            prefix = definition.get("id_prefix", "")
            object_type = definition.get("object_type")
            for position, item in enumerate(items, start=1):
                label = f"{collection}[{position}]"
                if not isinstance(item, dict):
                    errors.append(f"{label} must be a mapping")
                    continue
                registry_id = item.get("registry_id")
                if not isinstance(registry_id, str) or not registry_id.startswith(prefix):
                    errors.append(f"{label} has invalid registry_id for prefix {prefix}")
                    continue
                if registry_id in self.objects:
                    errors.append(f"duplicate registry_id: {registry_id}")
                else:
                    self.objects[registry_id] = item
                for key in required:
                    if key not in item:
                        errors.append(f"{registry_id} missing field: {key}")
                if item.get("object_type") != object_type:
                    errors.append(f"{registry_id} object_type must be {object_type}")
                if item.get("management_state") not in allowed_states:
                    errors.append(f"{registry_id} has invalid management_state")
                if not isinstance(item.get("revision"), int) or item.get("revision", 0) < 1:
                    errors.append(f"{registry_id} revision must be a positive integer")
                for list_key in ("source_records", "relationships", "transition_history"):
                    if not isinstance(item.get(list_key), list):
                        errors.append(f"{registry_id} {list_key} must be a list")
                history = item.get("transition_history")
                if isinstance(history, list) and history:
                    last = history[-1]
                    if not isinstance(last, dict) or last.get("to") != item.get("management_state"):
                        errors.append(f"{registry_id} transition history does not end at current state")
                archived = item.get("archived", False)
                if not isinstance(archived, bool):
                    errors.append(f"{registry_id} archived must be a boolean when present")
                if archived:
                    for key in ("archived_at", "archived_by", "archive_reason"):
                        if not item.get(key):
                            errors.append(f"{registry_id} archived object missing field: {key}")

        if errors:
            return errors

        self._validate_parents(schema_types, errors)
        self._validate_references(errors)
        self._validate_ordering(errors)
        self._validate_transition_histories(errors)
        self._validate_authority_and_evidence(errors)
        self._validate_deferrals(errors)
        self._validate_dependencies(errors)
        self._validate_relationships(errors)

        registry_text = self.registry_path.read_text(encoding="utf-8")
        if re.search(r"(^|\s)[&*][A-Za-z0-9_-]+", registry_text):
            errors.append("registry YAML aliases and anchors are prohibited")

        try:
            round_trip = yaml.safe_load(yaml.safe_dump(self.data, sort_keys=False))
        except yaml.YAMLError as error:
            errors.append(f"registry YAML round-trip failed: {error}")
        else:
            if round_trip != self.data:
                errors.append("registry YAML round-trip changed the data model")
        return errors

    def _validate_parents(self, schema_types: dict[str, Any], errors: list[str]) -> None:
        collection_ids = {
            collection: {item["registry_id"] for item in items}
            for collection, items in self.collections.items()
        }
        for collection, definition in schema_types.items():
            parent_field = definition.get("parent_field")
            parent_collection = definition.get("parent_collection")
            if not parent_field:
                continue
            valid_parents = collection_ids.get(parent_collection, set())
            for item in self.collections.get(collection, []):
                if item.get(parent_field) not in valid_parents:
                    errors.append(
                        f"{item['registry_id']} {parent_field} does not resolve in {parent_collection}"
                    )

    def _validate_ordering(self, errors: list[str]) -> None:
        ordered = ("projects", "missions", "phases", "sprints", "work_items")
        parent_fields = {
            "projects": "portfolio_id",
            "missions": "project_id",
            "phases": "mission_id",
            "sprints": "phase_id",
            "work_items": "project_id",
        }
        for collection in ordered:
            groups: dict[str, list[int]] = defaultdict(list)
            for item in self.collections.get(collection, []):
                order = item.get("order")
                if not isinstance(order, int) or order < 1:
                    errors.append(f"{item['registry_id']} order must be a positive integer")
                    continue
                groups[str(item.get(parent_fields[collection]))].append(order)
            for parent, values in groups.items():
                if len(values) != len(set(values)):
                    errors.append(f"duplicate {collection} order under {parent}")

        work_ids = {item["registry_id"] for item in self.collections.get("work_items", [])}
        for queue in self.collections.get("queues", []):
            entries = queue.get("entries")
            if not isinstance(entries, list):
                errors.append(f"{queue['registry_id']} entries must be a list")
                continue
            positions: list[int] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    errors.append(f"{queue['registry_id']} queue entry must be a mapping")
                    continue
                if entry.get("work_item_id") not in work_ids:
                    errors.append(f"{queue['registry_id']} queue entry does not resolve")
                if not isinstance(entry.get("position"), int) or entry["position"] < 1:
                    errors.append(f"{queue['registry_id']} queue position is invalid")
                else:
                    positions.append(entry["position"])
            if sorted(positions) != list(range(1, len(positions) + 1)):
                errors.append(f"{queue['registry_id']} positions must be contiguous from 1")

    @staticmethod
    def _document_ids(root: Path) -> set[str]:
        identities: set[str] = set()
        docs = root / "docs"
        if not docs.is_dir():
            return identities
        pattern = re.compile(r"^document_id:\s*([^\s]+)\s*$", re.MULTILINE)
        for path in docs.rglob("*.md"):
            match = pattern.search(path.read_text(encoding="utf-8", errors="replace"))
            if match:
                identities.add(match.group(1).strip("\"'"))
        return identities

    def _validate_references(self, errors: list[str]) -> None:
        local_ids = self._document_ids(ROOT)
        external_ids: dict[str, set[str]] = {}
        for project in self.collections.get("projects", []):
            repository = project.get("repository")
            if not isinstance(repository, dict):
                errors.append(f"{project['registry_id']} repository must be a mapping")
                continue
            presence = repository.get("presence")
            path_value = repository.get("path")
            name = repository.get("name")
            if presence == "present":
                if not isinstance(path_value, str) or not Path(path_value).is_dir():
                    errors.append(f"{project['registry_id']} present repository path does not exist")
                elif isinstance(name, str):
                    external_ids[name] = self._document_ids(Path(path_value))
            elif presence == "planned":
                if path_value is not None:
                    errors.append(f"{project['registry_id']} planned repository path must be null")
            else:
                errors.append(f"{project['registry_id']} repository presence is invalid")

        def source_resolves(reference: str) -> bool:
            if reference in local_ids:
                return True
            if ":" not in reference:
                return False
            repository_name, document_id = reference.split(":", 1)
            return document_id in external_ids.get(repository_name, set())

        for registry_id, item in self.objects.items():
            for reference in item.get("source_records", []):
                if not isinstance(reference, str) or not source_resolves(reference):
                    errors.append(f"{registry_id} source record does not resolve: {reference}")

        missions = {item["registry_id"]: item for item in self.collections.get("missions", [])}
        phases = {item["registry_id"]: item for item in self.collections.get("phases", [])}
        sprints = {item["registry_id"]: item for item in self.collections.get("sprints", [])}
        for item in self.collections.get("work_items", []):
            mission_id = item.get("mission_id")
            phase_id = item.get("phase_id")
            sprint_id = item.get("sprint_id")
            if mission_id is not None:
                mission = missions.get(mission_id)
                if mission is None or mission.get("project_id") != item.get("project_id"):
                    errors.append(f"{item['registry_id']} mission_id is inconsistent with project")
            if phase_id is not None:
                phase = phases.get(phase_id)
                if phase is None or phase.get("mission_id") != mission_id:
                    errors.append(f"{item['registry_id']} phase_id is inconsistent with mission")
            if sprint_id is not None:
                sprint = sprints.get(sprint_id)
                if sprint is None or sprint.get("phase_id") != phase_id:
                    errors.append(f"{item['registry_id']} sprint_id is inconsistent with phase")

        queue_membership: dict[str, set[str]] = defaultdict(set)
        for queue in self.collections.get("queues", []):
            if queue.get("scope_id") not in self.objects:
                errors.append(f"{queue['registry_id']} scope_id does not resolve")
            for entry in queue.get("entries", []):
                if isinstance(entry, dict) and isinstance(entry.get("work_item_id"), str):
                    queue_membership[entry["work_item_id"]].add(queue["registry_id"])
        for item in self.collections.get("work_items", []):
            declared = item.get("queue_ids")
            if isinstance(declared, list) and set(declared) != queue_membership[item["registry_id"]]:
                errors.append(f"{item['registry_id']} queue_ids do not match queue entries")

        for milestone in self.collections.get("milestones", []):
            if milestone.get("scope_id") not in self.objects:
                errors.append(f"{milestone['registry_id']} scope_id does not resolve")

    def _validate_authority_and_evidence(self, errors: list[str]) -> None:
        authority_states = {
            "missions": {"authorized", "active", "completed", "cancelled"},
            "phases": {"active", "completed", "cancelled"},
            "sprints": {"active", "completed", "cancelled"},
            "work_items": {"active", "completed", "cancelled", "deferred"},
        }
        for collection, states in authority_states.items():
            for item in self.collections.get(collection, []):
                if item.get("management_state") in states and not item.get("authority_reference"):
                    errors.append(f"{item['registry_id']} state requires authority_reference")
        for milestone in self.collections.get("milestones", []):
            if milestone.get("management_state") == "achieved":
                evidence = milestone.get("evidence_records")
                if not isinstance(evidence, list) or not evidence:
                    errors.append(f"{milestone['registry_id']} achieved state requires evidence_records")

        active_dependencies = {
            item.get("dependent_id")
            for item in self.collections.get("dependencies", [])
            if item.get("management_state") == "active"
        }
        for collection in ("missions", "phases", "sprints", "work_items"):
            for item in self.collections.get(collection, []):
                if item.get("management_state") != "blocked":
                    continue
                blockers = item.get("blocker_ids", [])
                if item["registry_id"] not in active_dependencies and not blockers:
                    errors.append(f"{item['registry_id']} blocked state requires a recorded blocker")

    def _validate_transition_histories(self, errors: list[str]) -> None:
        rules_by_collection = self.schema.get("transition_rules")
        if not isinstance(rules_by_collection, dict):
            errors.append("schema transition_rules are missing")
            return
        for collection, items in self.collections.items():
            rules = rules_by_collection.get(collection)
            if not isinstance(rules, dict):
                errors.append(f"schema transition rules missing for {collection}")
                continue
            for item in items:
                history = item.get("transition_history", [])
                previous_to: Any = None
                previous_at = ""
                for index, entry in enumerate(history):
                    if not isinstance(entry, dict):
                        continue
                    required = ("from", "to", "at", "actor", "reason", "authority_reference")
                    for field in required:
                        if field not in entry:
                            errors.append(f"{item['registry_id']} transition {index + 1} missing {field}")
                    observed_from = entry.get("from")
                    observed_to = entry.get("to")
                    observed_at = str(entry.get("at", ""))
                    if index and observed_from != previous_to:
                        errors.append(f"{item['registry_id']} transition history is not contiguous")
                    if index and observed_to not in rules.get(str(observed_from), []):
                        errors.append(
                            f"{item['registry_id']} records invalid transition: {observed_from} -> {observed_to}"
                        )
                    if previous_at and observed_at < previous_at:
                        errors.append(f"{item['registry_id']} transition history is not chronological")
                    previous_to = observed_to
                    previous_at = observed_at

    def _validate_deferrals(self, errors: list[str]) -> None:
        work = {item["registry_id"]: item for item in self.collections.get("work_items", [])}
        active_by_work: dict[str, int] = defaultdict(int)
        for deferral in self.collections.get("deferrals", []):
            work_id = deferral.get("work_item_id")
            if work_id not in work:
                errors.append(f"{deferral['registry_id']} work_item_id does not resolve")
                continue
            if deferral.get("management_state") == "active":
                active_by_work[work_id] += 1
                if work[work_id].get("management_state") != "deferred":
                    errors.append(f"{deferral['registry_id']} targets a non-deferred work item")
                if not deferral.get("authority_reference"):
                    errors.append(f"{deferral['registry_id']} requires authority_reference")
                if not deferral.get("reason") or not deferral.get("reentry_conditions"):
                    errors.append(f"{deferral['registry_id']} requires reason and reentry_conditions")
        for work_id, item in work.items():
            if item.get("management_state") == "deferred" and active_by_work[work_id] != 1:
                errors.append(f"{work_id} must have exactly one active deferral")

    def _validate_dependencies(self, errors: list[str]) -> None:
        graph: dict[str, set[str]] = defaultdict(set)
        for dependency in self.collections.get("dependencies", []):
            prerequisite = dependency.get("prerequisite_id")
            dependent = dependency.get("dependent_id")
            if prerequisite not in self.objects:
                errors.append(f"{dependency['registry_id']} prerequisite_id does not resolve")
            if dependent not in self.objects:
                errors.append(f"{dependency['registry_id']} dependent_id does not resolve")
            if prerequisite == dependent:
                errors.append(f"{dependency['registry_id']} cannot depend on itself")
            if dependency.get("management_state") == "active":
                graph[str(dependent)].add(str(prerequisite))
            if dependency.get("management_state") == "waived" and not dependency.get("authority_reference"):
                errors.append(f"{dependency['registry_id']} waived state requires authority_reference")

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return False
            if node in visited:
                return True
            visiting.add(node)
            if not all(visit(target) for target in graph[node]):
                return False
            visiting.remove(node)
            visited.add(node)
            return True

        if not all(visit(node) for node in list(graph)):
            errors.append("active dependencies contain a cycle")

    def _validate_relationships(self, errors: list[str]) -> None:
        allowed = set(self.schema.get("relationship_types", []))
        local_ids = self._document_ids(ROOT)
        for registry_id, item in self.objects.items():
            for relationship in item.get("relationships", []):
                if not isinstance(relationship, dict):
                    errors.append(f"{registry_id} relationship must be a mapping")
                    continue
                relation_type = relationship.get("type")
                target = relationship.get("target")
                if relation_type not in allowed:
                    errors.append(f"{registry_id} relationship type is invalid: {relation_type}")
                if not isinstance(target, str) or not target:
                    errors.append(f"{registry_id} relationship target is invalid")
                elif target not in self.objects and target not in local_ids and ":" not in target:
                    errors.append(f"{registry_id} relationship target does not resolve: {target}")

    def require_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise RegistryError("\n".join(errors))

    def _atomic_write(self) -> None:
        """Persist validated YAML by atomic replacement under the schema lock."""
        destination = self.registry_path
        mode = destination.stat().st_mode & 0o777
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        )
        temporary = Path(handle.name)
        try:
            yaml.dump(
                self.data,
                handle,
                Dumper=NoAliasSafeDumper,
                sort_keys=False,
                allow_unicode=True,
            )
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
            os.chmod(temporary, mode)
            os.replace(temporary, destination)
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if not handle.closed:
                handle.close()
            temporary.unlink(missing_ok=True)

    def mutate(
        self,
        operation: Callable[["WorkRegistry"], Any],
        *,
        action: str = "registry mutation",
        actor: str | None = None,
        reason: str | None = None,
    ) -> Any:
        """Apply one mutation under an exclusive lock and commit only valid state."""
        with self.schema_path.open("r", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = WorkRegistry(self.registry_path, self.schema_path)
            current.require_valid()
            result = operation(current)
            prior_revision = current.data["revision"]
            current.data["revision"] += 1
            current.data["updated_at"] = serializable_date()
            current.data.setdefault("mutation_history", []).append(
                {
                    "revision": current.data["revision"],
                    "previous_revision": prior_revision,
                    "at": timestamp(),
                    "actor": actor or os.environ.get("EMP_ACTOR") or os.environ.get("USER") or "EMP operator",
                    "action": action,
                    "reason": reason or action,
                }
            )
            current.require_valid()
            current._atomic_write()
            self.data = current.data
            self.objects = current.objects
            self.collections = current.collections
            return result

    def _touch(self, item: dict[str, Any]) -> None:
        item["revision"] += 1
        item["updated_at"] = timestamp()

    def _require_object(self, registry_id: str) -> dict[str, Any]:
        item = self.objects.get(registry_id)
        if item is None:
            raise RegistryError(f"unknown registry_id: {registry_id}")
        return item

    def _collection_for(self, registry_id: str) -> str:
        for collection, items in self.collections.items():
            if any(item.get("registry_id") == registry_id for item in items):
                return collection
        raise RegistryError(f"unknown registry_id: {registry_id}")

    def create(
        self, collection: str, item: dict[str, Any], actor: str = "EMP operator",
        reason: str = "Create registry object",
    ) -> str:
        collection = normalized_collection(collection)
        if collection not in self.schema.get("entity_types", {}):
            raise RegistryError(f"unknown entity collection: {collection}")
        if not isinstance(item, dict):
            raise RegistryError("created registry object must be a mapping")
        registry_id = item.get("registry_id")
        if not isinstance(registry_id, str) or not registry_id:
            raise RegistryError("created registry object requires registry_id")

        def operation(current: WorkRegistry) -> str:
            if registry_id in current.objects:
                raise RegistryError(f"registry_id already exists: {registry_id}")
            current.data["entities"][collection].append(copy.deepcopy(item))
            return registry_id

        return self.mutate(operation, action=f"create {registry_id}", actor=actor, reason=reason)

    def update(
        self, registry_id: str, field: str, value: Any, actor: str = "EMP operator",
        reason: str = "Update registry object",
    ) -> str:
        protected = {
            "registry_id", "object_type", "management_state", "created_at",
            "updated_at", "revision", "transition_history", "archived",
            "archived_at", "archived_by", "archive_reason",
        }
        if field in protected or "." in field or not field:
            raise RegistryError(f"field is mutation-protected: {field}")

        def operation(current: WorkRegistry) -> str:
            item = current._require_object(registry_id)
            if item.get("archived", False):
                raise RegistryError(f"archived object cannot be updated: {registry_id}")
            item[field] = copy.deepcopy(value)
            current._touch(item)
            return registry_id

        return self.mutate(
            operation, action=f"update {registry_id}.{field}", actor=actor, reason=reason
        )

    def archive(self, registry_id: str, actor: str, reason: str) -> str:
        if not actor or not reason:
            raise RegistryError("archive requires actor and reason")

        def operation(current: WorkRegistry) -> str:
            item = current._require_object(registry_id)
            if item.get("archived", False):
                raise RegistryError(f"object is already archived: {registry_id}")
            inbound: list[str] = []
            for other_id, other in current.objects.items():
                if other_id == registry_id or other.get("archived", False):
                    continue
                values = [value for key, value in other.items() if key != "source_records"]
                if any(current._contains_reference(value, registry_id) for value in values):
                    inbound.append(other_id)
            if inbound:
                raise RegistryError(
                    f"cannot archive {registry_id}; active references: {','.join(sorted(inbound))}"
                )
            item["archived"] = True
            item["archived_at"] = timestamp()
            item["archived_by"] = actor
            item["archive_reason"] = reason
            current._touch(item)
            return registry_id

        return self.mutate(
            operation, action=f"archive {registry_id}", actor=actor, reason=reason
        )

    @staticmethod
    def _contains_reference(value: Any, registry_id: str) -> bool:
        if isinstance(value, str):
            return value == registry_id
        if isinstance(value, list):
            return any(WorkRegistry._contains_reference(entry, registry_id) for entry in value)
        if isinstance(value, dict):
            return any(WorkRegistry._contains_reference(entry, registry_id) for entry in value.values())
        return False

    def transition(
        self,
        registry_id: str,
        new_state: str,
        actor: str,
        reason: str,
        authority_reference: str | None = None,
    ) -> str:
        if not actor or not reason:
            raise RegistryError("state transition requires actor and reason")

        def operation(current: WorkRegistry) -> str:
            current._apply_transition(
                registry_id, new_state, actor, reason, authority_reference
            )
            return registry_id

        return self.mutate(
            operation,
            action=f"transition {registry_id} to {new_state}",
            actor=actor,
            reason=reason,
        )

    def _apply_transition(
        self,
        registry_id: str,
        new_state: str,
        actor: str,
        reason: str,
        authority_reference: str | None = None,
        service: str | None = None,
    ) -> dict[str, Any]:
        item = self._require_object(registry_id)
        if item.get("archived", False):
            raise RegistryError(f"archived object cannot transition: {registry_id}")
        collection = self._collection_for(registry_id)
        old_state = str(item.get("management_state"))
        rules = self.schema.get("transition_rules", {}).get(collection, {})
        if new_state not in rules.get(old_state, []):
            raise RegistryError(f"invalid {collection} transition: {old_state} -> {new_state}")
        if service != "deferral" and collection == "work_items" and new_state == "deferred":
            raise RegistryError("use the deferral service to defer work")
        if service != "milestone" and collection == "milestones" and new_state == "achieved":
            raise RegistryError("use the milestone service to complete a milestone")
        if authority_reference:
            item["authority_reference"] = authority_reference
        item["management_state"] = new_state
        item["transition_history"].append(
            {
                "from": old_state,
                "to": new_state,
                "at": timestamp(),
                "actor": actor,
                "reason": reason,
                "authority_reference": authority_reference,
            }
        )
        self._touch(item)
        return item

    def iter_objects(self, collection: str = "all"):
        if collection == "all":
            for name in self.schema["entity_types"]:
                for item in self.collections.get(name, []):
                    yield name, item
            return
        collection = normalized_collection(collection)
        if collection not in self.schema["entity_types"]:
            raise RegistryError(f"unknown entity collection: {collection}")
        for item in self.collections.get(collection, []):
            yield collection, item

    def project_for_object(self, registry_id: str) -> str | None:
        item = self.objects.get(registry_id)
        if not item:
            return None
        object_type = item.get("object_type")
        if object_type == "Project":
            return registry_id
        if item.get("project_id"):
            return item["project_id"]
        parent_fields = {
            "Phase": "mission_id",
            "Sprint": "phase_id",
            "Deferral": "work_item_id",
        }
        parent_field = parent_fields.get(str(object_type))
        if parent_field and item.get(parent_field):
            return self.project_for_object(item[parent_field])
        return None

    def context(self, selector: str) -> list[str]:
        selector_key = selector.lower().replace("_", "-")
        projects = self.collections.get("projects", [])
        project = next(
            (
                item
                for item in projects
                if selector_key
                in {
                    str(item["registry_id"]).lower(),
                    str(item.get("slug", "")).lower(),
                }
            ),
            None,
        )
        if project is None:
            raise RegistryError(f"project is not registered: {selector}")
        project_id = project["registry_id"]
        portfolio = self.objects[project["portfolio_id"]]

        def scoped(collection: str) -> list[dict[str, Any]]:
            return [
                item
                for item in self.collections.get(collection, [])
                if self.project_for_object(item["registry_id"]) == project_id
            ]

        missions = scoped("missions")
        phases = scoped("phases")
        sprints = scoped("sprints")
        work_items = scoped("work_items")
        work_ids = {item["registry_id"] for item in work_items}
        queues = [
            queue
            for queue in self.collections.get("queues", [])
            if queue.get("scope_id") in {portfolio["registry_id"], project_id}
            and any(entry.get("work_item_id") in work_ids for entry in queue.get("entries", []))
        ]
        milestones = [
            item
            for item in self.collections.get("milestones", [])
            if item.get("scope_id") in {portfolio["registry_id"], project_id}
            or self.project_for_object(str(item.get("scope_id"))) == project_id
        ]
        deferrals = [
            item
            for item in self.collections.get("deferrals", [])
            if item.get("work_item_id") in work_ids and item.get("management_state") == "active"
        ]
        dependencies = [
            item
            for item in self.collections.get("dependencies", [])
            if item.get("dependent_id") in work_ids and item.get("management_state") == "active"
        ]
        blocked_ids = {
            item["registry_id"] for item in work_items if item.get("management_state") == "blocked"
        }
        blocked_ids.update(str(item["dependent_id"]) for item in dependencies)

        def ids(items: list[dict[str, Any]], states: set[str] | None = None) -> str:
            selected = items if states is None else [i for i in items if i.get("management_state") in states]
            return ",".join(str(item["registry_id"]) for item in selected) or "none"

        return [
            f"registry_path={self.registry_path}",
            f"registry_id={self.data['registry_id']}",
            f"registry_revision={self.data['revision']}",
            f"portfolio_id={portfolio['registry_id']}",
            f"portfolio_title={portfolio['title']}",
            f"portfolio_state={portfolio['management_state']}",
            f"portfolio_project_count={len(projects)}",
            f"management_project_id={project_id}",
            f"management_project_title={project['title']}",
            f"management_project_state={project['management_state']}",
            f"management_project_order={project['order']}",
            f"management_project_sources={','.join(project['source_records']) or 'none'}",
            f"management_current_missions={ids(missions, {'authorized', 'active', 'blocked'})}",
            f"management_current_phases={ids(phases, {'ready', 'active', 'blocked'})}",
            f"management_current_sprints={ids(sprints, {'ready', 'active', 'blocked'})}",
            f"management_open_work={ids(work_items, {'proposed', 'ready', 'active', 'blocked', 'deferred'})}",
            f"management_active_work={ids(work_items, {'active'})}",
            f"management_planned_work={ids(work_items, {'proposed', 'ready'})}",
            f"management_deferred_work={ids(work_items, {'deferred'})}",
            f"management_blocked_work={','.join(sorted(blocked_ids)) or 'none'}",
            f"management_completed_work={ids(work_items, {'completed'})}",
            f"management_queues={ids(queues)}",
            f"management_milestones={ids(milestones)}",
            f"management_active_deferrals={ids(deferrals)}",
            f"management_blocking_dependencies={ids(dependencies)}",
            "management_authority_boundary=registry-state-is-not-governance-or-controlled-document-lifecycle",
        ]


def build_registry() -> WorkRegistry:
    return WorkRegistry(
        configured_path("EMP_REGISTRY_PATH", DEFAULT_REGISTRY),
        configured_path("EMP_REGISTRY_SCHEMA_PATH", DEFAULT_SCHEMA),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("path")
    subparsers.add_parser("validate")
    subparsers.add_parser("show")
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("collection", nargs="?", default="all")
    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("registry_id")
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("collection")
    create_parser.add_argument("record", type=Path)
    create_parser.add_argument("reason")
    create_parser.add_argument("--actor", default=os.environ.get("EMP_ACTOR") or os.environ.get("USER") or "EMP operator")
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("registry_id")
    update_parser.add_argument("field")
    update_parser.add_argument("value")
    update_parser.add_argument("reason")
    update_parser.add_argument("--actor", default=os.environ.get("EMP_ACTOR") or os.environ.get("USER") or "EMP operator")
    archive_parser = subparsers.add_parser("archive")
    archive_parser.add_argument("registry_id")
    archive_parser.add_argument("reason")
    archive_parser.add_argument("--actor", default=os.environ.get("EMP_ACTOR") or os.environ.get("USER") or "EMP operator")
    transition_parser = subparsers.add_parser("transition")
    transition_parser.add_argument("registry_id")
    transition_parser.add_argument("new_state")
    transition_parser.add_argument("reason")
    transition_parser.add_argument("--authority-reference")
    transition_parser.add_argument("--actor", default=os.environ.get("EMP_ACTOR") or os.environ.get("USER") or "EMP operator")
    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("project", nargs="?", default="homelab")
    args = parser.parse_args()

    try:
        registry = build_registry()
        if args.command == "path":
            print(registry.registry_path)
            return 0
        registry.require_valid()
        if args.command == "validate":
            count = len(registry.objects)
            print(f"PASS: registry schema and YAML serialization ({count} objects)")
            print("PASS: registry identifiers, hierarchy, ordering, states, deferrals, and dependencies")
            print("PASS: registry authority boundary")
        elif args.command == "show":
            print(yaml.safe_dump(registry.data, sort_keys=False).rstrip())
        elif args.command == "list":
            print("collection\tregistry_id\tmanagement_state\torder\ttitle")
            for collection, item in registry.iter_objects(args.collection):
                print(
                    f"{collection}\t{item['registry_id']}\t{item['management_state']}\t"
                    f"{item.get('order', '')}\t{item['title']}"
                )
        elif args.command == "get":
            item = registry.objects.get(args.registry_id)
            if item is None:
                raise RegistryError(f"unknown registry_id: {args.registry_id}")
            print(yaml.safe_dump(item, sort_keys=False).rstrip())
        elif args.command == "create":
            print(registry.create(args.collection, load_mapping(args.record, "registry object"), args.actor, args.reason))
        elif args.command == "update":
            print(registry.update(args.registry_id, args.field, parse_yaml_value(args.value), args.actor, args.reason))
        elif args.command == "archive":
            print(registry.archive(args.registry_id, args.actor, args.reason))
        elif args.command == "transition":
            print(registry.transition(args.registry_id, args.new_state, args.actor, args.reason, args.authority_reference))
        elif args.command == "context":
            print("Engineering Work Registry Context")
            print("\n".join(registry.context(args.project)))
    except RegistryError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
