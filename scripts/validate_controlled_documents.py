#!/usr/bin/env python3
"""Validate repository-controlled discovery, EGR, and EMP architecture records."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INDEX_PATH = DOCS / "DOC-0001-REPOSITORY_DOCUMENT_INDEX.md"
REGISTRY_PATH = ROOT / "engineering/registry/work-registry.yaml"
REGISTRY_SCHEMA_PATH = ROOT / "engineering/registry/work-registry.schema.yaml"

FRAMEWORK_PATHS = {
    "DOC-0001": INDEX_PATH,
    "STD-0000": DOCS
    / "standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md",
    "PROC-0002": DOCS
    / "procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md",
    "TPL-0004": DOCS
    / "templates/TPL-0004-ENGINEERING_GOVERNANCE_RESOLUTION_TEMPLATE.md",
    "EMP-0001": DOCS
    / "emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md",
    "SPEC-0006": DOCS
    / "specifications/SPEC-0006-ENGINEERING_WORK_REGISTRY_MODEL.md",
    "SPEC-0008": DOCS
    / "specifications/SPEC-0008-ENGINEERING_TRANSACTION_PROFILE_SPECIFICATION.md",
    "SERVICE-0002": DOCS
    / "services/SERVICE-0002-EMP_MANAGEMENT_SERVICES_CATALOG.md",
}

INDEX_REGISTRATIONS = {
    "PROC-0002": {
        "title": "Engineering Governance Resolution Procedure",
        "status": "Active",
        "owner": "Engineering Governance",
        "path": "docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md",
    },
    "TPL-0004": {
        "title": "Engineering Governance Resolution Template",
        "status": "Active",
        "owner": "Engineering Governance",
        "path": "docs/templates/TPL-0004-ENGINEERING_GOVERNANCE_RESOLUTION_TEMPLATE.md",
    },
    "EMP-0001": {
        "title": "Engineering Management Platform Architecture",
        "status": "Active",
        "owner": "Engineering Management Platform",
        "path": "docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md",
    },
    "SPEC-0006": {
        "title": "Engineering Work Registry Model",
        "status": "Active",
        "owner": "Engineering Management Platform",
        "path": "docs/specifications/SPEC-0006-ENGINEERING_WORK_REGISTRY_MODEL.md",
    },
    "SPEC-0008": {
        "title": "Engineering Transaction Profile Specification",
        "status": "Draft",
        "owner": "Engineering Governance",
        "path": "docs/specifications/SPEC-0008-ENGINEERING_TRANSACTION_PROFILE_SPECIFICATION.md",
    },
    "SERVICE-0002": {
        "title": "EMP Management Services Catalog",
        "status": "Active",
        "owner": "Engineering Management Platform",
        "path": "docs/services/SERVICE-0002-EMP_MANAGEMENT_SERVICES_CATALOG.md",
    },
}

REQUIRED_METADATA = {
    "document_id",
    "title",
    "version",
    "status",
    "owner",
    "created",
    "last_updated",
    "classification",
    "predecessor_revision",
    "successor_revision",
    "approval_status",
    "approval_authority",
    "approval_reference",
    "approval_date",
    "persistence_status",
    "relationships",
}

LIFECYCLE_STATES = {
    "Draft",
    "Review",
    "Approved",
    "Active",
    "Superseded",
    "Archived",
}

APPROVAL_STATES = {"Pending", "Approved", "Rejected", "Withdrawn"}
PERSISTENCE_STATES = {"Pending", "Persisted", "Legacy", "Remediation Required"}

RELATIONSHIP_TYPES = {
    "governed_by",
    "governs",
    "implements",
    "implemented_by",
    "conforms_to",
    "constrains",
    "depends_on",
    "required_by",
    "validated_by",
    "validates",
    "authorized_by",
    "authorizes",
    "produces",
    "produced_by",
    "indexes",
    "indexed_by",
    "supersedes",
    "superseded_by",
    "related_to",
}

PLACEHOLDER_PATTERN = re.compile(
    r"(?:EGR|PROC|TPL)-0*XX|\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE
)
DOCUMENT_ID_PATTERN = re.compile(
    r'^document_id:\s*["\']?([^"\'\s]+)["\']?\s*$', re.MULTILINE
)
EGR_ID_PATTERN = re.compile(r"^EGR-[0-9]{6}$")


class Validation:
    def __init__(self) -> None:
        self.passed = 0
        self.errors: list[str] = []

    def check(self, condition: bool, message: str) -> None:
        if condition:
            self.passed += 1
            print(f"PASS: {message}")
        else:
            self.errors.append(message)
            print(f"FAIL: {message}")

    def finish(self) -> int:
        print()
        print(f"Controlled-document checks passed: {self.passed}")
        print(f"Controlled-document checks failed: {len(self.errors)}")
        if self.errors:
            return 1
        print("EGR framework, EMP architecture, and repository discovery are valid.")
        return 0


def repository_markdown_files() -> list[Path]:
    roots = [DOCS, ROOT / "engineering"]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*.md") if path.is_file())
    return sorted(set(files))


def load_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3 or parts[0].strip():
        raise ValueError("missing leading YAML front matter")
    metadata = yaml.safe_load(parts[1])
    if not isinstance(metadata, dict):
        raise ValueError("YAML front matter is not a mapping")
    return metadata


def document_identity_map(files: list[Path]) -> tuple[dict[str, Path], dict[str, list[Path]]]:
    identities: dict[str, Path] = {}
    duplicates: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        match = DOCUMENT_ID_PATTERN.search(text)
        if not match:
            continue
        document_id = match.group(1)
        if document_id in identities:
            if not duplicates[document_id]:
                duplicates[document_id].append(identities[document_id])
            duplicates[document_id].append(path)
        else:
            identities[document_id] = path
    return identities, duplicates


def controlled_document_rows(text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    in_table = False
    for line in text.splitlines():
        if line == "# Controlled Documents":
            in_table = True
            continue
        if in_table and line == "---":
            break
        if not in_table or not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] in {"Document ID", "-----------"}:
            continue
        rows[cells[0]] = {
            "title": cells[1],
            "status": cells[2],
            "owner": cells[3],
            "path": cells[4],
        }
    return rows


def relationship_pairs(metadata: dict[str, Any]) -> set[tuple[str, str]]:
    relationships = metadata.get("relationships")
    if not isinstance(relationships, list):
        return set()
    pairs: set[tuple[str, str]] = set()
    for relationship in relationships:
        if isinstance(relationship, dict):
            relation_type = relationship.get("type")
            target = relationship.get("target")
            if isinstance(relation_type, str) and isinstance(target, str):
                pairs.add((relation_type, target))
    return pairs


def validate_metadata(
    validation: Validation,
    path: Path,
    metadata: dict[str, Any],
    identities: dict[str, Path],
) -> None:
    label = path.relative_to(ROOT)
    missing = sorted(REQUIRED_METADATA - metadata.keys())
    validation.check(not missing, f"{label}: required metadata present")
    validation.check(metadata.get("status") in LIFECYCLE_STATES, f"{label}: lifecycle valid")
    validation.check(
        metadata.get("approval_status") in APPROVAL_STATES,
        f"{label}: approval status valid",
    )
    validation.check(
        metadata.get("persistence_status") in PERSISTENCE_STATES,
        f"{label}: persistence status valid",
    )
    if metadata.get("status") in {"Approved", "Active", "Superseded", "Archived"}:
        validation.check(bool(metadata.get("approval_authority")), f"{label}: approval authority present")
        validation.check(bool(metadata.get("approval_reference")), f"{label}: approval reference present")
        validation.check(bool(metadata.get("approval_date")), f"{label}: approval date present")
    else:
        validation.check(
            metadata.get("approval_status") == "Pending",
            f"{label}: non-operational revision has Pending approval",
        )

    relationships = metadata.get("relationships")
    validation.check(isinstance(relationships, list), f"{label}: relationships are a list")
    if not isinstance(relationships, list):
        return
    for position, relationship in enumerate(relationships, start=1):
        valid_shape = (
            isinstance(relationship, dict)
            and isinstance(relationship.get("type"), str)
            and isinstance(relationship.get("target"), str)
        )
        validation.check(valid_shape, f"{label}: relationship {position} has type and target")
        if not valid_shape:
            continue
        relation_type = relationship["type"]
        target = relationship["target"]
        validation.check(
            relation_type in RELATIONSHIP_TYPES,
            f"{label}: relationship type {relation_type} recognized",
        )
        validation.check(target in identities, f"{label}: relationship target {target} resolves")


def validate_repository_relationships(
    validation: Validation,
    identities: dict[str, Path],
) -> None:
    """Enforce SPEC-0001 relationship vocabulary for every controlled record."""
    for document_id, path in sorted(identities.items()):
        try:
            metadata = load_frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(
                False,
                f"{document_id}: relationship metadata readable ({error})",
            )
            continue
        relationships = metadata.get("relationships")
        if relationships is None:
            continue
        validation.check(
            isinstance(relationships, list),
            f"{document_id}: repository-wide relationships are a list",
        )
        if not isinstance(relationships, list):
            continue
        for position, relationship in enumerate(relationships, start=1):
            valid_shape = (
                isinstance(relationship, dict)
                and isinstance(relationship.get("type"), str)
                and isinstance(relationship.get("target"), str)
            )
            validation.check(
                valid_shape,
                f"{document_id}: repository-wide relationship {position} has type and target",
            )
            if not valid_shape:
                continue
            relation_type = relationship["type"]
            target = relationship["target"]
            validation.check(
                relation_type in RELATIONSHIP_TYPES,
                f"{document_id}: repository-wide relationship type {relation_type} recognized",
            )
            validation.check(
                target in identities,
                f"{document_id}: repository-wide relationship target {target} resolves",
            )


def validate_governance_cycles(
    validation: Validation,
    metadata_by_id: dict[str, dict[str, Any]],
) -> None:
    graph: dict[str, set[str]] = defaultdict(set)
    for document_id, metadata in metadata_by_id.items():
        for relation_type, target in relationship_pairs(metadata):
            if relation_type == "governed_by" and target in metadata_by_id:
                graph[document_id].add(target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        if not all(visit(target) for target in graph[node]):
            return False
        visiting.remove(node)
        visited.add(node)
        return True

    validation.check(
        all(visit(node) for node in list(graph)),
        "governed_by relationships contain no cycle",
    )


def main() -> int:
    validation = Validation()
    files = repository_markdown_files()
    identities, duplicates = document_identity_map(files)

    validation.check(not duplicates, "document identifiers are unique")
    validate_repository_relationships(validation, identities)
    for document_id, path in FRAMEWORK_PATHS.items():
        validation.check(path.is_file(), f"{document_id}: canonical framework path exists")
        validation.check(
            identities.get(document_id) == path,
            f"{document_id}: identity resolves to canonical framework path",
        )

    metadata_by_id: dict[str, dict[str, Any]] = {}
    for document_id, path in FRAMEWORK_PATHS.items():
        try:
            metadata = load_frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(False, f"{document_id}: valid YAML front matter ({error})")
            continue
        metadata_by_id[document_id] = metadata
        validation.check(metadata.get("document_id") == document_id, f"{document_id}: metadata identity matches")
        validate_metadata(validation, path, metadata, identities)

    try:
        index_text = INDEX_PATH.read_text(encoding="utf-8")
    except OSError as error:
        validation.check(False, f"DOC-0001 readable ({error})")
        return validation.finish()

    rows = controlled_document_rows(index_text)
    validation.check(REGISTRY_PATH.is_file(), "canonical EMP Work Registry exists")
    validation.check(REGISTRY_SCHEMA_PATH.is_file(), "canonical EMP Work Registry schema exists")
    validation.check(
        "engineering/registry/work-registry.yaml" in index_text,
        "DOC-0001 registers Work Registry discovery",
    )
    validation.check(
        "engineering/registry/work-registry.schema.yaml" in index_text,
        "DOC-0001 registers Work Registry schema discovery",
    )
    validation.check(
        "engctl registry validate" in index_text,
        "DOC-0001 registers Work Registry validation discovery",
    )
    validation.check(
        "| EGR | Engineering Governance Resolutions recording governance decisions |" in index_text,
        "DOC-0001 registers the EGR class",
    )
    validation.check(
        "docs/resolutions/" in index_text,
        "DOC-0001 registers the canonical EGR location",
    )
    validation.check(
        "EGR-000001" in index_text and "six-digit decimal sequence" in index_text,
        "DOC-0001 registers deterministic EGR numbering",
    )
    validation.check(
        "The absence of an EGR instance is valid" in index_text,
        "framework validation permits zero EGR instances",
    )

    for document_id, expected in INDEX_REGISTRATIONS.items():
        actual = rows.get(document_id)
        validation.check(actual is not None, f"DOC-0001 registers {document_id}")
        validation.check(actual == expected, f"DOC-0001 registration for {document_id} matches metadata and path")
        validation.check((ROOT / expected["path"]).is_file(), f"DOC-0001 path for {document_id} resolves")

    index_relationships = relationship_pairs(metadata_by_id.get("DOC-0001", {}))
    validation.check(("indexes", "PROC-0002") in index_relationships, "DOC-0001 indexes PROC-0002")
    validation.check(("indexes", "TPL-0004") in index_relationships, "DOC-0001 indexes TPL-0004")
    for document_id in ("PROC-0002", "TPL-0004"):
        pairs = relationship_pairs(metadata_by_id.get(document_id, {}))
        validation.check(("indexed_by", "DOC-0001") in pairs, f"{document_id} is indexed by DOC-0001")

    for document_id in ("EMP-0001", "SPEC-0006", "SPEC-0008", "SERVICE-0002"):
        pairs = relationship_pairs(metadata_by_id.get(document_id, {}))
        validation.check(
            ("indexed_by", "DOC-0001") in pairs,
            f"{document_id} is indexed by DOC-0001",
        )
        validation.check(
            ("indexes", document_id) in index_relationships,
            f"DOC-0001 indexes {document_id}",
        )

    emp_relationships = relationship_pairs(metadata_by_id.get("EMP-0001", {}))
    spec_relationships = relationship_pairs(metadata_by_id.get("SPEC-0006", {}))
    service_relationships = relationship_pairs(metadata_by_id.get("SERVICE-0002", {}))
    validation.check(
        ("implemented_by", "SPEC-0006") in emp_relationships
        and ("implements", "EMP-0001") in spec_relationships,
        "EMP architecture and Work Registry model are bidirectionally related",
    )
    validation.check(
        ("implemented_by", "SERVICE-0002") in emp_relationships
        and ("implements", "EMP-0001") in service_relationships,
        "EMP architecture and management-service catalog are bidirectionally related",
    )
    validation.check(
        ("implemented_by", "SERVICE-0002") in spec_relationships
        and ("implements", "SPEC-0006") in service_relationships,
        "Work Registry model and management-service catalog are bidirectionally related",
    )

    emp_text = FRAMEWORK_PATHS["EMP-0001"].read_text(encoding="utf-8")
    spec_text = FRAMEWORK_PATHS["SPEC-0006"].read_text(encoding="utf-8")
    service_text = FRAMEWORK_PATHS["SERVICE-0002"].read_text(encoding="utf-8")
    etp_text = FRAMEWORK_PATHS["SPEC-0008"].read_text(encoding="utf-8")
    etp_match = re.search(r"```yaml etp-profile\n(.*?)\n```", etp_text, re.DOTALL)
    validation.check(bool(etp_match), "SPEC-0008 contains the authoritative ETP YAML block")
    if etp_match:
        try:
            etp_profile = yaml.safe_load(etp_match.group(1))
        except yaml.YAMLError as error:
            validation.check(False, f"SPEC-0008 ETP YAML parses ({error})")
        else:
            validation.check(isinstance(etp_profile, dict), "SPEC-0008 ETP profile is a mapping")
            if isinstance(etp_profile, dict):
                validation.check(
                    etp_profile.get("profile_id") == "ETP-BASELINE-CONTROLLED-PUBLICATION",
                    "SPEC-0008 defines exactly the approved baseline profile identity",
                )
                validation.check(etp_profile.get("status") == "Active", "baseline ETP is Active")
                validation.check(
                    etp_profile.get("components", {}).get("construction") == "PROC-0004@1.6",
                    "baseline ETP resolves construction to PROC-0004 1.6 candidate",
                )
                validation.check(
                    etp_profile.get("components", {}).get("execution") == "PROC-0001@1.14",
                    "baseline ETP preserves PROC-0001 execution ownership",
                )
                validation.check(
                    etp_profile.get("components", {}).get("automation") == "deferred",
                    "baseline ETP defers automation",
                )
                validation.check(
                    etp_profile.get("compatibility", {}).get("requires_authority_preservation") is True,
                    "baseline ETP requires Authority Preservation",
                )
    for required_scope in (
        "projects",
        "missions",
        "phases",
        "sprints",
        "work queues",
        "milestones",
        "deferred-work",
        "dependencies",
        "engineering metrics",
        "portfolio status",
    ):
        validation.check(
            required_scope.lower() in emp_text.lower(),
            f"EMP-0001 defines management scope for {required_scope}",
        )
    for entity in (
        "Portfolio",
        "Project",
        "Mission",
        "Phase",
        "Sprint",
        "Work Item",
        "Work Queue",
        "Milestone",
        "Deferral",
        "Dependency",
        "Metric Definition",
    ):
        validation.check(
            f"## 3." in spec_text and entity in spec_text,
            f"SPEC-0006 defines the {entity} entity",
        )
    for service in (
        "Work Registry Service",
        "Portfolio Service",
        "Work Queue Service",
        "Dependency Service",
        "Milestone Service",
        "Engineering Metrics Service",
    ):
        validation.check(service in service_text, f"SERVICE-0002 defines {service}")
    validation.check(
        "shall not create a second global controller" in emp_text,
        "EMP-0001 preserves the existing global controller boundary",
    )
    validation.check(
        "shall not create a competing validation framework" in emp_text,
        "EMP-0001 preserves the EOS validation-service boundary",
    )

    egr_records: list[tuple[str, Path]] = sorted(
        (document_id, path)
        for document_id, path in identities.items()
        if document_id.startswith("EGR-")
    )
    validation.check(True, f"EGR instance count accepted: {len(egr_records)}")
    for document_id, path in egr_records:
        relative_path = path.relative_to(ROOT)
        validation.check(bool(EGR_ID_PATTERN.fullmatch(document_id)), f"{document_id}: identifier format valid")
        validation.check(path.parent == DOCS / "resolutions", f"{document_id}: canonical directory valid")
        validation.check(path.name.startswith(f"{document_id}-"), f"{document_id}: filename begins with identifier")
        try:
            metadata = load_frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(False, f"{relative_path}: valid YAML front matter ({error})")
            continue
        validate_metadata(validation, path, metadata, identities)
        validation.check(
            metadata.get("classification") == "Engineering Governance Resolution",
            f"{document_id}: classification valid",
        )
        validation.check(document_id in rows, f"{document_id}: registered in DOC-0001")
        if document_id in rows:
            validation.check(
                rows[document_id]["path"] == str(relative_path),
                f"{document_id}: index path agrees",
            )
        validation.check(
            ("indexed_by", "DOC-0001") in relationship_pairs(metadata),
            f"{document_id}: indexed_by relationship present",
        )

    for document_id, path in FRAMEWORK_PATHS.items():
        if document_id == "TPL-0004":
            continue
        text = path.read_text(encoding="utf-8")
        validation.check(
            PLACEHOLDER_PATTERN.search(text) is None,
            f"{document_id}: no unresolved implementation placeholders",
        )

    validate_governance_cycles(validation, metadata_by_id)
    return validation.finish()


if __name__ == "__main__":
    sys.exit(main())
