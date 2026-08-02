#!/usr/bin/env python3
"""Canonical native Zeus development-session state and append-only evidence."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.authority_resolution import canonical_json, digest


class NativeSessionError(ValueError):
    """Session identity, authority binding, lifecycle, or evidence is invalid."""


ACTIVE_STATES = {"CREATED", "VERIFIED", "ACTIVE", "SUSPENDED", "RESUMED", "VERIFYING", "BLOCKED"}
TERMINAL_STATES = {"COMPLETED", "CANCELLED", "SUPERSEDED", "FAILED"}
TRANSITIONS = {
    "CREATED": {"VERIFIED", "BLOCKED", "CANCELLED", "FAILED"},
    "VERIFIED": {"ACTIVE", "BLOCKED", "CANCELLED", "FAILED"},
    "ACTIVE": {"SUSPENDED", "VERIFYING", "BLOCKED", "CANCELLED", "FAILED"},
    "SUSPENDED": {"RESUMED", "CANCELLED", "SUPERSEDED", "FAILED"},
    "RESUMED": {"ACTIVE", "VERIFYING", "BLOCKED", "CANCELLED", "FAILED"},
    "VERIFYING": {"COMPLETED", "BLOCKED", "FAILED"},
    "BLOCKED": {"RESUMED", "CANCELLED", "SUPERSEDED", "FAILED"},
}


def session_identifier(execution_id: str) -> str:
    return "ZEUS-SESSION-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_json({"execution_id": execution_id})))


class NativeSessionStore:
    """Mutable current projection with immutable, create-only event publications."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)
        self.evidence_directory = self.directory / "published-evidence"

    def path(self, session_id: str) -> Path:
        return self.directory / f"{session_id}.json"

    def current_for_execution(self, execution_id: str) -> dict[str, Any] | None:
        session_id = session_identifier(execution_id)
        return self.load(session_id) if self.path(session_id).exists() else None

    def load(self, session_id: str) -> dict[str, Any]:
        try:
            value = json.loads(self.path(session_id).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise NativeSessionError(f"invalid native session: {error}") from error
        supplied = value.pop("state_digest", None)
        if supplied != digest(value):
            raise NativeSessionError("native session state digest mismatch")
        self._validate_evidence(value.get("evidence", []))
        value["state_digest"] = supplied
        return value

    def create(self, binding: Mapping[str, Any], *, at: datetime) -> dict[str, Any]:
        execution_id = str(binding["execution_id"])
        session_id = session_identifier(execution_id)
        if self.path(session_id).exists():
            existing = self.load(session_id)
            expected = {key: binding[key] for key in binding}
            observed = {key: existing.get(key) for key in binding}
            if expected != observed:
                raise NativeSessionError("duplicate session identity has a different authority binding")
            return existing
        for path in self.directory.glob("ZEUS-SESSION-*.json"):
            existing = self.load(path.stem)
            if existing.get("execution_id") == execution_id and existing.get("session_id") != session_id:
                raise NativeSessionError("one execution cannot resolve multiple sessions")
        required = ("operation", "mission_id", "wop_id", "wop_revision", "submission_id", "admission_id", "execution_id", "repository_identity", "admitted_baseline", "principal", "submitter", "execution_agent", "session_classification", "authorized_effect_profile")
        missing = [field for field in required if not binding.get(field)]
        if missing:
            raise NativeSessionError("session authority binding is incomplete: " + ", ".join(missing))
        timestamp = self._time(at)
        state = {
            "schema_version": 1, "session_id": session_id, **deepcopy(dict(binding)),
            "current_baseline": binding["admitted_baseline"], "lifecycle_state": "CREATED",
            "current_gate": "VALIDATE_WOP", "checkpoints": [], "evidence_references": [],
            "blockers": [], "next_authorized_action": "Verify session authority and repository baseline.",
            "created_at": timestamp, "updated_at": timestamp, "suspended_at": None,
            "resumed_at": None, "closed_at": None, "evidence": [],
        }
        self._append(state, "SESSION_CREATED", {"authority_binding_digest": digest(dict(binding))}, at)
        self.save(state)
        return self.load(session_id)

    def transition(self, session_id: str, target: str, *, at: datetime, event: str, payload: Mapping[str, Any] | None = None, current_gate: str | None = None, next_action: str | None = None) -> dict[str, Any]:
        state = self.load(session_id)
        source = state["lifecycle_state"]
        if source == target:
            return state
        if target not in TRANSITIONS.get(source, set()):
            raise NativeSessionError(f"invalid session transition: {source} -> {target}")
        state.pop("state_digest", None)
        state["lifecycle_state"] = target
        state["updated_at"] = self._time(at)
        if current_gate is not None:
            state["current_gate"] = current_gate
        if next_action is not None:
            state["next_authorized_action"] = next_action
        if target == "SUSPENDED": state["suspended_at"] = self._time(at)
        if target == "RESUMED": state["resumed_at"] = self._time(at)
        if target in TERMINAL_STATES: state["closed_at"] = self._time(at)
        self._append(state, event, {"from": source, "to": target, **dict(payload or {})}, at)
        self.save(state)
        return self.load(session_id)

    def checkpoint(self, session_id: str, checkpoint: Mapping[str, Any], *, at: datetime) -> dict[str, Any]:
        state = self.load(session_id); state.pop("state_digest", None)
        sealed = deepcopy(dict(checkpoint)); sealed["checkpoint_digest"] = digest(sealed)
        if any(item["checkpoint_digest"] == sealed["checkpoint_digest"] for item in state["checkpoints"]):
            return self.load(session_id)
        state["checkpoints"].append(sealed)
        self._append(state, "SESSION_CHECKPOINT", sealed, at)
        state["updated_at"] = self._time(at); self.save(state)
        return self.load(session_id)

    def save(self, value: Mapping[str, Any]):
        data = deepcopy(dict(value)); data.pop("state_digest", None)
        self._validate_evidence(data.get("evidence", [])); data["state_digest"] = digest(data)
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self.directory, prefix=".session.")
        try:
            with os.fdopen(descriptor, "w") as stream:
                json.dump(data, stream, indent=2, sort_keys=True); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, self.path(str(data["session_id"])))
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

    def _append(self, state, event, payload, at):
        previous = state["evidence"][-1]["evidence_digest"] if state["evidence"] else None
        material = {"sequence": len(state["evidence"]) + 1, "event": event, "observed_at": self._time(at), "previous_evidence_digest": previous, "payload": deepcopy(payload)}
        material["evidence_digest"] = digest(material)
        directory = self.evidence_directory / state["session_id"]; directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{material['sequence']:04d}.json"; encoded = json.dumps(material, indent=2, sort_keys=True) + "\n"
        try: descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        except FileExistsError:
            if path.read_text(encoding="utf-8") != encoded: raise NativeSessionError("published session evidence is immutable")
        else:
            with os.fdopen(descriptor, "w") as stream: stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
        state["evidence"].append(material); state["evidence_references"].append(str(path))

    @staticmethod
    def _validate_evidence(entries):
        previous = None
        for sequence, entry in enumerate(entries, 1):
            material = deepcopy(entry); supplied = material.pop("evidence_digest", None)
            if material.get("sequence") != sequence or material.get("previous_evidence_digest") != previous or supplied != digest(material):
                raise NativeSessionError("native session evidence chain mismatch")
            previous = supplied

    @staticmethod
    def _time(value):
        if value.tzinfo is None: raise NativeSessionError("timestamp must include timezone")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
