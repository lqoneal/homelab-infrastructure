"""Forensic, read-only comparison of an external WOP tree."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        stat = path.stat()
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256(path),
                "size": stat.st_size,
                "mode": oct(stat.st_mode & 0o777),
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    return records


def active_users(root: Path) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    proc = Path("/proc")
    for process in proc.iterdir():
        if not process.name.isdigit():
            continue
        hits: set[str] = set()
        for locator in (process / "cwd", process / "exe"):
            try:
                target = locator.resolve()
                if target == root or root in target.parents:
                    hits.add(f"{locator.name}:{target}")
            except (OSError, PermissionError):
                pass
        descriptors = process / "fd"
        try:
            for descriptor in descriptors.iterdir():
                try:
                    target = descriptor.resolve()
                    if target == root or root in target.parents:
                        hits.add(f"fd:{descriptor.name}:{target}")
                except (OSError, PermissionError):
                    pass
        except (OSError, PermissionError):
            pass
        if hits:
            try:
                command = (process / "cmdline").read_bytes().replace(b"\0", b" ").decode()
            except (OSError, UnicodeDecodeError):
                command = ""
            users.append(
                {"pid": int(process.name), "command": command, "references": sorted(hits)}
            )
    return sorted(users, key=lambda item: item["pid"])


def repository_consumers(repository: Path, external: Path) -> list[dict[str, Any]]:
    result = subprocess.run(
        [
            "rg", "-n", "-F", str(external), "scripts", "engineering",
            "--glob", "!engineering/evidence/**",
            "--glob", "!engineering/planning/**",
            "--glob",
            "!engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/**",
        ],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    records = []
    for line in result.stdout.splitlines():
        path, number, text = line.split(":", 2)
        classification = "test" if "test" in Path(path).parts or path.startswith(
            "scripts/tests/"
        ) else "production"
        records.append(
            {
                "path": path,
                "line": int(number),
                "classification": classification,
                "reference": text.strip(),
            }
        )
    return records


def service_consumers(external: Path) -> list[dict[str, str]]:
    records = []
    for base in (Path("/etc/systemd"), Path("/etc/cron.d")):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            try:
                for number, line in enumerate(
                    path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                ):
                    if str(external) in line:
                        records.append(
                            {"path": str(path), "line": str(number), "reference": line}
                        )
            except OSError:
                pass
    crontab = Path("/etc/crontab")
    if crontab.is_file():
        for number, line in enumerate(
            crontab.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if str(external) in line:
                records.append(
                    {"path": str(crontab), "line": str(number), "reference": line}
                )
    return records


def inventory(external: Path, canonical: Path, repository: Path) -> dict[str, Any]:
    outside = manifest(external)
    inside = manifest(canonical)
    canonical_by_digest: dict[str, list[str]] = {}
    canonical_by_name: dict[str, list[dict[str, str]]] = {}
    for item in inside:
        canonical_by_digest.setdefault(item["sha256"], []).append(item["path"])
        canonical_by_name.setdefault(Path(item["path"]).name, []).append(item)
    comparisons = []
    for item in outside:
        exact = canonical_by_digest.get(item["sha256"], [])
        same_name = canonical_by_name.get(Path(item["path"]).name, [])
        if exact:
            classification = "DUPLICATE_CONTENT"
        elif same_name:
            classification = "DIVERGENT_SAME_NAME"
        else:
            classification = "EXTERNAL_UNIQUE_REQUIRES_SEMANTIC_REVIEW"
        comparisons.append(
            {
                **item,
                "classification": classification,
                "canonical_exact_matches": exact,
                "canonical_same_name": [
                    {"path": value["path"], "sha256": value["sha256"]}
                    for value in same_name
                ],
            }
        )
    consumers = repository_consumers(repository, external)
    services = service_consumers(external)
    active = active_users(external)
    result = {
        "schema_version": 1,
        "document_type": "ExternalWOPInventory",
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "external_root": str(external),
        "canonical_wop_root": str(canonical),
        "external_root_mode": oct(external.stat().st_mode & 0o777),
        "external_manifest": outside,
        "canonical_manifest": inside,
        "comparison": comparisons,
        "counts": {
            "external_files": len(outside),
            "canonical_files": len(inside),
            "duplicate_content": sum(
                item["classification"] == "DUPLICATE_CONTENT" for item in comparisons
            ),
            "divergent_same_name": sum(
                item["classification"] == "DIVERGENT_SAME_NAME" for item in comparisons
            ),
            "external_unique": sum(
                item["classification"] == "EXTERNAL_UNIQUE_REQUIRES_SEMANTIC_REVIEW"
                for item in comparisons
            ),
            "production_consumers": sum(
                item["classification"] == "production" for item in consumers
            ),
            "test_consumers": sum(
                item["classification"] == "test" for item in consumers
            ),
            "service_consumers": len(services),
            "active_process_users": len(active),
        },
        "repository_consumers": consumers,
        "service_consumers": services,
        "active_process_users": active,
        "freeze_ready": not active and not services and not consumers,
    }
    result["inventory_digest"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result

