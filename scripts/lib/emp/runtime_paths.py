"""Explicit separation between repository evidence and mutable runtime state."""

from __future__ import annotations

import os
from pathlib import Path


def runtime_root(repository_root: Path | str) -> Path:
    """Return the configured mutable runtime root without silently relocating it."""
    root = Path(repository_root).resolve()
    configured = os.environ.get("ZEUS_RUNTIME_ROOT")
    return Path(configured).expanduser().resolve() if configured else root / ".zeus" / "runtime"


def runtime_path(repository_root: Path | str, *parts: str) -> Path:
    return runtime_root(repository_root).joinpath(*parts)


def runtime_write_available(repository_root: Path | str) -> bool:
    """Check the mutation boundary without creating files or directories."""
    path = runtime_root(repository_root)
    if path.exists():
        return path.is_dir() and os.access(path, os.W_OK)
    return path.parent.exists() and os.access(path.parent, os.W_OK)
