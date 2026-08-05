#!/usr/bin/env python3
"""Zeus-owned Codex provider wrapper.

The wrapper is the only lifecycle-facing adapter allowed to invoke the
lower-level ``engctl codex`` service.  It owns the mission-bound context,
process group, durable provider journal, bounded stop/resume semantics, and
fail-closed authority checks.  It never creates execution authority.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Mapping


class CodexWrapperError(ValueError):
    """The Codex provider cannot be safely controlled by Zeus."""


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _id(prefix: str, value: Any) -> str:
    return f"{prefix}-{uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(value, sort_keys=True))}"


@contextmanager
def _lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


class CodexExecutionStore:
    """Atomic journal for one Zeus-controlled provider execution."""

    def __init__(self, runtime_root: Path | str):
        self.root = Path(runtime_root) / "codex-provider"
        self.path = self.root / "executions.json"
        self.lock = self.root / "executions.lock"

    def load_all(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"schema_version": 1, "executions": {}}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CodexWrapperError(f"CODEX_JOURNAL_INVALID: {error}") from error
        if not isinstance(value, dict) or not isinstance(value.get("executions"), dict):
            raise CodexWrapperError("CODEX_JOURNAL_INVALID: expected executions mapping")
        return value

    def save_all(self, value: Mapping[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        descriptor, raw = tempfile.mkstemp(dir=self.root, prefix=".executions.")
        temporary = Path(raw)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(dict(value), stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def get(self, execution_id: str) -> dict[str, Any] | None:
        return self.load_all()["executions"].get(execution_id)


class CodexContext:
    """Validated context passed to the lower-level provider service."""

    @staticmethod
    def build(
        root: Path | str,
        authoritative: Mapping[str, Any],
        *,
        branch: str | None = None,
        mission_contract: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        repository = Path(root).resolve()
        transaction_id = authoritative.get("instance_id") or authoritative.get("execution_id") or authoritative.get("transaction_id")
        required = {
            "transaction_id": transaction_id,
            "wop_id": authoritative.get("wop_id"),
            "mission_id": authoritative.get("mission_id"),
            "execution_mode": authoritative.get("execution_mode"),
            "effect_profile": authoritative.get("effect_profile"),
            "repository_identity": authoritative.get("repository_identity") or authoritative.get("repository"),
            "protected_baselines": authoritative.get("protected_baselines"),
        }
        missing = [key for key, value in required.items() if value in (None, "", [])]
        if missing:
            raise CodexWrapperError("CODEX_CONTEXT_INCOMPLETE: " + ", ".join(missing))
        if Path(str(required["repository_identity"])).resolve() != repository:
            raise CodexWrapperError("CODEX_CONTEXT_REPOSITORY_MISMATCH")
        authority = authoritative.get("governance_authority") or authoritative.get("authority") or ""
        if isinstance(authority, Mapping):
            authority = authority.get("authority") or authority.get("owner") or ""
        if authority != "Engineering Governance":
            raise CodexWrapperError("CODEX_CONTEXT_AUTHORITY_MISMATCH")
        if not str(required["execution_mode"]).upper() in {"DEVELOPMENT", "QUALIFICATION"}:
            raise CodexWrapperError("CODEX_CONTEXT_EXECUTION_MODE_UNSUPPORTED")
        protected = required["protected_baselines"]
        if not isinstance(protected, (list, dict)):
            raise CodexWrapperError("CODEX_CONTEXT_PROTECTED_BASELINES_INVALID")
        context = {
            "schema_version": 1,
            "transaction_id": str(transaction_id),
            "wop_id": str(required["wop_id"]),
            "mission_id": str(required["mission_id"]),
            "execution_mode": str(required["execution_mode"]),
            "effect_profile": str(required["effect_profile"]),
            "governance_authority": "Engineering Governance",
            "repository": str(repository),
            "branch": branch or "",
            "protected_baselines": deepcopy(protected),
            "mission_contract": deepcopy(mission_contract or {}),
        }
        context["context_digest"] = _digest(context)
        return context


class CodexWrapper:
    """Mission-bound Codex adapter with durable supervision."""

    def __init__(self, root: Path | str, runtime_root: Path | str, *, engctl: Path | str | None = None):
        self.root = Path(root).resolve()
        self.store = CodexExecutionStore(runtime_root)
        self.engctl = Path(engctl) if engctl else self.root / "scripts" / "engctl"

    def provider_registry(self) -> dict[str, Any]:
        path = self.root / "engineering" / "dispatch" / "execution-agent-registry.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CodexWrapperError(f"CODEX_PROVIDER_REGISTRY_INVALID: {error}") from error
        if not isinstance(value, dict):
            raise CodexWrapperError("CODEX_PROVIDER_REGISTRY_INVALID")
        return value

    def providers(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.provider_registry().get("agents", []) if isinstance(item, Mapping)]

    def capabilities(self) -> dict[str, Any]:
        return {"provider": "zeus-codex", "service": "engctl codex", "capabilities": [
            "mission-bound-context", "process-supervision", "bounded-stop", "interruption-resume",
            "receipt-backed-progress", "fail-closed-boundary", "eens-event-contract",
        ], "operator_entrypoint": "zeus submit <authorized-wop>", "direct_engctl_codex": "LOW_LEVEL_ONLY"}

    def _active_provider(self, provider_id: str | None = None) -> dict[str, Any]:
        candidates = [item for item in self.providers() if item.get("active") is True and item.get("qualification_status") == "QUALIFIED"]
        if provider_id:
            candidates = [item for item in candidates if item.get("provider_id", item.get("agent_id")) == provider_id or item.get("agent_id") == provider_id]
        if len(candidates) != 1:
            raise CodexWrapperError("CODEX_PROVIDER_SELECTION_AMBIGUOUS" if len(candidates) > 1 else "CODEX_PROVIDER_UNAVAILABLE")
        provider = candidates[0]
        if str(self.root) not in {str(Path(item).resolve()) for item in provider.get("repository_access_scope", [])}:
            raise CodexWrapperError("CODEX_PROVIDER_REPOSITORY_SCOPE_DENIED")
        return provider

    def launch(
        self,
        authoritative: Mapping[str, Any],
        *,
        branch: str,
        mission_contract: Mapping[str, Any] | None = None,
        provider_id: str | None = None,
        timeout: int = 0,
        codex_args: list[str] | None = None,
        popen_factory: Callable[..., Any] | None = None,
        now: Callable[[], float] = time.time,
    ) -> dict[str, Any]:
        provider = self._active_provider(provider_id)
        context = CodexContext.build(self.root, authoritative, branch=branch, mission_contract=mission_contract)
        execution_id = context["transaction_id"]
        launch_id = _id("ZEUS-CODEX-LAUNCH", {"execution_id": execution_id, "context_digest": context["context_digest"], "provider": provider.get("agent_id")})
        self.store.root.mkdir(parents=True, exist_ok=True)
        context_file = self.store.root / f"context-{execution_id}.json"
        descriptor, raw = tempfile.mkstemp(dir=self.store.root, prefix=f".context-{execution_id}.")
        temporary_context = Path(raw)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(context, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_context, context_file)
        finally:
            temporary_context.unlink(missing_ok=True)
        command = [str(self.engctl), "codex", "--wop", context["wop_id"], "--context-file", str(context_file)]
        if timeout:
            command += ["--timeout", str(timeout)]
        command += ["--"] + list(codex_args or [])
        with _lock(self.store.lock):
            journal = self.store.load_all()
            existing = journal["executions"].get(execution_id)
            if existing and existing.get("launch_id") != launch_id:
                raise CodexWrapperError("CODEX_EXECUTION_IDENTITY_CONFLICT")
            if existing and existing.get("state") in {"RUNNING", "STOPPED", "COMPLETED"}:
                return {**deepcopy(existing), "replay": True}
            record = {
                "schema_version": 1, "execution_id": execution_id, "launch_id": launch_id,
                "provider_id": provider.get("provider_id", provider.get("agent_id")), "agent_id": provider.get("agent_id"),
                "session_id": _id("ZEUS-CODEX-SESSION", launch_id), "context": context,
                "command": command, "context_file": str(context_file), "context_digest": context["context_digest"],
                "branch": branch, "working_directory": str(self.root),
                "state": "LAUNCH_REQUESTED", "launch_timestamp": now(), "attempt": 1,
                "receipts": {"launch_request": _id("ZEUS-RECEIPT-CODEX-LAUNCH", launch_id)},
                "eens": {"event": "provider.launch.requested", "event_id": _id("EENS-CODEX", launch_id)},
            }
            factory = popen_factory or subprocess.Popen
            env = os.environ.copy()
            env.update({
                "CODEX_WOP": context["wop_id"], "ZEUS_CODEX_EXECUTION_ID": execution_id,
                "ZEUS_CODEX_SESSION_ID": record["session_id"], "ZEUS_CODEX_REPOSITORY": str(self.root),
                "ZEUS_CODEX_BRANCH": branch, "ZEUS_CODEX_EFFECT_PROFILE": context["effect_profile"],
                "ZEUS_CODEX_AUTHORITY": context["governance_authority"], "ENGINEERING_CODEX_WRAPPER": "zeus-codex-v1",
                "ZEUS_CODEX_CONTEXT_FILE": str(context_file),
                "ZEUS_CODEX_CONTEXT_JSON": json.dumps(context, sort_keys=True, separators=(",", ":")),
            })
            try:
                stdout_path = self.store.root / f"{execution_id}.stdout.log"
                stderr_path = self.store.root / f"{execution_id}.stderr.log"
                stdout_stream = stdout_path.open("a", encoding="utf-8")
                stderr_stream = stderr_path.open("a", encoding="utf-8")
                try:
                    process = factory(command, cwd=str(self.root), env=env, start_new_session=True,
                                      stdin=subprocess.DEVNULL, stdout=stdout_stream,
                                      stderr=stderr_stream, text=True)
                finally:
                    stdout_stream.close()
                    stderr_stream.close()
                record.update(state="RUNNING", process_id=getattr(process, "pid", None), process_group_id=getattr(process, "pid", None),
                              stdout_path=str(stdout_path), stderr_path=str(stderr_path),
                              receipts={**record["receipts"], "launch_acknowledgment": _id("ZEUS-RECEIPT-CODEX-ACK", launch_id)},
                              next_authorized_action="Monitor Codex through Zeus; use the Zeus execution interface for stop or resume.")
            except Exception as error:
                record.update(state="LAUNCH_FAILED", blocker="CODEX_PROVIDER_LAUNCH_FAILED", error=str(error),
                              next_authorized_action="Retry the same execution after preserving launch diagnostics.")
            record["record_digest"] = _digest(record)
            journal["executions"][execution_id] = record
            self.store.save_all(journal)
            return record

    def status(self, execution_id: str) -> dict[str, Any]:
        with _lock(self.store.lock):
            journal = self.store.load_all()
            record = journal["executions"].get(execution_id)
            if not record:
                raise CodexWrapperError("CODEX_EXECUTION_NOT_FOUND")
            if record.get("state") == "RUNNING" and record.get("process_id"):
                try:
                    os.kill(int(record["process_id"]), 0)
                except OSError:
                    record.update(state="INTERRUPTED", blocker="CODEX_PROCESS_EXITED",
                                  next_authorized_action="Resume the same execution through Zeus after reviewing provider output.")
                    record["receipts"] = {**record.get("receipts", {}), "interrupted": _id("ZEUS-RECEIPT-CODEX-INTERRUPTED", record["launch_id"])}
                    record["record_digest"] = _digest(record)
                    journal["executions"][execution_id] = record
                    self.store.save_all(journal)
            return deepcopy(record)

    def stop(self, execution_id: str, *, timeout: float = 2.0) -> dict[str, Any]:
        with _lock(self.store.lock):
            journal = self.store.load_all()
            record = journal["executions"].get(execution_id)
            if not record:
                raise CodexWrapperError("CODEX_EXECUTION_NOT_FOUND")
            pid = record.get("process_group_id") or record.get("process_id")
            if record.get("state") != "RUNNING":
                return {**deepcopy(record), "replay": True}
            if not pid:
                record.update(state="STOPPED", blocker="CODEX_PROCESS_ID_MISSING")
            else:
                try:
                    os.killpg(int(pid), signal.SIGTERM)
                    deadline = time.time() + timeout
                    while time.time() < deadline:
                        try:
                            os.kill(int(pid), 0)
                        except OSError:
                            break
                        time.sleep(0.02)
                    try:
                        os.killpg(int(pid), signal.SIGKILL)
                    except OSError:
                        pass
                    record.update(state="STOPPED", stop_signal="SIGTERM/SIGKILL")
                except OSError as error:
                    record.update(state="STOPPED", blocker="CODEX_PROCESS_ALREADY_EXITED", detail=str(error))
            record["receipts"] = {**record.get("receipts", {}), "stop": _id("ZEUS-RECEIPT-CODEX-STOP", record["launch_id"])}
            record["record_digest"] = _digest(record)
            journal["executions"][execution_id] = record
            self.store.save_all(journal)
            return record

    def resume(self, execution_id: str, **kwargs: Any) -> dict[str, Any]:
        record = self.status(execution_id)
        if record.get("state") == "RUNNING":
            return {**record, "replay": True}
        if record.get("state") not in {"STOPPED", "LAUNCH_FAILED", "INTERRUPTED"}:
            raise CodexWrapperError("CODEX_RESUME_NOT_RECOVERABLE")
        authoritative = kwargs.pop("authoritative", None)
        if not isinstance(authoritative, Mapping):
            raise CodexWrapperError("CODEX_RESUME_CONTEXT_REQUIRED")
        return self.launch(authoritative, **kwargs, branch=record["branch"], provider_id=record.get("provider_id"))
