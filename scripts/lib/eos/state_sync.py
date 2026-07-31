#!/usr/bin/env python3
"""Deterministic repository-to-EOS state projection."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = 1


class SynchronizationError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise SynchronizationError(f"cannot load {path}: {error}") from error
    if not isinstance(value, dict):
        raise SynchronizationError(f"{path} must contain a mapping")
    return value


def frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SynchronizationError(f"{path} has no YAML front matter")
    try:
        _, header, _ = text.split("---", 2)
        value = yaml.safe_load(header)
    except (ValueError, yaml.YAMLError) as error:
        raise SynchronizationError(f"invalid front matter in {path}: {error}") from error
    if not isinstance(value, dict):
        raise SynchronizationError(f"{path} front matter must be a mapping")
    return value


def operational_alpha_lifecycle(path: Path) -> dict[str, str]:
    """Read the current controlled OA lifecycle for a derived EOS projection."""
    values = dict(re.findall(
        r"^([A-Z0-9_-]+)=([^\n]+)$", path.read_text(encoding="utf-8"), re.MULTILINE
    ))
    required = (
        "CURRENT_IMPLEMENTATION_WOP", "CURRENT_GATE", "CURRENT_GATE_STATE",
        "CURRENT_EXECUTION_STATE", "SUCCESSOR_ELIGIBILITY", "HISTORICAL_PROGRESSIVE_RUNTIME",
    )
    missing = [field for field in required if not values.get(field)]
    if missing:
        raise SynchronizationError(
            "Operational Alpha lifecycle projection is incomplete: " + ", ".join(missing)
        )
    return {field: values[field] for field in required}


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise SynchronizationError(
            f"git {' '.join(args)} failed: {error.stderr.strip()}"
        ) from error


def render(root: Path, eos_workspace: Path, project: str) -> dict[Path, bytes]:
    matrix_path = root / "engineering/eos/repository-eos-authority.yaml"
    project_path = root / "docs/project/PROJ-0001-PROJECT_STATE.md"
    registry_path = root / "engineering/registry/work-registry.yaml"
    interface_path = root / "engineering/execution/execution-interface.yaml"
    emm_path = root / "engineering/metadata/operational-alpha-emm.yaml"
    progress_path = root / "engineering/operations/zeus-operational-alpha-progress.md"
    sources = [matrix_path, project_path, registry_path, interface_path]
    if progress_path.is_file():
        sources.append(progress_path)
    if emm_path.is_file():
        sources.append(emm_path)
    for source in sources:
        if not source.is_file():
            raise SynchronizationError(f"canonical source missing: {source}")

    matrix = load_yaml(matrix_path)
    if matrix.get("schema_version") != SCHEMA_VERSION:
        raise SynchronizationError("unsupported authority-matrix schema version")
    if matrix.get("canonical_platform_state") != "repository":
        raise SynchronizationError("repository must be canonical platform state")

    metadata = frontmatter(project_path)
    if metadata.get("document_id") != "PROJ-0001" or metadata.get("status") != "Active":
        raise SynchronizationError("PROJ-0001 must be the Active project-state source")

    registry = load_yaml(registry_path)
    interface = load_yaml(interface_path)
    emm = load_yaml(emm_path) if emm_path.is_file() else None
    oa_lifecycle = operational_alpha_lifecycle(progress_path) if progress_path.is_file() else None
    if interface.get("schema_version") == 3 and (
        not isinstance(emm, dict) or emm.get("schema_version") != 1 or not emm.get("emm_id")
    ):
        raise SynchronizationError("valid Operational Alpha EMM is required")
    head = git(root, "rev-parse", "HEAD")
    branch = git(root, "branch", "--show-current")
    remote = git(root, "remote", "get-url", "origin") if git(root, "remote") else ""
    source_digests = {
        str(path.relative_to(root)): digest(path.read_bytes()) for path in sources
    }

    state_dir = eos_workspace / "eos/state"
    identity = (
        "---\n"
        "document_id: EOS-ID\n"
        "schema_version: 1\n"
        "status: Derived\n"
        "authority: repository\n"
        f"project: {project}\n"
        f"repository_root: {root}\n"
        f"repository_remote: {remote}\n"
        "---\n\n"
        "# EOS Repository Identity Projection\n\n"
        "This file is generated from repository identity. It is not an independent\n"
        "engineering authority.\n"
    ).encode()

    state_header = (
        "---\n"
        "document_id: EOS-STATE\n"
        "schema_version: 1\n"
        "status: Active\n"
        "authority: repository\n"
        f"project: {project}\n"
        f"project_state: PROJ-0001@{metadata.get('version')}\n"
        f"phase: {metadata.get('phase')}\n"
        f"repository_branch: {branch}\n"
        f"repository_commit: {head}\n"
        f"project_state_sha256: {source_digests[str(project_path.relative_to(root))]}\n"
        f"registry_revision: {registry.get('revision')}\n"
        f"execution_interface_schema: {interface.get('schema_version')}\n"
    ) + (f"operational_alpha_wop: {oa_lifecycle['CURRENT_IMPLEMENTATION_WOP']}\n"
         f"operational_alpha_lifecycle: {oa_lifecycle['CURRENT_GATE_STATE']}\n"
         f"operational_alpha_execution_state: {oa_lifecycle['CURRENT_EXECUTION_STATE']}\n"
         f"operational_alpha_successor_eligibility: {oa_lifecycle['SUCCESSOR_ELIGIBILITY']}\n"
         f"historical_progressive_runtime: {oa_lifecycle['HISTORICAL_PROGRESSIVE_RUNTIME']}\n"
         if oa_lifecycle else "") + (f"emm_id: {emm.get('emm_id')}\n"
         f"emm_version: {emm.get('version')}\n" if emm else "") + (
        "---\n\n"
        "# EOS Engineering State Projection\n\n"
        "This deterministic runtime projection is generated from authoritative\n"
        "repository records. Modify the repository sources, never this file.\n"
    )
    state = state_header.encode()

    projection_digests = {
        "EOS-ID.md": digest(identity),
        "EOS-STATE.md": digest(state),
    }
    source_lines = "\n".join(
        f"- path: {path}\n  sha256: {value}"
        for path, value in sorted(source_digests.items())
    )
    projection_lines = "\n".join(
        f"- path: {path}\n  sha256: {value}"
        for path, value in sorted(projection_digests.items())
    )
    manifest = (
        "---\n"
        "document_id: EOS-MANIFEST\n"
        "schema_version: 1\n"
        "status: Derived\n"
        "authority: repository\n"
        f"project: {project}\n"
        "---\n\n"
        "# EOS Projection Manifest\n\n"
        "## Canonical sources\n\n"
        f"{source_lines}\n\n"
        "## Derived projections\n\n"
        f"{projection_lines}\n"
    ).encode()
    return {
        state_dir / "EOS-ID.md": identity,
        state_dir / "EOS-STATE.md": state,
        state_dir / "EOS-MANIFEST.md": manifest,
    }


def atomic_write(path: Path, data: bytes) -> bool:
    if path.is_file() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def validate(expected: dict[Path, bytes]) -> list[str]:
    return [
        str(path)
        for path, data in expected.items()
        if not path.is_file() or path.read_bytes() != data
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("render", "synchronize", "validate"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", default="homelab")
    args = parser.parse_args()
    try:
        expected = render(args.root.resolve(), args.workspace.resolve(), args.project)
        if args.action == "validate":
            drift = validate(expected)
            if drift:
                for path in drift:
                    print(f"DRIFT: {path}")
                return 1
            print("Repository–EOS synchronization validation passed.")
            return 0
        if args.action == "render":
            for path, data in expected.items():
                print(f"=== {path}")
                print(data.decode(), end="")
            return 0
        changed = [str(path) for path, data in expected.items() if atomic_write(path, data)]
        print(f"Repository–EOS synchronization complete: changed={len(changed)}")
        for path in changed:
            print(f"UPDATED: {path}")
        return 0
    except SynchronizationError as error:
        print(f"FAIL: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
