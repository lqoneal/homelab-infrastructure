"""The single Development WOP validation service.

All source review, package construction, submission, and inspection callers use
this service.  It deliberately performs no writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.wop_schema import REQUIRED_FIELDS, is_wop_id


@dataclass(frozen=True)
class ValidationResult:
    source: str
    metadata: Mapping[str, Any]
    missing: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not (self.missing or self.conflicts or self.errors)

    def as_dict(self) -> dict[str, Any]:
        return {
            "result": "PASS" if self.valid else "FAIL",
            "source": self.source,
            "metadata": dict(self.metadata),
            "missing": list(self.missing),
            "conflicts": list(self.conflicts),
            "errors": list(self.errors),
        }


def validate_metadata(metadata: Mapping[str, Any], *, source: Path | str = "<source>") -> ValidationResult:
    missing = tuple(field for field in REQUIRED_FIELDS if metadata.get(field) in (None, "", []))
    errors: list[str] = []
    if metadata.get("wop_id") and not is_wop_id(metadata["wop_id"]):
        errors.append("wop_id must match the canonical WOP identity format")
    if metadata.get("execution_mode") and str(metadata["execution_mode"]).upper() != "DEVELOPMENT":
        errors.append("execution_mode must be DEVELOPMENT")
    return ValidationResult(str(source), metadata, missing=missing, errors=tuple(errors))


def validate_source(source: Path) -> ValidationResult:
    """Parse and validate a source without creating package or runtime state."""
    from scripts.lib.emp.wop_packaging import PackagingError, extract

    try:
        metadata, _ = extract(source, validate=False)
    except PackagingError as error:
        return ValidationResult(str(source), {}, missing=tuple(error.missing), conflicts=tuple(error.conflicts), errors=(str(error),))
    return validate_metadata(metadata, source=source)


def require_valid_source(source: Path) -> ValidationResult:
    result = validate_source(source)
    if not result.valid:
        from scripts.lib.emp.wop_packaging import PackagingError

        detail = list(result.missing) + list(result.conflicts) + list(result.errors)
        raise PackagingError("Development WOP rejected: " + "; ".join(detail), missing=result.missing, conflicts=result.conflicts)
    return result


def validate_generated_package(package: Path) -> dict[str, Any]:
    """Validate a generated package through the same canonical boundary."""
    from scripts.lib.emp.stage1_runtime import validate_package

    metadata, evidence = validate_package(package)
    import yaml
    manifest = yaml.safe_load((package / "manifests" / "immutable-manifest.yaml").read_text(encoding="utf-8")) or {}
    gates = yaml.safe_load((package / "gates.yaml").read_text(encoding="utf-8")) or {}
    combined = dict(metadata)
    combined.update({key: manifest.get(key) for key in ("protected_baselines", "effect_profile", "governance_authority", "repository_identity") if manifest.get(key) is not None})
    combined["gates"] = gates.get("gates")
    result = validate_metadata(combined, source=package)
    if not result.valid:
        from scripts.lib.emp.wop_packaging import PackagingError

        detail = list(result.missing) + list(result.errors)
        raise PackagingError("generated package rejected: " + "; ".join(detail), missing=result.missing)
    return {"metadata": combined, "evidence": evidence}
