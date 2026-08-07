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
from scripts.lib.wop.canonical_package import CanonicalPackageError, load as load_canonical_package, package_digest as canonical_package_digest


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
    "approval authorized lifecycle state": "approval_authorized_lifecycle_state",
    "approval_authorized_lifecycle_state": "approval_authorized_lifecycle_state",
    "authoritative references": "authoritative_references",
    "authoritative_references": "authoritative_references",
    "execution package authority node id": "execution_package_authority_node_id",
    "execution_package_authority_node_id": "execution_package_authority_node_id",
    "execution package authorization decision record": "execution_package_authorization_decision_record",
    "execution_package_authorization_decision_record": "execution_package_authorization_decision_record",
    "target operation": "target_operation", "target_operation": "target_operation",
    "target mission id": "target_mission_id", "target_mission_id": "target_mission_id",
    "target mission class": "target_mission_class", "target_mission_class": "target_mission_class",
    "target mission contract locator": "target_mission_contract_locator",
    "target registry locator": "target_registry_locator",
    "target package locator": "target_package_locator",
    "activation policy": "activation_policy", "publication approval policy": "publication_approval_policy",
}

for _section in (
    "completion_report_requirement", "deliverables", "dependencies_and_entry_criteria",
    "execution_sequence", "explicit_authority", "governing_references",
    "mission_classification", "prohibited_activities", "publication_and_synchronization",
    "scope", "stop_resume_and_escalation", "success_and_acceptance_criteria",
    "validation_profile",
):
    KEYS[f"sections {_section.replace('_', ' ')}"] = f"sections_{_section}"
    KEYS[f"sections.{_section}"] = f"sections_{_section}"


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

    list_fields = {"scope", "dependencies", "protected_baselines", "gates", "qualification_requirements", "completion_requirements", "authoritative_references"}
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


def package(source: Path, destination_root: Path, repository_root: Path | str | None = None) -> tuple[Path, dict[str, Any]]:
    if is_canonical_source(source):
        return adapt_canonical_package(source, destination_root, repository_root=repository_root)
    from scripts.lib.emp.wop_validation import require_valid_source
    validation = require_valid_source(source, repository_root=repository_root)
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
        sections = {
            key.removeprefix("sections_"): metadata[key]
            for key in metadata if key.startswith("sections_")
        }
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
        "approval": {"authorized_lifecycle_state": metadata["approval_authorized_lifecycle_state"]},
        "authoritative_references": metadata["authoritative_references"],
        "execution_package_references": {
            "authority_node_id": metadata["execution_package_authority_node_id"],
            "authorization_decision_record": metadata["execution_package_authorization_decision_record"],
            "immutable_wop": metadata["wop_id"],
        },
        "sections": sections,
        "execution_mode": execution_mode, "governance_authority": metadata["governance_authority"],
        "repository_identity": metadata["repository_identity"],
        "effect_profile": metadata["effect_profile"],
        "required_execution_files": ["bootstrap.md", "roadmap.md", "mission.yaml", "gates.yaml", "manifests/immutable-manifest.yaml", source_copy.name],
        "source_document_digest": digest,
    }
        target_fields = {
            key: metadata[key] for key in (
                "target_operation", "target_mission_id", "target_mission_class",
                "target_mission_contract_locator", "target_registry_locator",
                "target_package_locator", "activation_policy",
                "publication_approval_policy",
            ) if metadata.get(key) not in (None, "")
        }
        if target_fields:
            mission["target_mission"] = target_fields
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


def is_canonical_source(source: Path) -> bool:
    """Return true only for an explicitly identified canonical package YAML."""
    source = Path(source)
    if not source.is_file() or source.suffix.lower() not in {".yaml", ".yml"}:
        return False
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return False
    return isinstance(value, Mapping) and value.get("schema_version") == "canonical-wop-package/1" and isinstance(value.get("package_identity"), Mapping)


