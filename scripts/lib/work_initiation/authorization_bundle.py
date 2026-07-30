#!/usr/bin/env python3
"""Canonical Authorization Bundle resolution for Engineering Work Initiation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml


SCHEMA_VERSION = 1
DOCUMENT_TYPE = "ZeusAuthorizationBundle"
REQUIRED_LOCATORS = (
    "admission_record",
    "authority_graph",
    "wop",
    "state",
    "receipt",
)
OPTIONAL_LOCATORS = ("lease", "revocation")
OPTIONAL_VALUES = ("expected_authority",)
ALLOWED_FIELDS = {
    "schema_version",
    "document_type",
    *REQUIRED_LOCATORS,
    *OPTIONAL_LOCATORS,
    *OPTIONAL_VALUES,
}
LEGACY_ENV = {
    "admission_record": "EOS_WOP_ADMISSION_RECORD",
    "authority_graph": "EOS_SHADOW_AUTHORITY_GRAPH",
    "wop": "EOS_SHADOW_WOP",
    "state": "EOS_SHADOW_STATE",
    "receipt": "EOS_SHADOW_RECEIPT",
    "lease": "EOS_SHADOW_LEASE",
    "revocation": "EOS_SHADOW_REVOCATION",
    "expected_authority": "EOS_SHADOW_EXPECTED_AUTHORITY",
}


class AuthorizationBundleError(ValueError):
    """The authorization inputs cannot be resolved without ambiguity."""


def _mapping(path: Path, label: str) -> Mapping[str, object]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise AuthorizationBundleError(f"{label} is unavailable or corrupted: {exc}") from exc
    if not isinstance(value, dict):
        raise AuthorizationBundleError(f"{label} must be a mapping")
    return value


def _locator(value: object, field: str, base: Path) -> str:
    if not isinstance(value, str) or not value:
        raise AuthorizationBundleError(f"authorization bundle field {field!r} is invalid")
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    if not path.is_file():
        raise AuthorizationBundleError(
            f"authorization bundle locator {field!r} is unavailable: {path}"
        )
    return str(path)


def _wop_id(path: Path) -> str:
    value = _mapping(path, "authorization WOP")
    wop_id = value.get("wop_id")
    if (
        not isinstance(wop_id, str)
        or not wop_id.startswith("WOP-")
        or len(wop_id) < 5
    ):
        raise AuthorizationBundleError("authorization input WOP identity is invalid")
    return wop_id


@dataclass(frozen=True)
class ResolvedAuthorizationBundle:
    source: str
    values: Mapping[str, str]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "document_type": "ResolvedZeusAuthorizationBundle",
            "source": self.source,
            **self.values,
        }


def resolve(
    bundle_path: Path | None,
    environment: Mapping[str, str] | None = None,
) -> ResolvedAuthorizationBundle:
    """Resolve the canonical bundle or the documented legacy environment path."""
    env = os.environ if environment is None else environment
    if bundle_path is not None:
        bundle_path = bundle_path.resolve()
        value = _mapping(bundle_path, "authorization bundle")
        unknown = sorted(set(value) - ALLOWED_FIELDS)
        if unknown:
            raise AuthorizationBundleError(
                "authorization bundle has unknown fields: " + ", ".join(unknown)
            )
        if value.get("schema_version") != SCHEMA_VERSION:
            raise AuthorizationBundleError("authorization bundle schema_version must be 1")
        if value.get("document_type") != DOCUMENT_TYPE:
            raise AuthorizationBundleError(
                f"authorization bundle document_type must be {DOCUMENT_TYPE}"
            )
        missing = [
            field
            for field in REQUIRED_LOCATORS
            if not isinstance(value.get(field), str) or not value.get(field)
        ]
        if missing:
            raise AuthorizationBundleError(
                "authorization bundle is incomplete: " + ", ".join(missing)
            )
        resolved: dict[str, str] = {}
        for field in REQUIRED_LOCATORS + OPTIONAL_LOCATORS:
            if value.get(field) is not None:
                resolved[field] = _locator(value[field], field, bundle_path.parent)
        for field in OPTIONAL_VALUES:
            selected = value.get(field)
            if selected is not None:
                if not isinstance(selected, str) or not selected:
                    raise AuthorizationBundleError(
                        f"authorization bundle field {field!r} is invalid"
                    )
                resolved[field] = selected
        for field, variable in LEGACY_ENV.items():
            legacy = env.get(variable, "")
            if legacy and legacy != resolved.get(field, ""):
                raise AuthorizationBundleError(
                    f"{variable} conflicts with the canonical authorization bundle"
                )
        resolved["wop_id"] = _wop_id(Path(resolved["wop"]))
        return ResolvedAuthorizationBundle("canonical_bundle", resolved)

    legacy = {
        field: env.get(variable, "")
        for field, variable in LEGACY_ENV.items()
        if env.get(variable, "")
    }
    for field in REQUIRED_LOCATORS + OPTIONAL_LOCATORS:
        if field in legacy:
            legacy[field] = _locator(legacy[field], field, Path.cwd())
    if legacy.get("wop"):
        legacy["wop_id"] = _wop_id(Path(legacy["wop"]))
    else:
        legacy["wop_id"] = env.get("EOS_WOP_ADMISSION_WOP_ID", "")
    legacy.setdefault("admission_record", env.get("EOS_WOP_ADMISSION_RECORD", ""))
    for field in REQUIRED_LOCATORS:
        legacy.setdefault(field, "")
    return ResolvedAuthorizationBundle("legacy_environment", legacy)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args(argv)
    try:
        result = resolve(args.bundle)
    except AuthorizationBundleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 77
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
