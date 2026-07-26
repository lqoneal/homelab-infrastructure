#!/usr/bin/env python3
"""Operational-grade, checkpointed artifact gate handler."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from scripts.lib.emp.authority_resolution import digest
from scripts.lib.emp.gate_handlers import (
    API_VERSION,
    REQUIRED_CAPABILITIES,
    GateHandlerError,
    HandlerManifest,
)


class OperationalContextError(GateHandlerError):
    """Operational execution context or service boundary is invalid."""


def _safe_relative(value: str) -> Path:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise OperationalContextError("artifact path must be safe and relative")
    return Path(*candidate.parts)


class OperationalExecutionContextService:
    """Build immutable handler context from already verified runtime state."""

    VERSION = "zeus-operational-execution-context/1"

    @classmethod
    def create(
        cls,
        *,
        execution_id: str,
        mission_id: str,
        repository: Path | str,
        repository_baseline: str,
        wop_submission_digest: str,
        workspace: Path | str,
        gate_plan: Mapping[str, Any],
        authorization: Mapping[str, Any],
    ) -> dict[str, Any]:
        root = Path(repository).resolve()
        work = Path(workspace).resolve()
        if work == root or root in work.parents:
            raise OperationalContextError(
                "operational handler workspace must be isolated from repository"
            )
        if not execution_id or not mission_id:
            raise OperationalContextError("execution and mission identity are required")
        if len(repository_baseline) != 40 or len(wop_submission_digest) != 64:
            raise OperationalContextError("repository or WOP digest is invalid")
        if authorization.get("decision") != "AUTHORIZED":
            raise OperationalContextError("execution authorization is not granted")
        if authorization.get("execution_id") != execution_id:
            raise OperationalContextError("authorization execution binding mismatch")
        plan = cls._validate_plan(gate_plan)
        value = {
            "schema_version": 1,
            "service_version": cls.VERSION,
            "execution_id": execution_id,
            "mission_id": mission_id,
            "repository": str(root),
            "repository_baseline": repository_baseline,
            "wop_submission_digest": wop_submission_digest,
            "workspace": str(work),
            "gate_plan": plan,
            "gate_plan_digest": digest(plan),
            "authorization": deepcopy(dict(authorization)),
        }
        value["context_digest"] = digest(value)
        return value

    @staticmethod
    def _validate_plan(value):
        if not isinstance(value, Mapping) or not isinstance(value.get("gates"), Mapping):
            raise OperationalContextError("gate plan must contain gates")
        plan = deepcopy(dict(value))
        for gate_id, gate in plan["gates"].items():
            if not gate_id or not isinstance(gate, Mapping):
                raise OperationalContextError("gate definition is invalid")
            actions = gate.get("actions")
            if not isinstance(actions, list) or not actions:
                raise OperationalContextError(f"gate {gate_id} requires actions")
            identifiers = set()
            for action in actions:
                if not isinstance(action, Mapping):
                    raise OperationalContextError("action must be an object")
                action_id = action.get("action_id")
                if not action_id or action_id in identifiers:
                    raise OperationalContextError("action identity is missing or duplicate")
                identifiers.add(action_id)
                if action.get("action_type") not in {
                    "create_artifact",
                    "verify_artifact",
                }:
                    raise OperationalContextError("action type is not supported")
                _safe_relative(str(action.get("path", "")))
                if action["action_type"] == "create_artifact":
                    if not isinstance(action.get("content"), str):
                        raise OperationalContextError("artifact content must be text")
                    expected = digest({"content": action["content"]})
                    if action.get("content_digest") != expected:
                        raise OperationalContextError("artifact content digest mismatch")
                elif len(str(action.get("content_digest", ""))) != 64:
                    raise OperationalContextError("verification digest is invalid")
            dependencies = gate.get("dependencies", [])
            if not isinstance(dependencies, list) or any(
                not isinstance(item, str) or not item for item in dependencies
            ):
                raise OperationalContextError("gate dependencies are invalid")
        return plan

    @staticmethod
    def validate(value: Mapping[str, Any]):
        material = deepcopy(dict(value))
        supplied = material.pop("context_digest", None)
        if supplied != digest(material):
            raise OperationalContextError("operational context digest mismatch")
        if material.get("service_version") != OperationalExecutionContextService.VERSION:
            raise OperationalContextError("operational context version is incompatible")
        OperationalExecutionContextService._validate_plan(material["gate_plan"])
        if material["gate_plan_digest"] != digest(material["gate_plan"]):
            raise OperationalContextError("gate plan digest mismatch")


class ActionCheckpointStore:
    """Create/update a deterministic action checkpoint in an isolated workspace."""

    def __init__(self, workspace: Path | str, execution_id: str, gate_id: str):
        self.directory = Path(workspace) / ".zeus-checkpoints" / execution_id
        self.path = self.directory / f"{gate_id}.json"

    def load(self):
        if not self.path.exists():
            return {"schema_version": 1, "completed_actions": [], "entries": []}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise OperationalContextError(f"invalid action checkpoint: {error}") from error
        supplied = value.pop("checkpoint_digest", None)
        if supplied != digest(value):
            raise OperationalContextError("action checkpoint digest mismatch")
        value["checkpoint_digest"] = supplied
        return value

    def record(self, action_id: str, result: Mapping[str, Any]):
        value = self.load()
        if action_id in value["completed_actions"]:
            entry = next(
                item for item in value["entries"] if item["action_id"] == action_id
            )
            if entry["result_digest"] != digest(result):
                raise OperationalContextError("checkpoint result disagreement")
            return value
        value.pop("checkpoint_digest", None)
        value["completed_actions"].append(action_id)
        value["entries"].append(
            {"action_id": action_id, "result_digest": digest(result)}
        )
        value["checkpoint_digest"] = digest(
            {key: item for key, item in value.items() if key != "checkpoint_digest"}
        )
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            dir=self.directory, prefix=".checkpoint."
        )
        try:
            with os.fdopen(descriptor, "w") as stream:
                json.dump(value, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return value


class OperationalArtifactGateHandler:
    """First operational handler: bounded create/verify artifact gates only."""

    manifest = HandlerManifest(
        handler_id="zeus.operational.artifact",
        version="1.0.0",
        api_version=API_VERSION,
        modes=("operational",),
        gates=("EXECUTE_WORK", "VERIFY_COMPLETION"),
        capabilities=frozenset(
            REQUIRED_CAPABILITIES
            | {"artifact-create", "artifact-verify", "action-checkpoints"}
        ),
        mutating=True,
    )

    def verify_current(self, gate_id, context):
        operational = context.get("operational_context")
        if not isinstance(operational, Mapping):
            raise OperationalContextError("operational execution context is required")
        OperationalExecutionContextService.validate(operational)
        if context.get("cancellation_requested"):
            raise OperationalContextError("execution cancellation requested")
        if operational["execution_id"] != context["execution_id"]:
            raise OperationalContextError("runtime/context execution mismatch")
        if operational["wop_submission_digest"] != context["wop"]["submission_digest"]:
            raise OperationalContextError("runtime/context WOP mismatch")
        observed = subprocess.run(
            ["git", "-C", operational["repository"], "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if (
            observed.returncode
            or observed.stdout.strip() != operational["repository_baseline"]
        ):
            raise OperationalContextError("repository baseline verification failed")
        gate = operational["gate_plan"]["gates"].get(gate_id)
        if gate is None:
            raise OperationalContextError(f"gate plan does not define {gate_id}")
        missing_dependencies = [
            item
            for item in gate.get("dependencies", [])
            if item not in context.get("completed_gates", [])
        ]
        if missing_dependencies:
            raise OperationalContextError(
                "gate dependencies are incomplete: " + ", ".join(missing_dependencies)
            )
        checkpoint = ActionCheckpointStore(
            operational["workspace"], context["execution_id"], gate_id
        ).load()
        return {
            "verification": "PASS",
            "repository_baseline": observed.stdout.strip(),
            "authorization_reference": operational["authorization"].get("reference"),
            "completed_actions": checkpoint["completed_actions"],
            "gate_plan_digest": operational["gate_plan_digest"],
        }

    def determine_required(self, gate_id, context, verification):
        actions = context["operational_context"]["gate_plan"]["gates"][gate_id][
            "actions"
        ]
        pending = [
            item["action_id"]
            for item in actions
            if item["action_id"] not in verification["completed_actions"]
        ]
        return {
            "required": bool(pending),
            "disposition": "REQUIRED" if pending else "PREVIOUSLY_SATISFIED",
            "pending_actions": pending,
        }

    def execute_required(self, gate_id, context, work):
        operational = context["operational_context"]
        workspace = Path(operational["workspace"])
        workspace.mkdir(parents=True, exist_ok=True)
        checkpoint = ActionCheckpointStore(
            workspace, context["execution_id"], gate_id
        )
        results = []
        for action in operational["gate_plan"]["gates"][gate_id]["actions"]:
            if action["action_id"] not in work["pending_actions"]:
                continue
            if context.get("cancellation_requested") or (
                workspace / ".cancel-requested"
            ).exists():
                raise OperationalContextError("execution cancellation requested")
            result = self._execute_action(workspace, action)
            checkpoint.record(action["action_id"], result)
            results.append(result)
        return {
            "status": "COMPLETED",
            "result": "OPERATIONAL_GATE_COMPLETED",
            "gate_idempotency_key": context["gate_idempotency_key"],
            "action_results": results,
            "artifacts": [
                item["artifact"] for item in results if item.get("artifact")
            ],
            "side_effects_performed": any(
                item["disposition"] == "CREATED" for item in results
            ),
        }

    def verify_result(self, gate_id, context, result):
        operational = context["operational_context"]
        workspace = Path(operational["workspace"])
        actions = operational["gate_plan"]["gates"][gate_id]["actions"]
        failures = []
        for action in actions:
            path = workspace / _safe_relative(action["path"])
            if not path.is_file():
                failures.append(f"missing:{action['action_id']}")
                continue
            observed = digest({"content": path.read_text(encoding="utf-8")})
            if observed != action["content_digest"]:
                failures.append(f"digest:{action['action_id']}")
        if failures:
            raise OperationalContextError(
                "post-execution verification failed: " + ", ".join(failures)
            )
        checkpoint = ActionCheckpointStore(
            workspace, context["execution_id"], gate_id
        ).load()
        expected = {item["action_id"] for item in actions}
        if set(checkpoint["completed_actions"]) != expected:
            raise OperationalContextError("action checkpoint is incomplete")
        return {
            "verification": "PASS",
            "verified_actions": sorted(expected),
            "checkpoint_digest": checkpoint["checkpoint_digest"],
            "result_digest": digest(result),
        }

    @staticmethod
    def _execute_action(workspace: Path, action: Mapping[str, Any]):
        path = workspace / _safe_relative(action["path"])
        expected = action["content_digest"]
        if action["action_type"] == "verify_artifact":
            if not path.is_file():
                raise OperationalContextError(f"artifact does not exist: {action['path']}")
            observed = digest({"content": path.read_text(encoding="utf-8")})
            if observed != expected:
                raise OperationalContextError("artifact verification failed")
            return {
                "action_id": action["action_id"],
                "disposition": "VERIFIED",
                "artifact": action["path"],
                "content_digest": observed,
            }
        path.parent.mkdir(parents=True, exist_ok=True)
        content = action["content"]
        if path.exists():
            if not path.is_file() or digest(
                {"content": path.read_text(encoding="utf-8")}
            ) != expected:
                raise OperationalContextError("existing artifact conflicts")
            disposition = "PREVIOUSLY_SATISFIED"
        else:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o440)
            with os.fdopen(descriptor, "w") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            disposition = "CREATED"
        return {
            "action_id": action["action_id"],
            "disposition": disposition,
            "artifact": action["path"],
            "content_digest": expected,
        }