def _canonical_stage1_metadata(package_value: Mapping[str, Any], canonical_digest: str, source_digest_value: str) -> dict[str, Any]:
    identity = package_value["package_identity"]
    requirements = package_value["requirements"]
    reconciliation = package_value.get("reconciliation_contract", {})
    authority = package_value.get("authority_binding", {})
    scope = [str(item.get("objective", item["requirement_id"])) for item in requirements]
    dependencies = [
        str(declaration.get("id"))
        for declaration in package_value.get("technical_prerequisites", {}).get("declarations", [])
        if isinstance(declaration, Mapping) and declaration.get("id")
    ] or ["none"]
    return {
        "schema_version": 1,
        "document_type": "EngineeringWorkOrder",
        "mission_id": str(identity["mission_id"]),
        "wop_id": str(identity["wop_id"]),
        "phase_id": str(identity["mission_id"]) + "-DEVELOPMENT",
        "revision": int(identity["revision"]),
        "status": "Active",
        "title": f"Canonical package adapter for {identity['gate_id']}",
        "objective": f"Adapt validated {package_value['schema_version']} package {identity['package_id']} into the existing Zeus Stage 1 package model.",
        "scope": scope,
        "dependencies": dependencies,
        "priority": 0,
        "candidate_state": "CANDIDATE",
        "qualification_requirements": [str(item.get("acceptance", item["requirement_id"])) for item in requirements],
        "completion_requirements": ["canonical package provenance preserved", "Stage 1 package validation passes", "operator review before submission"],
        "approval": {"authorized_lifecycle_state": "Active"},
        "authoritative_references": ["PROC-0001@1.11", "TPL-0001@1.7", "STD-0000", "STD-0001", "STD-0002", "STD-0003", "STD-0004"],
        "execution_package_references": {
            "authority_node_id": "canonical-package-adapter",
            "authorization_decision_record": "EXTERNAL_AUTHORITY_REQUIRED",
            "immutable_wop": str(identity["wop_id"]),
        },
        "sections": {
            "completion_report_requirement": "Record canonical and Stage 1 identities, validation evidence, and the next governed lifecycle action.",
            "deliverables": ["validated canonical package", "deterministic Stage 1 representation", "provenance mapping"],
            "execution_sequence": package_value.get("bootstrap", {}).get("steps", []),
            "dependencies_and_entry_criteria": package_value.get("technical_prerequisites", {}),
            "explicit_authority": authority,
            "governing_references": ["canonical package schema", "published WOP architecture", "existing Stage 1 runtime"],
            "mission_classification": "Development WOP source adapter; non-authoritative until existing lifecycle authority is resolved.",
            "prohibited_activities": package_value.get("publication_boundary", {}).get("prohibited_effects", []),
            "publication_and_synchronization": package_value.get("publication_boundary", {}),
            "scope": scope,
            "stop_resume_and_escalation": package_value.get("recovery_contract", {}),
            "success_and_acceptance_criteria": [str(item.get("acceptance", item["requirement_id"])) for item in requirements],
            "validation_profile": package_value.get("evidence_contract", {}),
        },
        "execution_mode": "DEVELOPMENT",
        "governance_authority": str(authority.get("authority_source", "External mission authority")),
        "repository_identity": str(reconciliation.get("repository_identity", "")),
        "effect_profile": "DEVELOPMENT-NONPRODUCTION-READONLY-ADAPTER",
        "required_execution_files": ["bootstrap.md", "roadmap.md", "mission.yaml", "gates.yaml", "manifests/immutable-manifest.yaml", "source-wop.yaml"],
        "source_document_digest": source_digest_value,
        "canonical_package_schema": str(package_value["schema_version"]),
        "canonical_package_id": str(identity["package_id"]),
        "canonical_package_digest": canonical_digest,
        "canonical_gate_id": str(identity["gate_id"]),
        "canonical_baseline_commit": str(identity["baseline_commit"]),
        "canonical_authority_classification": "EXTERNAL_ONLY_NON_AUTHORITATIVE_SOURCE",
    }


