"""Transactional adoption of the pre-repository-binding Zeus runtime."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.emp.runtime_paths import runtime_identity


class RuntimeAdoptionError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: list[dict[str, str]] | None = None):
        self.diagnostics = diagnostics or []
        super().__init__(message)


def _digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _inventory(root: Path) -> dict[str, Any]:
    return {"files": sum(1 for p in root.rglob("*") if p.is_file()), "digest": _digest_tree(root)}


def _baselines(repository: Path) -> dict[str, str]:
    values = {}
    for tag in ("OA-v1.0.0", "OB-PLAN-v1.0.0"):
        import subprocess
        result = subprocess.run(["git", "-C", str(repository), "rev-parse", f"refs/tags/{tag}"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeAdoptionError(f"protected baseline tag unavailable: {tag}")
        values[tag] = result.stdout.strip()
    return values


def _verify(source: Path, repository: Path, destination: Path) -> dict[str, Any]:
    if not source.is_dir():
        raise RuntimeAdoptionError("legacy runtime source is not a directory")
    if source.resolve() == repository.resolve() or repository.resolve() in source.resolve().parents:
        raise RuntimeAdoptionError("runtime source is inside the repository")
    if not os.access(source, os.R_OK | os.X_OK) or not os.access(source.parent, os.W_OK | os.X_OK):
        raise RuntimeAdoptionError("legacy runtime is not safely readable/writable")
    evidence = source / "evidence" / "bootstrap-evidence.json"
    if not evidence.is_file():
        raise RuntimeAdoptionError("LEGACY_RUNTIME_REQUIRES_ADOPTION: bootstrap evidence is missing")
    try:
        bootstrap = json.loads(evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeAdoptionError(f"bootstrap evidence is invalid: {error}") from error
    if bootstrap.get("repository_root") != str(repository.resolve()):
        raise RuntimeAdoptionError("legacy runtime repository root does not match this repository")
    if bootstrap.get("schema_version") != 1:
        raise RuntimeAdoptionError("legacy runtime schema is incompatible")
    required_state = (source / "orchestration-state.json", source / "stage1", source / "stage1" / "eens")
    if any(not path.exists() for path in required_state):
        raise RuntimeAdoptionError("legacy runtime history or EENS evidence is incomplete")
    identity = runtime_identity(repository)
    destination_existing = destination.exists()
    if destination_existing and not destination.is_dir():
        raise RuntimeAdoptionError("canonical runtime destination is not a directory")
    marker = destination / "runtime-identity.json"
    if marker.is_file():
        try:
            value = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeAdoptionError(f"canonical runtime identity is invalid: {error}") from error
        if value.get("repository_fingerprint") != identity["repository_fingerprint"]:
            raise RuntimeAdoptionError("canonical runtime belongs to another repository")
    baselines = _baselines(repository)
    declared_baselines = bootstrap.get("protected_baselines")
    if isinstance(declared_baselines, dict):
        for tag, expected in baselines.items():
            if declared_baselines.get(tag) not in (None, expected):
                raise RuntimeAdoptionError(f"protected baseline mismatch: {tag}")
    source_inventory = _inventory(source)
    adoption_id = hashlib.sha256((str(source.resolve()) + source_inventory["digest"] + identity["repository_fingerprint"]).encode()).hexdigest()[:24]
    return {"identity": identity, "baselines": baselines, "source_inventory": source_inventory,
            "destination_inventory": _inventory(destination) if destination_existing else None,
            "adoption_id": adoption_id, "source": str(source.resolve()), "destination": str(destination.resolve()),
            "bootstrap": bootstrap}


def adopt(repository: Path | str, *, source: Path | str | None = None, dry_run: bool = False) -> dict[str, Any]:
    repository = Path(repository).resolve()
    identity = runtime_identity(repository)
    destination = Path.home() / ".local" / "state" / "zeus-runtime" / identity["repository_id"]
    source_path = Path(source).expanduser().resolve() if source else Path.home() / ".local" / "state" / "zeus-runtime" / repository.name
    report = _verify(source_path, repository, destination)
    lock_parent = source_path.parent
    lock_parent.mkdir(parents=True, exist_ok=True)
    temporary_lock = tempfile.NamedTemporaryFile(prefix="zeus-runtime-adopt-lock-", delete=False)
    lock_path = Path(temporary_lock.name) if dry_run else lock_parent / ".zeus-runtime-adoption.lock"
    temporary_lock.close()
    if not dry_run:
        lock_path.unlink(missing_ok=True)
    try:
        lock = lock_path.open("a+")
    except OSError as error:
        raise RuntimeAdoptionError(f"cannot create runtime adoption lock: {error}") from error
    try:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeAdoptionError("another runtime adoption is active") from error
        binding = {"schema_version": 1, "repository_root": str(repository), "repository_identity": "homelab", "repository_fingerprint": identity["repository_fingerprint"], "runtime_identity": identity["repository_id"], "runtime_root": str(destination), "protected_baselines": report["baselines"], "adopted_from": str(source_path), "adoption_id": report["adoption_id"]}
        report["binding"] = binding
        report["action"] = "ALREADY_ADOPTED" if (destination / "runtime-binding.yaml").is_file() else "MIGRATED"
        if dry_run:
            report["result"] = "PASS"; report["dry_run"] = True; return report
        if (destination / "runtime-binding.yaml").is_file():
            existing = yaml.safe_load((destination / "runtime-binding.yaml").read_text(encoding="utf-8")) or {}
            if existing.get("adoption_id") != binding["adoption_id"]:
                raise RuntimeAdoptionError("canonical runtime has a different adoption identity")
            report["result"] = "PASS"; report["dry_run"] = False; return report
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".zeus-runtime-adopt-", dir=str(destination.parent)))
        backup = destination.parent / f".zeus-runtime-backup-{report['adoption_id']}"
        try:
            shutil.copytree(source_path, staging / destination.name)
            staged = staging / destination.name
            if destination.exists():
                for item in destination.iterdir():
                    target = staged / item.name
                    if item.name in {"operator-interface-state.json", "operator-interface-state.json.lock"}:
                        continue
                    if target.exists() and item.is_file() and target.read_bytes() != item.read_bytes():
                        raise RuntimeAdoptionError(f"canonical runtime conflict: {item.name}")
                    if not target.exists():
                        shutil.copy2(item, target) if item.is_file() else shutil.copytree(item, target)
            marker_payload = {**identity, "runtime_root": str(destination)}
            (staged / "runtime-identity.json").write_text(json.dumps(marker_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (staged / "runtime-binding.yaml").write_text(yaml.safe_dump(binding, sort_keys=False), encoding="utf-8")
            checkpoint = {"adoption_id": report["adoption_id"], "source": report["source"], "destination": report["destination"], "source_inventory": report["source_inventory"], "created_at": datetime.now(timezone.utc).isoformat()}
            (staged / "adoption-checkpoint.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if destination.exists(): os.replace(destination, backup)
            os.replace(staged, destination)
            shutil.rmtree(backup, ignore_errors=True); staging.rmdir()
        except Exception:
            if not destination.exists() and backup.exists(): os.replace(backup, destination)
            shutil.rmtree(staging, ignore_errors=True); raise
        report["result"] = "PASS"; report["dry_run"] = False; return report
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN); lock.close()
        if dry_run: lock_path.unlink(missing_ok=True)
