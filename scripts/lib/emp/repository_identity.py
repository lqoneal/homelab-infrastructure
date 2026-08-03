"""Canonical repository identity resolution for all Zeus WOP surfaces.

The WOP-facing ``repository_identity`` value may be a canonical repository
path, normalized remote locator, stable runtime repository id, fingerprint, or
an explicitly derivable short-name alias.  The resolver always returns the
canonical repository path for internal lifecycle comparisons.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping


class RepositoryIdentityError(ValueError):
    def __init__(self, message: str, *, declared: Any = None, identity: Mapping[str, Any] | None = None):
        self.declared = declared
        self.identity = dict(identity or {})
        super().__init__(message)


def normalize_remote(value: str) -> str:
    """Normalize equivalent SSH/HTTPS GitHub locators without guessing."""
    text = str(value).strip()
    text = re.sub(r"^git\+ssh://git@", "git@", text)
    text = re.sub(r"^ssh://git@", "git@", text)
    text = text.rstrip("/")
    if text.endswith(".git"):
        text = text[:-4]
    if text.startswith("https://github.com/"):
        text = "git@github.com:" + text[len("https://github.com/"):]
    if text.startswith("http://github.com/"):
        text = "git@github.com:" + text[len("http://github.com/"):]
    return text


def resolve(repository_root: Path | str) -> dict[str, str]:
    root = Path(repository_root).resolve()
    remote = subprocess.run(
        ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    canonical_remote = normalize_remote(remote) if remote else ""
    # Runtime identity v2 historically fingerprints the configured remote
    # verbatim. Preserve that value so adoption and existing evidence remain
    # stable while comparisons use the normalized locator below.
    fingerprint = hashlib.sha256(f"{root}\n{remote or root}".encode()).hexdigest()
    return {
        "repository_path": str(root),
        "repository_identity": remote or str(root),
        "repository_remote_identity": canonical_remote,
        "repository_id": f"{root.name}-{fingerprint[:16]}",
        "repository_fingerprint": fingerprint,
        "repository_short_name": root.name,
        "repository_identity_source": "published runtime identity / repository remote",
        "repository_identity_version": "1",
        # Existing lifecycle stores compare this value directly.
        "canonical_repository_identity": str(root),
    }


def resolve_declared(declared: Any, repository_root: Path | str) -> dict[str, str]:
    identity = resolve(repository_root)
    if declared in (None, ""):
        raise RepositoryIdentityError("repository_identity is required", declared=declared, identity=identity)
    value = str(declared).strip().strip("`")
    normalized = normalize_remote(value)
    candidates = {
        identity["repository_path"], identity["repository_remote_identity"],
        identity["repository_id"], identity["repository_fingerprint"],
        identity["repository_short_name"],
    }
    # Only a path that resolves exactly to the canonical root is accepted.
    try:
        if Path(value).is_absolute() and str(Path(value).resolve()) == identity["repository_path"]:
            return identity
    except OSError:
        pass
    if normalized in {identity["repository_remote_identity"], normalize_remote(identity["repository_remote_identity"])} or value in candidates:
        return identity
    raise RepositoryIdentityError(
        "repository identity mismatch: declared value is not the canonical repository, authorized alias, id, or fingerprint",
        declared=value, identity=identity,
    )


def canonicalize_metadata(metadata: Mapping[str, Any], repository_root: Path | str) -> tuple[dict[str, Any], dict[str, str]]:
    result = dict(metadata)
    identity = resolve_declared(result.get("repository_identity"), repository_root)
    result["repository_identity"] = identity["canonical_repository_identity"]
    return result, identity
