"""Deterministic cross-authority publication-closure preflight.

This module is deliberately read-only.  Reverse dependencies are derived from
tracked source and the existing Model-B authority metadata; no dependency
registry or receipt is created by a preflight.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

LIVE_PROC_RE = re.compile(r"\bPROC-0001@(?P<revision>[0-9]+(?:\.[0-9]+)*)\b")
PROC_PATH = "docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md"
EMM_PATH = "engineering/metadata/operation-beta-emm.yaml"
INTERFACE_PATH = "engineering/execution/execution-interface.yaml"
ROADMAP_PATH = "engineering/docs/architecture/OPERATION-BETA-ROADMAP.md"
WOP_PATH = "engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md"


class PublicationClosureError(ValueError):
    """A publication closure cannot be proven."""


def _tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise PublicationClosureError("canonical tracked-file inventory unavailable")
    # Untracked files are intentionally excluded from authority discovery.
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=False,
    )
    if tracked.returncode:
        raise PublicationClosureError("canonical tracked-file inventory unavailable")
    return sorted(path for path in tracked.stdout.splitlines() if path)


def _classification(path: str) -> str:
    if path.startswith("scripts/tests/"):
        return "TEST_FIXTURE"
    if path.startswith("engineering/evidence/") or "/archive/" in path or path.startswith("engineering/work-orders/"):
        return "HISTORICAL_DEPENDENT"
    if path.startswith("scripts/lib/") or path == INTERFACE_PATH:
        return "LIVE_DEPENDENT"
    return "NONAUTHORITATIVE_REFERENCE"


def _dependent(path: str, binding: str, classification: str, disposition: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "dependent": path,
        "binding": binding,
        "classification": classification,
    }
    if disposition:
        value["disposition"] = disposition
    return value


def _controlled_document_dependents(root: Path, source: str, revision: str) -> list[dict[str, Any]]:
    if source != "PROC-0001":
        raise PublicationClosureError("unsupported controlled-document source")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", str(revision)):
        raise PublicationClosureError("controlled-document revision is missing or ambiguous")
    if not (root / PROC_PATH).is_file():
        raise PublicationClosureError("canonical controlled-document source unavailable")
    values: list[dict[str, Any]] = []
    for path in _tracked_files(root):
        if _classification(path) != "LIVE_DEPENDENT":
            continue
        try:
            text = (root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise PublicationClosureError(f"canonical dependency source unavailable: {path}")
        for match in LIVE_PROC_RE.finditer(text):
            values.append(_dependent(path, f"PROC-0001@{match.group('revision')}", "LIVE_DEPENDENT"))
        if path == INTERFACE_PATH:
            try:
                document = yaml.safe_load(text) or {}
                binding = document.get("semantic_bindings", {}).get("execution_lifecycle", {})
                if binding.get("owner") == "PROC-0001":
                    values.append(_dependent(path, f"PROC-0001@{binding.get('revision')}", "LIVE_DEPENDENT"))
            except yaml.YAMLError as error:
                raise PublicationClosureError(f"ambiguous execution-interface dependency: {error}") from error
    unique = {(item["dependent"], item["binding"]): item for item in values}
    return list(unique.values())


def _model_b_dependents(root: Path, source_class: str, source: str) -> list[dict[str, Any]]:
    try:
        emm = yaml.safe_load((root / EMM_PATH).read_text(encoding="utf-8")) or {}
        interface = yaml.safe_load((root / INTERFACE_PATH).read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise PublicationClosureError(f"Model-B dependency source unavailable: {error}") from error
    if not isinstance(emm, Mapping) or not isinstance(interface, Mapping):
        raise PublicationClosureError("Model-B dependency source is ambiguous")
    current_emm = str(emm.get("emm_id", ""))
    current_wop = str(emm.get("current_wop", ""))
    current_roadmap = str(emm.get("current_roadmap", ""))
    if not current_emm or not current_wop or not current_roadmap:
        raise PublicationClosureError("Model-B dependency source is incomplete")
    if not (root / WOP_PATH).is_file() or not (root / ROADMAP_PATH).is_file():
        raise PublicationClosureError("Model-B dependency source is missing")
    semantic = interface.get("semantic_bindings", {})
    lifecycle = semantic.get("execution_lifecycle", {}) if isinstance(semantic, Mapping) else {}
    metadata_owner = interface.get("metadata_model", {}).get("owner") if isinstance(interface.get("metadata_model"), Mapping) else None
    if metadata_owner != current_emm or lifecycle.get("owner") != "PROC-0001":
        raise PublicationClosureError("Model-B execution-interface binding is incompatible")
    values: list[dict[str, Any]] = []
    if source_class == "EMM":
        if source != current_emm:
            raise PublicationClosureError("unknown EMM source")
        values.extend([
            _dependent(EMM_PATH, current_emm, "LIVE_DEPENDENT"),
            _dependent(WOP_PATH, current_emm, "LIVE_DEPENDENT"),
            _dependent(ROADMAP_PATH, current_emm, "LIVE_DEPENDENT"),
            _dependent(INTERFACE_PATH, current_emm, "LIVE_DEPENDENT"),
        ])
    elif source_class == "IMMUTABLE_WOP":
        if source != current_wop:
            raise PublicationClosureError("unknown current WOP source")
        values.extend([
            _dependent(EMM_PATH, current_wop, "LIVE_DEPENDENT"),
            _dependent(ROADMAP_PATH, current_wop, "LIVE_DEPENDENT"),
            _dependent(INTERFACE_PATH, current_wop, "LIVE_DEPENDENT"),
        ])
    elif source_class == "EXECUTABLE_ROADMAP":
        if source not in {current_roadmap, "OPERATION-BETA-ROADMAP"}:
            raise PublicationClosureError("unknown current roadmap source")
        values.append(_dependent(INTERFACE_PATH, current_roadmap, "LIVE_DEPENDENT"))
    else:
        raise PublicationClosureError(f"unsupported Model-B source class: {source_class}")
    return values


def discover_reverse_dependencies(
    root: Path | str,
    *,
    source_class: str,
    source: str,
    revision_or_digest: str,
) -> list[dict[str, Any]]:
    """Return deterministic reverse dependents, including historical entries."""
    root = Path(root).resolve()
    if source_class == "CONTROLLED_DOCUMENT":
        values = _controlled_document_dependents(root, source, revision_or_digest)
        # Historical exact references are visible to callers but never live.
        for path in _tracked_files(root):
            if _classification(path) != "HISTORICAL_DEPENDENT":
                continue
            try:
                text = (root / path).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if LIVE_PROC_RE.search(text):
                values.append(_dependent(path, LIVE_PROC_RE.search(text).group(0), "HISTORICAL_DEPENDENT"))
        return sorted(values, key=lambda item: (item["classification"], item["dependent"], item["binding"]))
    return sorted(_model_b_dependents(root, source_class, source), key=lambda item: item["dependent"])


def publication_preflight(
    root: Path | str,
    *,
    source: str,
    source_class: str,
    revision_or_digest: str,
    disposition_overrides: Mapping[str, Mapping[str, Any] | str] | None = None,
) -> dict[str, Any]:
    """Evaluate publication closure without changing repository or runtime state."""
    root = Path(root).resolve()
    blockers: list[str] = []
    try:
        dependents = discover_reverse_dependencies(
            root, source_class=source_class, source=source, revision_or_digest=revision_or_digest
        )
    except PublicationClosureError as error:
        return {
            "source": source, "source_class": source_class,
            "source_revision_or_digest": revision_or_digest,
            "live_reverse_dependents": [], "dependent_dispositions": {},
            "unresolved_dependents": ["<dependency-graph>"],
            "publication_closure": "FAIL", "publication_allowed": "NO",
            "blockers": [str(error)],
        }
    dispositions: dict[str, str] = {}
    unresolved: list[str] = []
    overrides = disposition_overrides or {}
    for item in dependents:
        path = item["dependent"]
        classification = item["classification"]
        if classification != "LIVE_DEPENDENT":
            continue
        override = overrides.get(path)
        if isinstance(override, Mapping):
            disposition = str(override.get("disposition", ""))
            if disposition == "COMPATIBILITY_PROVEN" and override.get("evidence") is not True:
                unresolved.append(path)
                blockers.append(f"compatibility evidence missing: {path}")
                continue
        else:
            disposition = str(override or "")
        if not disposition:
            if source_class == "CONTROLLED_DOCUMENT":
                actual = item["binding"].split("@", 1)[1]
                disposition = "RECONCILED" if actual == str(revision_or_digest) else ""
            else:
                disposition = "RECONCILED"
        if disposition not in {"RECONCILED", "EXPLICITLY_SUPERSEDED", "COMPATIBILITY_PROVEN"}:
            unresolved.append(path)
            blockers.append(f"no valid disposition: {path}")
        else:
            dispositions[path] = disposition
    result = "PASS" if not unresolved and not blockers else "FAIL"
    return {
        "source": source, "source_class": source_class,
        "source_revision_or_digest": revision_or_digest,
        "live_reverse_dependents": [item for item in dependents if item["classification"] == "LIVE_DEPENDENT"],
        "dependent_dispositions": dispositions,
        "unresolved_dependents": sorted(set(unresolved)),
        "publication_closure": result,
        "publication_allowed": "YES" if result == "PASS" else "NO",
        "blockers": sorted(set(blockers)),
    }


def preflight_current_publication(root: Path | str, candidate_paths: list[str] | tuple[str, ...]) -> dict[str, Any]:
    """Protected-boundary adapter for the current canonical controlled source."""
    root = Path(root).resolve()
    revision = "2.11"
    if PROC_PATH in candidate_paths:
        try:
            text = (root / PROC_PATH).read_text(encoding="utf-8")
            match = re.search(r"^version:\s*([^\s]+)", text, re.MULTILINE)
            revision = match.group(1) if match else ""
        except OSError:
            revision = ""
    return publication_preflight(
        root, source="PROC-0001", source_class="CONTROLLED_DOCUMENT", revision_or_digest=revision
    )
