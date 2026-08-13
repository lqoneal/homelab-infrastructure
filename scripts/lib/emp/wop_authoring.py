"""Canonical Phase 1 mission-source to Development WOP authoring.

This is deliberately a source transformation layer over the existing WOP
schema, validator, repository resolver, and packaging service.  It does not
submit, admit, or create lifecycle state.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.repository_identity import RepositoryIdentityError, canonicalize_metadata, resolve
from scripts.lib.emp.wop_packaging import lint_source, markdown_template, source_digest
from scripts.lib.emp.wop_schema import REQUIRED_FIELDS
from scripts.lib.emp.wop_validation import validate_source


class AuthoringError(ValueError):
    pass


TEMPLATE = "docs/templates/TPL-0001-ENGINEERING_WORK_ORDER_TEMPLATE.md"
CONTEXT = "engineering/docs/architecture/OPERATION-BETA-AUTHORITY-MODEL.md"
REFERENCES = ["PROC-0001@2.11", "TPL-0001@1.7", "STD-0000", "STD-0001", "STD-0002", "STD-0003", "STD-0004"]
SECTION_NAMES = [
    "purpose_and_expected_outcome", "mission_classification", "governing_references", "scope",
    "explicit_authority", "prohibited_activities", "dependencies_and_entry_criteria", "deliverables",
    "execution_sequence", "success_and_acceptance_criteria", "validation_profile",
    "publication_and_synchronization", "stop_resume_and_escalation", "completion_report_requirement",
]
PLACEHOLDER = re.compile(r"<[^>]+>|\b(?:TODO|TBD|FIXME|EXAMPLE_ONLY)\b|Complete the .* section", re.I)


def _compact(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.strip().split())
    if isinstance(value, list):
        values = [_compact(item) for item in value]
        return sorted(values, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, Mapping):
        return {str(key): _compact(value[key]) for key in sorted(value)}
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_compact(value), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _text(value: Any, default: str = "") -> str:
    if value in (None, "", []):
        return default
    if isinstance(value, list):
        return "; ".join(_text(item) for item in value)
    return str(value).strip()


def _load_source(path: Path) -> dict[str, Any]:
    if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
        raise AuthoringError("unsupported mission source; use YAML or JSON structured mission source")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise AuthoringError(f"unreadable mission source: {error}") from error
    if not isinstance(value, Mapping) or not isinstance(value.get("mission"), Mapping):
        raise AuthoringError("mission source must contain a mission mapping")
    return dict(value)


def _atomic_write(path: Path, content: str) -> bool:
    path = path.resolve()
    if path.exists():
        if path.read_text(encoding="utf-8") == content:
            return True
        raise AuthoringError(f"identifier/output collision: existing output differs at {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise
    return False


def author(source: Path, repository_root: Path, output: Path | None = None) -> dict[str, Any]:
    raw = _load_source(source)
    mission = dict(raw["mission"])
    operation = str(raw.get("operation", mission.get("operation", ""))).upper()
    if operation != "BETA":
        raise AuthoringError("Operation Beta is required; Operational Alpha is not a fallback context")
    if any("ALPHA" in str(value).upper() for value in (raw, mission)):
        raise AuthoringError("Operational Alpha authority or context is not accepted")
    repository = mission.get("repository") or raw.get("repository")
    identity = resolve(repository_root)
    try:
        canonical_path = canonicalize_metadata({"repository_identity": repository}, repository_root)[0]["repository_identity"]
    except RepositoryIdentityError as error:
        raise AuthoringError(str(error)) from error
    if canonical_path != identity["canonical_repository_identity"]:
        raise AuthoringError("repository identity could not be resolved")
    title = _text(mission.get("title"))
    objective = _text(mission.get("objective"))
    if not title or not objective:
        raise AuthoringError("mission title and objective are required")
    scope = mission.get("scope") or {}
    if not isinstance(scope, Mapping):
        raise AuthoringError("mission scope must be a mapping with include/exclude")
    include = scope.get("include") or []
    exclude = scope.get("exclude") or []
    if not include:
        raise AuthoringError("mission scope.include is required")
    acceptance = mission.get("acceptance_criteria") or []
    validation = mission.get("validation") or []
    evidence = mission.get("evidence") or []
    restrictions = mission.get("restrictions") or []
    normalized = {"schema_version": raw.get("schema_version", "1.0"), "operation": "BETA", "mission": {
        "title": title, "objective": objective, "repository": str(repository), "scope": scope,
        "restrictions": restrictions, "acceptance_criteria": acceptance, "validation": validation, "evidence": evidence,
    }}
    context_digest = _digest({"operation": "BETA", "repository": identity, "context": source_digest(repository_root / CONTEXT)})
    template_path = repository_root / TEMPLATE
    if not template_path.is_file():
        raise AuthoringError(f"authoritative Development template unavailable: {template_path}")
    template_digest = source_digest(template_path)
    content_digest = _digest({"source": normalized, "context": context_digest, "template": template_digest})
    short = content_digest[:16].upper()
    wop_id = f"WOP-BETA-{short}"
    mission_id = f"MISSION-BETA-{short}"
    metadata: dict[str, Any] = {
        "wop_id": wop_id, "mission_id": mission_id, "title": title, "objective": objective,
        "scope": [f"INCLUDE: {_text(include)}", f"EXCLUDE: {_text(exclude, 'None')}"],
        "dependencies": ["Operation Beta context resolved", "canonical repository identity resolved"],
        "execution_mode": "DEVELOPMENT", "governance_authority": "Engineering Governance",
        "repository_identity": identity["canonical_repository_identity"], "effect_profile": "DEVELOPMENT-AUTHORING-NONPRODUCTION",
        "protected_baselines": ["OA-v1.0.0", "OB-PLAN-v1.0.0"], "gates": ["P1-G1", "VALIDATE", "QUALIFY", "REVIEW"],
        "qualification_requirements": list(validation) or ["focused validation passes", "Zeus-specific inspection passes"],
        "completion_requirements": list(evidence) or ["verification evidence", "operator review"],
        "approval_authorized_lifecycle_state": "Active", "authoritative_references": REFERENCES,
        "execution_package_authority_node_id": "work-package", "execution_package_authorization_decision_record": "ADR-REVIEW-REQUIRED",
    }
    sections = {
        "purpose_and_expected_outcome": f"Purpose: {objective}\nExpected outcome: a validated Development WOP candidate; no submission or admission is performed.",
        "mission_classification": "Category B — Local Engineering Environment Work; Operation Beta development context.",
        "governing_references": "; ".join(REFERENCES),
        "scope": f"In scope: {_text(include)}\nOut of scope: {_text(exclude, 'publication, admission, execution, EOS synchronization')}",
        "explicit_authority": "Authoring and validation only; exact next submission command may be reported but not invoked.",
        "prohibited_activities": "Mission submission, admission, execution authority, dispatch, publication, push, merge, EOS synchronization.",
        "dependencies_and_entry_criteria": "Operation Beta, repository identity, active Development template, and controlled schema resolve successfully.",
        "deliverables": "Canonical WOP source, traceability record, lint/validation/readiness evidence, and completion report.",
        "execution_sequence": "Normalize source; resolve context; derive identities; apply template; lint; validate; determine readiness; stop for review.",
        "success_and_acceptance_criteria": _text(acceptance, "Canonical output has no placeholders and reports ADMISSION_READY."),
        "validation_profile": _text(validation, "Focused tests, WOP validation, Registry, controlled-document, and platform checks pass."),
        "publication_and_synchronization": "No publication and no EOS synchronization under P1-G1.",
        "stop_resume_and_escalation": "Stop at AWAITING_OPERATOR_REVIEW; request new authority for any downstream lifecycle action.",
        "completion_report_requirement": "Completion Report and reproducible Zeus-specific verification commands are required.",
    }
    metadata.update({f"sections_{name}": value for name, value in sections.items()})
    rendered = markdown_template(metadata)
    blockers = []
    if PLACEHOLDER.search(rendered):
        blockers.append("unresolved template placeholder")
    generated = Path(output) if output else source.with_name(f"{wop_id}.md")
    replayed = _atomic_write(generated, rendered)
    trace = {
        "result": "PASS", "readiness": "ADMISSION_READY" if not blockers else "BLOCKED", "wop_id": wop_id, "mission_id": mission_id,
        "operation": "BETA", "repository": identity, "source": {"path": str(source.resolve()), "digest": source_digest(source), "normalized_digest": _digest(normalized)},
        "template": {"path": str(template_path), "digest": template_digest, "identity": "TPL-0001@2.0"},
        "context": {"identity": "Operation Beta", "digest": context_digest}, "output_digest": hashlib.sha256(rendered.encode()).hexdigest(),
        "source_to_output": {"mission.title": "title", "mission.objective": "objective", "mission.scope": "sections_scope", "mission.acceptance_criteria": "sections_success_and_acceptance_criteria", "mission.validation": "qualification_requirements/sections_validation_profile", "mission.evidence": "completion_requirements"},
        "lint": {"result": "PASS" if not lint_source(generated, metadata) else "FAIL", "issues": lint_source(generated, metadata)},
        "validation": validate_source(generated, repository_root=repository_root).as_dict(), "blockers": blockers,
        "next_action": f"zeus submit {generated}",
    }
    trace_path = generated.with_suffix(generated.suffix + ".traceability.json")
    _atomic_write(trace_path, json.dumps(trace, indent=2, sort_keys=True) + "\n")
    return {"result": "PASS" if not blockers else "BLOCKED", "output": str(generated.resolve()), "traceability": str(trace_path.resolve()), "replayed": replayed, **trace}


def inspect(path: Path, repository_root: Path) -> dict[str, Any]:
    trace_path = path.with_suffix(path.suffix + ".traceability.json")
    if not trace_path.is_file():
        raise AuthoringError(f"traceability record not found: {trace_path}")
    try:
        value = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuthoringError(f"invalid traceability record: {error}") from error
    if value.get("output_digest") != hashlib.sha256(path.read_bytes()).hexdigest():
        value["readiness"] = "BLOCKED"
        value.setdefault("blockers", []).append("traceability output digest mismatch")
    return value