def adapt_canonical_package(source: Path, destination_root: Path, repository_root: Path | str | None = None) -> tuple[Path, dict[str, Any]]:
    """Adapt a validated canonical YAML package into the existing Stage 1 tree.

    This function does not create authority or lifecycle records.  It only
    creates the representation consumed by the existing Stage 1 validator and
    runtime, preserving canonical and derived digests as separate identities.
    """
    from scripts.lib.emp.wop_validation import validate_generated_package

    source = Path(source).resolve()
    try:
        package_value = load_canonical_package(source)
    except CanonicalPackageError as error:
        raise PackagingError(f"canonical WOP package rejected: {error}") from error
    digest = canonical_package_digest(package_value)
    raw_digest = source_digest(source)
    identity = package_value["package_identity"]
    package_id = f"canonical-{digest[:24]}"
    destination_root = Path(destination_root).resolve()
    destination = destination_root / str(identity["wop_id"]) / package_id
    if destination.exists():
        validate_generated_package(destination)
        manifest = yaml.safe_load((destination / "manifests" / "immutable-manifest.yaml").read_text(encoding="utf-8")) or {}
        if manifest.get("canonical_package_digest") != digest or manifest.get("canonical_source_digest") != raw_digest:
            raise PackagingError("existing adapted package canonical provenance mismatch")
        return destination, {"packaged": True, "adapted": True, "replayed": True, "package_id": package_id,
                             "canonical_package_digest": digest, "source_digest": raw_digest, "stage1_package": str(destination)}

    staging_parent = destination_root if destination_root.is_dir() else destination_root.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".zeus-canonical-wop-staging-", dir=str(staging_parent)))
    temporary = staging / package_id
    temporary.mkdir()
    try:
        metadata = _canonical_stage1_metadata(package_value, digest, raw_digest)
        (temporary / "source-wop.yaml").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        (temporary / "mission.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
        bootstrap = package_value["bootstrap"]
        (temporary / "bootstrap.md").write_text("# Canonical WOP bootstrap\n\n" + "\n".join(f"- {step}" for step in bootstrap["steps"]) + "\n", encoding="utf-8")
        (temporary / "roadmap.md").write_text("# Canonical WOP requirements\n\n" + "\n".join(f"- {item['requirement_id']}: {item['objective']}" for item in package_value["requirements"]) + "\n", encoding="utf-8")
        (temporary / "gates.yaml").write_text(yaml.safe_dump({"schema_version": 1, "gates": package_value["requirements"], "canonical_execution_graph": package_value["execution_graph"]}, sort_keys=False), encoding="utf-8")
        manifests = temporary / "manifests"
        manifests.mkdir()
        manifest = {
            "schema_version": 1,
            "manifest_id": str(identity["wop_id"]) + "-CANONICAL-ADAPTER-MANIFEST",
            "mission_id": str(identity["mission_id"]),
            "wop_id": str(identity["wop_id"]),
            "execution_mode": "DEVELOPMENT",
            "governance_authority": metadata["governance_authority"],
            "repository_identity": metadata["repository_identity"],
            "effect_profile": metadata["effect_profile"],
            "protected_baselines": [str(identity["baseline_commit"])],
            "source_document_digest": raw_digest,
            "canonical_package_schema": package_value["schema_version"],
            "canonical_package_id": str(identity["package_id"]),
            "canonical_package_digest": digest,
            "canonical_source_digest": raw_digest,
            "canonical_gate_id": str(identity["gate_id"]),
            "canonical_baseline_commit": str(identity["baseline_commit"]),
            "canonical_authority_classification": "EXTERNAL_ONLY_NON_AUTHORITATIVE_SOURCE",
        }
        (manifests / "immutable-manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        validate_generated_package(temporary)
        destination_root.mkdir(parents=True, exist_ok=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temporary, destination)
        staging.rmdir()
        return destination, {"packaged": True, "adapted": True, "replayed": False, "package_id": package_id,
                             "canonical_package_digest": digest, "source_digest": raw_digest, "stage1_package": str(destination)}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def template_metadata(wop_id: str, mission_id: str, repository_identity: str) -> dict[str, Any]:
    metadata = {
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
        "approval_authorized_lifecycle_state": "Active",
        "authoritative_references": ["PROC-0001@1.11", "TPL-0001@1.7", "STD-0000", "STD-0001", "STD-0002", "STD-0003", "STD-0004"],
        "execution_package_authority_node_id": "work-package",
        "execution_package_authorization_decision_record": "ADR-REVIEW-REQUIRED",
    }
    metadata.update({
        f"sections_{name}": f"Complete the {name.replace('_', ' ')} section for this bounded development WOP."
        for name in (
            "completion_report_requirement", "deliverables", "dependencies_and_entry_criteria",
            "execution_sequence", "explicit_authority", "governing_references",
            "mission_classification", "prohibited_activities", "publication_and_synchronization",
            "scope", "stop_resume_and_escalation", "success_and_acceptance_criteria",
            "validation_profile",
        )
    })
    return metadata


def markdown_template(metadata: Mapping[str, Any]) -> str:
    lines = [f"# {metadata['title']}", ""]
    for key in ESSENTIAL:
        label = key.replace("_", " ").title()
        value = metadata[key]
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        if key.startswith("sections_"):
            label = "Sections " + key.removeprefix("sections_").replace("_", " ").title()
        lines.append(f"{label}: {value}")
    return "\n".join(lines) + "\n"


def docx_template(metadata: Mapping[str, Any], destination: Path) -> Path:
    rows = []
    for key in ESSENTIAL:
        label = key.replace("_", " ").title()
        if key.startswith("sections_"):
            label = "Sections " + key.removeprefix("sections_").replace("_", " ").title()
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
