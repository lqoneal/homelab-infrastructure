#!/usr/bin/env python3
"""Pluggable, verification-first Operational Gate Handler Framework."""

from __future__ import annotations

import multiprocessing
import queue
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.authority_resolution import digest


API_VERSION = "zeus-gate-handler/1"
REQUIRED_CAPABILITIES = {
    "verification-first",
    "deterministic",
    "idempotent",
    "restartable",
    "structured-evidence",
    "cancellation",
}
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class GateHandlerError(ValueError):
    """Handler registration, negotiation, loading, or execution failed."""


class GateHandlerTimeout(GateHandlerError):
    """Handler exceeded its controlled execution deadline."""


@dataclass(frozen=True)
class HandlerManifest:
    handler_id: str
    version: str
    api_version: str
    modes: tuple[str, ...]
    gates: tuple[str, ...]
    capabilities: frozenset[str]
    mutating: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]):
        required = {
            "handler_id",
            "version",
            "api_version",
            "modes",
            "gates",
            "capabilities",
            "mutating",
        }
        missing = sorted(required - set(value))
        if missing:
            raise GateHandlerError(f"handler manifest missing: {', '.join(missing)}")
        manifest = cls(
            handler_id=str(value["handler_id"]),
            version=str(value["version"]),
            api_version=str(value["api_version"]),
            modes=tuple(value["modes"]),
            gates=tuple(value["gates"]),
            capabilities=frozenset(value["capabilities"]),
            mutating=bool(value["mutating"]),
        )
        manifest.validate()
        return manifest

    def validate(self):
        if not self.handler_id or not VERSION.fullmatch(self.version):
            raise GateHandlerError("handler identity or semantic version is invalid")
        if self.api_version != API_VERSION:
            raise GateHandlerError("handler API version is incompatible")
        if not self.modes or not set(self.modes) <= {"qualification", "operational"}:
            raise GateHandlerError("handler modes are invalid")
        if not self.gates or any(not gate for gate in self.gates):
            raise GateHandlerError("handler gates are invalid")
        missing = REQUIRED_CAPABILITIES - self.capabilities
        if missing:
            raise GateHandlerError(
                "handler capabilities missing: " + ", ".join(sorted(missing))
            )
        if "qualification" in self.modes and self.mutating:
            raise GateHandlerError("qualification handler must be non-mutating")

    def to_mapping(self):
        return {
            "handler_id": self.handler_id,
            "version": self.version,
            "api_version": self.api_version,
            "modes": list(self.modes),
            "gates": list(self.gates),
            "capabilities": sorted(self.capabilities),
            "mutating": self.mutating,
        }


