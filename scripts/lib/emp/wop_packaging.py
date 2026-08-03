"""Deterministic normalization of Markdown/DOCX WOP sources.

This module only constructs a package from explicitly present source facts. It
never supplies authority, scope, dependencies, effects, or baselines.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree

import yaml
from scripts.lib.emp.wop_schema import REQUIRED_FIELDS


class PackagingError(ValueError):
    def __init__(self, message: str, *, missing=None, conflicts=None):
        self.missing = list(missing or [])
        self.conflicts = list(conflicts or [])
        super().__init__(message)


ESSENTIAL = REQUIRED_FIELDS
KEYS = {
    "wop id": "wop_id", "wop_id": "wop_id", "mission id": "mission_id", "mission_id": "mission_id",
    "mission": "mission_id", "title": "title", "objective": "objective", "scope": "scope", "dependencies": "dependencies",
    "execution mode": "execution_mode", "execution_mode": "execution_mode",
    "governance authority": "governance_authority", "governance_authority": "governance_authority",
    "repository identity": "repository_identity", "repository_identity": "repository_identity",
    "effect profile": "effect_profile", "effect_profile": "effect_profile",
    "protected baselines": "protected_baselines", "protected_baseline": "protected_baselines",
    "gates": "gates", "qualification requirements": "qualification_requirements",
    "qualification": "qualification_requirements", "completion requirements": "completion_requirements",
    "completion": "completion_requirements",
}


def source_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _docx_text(path: Path) -> str:
    try:
        with ZipFile(path) as archive:
            document = ElementTree.fromstring(archive.read("word/document.xml"))
    except (OSError, BadZipFile, KeyError, ElementTree.ParseError) as error:
        raise PackagingError(f"invalid DOCX source: {error}") from error
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    # Read body paragraphs outside tables first; table cells are normalized
    # below once, preventing duplicate metadata conflicts in DOCX sources.
    for paragraph in document.findall("./w:body/w:p", namespace):
        value = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip()
        if value:
            paragraphs.append(value)
    # DOCX authors commonly place controlled metadata in a two-column table.
    # Preserve row order and feed it through the same strict key parser; no
    # defaults or authority are inferred from table layout.
    for row in document.findall(".//w:tr", namespace):
        cells = []
        for cell in row.findall("./w:tc", namespace):
            cells.append("".join(node.text or "" for node in cell.findall(".//w:t", namespace)).strip())
        cells = [cell for cell in cells if cell]
        if len(cells) >= 2:
            paragraphs.append(f"{cells[0]}: {' '.join(cells[1:])}")
    if not paragraphs:
        raise PackagingError("invalid DOCX source: no readable paragraphs")
    return "\n".join(paragraphs)


def _scalar(value: str) -> Any:
    value = value.strip().strip("`")
    if not value:
        return None
    if value.startswith("[") or value.startswith("{"):
        try:
            parsed = yaml.safe_load(value)
            return parsed
        except yaml.YAMLError:
            pass
    return value


def _parse(text: str) -> dict[str, Any]:
    found: dict[str, list[Any]] = {}
    current: str | None = None
    current_heading_level: int | None = None
    section_lines: list[str] = []

    def flush():
        nonlocal section_lines
        if current and section_lines:
            content = "\n".join(section_lines).strip()
            if content:
                found.setdefault(current, []).append(content)
        section_lines = []

    for raw in text.splitlines():
        line = raw.strip()
        if not found.get("wop_id") and re.fullmatch(r"WOP-[A-Z0-9-]+", line):
            found.setdefault("wop_id", []).append(line)
            current = None
            current_heading_level = None
            continue
        heading_match = re.match(r"^(#+)\s*(.*)$", line)
        if heading_match:
            heading_level = len(heading_match.group(1))
            heading = heading_match.group(2).strip().lower()
            # A metadata section owns nested headings, but ends at the next
            # peer or higher-level heading. Previously only recognized
            # metadata headings flushed the section, so Scope and Completion
            # Requirements absorbed every later section in a canonical WOP.
            if current and current_heading_level is not None and heading_level <= current_heading_level:
                flush()
                current = None
                current_heading_level = None
            if heading in KEYS:
                current = KEYS[heading]
                current_heading_level = heading_level
            continue
        match = re.match(r"^(?:[-*]\s*)?([^:]+):\s*(.*)$", line)
        if match and match.group(1).strip().lower() in KEYS:
            flush()
            key = KEYS[match.group(1).strip().lower()]
            found.setdefault(key, []).append(_scalar(match.group(2)))
            current = None
            current_heading_level = None
            continue
        if current and line:
            section_lines.append(re.sub(r"^[-*]\s*", "", line))
    flush()

    result: dict[str, Any] = {}
    conflicts: list[str] = []
    for key, values in found.items():
        values = [v for v in values if v not in (None, "")]
        if not values:
            continue
        normalized = [yaml.safe_dump(v, sort_keys=True) for v in values]
        if len(set(normalized)) > 1:
            conflicts.append(key)
        result[key] = values[0]
    if conflicts:
        raise PackagingError("conflicting source metadata: " + ", ".join(sorted(conflicts)), conflicts=conflicts)

    list_fields = {"scope", "dependencies", "protected_baselines", "gates", "qualification_requirements", "completion_requirements"}
    for key in list_fields:
        if key not in result:
            continue
        value = result[key]
        if isinstance(value, str):
            result[key] = [item.strip() for item in re.split(r"[;,]\s*|\n", value) if item.strip()]
        elif not isinstance(value, list):
            result[key] = [value]
    return result


def extract(source: Path, *, validate: bool = True) -> tuple[dict[str, Any], str]:
    if source.suffix.lower() == ".docx":
        text = _docx_text(source)
    elif source.suffix.lower() in {".md", ".markdown", ".txt"}:
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise PackagingError(f"invalid Markdown source: {error}") from error
    else:
        raise PackagingError("unsupported WOP source; use a package directory, Markdown, or DOCX")
    metadata = _parse(text)
    if validate:
        missing = [key for key in ESSENTIAL if not metadata.get(key)]
        if missing:
            raise PackagingError("required WOP metadata unresolved: " + ", ".join(missing), missing=missing)
    return metadata, text


def package(source: Path, destination_root: Path) -> tuple[Path, dict[str, Any]]:
    from scripts.lib.emp.wop_validation import require_valid_source
    validation = require_valid_source(source)
    metadata = dict(validation.metadata)
    digest = source_digest(source)
    package_id = hashlib.sha256((str(metadata["wop_id"]) + ":" + digest).encode()).hexdigest()[:24]
    destination_root = Path(destination_root).resolve()
    destination = destination_root / str(metadata["wop_id"]) / package_id
    if destination.exists():
        existing = destination / "mission.yaml"
        if existing.is_file():
            required = ("mission.yaml", "bootstrap.md", "roadmap.md", "gates.yaml", "manifests/immutable-manifest.yaml")
            missing = [item for item in required if not (destination / item).is_file()]
            if missing:
                raise PackagingError("existing generated package is invalid; missing " + ", ".join(missing), missing=missing)
            try:
                from scripts.lib.emp.wop_validation import validate_generated_package
                validate_generated_package(destination)
                manifest_value = yaml.safe_load((destination / "manifests/immutable-manifest.yaml").read_text(encoding="utf-8"))
                source_copy = destination / ("source-wop" + source.suffix.lower())
                if not source_copy.is_file() or hashlib.sha256(source_copy.read_bytes()).hexdigest() != digest:
                    raise PackagingError("existing generated package source digest mismatch")
                if manifest_value.get("source_document_digest") != digest:
                    raise PackagingError("existing generated package manifest digest mismatch")
            except Exception as error:
                raise PackagingError(f"existing generated package is invalid: {error}") from error
            return destination, {"packaged": True, "package_id": package_id, "source_digest": digest, "replayed": True}
    # Stage outside the destination tree. This means a parse, generation, or
    # validation failure cannot even create `engineering/work-orders/<WOP_ID>`.
    staging_parent = destination_root if destination_root.is_dir() else destination_root.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".zeus-wop-staging-", dir=str(staging_parent)))
    temporary = staging / package_id
    temporary.mkdir()
    parent_created = False
    try:
        source_copy = temporary / ("source-wop" + source.suffix.lower())
        shutil.copy2(source, source_copy)
        execution_mode = str(metadata["execution_mode"]).upper()
        mission = {
        "schema_version": 1, "document_type": "EngineeringWorkOrder",
        "mission_id": metadata["mission_id"], "wop_id": metadata["wop_id"],
        "phase_id": str(metadata["mission_id"]) + "-DEVELOPMENT",
        "revision": int(metadata.get("revision", 1)), "status": "Active",
        "title": metadata["title"], "objective": metadata["objective"],
        "scope": metadata["scope"], "dependencies": metadata["dependencies"],
        "priority": int(metadata.get("priority", 0)), "candidate_state": "CANDIDATE",
        "qualification_requirements": metadata["qualification_requirements"],
        "completion_requirements": metadata["completion_requirements"],
        "execution_mode": execution_mode, "governance_authority": metadata["governance_authority"],
        "repository_identity": metadata["repository_identity"],
        "effect_profile": metadata["effect_profile"],
        "required_execution_files": ["bootstrap.md", "roadmap.md", "mission.yaml", "gates.yaml", "manifests/immutable-manifest.yaml", source_copy.name],
        "source_document_digest": digest,
        }
        (temporary / "mission.yaml").write_text(yaml.safe_dump(mission, sort_keys=False), encoding="utf-8")
        (temporary / "bootstrap.md").write_text(
        f"# {mission['title']}\n\n{mission['objective']}\n\nSource: {source_copy.name}\n", encoding="utf-8")
        (temporary / "roadmap.md").write_text(
        "# Development WOP Roadmap\n\nQualification requirements:\n" +
        "\n".join(f"- {item}" for item in metadata["qualification_requirements"]) +
        "\n\nCompletion requirements:\n" +
        "\n".join(f"- {item}" for item in metadata["completion_requirements"]) + "\n", encoding="utf-8")
        (temporary / "gates.yaml").write_text(yaml.safe_dump({"schema_version": 1, "gates": metadata["gates"]}, sort_keys=False), encoding="utf-8")
        manifest = {"schema_version": 1, "manifest_id": str(metadata["wop_id"]) + "-MANIFEST", "mission_id": metadata["mission_id"], "wop_id": metadata["wop_id"], "execution_mode": execution_mode, "governance_authority": metadata["governance_authority"], "repository_identity": metadata["repository_identity"], "effect_profile": metadata["effect_profile"], "protected_baselines": metadata["protected_baselines"], "source_document_digest": digest}
        manifest_dir = temporary / "manifests"; manifest_dir.mkdir()
        (manifest_dir / "immutable-manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

        # The complete candidate is validated before it can enter the
        # repository. Import lazily to keep the packaging parser independent
        # from Stage 1's runtime owner.
        from scripts.lib.emp.wop_validation import validate_generated_package
        validate_generated_package(temporary)
        if hashlib.sha256(source_copy.read_bytes()).hexdigest() != digest:
            raise PackagingError("source preservation digest mismatch")
        manifest_value = yaml.safe_load((temporary / "manifests/immutable-manifest.yaml").read_text())
        if manifest_value.get("source_document_digest") != digest:
            raise PackagingError("immutable manifest source digest mismatch")
        destination_root.mkdir(parents=True, exist_ok=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        parent_created = True
        os.replace(temporary, destination)
        staging.rmdir()
        return destination, {"packaged": True, "package_id": package_id, "source_digest": digest, "replayed": False, "promoted": True}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        if parent_created:
            try:
                destination.parent.rmdir()
            except OSError:
                pass
        raise


def is_canonical_package(source: Path) -> bool:
    return source.is_dir() and (source / "mission.yaml").is_file() and (source / "manifests/immutable-manifest.yaml").is_file()


def template_metadata(wop_id: str, mission_id: str, repository_identity: str) -> dict[str, Any]:
    return {
        "wop_id": wop_id, "mission_id": mission_id, "title": "Development WOP",
        "objective": "Perform a bounded non-production engineering qualification.",
        "scope": ["validate the bounded workflow", "preserve protected baselines"],
        "dependencies": ["none"], "execution_mode": "DEVELOPMENT",
        "governance_authority": "Engineering Governance",
        "repository_identity": repository_identity,
        "effect_profile": "DEVELOPMENT-AUTHORING-NONPRODUCTION",
        "protected_baselines": ["OA-v1.0.0", "OB-PLAN-v1.0.0"],
        "gates": ["VALIDATE", "QUALIFY", "CLOSE"],
        "qualification_requirements": ["package validation evidence"],
        "completion_requirements": ["reviewable completion report"],
    }


def markdown_template(metadata: Mapping[str, Any]) -> str:
    lines = [f"# {metadata['title']}", ""]
    for key in ESSENTIAL:
        label = key.replace("_", " ").title()
        value = metadata[key]
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        lines.append(f"{label}: {value}")
    return "\n".join(lines) + "\n"


def docx_template(metadata: Mapping[str, Any], destination: Path) -> Path:
    rows = []
    for key in ESSENTIAL:
        label = key.replace("_", " ").title()
        value = metadata[key]
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        rows.append(f"<w:tr><w:tc><w:p><w:r><w:t>{label}</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>{value}</w:t></w:r></w:p></w:tc></w:tr>")
    xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:tbl>' + "".join(rows) + "</w:tbl></w:body></w:document>"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", xml)
    return destination


def lint_source(source: Path, metadata: Mapping[str, Any]) -> list[str]:
    """Return non-blocking authoring quality warnings.

    Lint never supplies missing authority and never changes validation outcome.
    """
    issues: list[str] = []
    if source.suffix.lower() in {".md", ".markdown", ".txt"}:
        text = source.read_text(encoding="utf-8")
        if not re.search(r"^#\s+", text, re.MULTILINE):
            issues.append("document has no Markdown title heading")
        if "scope" not in text.lower():
            issues.append("scope section is not visibly labeled")
    if str(metadata.get("execution_mode", "")).upper() != "DEVELOPMENT":
        issues.append("execution mode is not DEVELOPMENT")
    if str(metadata.get("effect_profile", "")).upper().startswith("PRODUCTION"):
        issues.append("effect profile appears production-scoped")
    return issues
