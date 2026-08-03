"""Canonical, repository-bound Zeus runtime discovery and paths."""

from __future__ import annotations

import os
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


class RuntimeDiscoveryError(RuntimeError):
    """No safe mutable runtime could be selected."""

    def __init__(self, message: str, diagnostics: list[dict[str, str]] | None = None):
        self.diagnostics = diagnostics or []
        super().__init__(message)


def _identity(repository: Path) -> dict[str, str]:
    canonical = str(repository.resolve())
    remote = subprocess.run(
        ["git", "-C", canonical, "config", "--get", "remote.origin.url"],
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    repository_identity = remote or canonical
    fingerprint = hashlib.sha256(f"{canonical}\n{repository_identity}".encode()).hexdigest()
    return {
        "repository": canonical,
        "repository_identity": repository_identity,
        "repository_fingerprint": fingerprint,
        "repository_id": f"{Path(canonical).name}-{fingerprint[:16]}",
        "runtime_schema": "zeus-runtime/2",
    }


def runtime_identity(repository_root: Path | str) -> dict[str, str]:
    return _identity(Path(repository_root).resolve())


def _config(repository: Path) -> tuple[str | None, str | None]:
    for candidate in (repository / ".zeus" / "config.yaml", repository / ".zeus" / "config.yml"):
        if not candidate.is_file():
            continue
        try:
            import yaml
            value = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError, ImportError) as error:
            raise RuntimeDiscoveryError(f"invalid Zeus runtime configuration: {error}") from error
        runtime = value.get("runtime") if isinstance(value, dict) else None
        if not isinstance(runtime, dict):
            raise RuntimeDiscoveryError("invalid Zeus runtime configuration: runtime must be a mapping")
        root = runtime.get("root")
        system = runtime.get("system_root")
        if root is not None and not isinstance(root, str):
            raise RuntimeDiscoveryError("invalid Zeus runtime configuration: runtime.root must be a path")
        if system is not None and not isinstance(system, str):
            raise RuntimeDiscoveryError("invalid Zeus runtime configuration: runtime.system_root must be a path")
        return root, system
    return None, None


def _candidate_path(value: str, repository: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    return (path if path.is_absolute() else repository / path).resolve()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _check_candidate(path: Path, identity: dict[str, str], *, create: bool) -> str | None:
    repository = Path(identity["repository"])
    if _inside(path, repository):
        return "runtime path is inside the repository/protected baseline"
    if path.exists() and not path.is_dir():
        return "runtime path is not a directory"
    parent = path if path.exists() else path.parent
    if not parent.exists():
        if not create:
            # Read-only projections may resolve a not-yet-created safe default;
            # only a mutating command must prove creation and writability.
            return None
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            return f"parent path cannot be created: {error}"
    if not os.access(parent, os.W_OK | os.X_OK):
        return "runtime path is not writable"
    marker = path / "runtime-identity.json"
    if marker.exists():
        try:
            stored = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return f"runtime identity is unreadable: {error}"
        if stored.get("repository_fingerprint") != identity["repository_fingerprint"]:
            return "runtime identity belongs to another repository"
    elif path.exists() and any(path.iterdir()):
        return "existing runtime has no repository binding"
    return None


def resolve_runtime(repository_root: Path | str, *, explicit: Path | str | None = None,
                    require_writable: bool = False) -> dict[str, Any]:
    repository = Path(repository_root).resolve()
    identity = _identity(repository)
    configured, system = _config(repository)
    sources: list[tuple[str, str | None]] = [
        ("command-line", str(explicit) if explicit is not None else None),
        ("environment", os.environ.get("ZEUS_RUNTIME_ROOT")),
        ("repository-config", configured),
        ("user-state-default", str(Path.home() / ".local" / "state" / "zeus-runtime" / identity["repository_id"])),
        ("system-config", system or os.environ.get("ZEUS_SYSTEM_RUNTIME_ROOT")),
    ]
    diagnostics: list[dict[str, str]] = []
    for source, raw in sources:
        if not raw:
            continue
        candidate = _candidate_path(raw, repository)
        reason = _check_candidate(candidate, identity, create=require_writable)
        if reason:
            diagnostics.append({"source": source, "candidate": str(candidate), "reason": reason})
            if source in {"command-line", "environment"}:
                raise RuntimeDiscoveryError(
                    f"NO_WRITABLE_RUNTIME_ROOT: {source} override rejected ({reason})",
                    diagnostics,
                )
            continue
        return {"root": candidate, "source": source, "identity": identity, "diagnostics": diagnostics}
    detail = "; ".join(f"{item['source']}={item['reason']}" for item in diagnostics)
    raise RuntimeDiscoveryError(
        "NO_WRITABLE_RUNTIME_ROOT" + (f" ({detail})" if detail else ""), diagnostics
    )


def initialize_runtime(repository_root: Path | str, *, explicit: Path | str | None = None) -> dict[str, Any]:
    resolved = resolve_runtime(repository_root, explicit=explicit, require_writable=True)
    root = resolved["root"]
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "runtime-identity.json"
    payload = {**resolved["identity"], "runtime_root": str(root)}
    if marker.exists():
        existing = json.loads(marker.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeDiscoveryError("runtime identity conflict")
    else:
        marker.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for directory in ("stage1", "mission-admissions", "mission-executions", "native-sessions", "eens", "evidence"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    resolved["initialized"] = True
    return resolved


def runtime_root(repository_root: Path | str) -> Path:
    """Return the deterministic selected root without creating runtime state."""
    try:
        return resolve_runtime(repository_root)["root"]
    except RuntimeDiscoveryError as error:
        # Legacy direct runtime consumers may inspect a pre-existing unbound
        # user-state directory. Do not adopt it for CLI mutation (which calls
        # initialize_runtime and fails closed); retain a stable read path for
        # existing admission/execution stores and compatibility tests.
        if not os.environ.get("ZEUS_RUNTIME_ROOT") and error.diagnostics and all(
            item["source"] == "user-state-default" for item in error.diagnostics
        ):
            identity = _identity(Path(repository_root).resolve())
            return Path.home() / ".local" / "state" / "zeus-runtime" / identity["repository_id"]
        raise


def runtime_path(repository_root: Path | str, *parts: str) -> Path:
    return runtime_root(repository_root).joinpath(*parts)


def runtime_write_available(repository_root: Path | str) -> bool:
    """Check the mutation boundary without creating files or directories."""
    try:
        resolve_runtime(repository_root, require_writable=False)
        return True
    except RuntimeDiscoveryError:
        return False
