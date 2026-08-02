#!/usr/bin/env python3
"""Durable, fail-closed state for the Zeus operator interface."""

from __future__ import annotations

import fcntl
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from scripts.lib.emp.orchestration import OrchestrationError
from scripts.lib.emp.runtime_paths import runtime_path
from scripts.lib.emp.runtime_paths import runtime_root

SCHEMA_VERSION = 1
ORIENTATION_LIMIT = 100
STATE_RELATIVE_PATH = Path("operator-interface-state.json")
STATE_KEYS = {"schema_version", "invocation_count", "orientation_limit"}

ORIENTATION = """\
Zeus is a supervised engineering orchestration interface. It presents status,
WOP guidance, and controlled mission lifecycle operations; it does not itself
grant approval or execution authority.

Start with `zeus status`, `zeus --help`, or `zeus show wop-requirements`.
Missions are staged, admitted through WOP controls, approved by the designated
authority, selected, executed, qualified, and reconciled by their respective
controlled services. Unsupported natural-language requests are not unrestricted
engineering instructions. Operational guidance:
engineering/operations/zeus-operator-interface.md
"""


def initial_state() -> dict[str, int]:
    return {
        "schema_version": SCHEMA_VERSION,
        "invocation_count": 0,
        "orientation_limit": ORIENTATION_LIMIT,
    }


def authoritative_state_path(repository_root: Path) -> Path:
    return runtime_path(repository_root, STATE_RELATIVE_PATH.name)


def _reject_symlinks(root: Path, path: Path) -> None:
    root = root.resolve()
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise OrchestrationError(
                "operator-interface runtime path may not use symbolic links"
            )


def validate_state(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise OrchestrationError("operator-interface state must be an object")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise OrchestrationError(
            "incompatible operator-interface schema version: "
            f"expected {SCHEMA_VERSION}, found {value.get('schema_version')!r}"
        )
    if set(value) != STATE_KEYS:
        raise OrchestrationError("operator-interface state shape is invalid")
    count = value["invocation_count"]
    limit = value["orientation_limit"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise OrchestrationError(
            "operator-interface invocation_count must be a non-negative integer"
        )
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or limit != ORIENTATION_LIMIT
    ):
        raise OrchestrationError(
            f"operator-interface orientation_limit must be {ORIENTATION_LIMIT}"
        )
    return value


class OperatorInterfaceStore:
    def __init__(self, repository_root: Path, path: Path | None = None):
        # Test overrides are explicitly isolated and checked from their parent's
        # parent so a symlinked containing directory remains observable.
        self.root = path.parent.parent.resolve() if path is not None else runtime_root(repository_root)
        self.path = path or authoritative_state_path(self.root)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _verify_paths(self) -> None:
        _reject_symlinks(self.root, self.path)
        _reject_symlinks(self.root, self.lock_path)

    def _load_locked(self) -> dict[str, int]:
        self._verify_paths()
        if not self.path.exists():
            return initial_state()
        try:
            value = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise OrchestrationError(
                f"invalid operator-interface state: {error}"
            ) from error
        return validate_state(value)

    def _save_locked(self, value: dict[str, int]) -> None:
        validate_state(value)
        self._verify_paths()
        serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
        descriptor, temporary = tempfile.mkstemp(
            dir=self.path.parent, prefix=".operator-interface."
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            os.chmod(self.path, 0o600)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self._verify_paths()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path.parent, 0o700)
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.lock_path, flags, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            self._verify_paths()
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def increment(self) -> dict[str, int]:
        with self._locked():
            value = self._load_locked()
            value["invocation_count"] += 1
            self._save_locked(value)
            return dict(value)

    def load(self) -> dict[str, int]:
        # Presentation state is optional.  Read-only controllers must not
        # acquire a lock, create a lock file, or initialize state.
        return dict(self._load_locked())


def status(value: dict[str, int]) -> dict[str, Any]:
    return {
        **value,
        "automatic_orientation_active": (
            value["invocation_count"] < value["orientation_limit"]
        ),
    }