class HandlerRegistry:
    """Registers controlled implementations and discovers matching manifests."""

    def __init__(self):
        self._implementations: dict[str, Any] = {}
        self._discovered: dict[str, HandlerManifest] = {}

    def register(self, handler):
        manifest = handler.manifest
        if not isinstance(manifest, HandlerManifest):
            raise GateHandlerError("handler manifest object is required")
        manifest.validate()
        existing = self._implementations.get(manifest.handler_id)
        if existing is not None and existing.manifest != manifest:
            raise GateHandlerError("handler identifier is already registered")
        self._implementations[manifest.handler_id] = handler
        return manifest

    def discover(self, directory: Path | str):
        directory = Path(directory)
        if not directory.is_dir():
            raise GateHandlerError(f"handler manifest directory missing: {directory}")
        discovered = []
        for path in sorted(directory.glob("*.yaml")):
            try:
                value = yaml.safe_load(path.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as error:
                raise GateHandlerError(f"invalid handler manifest {path}: {error}") from error
            if not isinstance(value, dict):
                raise GateHandlerError(f"handler manifest must be an object: {path}")
            manifest = HandlerManifest.from_mapping(value)
            implementation = self._implementations.get(manifest.handler_id)
            if implementation is None:
                raise GateHandlerError(
                    f"no controlled implementation registered for {manifest.handler_id}"
                )
            if implementation.manifest != manifest:
                raise GateHandlerError(
                    f"manifest and implementation disagree for {manifest.handler_id}"
                )
            if manifest.handler_id in self._discovered:
                raise GateHandlerError(
                    f"duplicate discovered handler: {manifest.handler_id}"
                )
            self._discovered[manifest.handler_id] = manifest
            discovered.append(manifest)
        return discovered

    def activate_registered(self, handler_id: str):
        """Activate an injected compatibility implementation without discovery."""
        implementation = self._implementations.get(handler_id)
        if implementation is None:
            raise GateHandlerError(f"handler is not registered: {handler_id}")
        self._discovered[handler_id] = implementation.manifest
        return implementation.manifest

    def negotiate(self, *, mode: str, gates, required_capabilities=None):
        required = REQUIRED_CAPABILITIES | set(required_capabilities or ())
        candidates = []
        for handler_id, manifest in self._discovered.items():
            if (
                mode in manifest.modes
                and set(gates) <= set(manifest.gates)
                and required <= manifest.capabilities
            ):
                candidates.append((manifest.version, handler_id))
        if not candidates:
            raise GateHandlerError("no compatible gate handler is available")
        _, handler_id = sorted(candidates, reverse=True)[0]
        return self._implementations[handler_id]

    def inventory(self):
        return [
            self._discovered[key].to_mapping() for key in sorted(self._discovered)
        ]


class QualificationGateHandler:
    """Deterministic, non-mutating reference implementation."""

    manifest = HandlerManifest(
        handler_id="zeus.qualification.reference",
        version="1.0.0",
        api_version=API_VERSION,
        modes=("qualification",),
        gates=("EXECUTE_WORK", "VERIFY_COMPLETION"),
        capabilities=frozenset(REQUIRED_CAPABILITIES),
        mutating=False,
    )

    def verify_current(self, gate_id, context):
        return {
            "condition": "VERIFIED",
            "gate_id": gate_id,
            "repository": context["repository"],
            "wop_submission_digest": context["wop"]["submission_digest"],
            "side_effects_observed": False,
        }

    def determine_required(self, gate_id, context, verification):
        completed = gate_id in context.get("completed_gates", [])
        return {
            "required": not completed,
            "disposition": "PREVIOUSLY_SATISFIED" if completed else "REQUIRED",
        }

    def execute_required(self, gate_id, context, work):
        return {
            "status": "COMPLETED",
            "result": (
                "QUALIFIED_SIMULATION"
                if gate_id == "EXECUTE_WORK"
                else "QUALIFICATION_VERIFIED"
            ),
            "gate_idempotency_key": context["gate_idempotency_key"],
            "artifacts": [],
            "side_effects_performed": False,
        }

    def verify_result(self, gate_id, context, result):
        return {
            "verification": "PASS",
            "side_effects_performed": result["side_effects_performed"],
            "result_digest": digest(result),
        }


class LegacyHandlerAdapter:
    """Compatibility adapter; new operational handlers must use the full contract."""

    def __init__(self, handler, gates):
        self.handler = handler
        self.manifest = HandlerManifest(
            handler_id="zeus.compatibility.injected",
            version="1.0.0",
            api_version=API_VERSION,
            modes=("qualification",),
            gates=tuple(gates),
            capabilities=frozenset(REQUIRED_CAPABILITIES),
            mutating=False,
        )

    def verify_current(self, gate_id, context):
        return {"condition": "VERIFIED", "compatibility_adapter": True}

    def determine_required(self, gate_id, context, verification):
        return {"required": True, "disposition": "REQUIRED"}

    def execute_required(self, gate_id, context, work):
        return self.handler.execute(gate_id, context)

    def verify_result(self, gate_id, context, result):
        return {"verification": "PASS", "result_digest": digest(result)}


def _execute_worker(handler, gate_id, context, output):
    try:
        verification = handler.verify_current(gate_id, context)
        work = handler.determine_required(gate_id, context, verification)
        trace = [
            {"step": "VERIFY_CURRENT", "result": verification},
            {"step": "DETERMINE_REQUIRED", "result": work},
        ]
        if work["required"]:
            result = handler.execute_required(gate_id, context, work)
            disposition = "EXECUTED"
            trace.append({"step": "EXECUTE_REQUIRED", "result": result})
        else:
            result = {
                "status": "COMPLETED",
                "result": "PREVIOUSLY_SATISFIED",
                "side_effects_performed": False,
                "artifacts": [],
            }
            disposition = "PREVIOUSLY_SATISFIED"
            trace.append({"step": "SKIP_SATISFIED", "result": result})
        final = handler.verify_result(gate_id, context, result)
        trace.append({"step": "VERIFY_RESULT", "result": final})
        output.put(
            {
                "ok": True,
                "value": {
                    **deepcopy(result),
                    "verification_first": True,
                    "disposition": disposition,
                    "handler_trace": trace,
                    "handler_id": handler.manifest.handler_id,
                    "handler_version": handler.manifest.version,
                },
            }
        )
    except Exception as error:
        output.put(
            {
                "ok": False,
                "error_type": type(error).__name__,
                "message": str(error),
            }
        )


class GateHandlerFramework:
    """Negotiates and executes handlers inside a bounded child process."""

    def __init__(
        self,
        registry: HandlerRegistry,
        *,
        timeout_seconds: float = 5.0,
        isolated: bool = True,
    ):
        if timeout_seconds <= 0:
            raise GateHandlerError("handler timeout must be positive")
        self.registry = registry
        self.timeout_seconds = timeout_seconds
        self.isolated = isolated

    def execute(self, *, mode, gate_id, context):
        handler = self.registry.negotiate(mode=mode, gates=[gate_id])
        if not self.isolated:
            output = queue.Queue(maxsize=1)
            _execute_worker(handler, gate_id, deepcopy(dict(context)), output)
            result = output.get_nowait()
            if not result["ok"]:
                raise GateHandlerError(
                    f"handler failure {result['error_type']}: {result['message']}"
                )
            return result["value"]
        process_context = multiprocessing.get_context("fork")
        output = process_context.Queue(maxsize=1)
        process = process_context.Process(
            target=_execute_worker,
            args=(handler, gate_id, deepcopy(dict(context)), output),
        )
        process.start()
        process.join(self.timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join()
            raise GateHandlerTimeout(
                f"handler timed out after {self.timeout_seconds} seconds"
            )
        try:
            result = output.get_nowait()
        except queue.Empty as error:
            raise GateHandlerError(
                f"handler process exited without result (exit={process.exitcode})"
            ) from error
        if not result["ok"]:
            raise GateHandlerError(
                f"handler failure {result['error_type']}: {result['message']}"
            )
        return result["value"]


def qualification_framework(repository_root: Path | str):
    registry = HandlerRegistry()
    registry.register(QualificationGateHandler())
    registry.discover(Path(repository_root) / "engineering/handlers")
    return GateHandlerFramework(registry)


def operational_framework(repository_root: Path | str):
    """Resolve the published operational artifact handler without legacy dispatch."""
    from scripts.lib.emp.operational_gate_handler import OperationalArtifactGateHandler

    registry = HandlerRegistry()
    registry.register(OperationalArtifactGateHandler())
    registry.discover(Path(repository_root) / "engineering/handlers/operational")
    return GateHandlerFramework(registry)
