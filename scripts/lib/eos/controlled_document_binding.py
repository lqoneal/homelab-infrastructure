"""Fail-closed exact controlled-document binding resolution."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml


class ControlledDocumentBindingError(ValueError):
    """An exact controlled-document binding cannot be proven current."""


PROC_0001_PATH = "docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md"


def _metadata(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        raise ControlledDocumentBindingError("controlled document has invalid front matter")
    _, header, _ = text.split("---", 2)
    value = yaml.safe_load(header)
    if not isinstance(value, dict):
        raise ControlledDocumentBindingError("controlled document metadata is invalid")
    return value


def resolve_exact(root: Path | str, document_id: str, revision: str) -> dict[str, Any]:
    root = Path(root).resolve()
    if document_id != "PROC-0001":
        raise ControlledDocumentBindingError(f"unsupported controlled document: {document_id}")
    relative = PROC_0001_PATH
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ControlledDocumentBindingError("PROC-0001 canonical source unavailable")
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", relative],
        text=True, capture_output=True, check=False,
    )
    if tracked.returncode != 0:
        raise ControlledDocumentBindingError("PROC-0001 source is not tracked")
    metadata = _metadata(path)
    expected = str(revision)
    if (
        metadata.get("document_id") != document_id
        or str(metadata.get("version")) != expected
        or metadata.get("status") != "Active"
        or metadata.get("approval_status") != "Approved"
        or metadata.get("persistence_status") != "Persisted"
    ):
        raise ControlledDocumentBindingError("PROC-0001 exact revision is not active and approved")
    index = (root / "docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md").read_text(encoding="utf-8")
    registration = f"| PROC-0001 |"
    if registration not in index or relative not in index:
        raise ControlledDocumentBindingError("PROC-0001 is not registered at its canonical path")
    return {
        "document_id": document_id,
        "revision": expected,
        "path": relative,
        "status": metadata["status"],
        "approval_status": metadata["approval_status"],
        "persistence_status": metadata["persistence_status"],
        "approval_source": metadata.get("approval_reference"),
        "publication_source": "DOC-0001 plus tracked canonical source and Git history",
        "registry_entry": registration + index.split(registration, 1)[1].splitlines()[0],
    }
