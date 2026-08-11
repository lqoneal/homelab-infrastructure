#!/usr/bin/env python3
"""Validate repository-controlled discovery, EGR, and EMP architecture records."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lib.document_synchronization import analyze as analyze_synchronization
from lib.document_synchronization import load_metadata as load_synchronization_metadata
from lib.implementation_coverage import analyze as analyze_implementation_coverage
from lib.implementation_coverage import canonical_report as canonical_coverage_report
from lib.implementation_coverage import load_policy as load_coverage_policy
from lib.engineering_conformance import analyze as analyze_conformance
from lib.engineering_conformance import canonical_report as canonical_conformance_report
from lib.engineering_conformance import load_contracts
from lib.engineering_assurance import analyze as analyze_assurance
from lib.engineering_assurance import canonical_report as canonical_assurance_report
from lib.engineering_assurance import load_catalog as load_assurance_catalog


DOCS = ROOT / "docs"
INDEX_PATH = DOCS / "DOC-0001-REPOSITORY_DOCUMENT_INDEX.md"
REGISTRY_PATH = ROOT / "engineering/registry/work-registry.yaml"
REGISTRY_SCHEMA_PATH = ROOT / "engineering/registry/work-registry.schema.yaml"
SEMANTIC_PROFILE_PATH = (
    ROOT / "engineering/validation/controlled-document-semantic-profiles.yaml"
)

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


def load_semantic_catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(SEMANTIC_PROFILE_PATH.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict):
        raise ValueError("semantic profile catalog is not a mapping")
    return catalog


def semantic_profile_for(path: Path, metadata: dict[str, Any] | None = None) -> str | None:
    """Resolve a reusable profile without changing legacy document admission."""
    declared = (metadata or {}).get("semantic_validation_profile")
    if isinstance(declared, str):
        return declared
    name = path.name.lower()
    try:
        relative = str(path.relative_to(ROOT)).lower()
    except ValueError:
        relative = str(path).lower()
    if (
        name == "roadmap.md"
        or "implementation-roadmap" in name
        or name == "zeus-canonical-development-roadmap.md"
    ):
        return "Roadmap"
    if name == "gate-specification.yaml":
        return "Gate Specification"
    if name == "immutable-wop.yaml":
        return "WOP"
    if name == "verification.md" and "/gates/" in relative:
        return "Operator Verification Guide"
    if "completion-report" in name:
        return "Completion Report"
    if (
        name == "zeus-wop-submission-procedure.md"
        or name == "zeus-development-mode.md"
        or name == "zeus-execution-lifecycle-procedure.md"
    ):
        return "Procedure"
    classification = str((metadata or {}).get("classification", ""))
    for profile in ("Standard", "Specification", "Procedure", "Policy", "Template"):
        if profile.lower() in classification.lower():
            return profile
    return None


CONCEPT_ALIASES = {
    "purpose": ("purpose", "intent"),
    "entry": ("entry", "prerequisite", "required inputs"),
    "sequence": ("sequence", "workflow", "steps", "stage"),
    "stop": ("stop", "fail-closed", "blocked"),
    "outputs": ("outputs", "required outputs", "produces"),
    "objective": ("objective", "purpose"),
    "sequencing": ("sequence", "sequencing", "ordering"),
    "dependencies": ("dependencies", "prerequisite", "enables"),
    "completion": ("completion", "complete", "last gate"),
    "traceability": ("traceability", "controlled id", "supersedes"),
    "validation": ("validation", "verification"),
    "acceptance": ("acceptance", "approved", "pass"),
    "engineering explanation": ("engineering explanation", "intent and implementation", "rationale"),
    "operator explanation": ("operator explanation", "operator verification", "steps and expected results"),
    "verification steps": ("verification steps", "steps and expected results"),
    "expected outputs": ("expected outputs", "expected results", "expect "),
    "evidence inspection": ("evidence inspection", "inspect every file", "inspect the evidence"),
    "pass criteria": ("pass criteria", "pass requires"),
    "fail criteria": ("fail criteria", "fail includes", "is fail"),
    "acceptance procedure": ("acceptance procedure", "accept only after pass", "approve "),
    "rejection procedure": ("rejection procedure", "reject with", "decline "),
    "resume procedure": ("resume procedure", "run `zeus resume`", "resume stops"),
}

PROFILE_DIMENSIONS = {
    "required_engineering_content",
    "required_traceability",
    "required_evidence",
    "required_command_documentation",
    "required_validation_criteria",
    "required_acceptance_criteria",
}


def contains_concept(text: str, concept: str) -> bool:
    terms = CONCEPT_ALIASES.get(concept.lower(), (concept,))
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def nested_value(document: Any, dotted_key: str) -> Any:
    value = document
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def resolve_command(command: str) -> Path | None:
    executable = shlex.split(command)[0] if command.strip() else ""
    if not executable:
        return None
    candidates = (
        ROOT / executable,
        ROOT / "scripts" / executable,
        ROOT / "engineering" / executable,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    resolved = shutil.which(executable)
    return Path(resolved) if resolved else None


def command_exists(command: str) -> bool:
    return resolve_command(command) is not None


def command_interface_check(command: str, documentation: str) -> tuple[bool, dict[str, Any]]:
    """Inspect help-only interfaces; never execute the declared operation."""
    try:
        tokens = shlex.split(command)
    except ValueError as error:
        return False, {"command": command, "error": f"invalid shell syntax: {error}"}
    executable = resolve_command(command)
    if executable is None:
        return False, {"command": command, "error": "executable does not resolve"}

    command_path: list[str] = []
    help_text = ""
    for token in tokens[1:]:
        if token.startswith("-") or token.upper() == token or re.search(r"\d", token):
            break
        probe = [str(executable), *command_path, "--help"]
        completed = subprocess.run(
            probe,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        help_text = completed.stdout + completed.stderr
        if completed.returncode != 0 or token not in help_text:
            break
        command_path.append(token)

    probe = [str(executable), *command_path, "--help"]
    completed = subprocess.run(
        probe,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    help_text = completed.stdout + completed.stderr
    options = [token.split("=", 1)[0] for token in tokens if token.startswith("-")]
    missing_options = [option for option in options if option not in help_text]
    exit_documented = bool(
        re.search(r"\b(exit|return)\s+(?:status|code)\b|\bnonzero\b|\bnon-zero\b|\bexit\s+\d+\b", documentation, re.I)
    )
    result = {
        "command": command,
        "executable": str(executable),
        "interface": " ".join(command_path),
        "help_probe": " ".join(probe),
        "help_exit": completed.returncode,
        "missing_options": missing_options,
        "exit_behavior_documented": exit_documented,
        "execution_mode": "interface_only",
    }
    return completed.returncode == 0 and not missing_options and exit_documented, result


def semantic_validate_path(
    validation: Validation,
    path: Path,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    try:
        display_path = path.relative_to(ROOT)
    except ValueError:
        display_path = path
    result: dict[str, Any] = {"path": str(display_path), "criteria": []}
    if not path.is_file():
        validation.check(False, f"semantic target exists: {path}")
        result["profile"] = None
        result["criteria"].append({"criterion": "DOC-COMP-001", "status": "FAIL"})
        return result

    metadata: dict[str, Any] = {}
    text = path.read_text(encoding="utf-8")
    document: Any = None
    if path.suffix.lower() in {".yaml", ".yml"}:
        document = yaml.safe_load(text)
        if isinstance(document, dict):
            metadata = document
    elif text.startswith("---"):
        try:
            metadata = load_frontmatter(path)
        except (ValueError, yaml.YAMLError):
            metadata = {}

    profile_name = semantic_profile_for(path, metadata)
    profiles = catalog.get("profiles", {})
    profile = profiles.get(profile_name) if isinstance(profiles, dict) else None
    validation.check(
        isinstance(profile, dict),
        f"{result['path']}: semantic profile resolves ({profile_name or 'none'})",
    )
    result["profile"] = profile_name
    if not isinstance(profile, dict):
        result["criteria"].append({"criterion": "DOC-COMP-001", "status": "FAIL"})
        return result
    result["criteria"].append({"criterion": "DOC-COMP-001", "status": "PASS"})

    failures = 0
    for heading in profile.get("required_markdown", []):
        matched = bool(re.search(rf"^#+\s+.*\b{re.escape(str(heading))}\b", text, re.I | re.M))
        validation.check(matched, f"{result['path']}: required semantic section {heading}")
        failures += int(not matched)
    for concept in profile.get("required_concepts", []):
        matched = contains_concept(text, str(concept))
        validation.check(matched, f"{result['path']}: required semantic concept {concept}")
        failures += int(not matched)
    for key in profile.get("required_yaml", []):
        matched = nonempty(nested_value(document, str(key)))
        validation.check(matched, f"{result['path']}: required semantic field {key}")
        failures += int(not matched)

    item_key = profile.get("per_item")
    required_item_fields = profile.get("per_item_required", [])
    if item_key and isinstance(document, dict):
        items = document.get(item_key)
        validation.check(isinstance(items, list) and bool(items), f"{result['path']}: {item_key} contains entries")
        if not isinstance(items, list) or not items:
            failures += 1
        else:
            for position, item in enumerate(items, start=1):
                for key in required_item_fields:
                    matched = isinstance(item, dict) and nonempty(item.get(key))
                    validation.check(
                        matched,
                        f"{result['path']}: {item_key}[{position}] required field {key}",
                    )
                    failures += int(not matched)

    commands: list[str] = []
    command_documentation = text
    if profile_name == "Gate Specification" and isinstance(document, dict):
        for item in document.get("gates", []):
            if isinstance(item, dict):
                commands.extend(
                    command for command in item.get("operator_acceptance_procedure", [])
                    if isinstance(command, str)
                )
                guide = item.get("manual_verification_procedure")
                if isinstance(guide, str):
                    guide_path = path.parent / guide
                    if guide_path.is_file():
                        command_documentation += "\n" + guide_path.read_text(encoding="utf-8")
    command_results: list[dict[str, Any]] = []
    for command in commands:
        try:
            matched, command_result = command_interface_check(command, command_documentation)
        except (OSError, subprocess.SubprocessError) as error:
            matched = False
            command_result = {"command": command, "error": str(error)}
        command_results.append(command_result)
        validation.check(matched, f"{result['path']}: command interface, syntax, help, and exit documentation: {command}")
        failures += int(not matched)
    if command_results:
        result["command_validation"] = command_results

    for criterion in profile.get("criteria", []):
        if criterion == "DOC-COMP-001":
            continue
        status = "FAIL" if criterion == "DOC-COMP-002" and failures else "MANUAL_REVIEW"
        result["criteria"].append({"criterion": criterion, "status": status})
    result["status"] = "FAIL" if failures else "PASS_WITH_MANUAL_CRITERIA"
    return result


def coverage_report(catalog: dict[str, Any]) -> dict[str, Any]:
    procedures = catalog.get("procedure_references", {})
    criteria = catalog.get("criteria", {})
    return {
        "schema_version": 1,
        "authority": catalog.get("authority"),
        "catalog": str(SEMANTIC_PROFILE_PATH.relative_to(ROOT)),
        "criteria": [
            {
                "criterion": identifier,
                "coverage": definition.get("automation", "not_automated"),
                "validation_implementation": (
                    "scripts/validate_controlled_documents.py"
                    if definition.get("automation") != "manual"
                    else None
                ),
                "procedure_reference": [
                    procedures.get("publication"),
                    procedures.get("qualification"),
                ],
                "evidence_reference": definition.get("required_evidence"),
            }
            for identifier, definition in sorted(criteria.items())
        ],
    }


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
    parser = argparse.ArgumentParser(
        description="Validate structural and additive semantic controlled-document requirements."
    )
    parser.add_argument(
        "--semantic-path",
        action="append",
        default=[],
        metavar="PATH",
        help="validate one repository-relative document using its resolved semantic profile",
    )
    parser.add_argument(
        "--semantic-all",
        action="store_true",
        help="validate every registered semantic artifact (including Zeus domain artifacts)",
    )
    parser.add_argument(
        "--semantic-report",
        metavar="PATH",
        help="write machine-readable semantic results as JSON",
    )
    parser.add_argument(
        "--coverage-report",
        metavar="PATH",
        help="write the criterion automation coverage report as JSON",
    )
    parser.add_argument(
        "--synchronization-metadata",
        default="engineering/validation/implementation-synchronization.yaml",
        metavar="PATH",
        help="repository-relative implementation synchronization declarations",
    )
    parser.add_argument(
        "--synchronization",
        action="store_true",
        help="run the additive implementation synchronization validation layer",
    )
    parser.add_argument(
        "--synchronization-report",
        metavar="PATH",
        help="write the deterministic implementation synchronization report as JSON",
    )
    parser.add_argument(
        "--implementation-coverage",
        action="store_true",
        help="run the additive repository-wide implementation coverage layer",
    )
    parser.add_argument(
        "--implementation-coverage-policy",
        default="engineering/validation/implementation-coverage.yaml",
        metavar="PATH",
        help="repository-relative artifact discovery and classification policy",
    )
    parser.add_argument(
        "--implementation-coverage-report",
        metavar="PATH",
        help="write the deterministic implementation coverage report as JSON",
    )
    parser.add_argument(
        "--conformance",
        action="store_true",
        help="run the additive engineering contract conformance validation layer",
    )
    parser.add_argument(
        "--conformance-only",
        action="store_true",
        help="run only engineering contract conformance validation",
    )
    parser.add_argument(
        "--engineering-contracts",
        default="engineering/validation/engineering-contracts.yaml",
        metavar="PATH",
        help="repository-relative machine-readable engineering contract catalog",
    )
    parser.add_argument(
        "--conformance-report",
        metavar="PATH",
        help="write the canonical engineering conformance report as JSON",
    )
    parser.add_argument(
        "--assurance",
        action="store_true",
        help="run the additive engineering assurance validation layer",
    )
    parser.add_argument(
        "--assurance-only",
        action="store_true",
        help="run only engineering assurance validation",
    )
    parser.add_argument(
        "--engineering-properties",
        default="engineering/validation/engineering-properties.yaml",
        metavar="PATH",
        help="repository-relative machine-readable Engineering Assurance Catalog",
    )
    parser.add_argument(
        "--assurance-report",
        metavar="PATH",
        help="write the canonical Engineering Assurance Report as JSON",
    )
    args = parser.parse_args()
    validation = Validation()
    if args.assurance_only:
        args.assurance = True
        try:
            assurance = analyze_assurance(
                ROOT, load_assurance_catalog(ROOT / args.engineering_properties)
            )
        except (OSError, ValueError, SyntaxError, yaml.YAMLError) as error:
            validation.check(False, f"engineering assurance validation loads ({error})")
        else:
            validation.check(
                all(
                    item["determination"] == "ASSURED"
                    for item in assurance["assurance_determinations"]
                ),
                "declared engineering properties are assured",
            )
            if args.assurance_report:
                report_path = ROOT / args.assurance_report
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(canonical_assurance_report(assurance), encoding="utf-8")
                validation.check(True, f"assurance report written: {report_path}")
        return validation.finish()
    if args.conformance_only:
        args.conformance = True
        try:
            conformance = analyze_conformance(
                ROOT, load_contracts(ROOT / args.engineering_contracts)
            )
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(False, f"conformance validation loads ({error})")
        else:
            validation.check(
                not conformance["invariant_failures"],
                "documented engineering contracts conform to discovered implementation",
            )
            if args.conformance_report:
                report_path = ROOT / args.conformance_report
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    canonical_conformance_report(conformance), encoding="utf-8"
                )
                validation.check(
                    True, f"conformance report written: {report_path}"
                )
        return validation.finish()
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

    semantic_results: list[dict[str, Any]] = []
    if args.semantic_path or args.semantic_all or args.coverage_report:
        try:
            catalog = load_semantic_catalog()
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(False, f"semantic profile catalog loads ({error})")
            catalog = {}
        else:
            validation.check(
                catalog.get("authority") == "SPEC-0001",
                "semantic profile catalog delegates to SPEC-0001",
            )
            criteria = catalog.get("criteria", {})
            profiles = catalog.get("profiles", {})
            validation.check(isinstance(criteria, dict) and bool(criteria), "semantic criterion catalog is non-empty")
            validation.check(isinstance(profiles, dict) and bool(profiles), "semantic profile catalog is non-empty")
            if isinstance(criteria, dict):
                validation.check(
                    all(
                        isinstance(definition, dict)
                        and definition.get("identifier") == identifier
                        for identifier, definition in criteria.items()
                    ),
                    "semantic criterion identifiers agree with catalog keys",
                )
            if isinstance(profiles, dict) and isinstance(criteria, dict):
                for profile_name, profile in profiles.items():
                    references = profile.get("criteria", []) if isinstance(profile, dict) else []
                    validation.check(
                        bool(references) and all(reference in criteria for reference in references),
                        f"semantic profile {profile_name} criterion references resolve",
                    )
                    validation.check(
                        isinstance(profile, dict)
                        and bool(
                            profile.get("required_markdown")
                            or profile.get("required_concepts")
                            or profile.get("required_yaml")
                        )
                        and all(nonempty(profile.get(dimension)) for dimension in PROFILE_DIMENSIONS),
                        f"semantic profile {profile_name} defines every semantic dimension",
                    )

        targets = [ROOT / supplied for supplied in args.semantic_path]
        if args.semantic_all:
            semantic_roots = [DOCS, ROOT / "engineering"]
            for semantic_root in semantic_roots:
                if not semantic_root.exists():
                    continue
                for path in semantic_root.rglob("*"):
                        if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml"}:
                            metadata: dict[str, Any] = {}
                        if path.suffix.lower() in {".yaml", ".yml"}:
                            try:
                                loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
                            except (OSError, yaml.YAMLError):
                                loaded = None
                            if isinstance(loaded, dict):
                                metadata = loaded
                        relative = str(path.relative_to(ROOT)).lower()
                        registered_domain_path = (
                            path.name.lower()
                            in {"roadmap.md", "gate-specification.yaml", "immutable-wop.yaml"}
                            or (path.name.lower() == "verification.md" and "/gates/" in relative)
                        )
                        if metadata.get("semantic_validation_profile") or registered_domain_path:
                            targets.append(path)
        for target in sorted(set(targets)):
            semantic_results.append(semantic_validate_path(validation, target, catalog))

        if args.coverage_report:
            report_path = ROOT / args.coverage_report
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(coverage_report(catalog), indent=2) + "\n",
                encoding="utf-8",
            )
            validation.check(True, f"coverage report written: {report_path}")

    if args.semantic_report:
        report_path = ROOT / args.semantic_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {"schema_version": 1, "results": semantic_results},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        validation.check(True, f"semantic report written: {report_path}")
    if args.synchronization or args.synchronization_report:
        metadata_path = ROOT / args.synchronization_metadata
        try:
            synchronization = analyze_synchronization(
                ROOT, load_synchronization_metadata(metadata_path)
            )
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(False, f"synchronization validation loads ({error})")
        else:
            validation.check(
                all(
                    item["drift_status"] in {
                        "PASS",
                        "OUT_OF_SYNC",
                        "IMPLEMENTATION_CHANGED",
                        "DOCUMENT_CHANGED",
                        "MISSING_ARTIFACT",
                        "SUPERSEDED",
                        "UNKNOWN",
                    }
                    for item in synchronization["synchronized_artifacts"]
                ),
                "synchronization drift classifications are recognized",
            )
            validation.check(
                not any(
                    item["drift_status"] in {
                        "OUT_OF_SYNC",
                        "IMPLEMENTATION_CHANGED",
                        "DOCUMENT_CHANGED",
                        "MISSING_ARTIFACT",
                        "UNKNOWN",
                    }
                    for item in synchronization["synchronized_artifacts"]
                ),
                "declared documentation and implementation are synchronized",
            )
            if args.synchronization_report:
                report_path = ROOT / args.synchronization_report
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    json.dumps(synchronization, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                validation.check(
                    True,
                    f"synchronization report written: {report_path}",
                )
    if args.implementation_coverage or args.implementation_coverage_report:
        try:
            implementation_coverage = analyze_implementation_coverage(
                ROOT,
                load_synchronization_metadata(ROOT / args.synchronization_metadata),
                load_coverage_policy(ROOT / args.implementation_coverage_policy),
            )
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(False, f"implementation coverage validation loads ({error})")
        else:
            states = {
                item["coverage_state"]
                for item in implementation_coverage[
                    "discovered_implementation_artifacts"
                ]
            }
            validation.check(
                states
                <= {
                    "synchronized",
                    "undocumented",
                    "orphaned_declaration",
                    "obsolete_declaration",
                    "excluded_by_policy",
                    "external_dependency",
                    "unknown_classification",
                },
                "implementation coverage classifications are recognized",
            )
            metrics = implementation_coverage["coverage_metrics"]
            validation.check(
                metrics["undocumented_artifacts"] == 0,
                "all mandatory implementation artifacts have synchronization declarations",
            )
            validation.check(
                metrics["orphan_declarations"] == 0,
                "all synchronization declarations resolve to discovered endpoints",
            )
            validation.check(
                not implementation_coverage["synchronization_gaps"],
                "implementation coverage has no unknown or undocumented gaps",
            )
            if args.implementation_coverage_report:
                report_path = ROOT / args.implementation_coverage_report
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    canonical_coverage_report(implementation_coverage),
                    encoding="utf-8",
                )
                validation.check(
                    True,
                    f"implementation coverage report written: {report_path}",
                )
    if args.conformance or args.conformance_report:
        try:
            conformance = analyze_conformance(
                ROOT, load_contracts(ROOT / args.engineering_contracts)
            )
        except (OSError, ValueError, yaml.YAMLError) as error:
            validation.check(False, f"conformance validation loads ({error})")
        else:
            validation.check(
                not conformance["invariant_failures"],
                "documented engineering contracts conform to discovered implementation",
            )
            validation.check(
                not conformance["incompatible_implementation"],
                "no incompatible engineering implementation is discovered",
            )
            if args.conformance_report:
                report_path = ROOT / args.conformance_report
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    canonical_conformance_report(conformance), encoding="utf-8"
                )
                validation.check(
                    True,
                    f"conformance report written: {report_path}",
                )
    if args.assurance or args.assurance_report:
        try:
            assurance = analyze_assurance(
                ROOT, load_assurance_catalog(ROOT / args.engineering_properties)
            )
        except (OSError, ValueError, SyntaxError, yaml.YAMLError) as error:
            validation.check(False, f"engineering assurance validation loads ({error})")
        else:
            validation.check(
                all(
                    item["determination"] == "ASSURED"
                    for item in assurance["assurance_determinations"]
                ),
                "declared engineering properties are assured",
            )
            if args.assurance_report:
                report_path = ROOT / args.assurance_report
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(canonical_assurance_report(assurance), encoding="utf-8")
                validation.check(True, f"assurance report written: {report_path}")
    return validation.finish()


if __name__ == "__main__":
    sys.exit(main())
