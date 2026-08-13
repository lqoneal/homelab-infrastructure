"""Read-only recognition of canonical WOP/EENS maturity inputs."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping
import yaml

class MaturityRecognitionError(ValueError):
    """The maturity input chain is missing, stale, or contradictory."""

WOP = "docs/specifications/SPEC-0015-WOP-PACKAGE-MATURITY-ROADMAP.md"
EENS = "docs/specifications/SPEC-0016-EENS-MATURITY-ROADMAP.md"
INTEGRATION = "engineering/convergence/engineering-system-convergence/gates/C18-system-convergence-roadmap/evidence/QUALIFIED-WOP-EENS-CANONICAL-INTEGRATION-001.yaml"
QUALIFICATION = "engineering/convergence/engineering-system-convergence/gates/C18-system-convergence-roadmap/evidence/QUALIFIED-WOP-EENS-CANONICAL-QUALIFICATION-002.yaml"
C06_REVIEW = "engineering/convergence/engineering-system-convergence/gates/C06-wop-and-execution-contract/evidence/REBASED-C06-WOP-EENS-FOUNDATIONAL-DEVELOPMENT-BOUNDARY-REVIEW.yaml"
ROADMAP = "engineering/convergence/engineering-system-convergence/roadmap.yaml"
ROADMAP_REFERENCE = "engineering/convergence/engineering-system-convergence/ESC-ROADMAP-001.md"
STATE = "engineering/convergence/engineering-system-convergence/STATE.yaml"
PROJECT_STATE = "docs/project/PROJ-0001-PROJECT_STATE.md"
BINDING_MANIFEST = "engineering/convergence/engineering-system-convergence/binding-manifest.yaml"

def _load(root: Path, relative: str) -> tuple[dict[str, Any], str]:
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file() or path.is_symlink():
        raise MaturityRecognitionError(f"authoritative maturity source unavailable: {relative}")
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md" and text.startswith("---\n"):
            text = text.split("\n---\n", 1)[0][4:]
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise MaturityRecognitionError(f"malformed maturity source: {relative}: {error}") from error
    if not isinstance(value, Mapping):
        raise MaturityRecognitionError(f"maturity source must be a mapping: {relative}")
    return dict(value), hashlib.sha256(path.read_bytes()).hexdigest()

def resolve(repository_root: Path | str) -> dict[str, Any]:
    """Resolve maturity provenance without promoting downstream authority."""
    root = Path(repository_root).resolve()
    wop, wop_digest = _load(root, WOP)
    eens, eens_digest = _load(root, EENS)
    integration, integration_digest = _load(root, INTEGRATION)
    qualification, qualification_digest = _load(root, QUALIFICATION)
    review, review_digest = _load(root, C06_REVIEW)
    roadmap, roadmap_digest = _load(root, ROADMAP)
    roadmap_reference, roadmap_reference_digest = _load(root, ROADMAP_REFERENCE)
    state, state_digest = _load(root, STATE)
    project_state, project_state_digest = _load(root, PROJECT_STATE)
    manifest, _ = _load(root, BINDING_MANIFEST)
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise MaturityRecognitionError("canonical binding manifest sources are missing")
    for entry in sources:
        if not isinstance(entry, Mapping) or not entry.get("path") or not entry.get("sha256"):
            raise MaturityRecognitionError("canonical binding manifest contains an invalid source entry")
        path = root / str(entry["path"])
        if not path.is_file() or path.is_symlink():
            raise MaturityRecognitionError(f"authoritative binding source unavailable: {entry.get('path')}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise MaturityRecognitionError(f"authoritative binding digest mismatch: {entry['path']}")
    roadmap_id = roadmap.get("roadmap_id")
    if roadmap_id != "ESC-ROADMAP-001" or roadmap.get("classification") != "AUTHORITATIVE_EXECUTABLE_ROADMAP":
        raise MaturityRecognitionError("canonical roadmap identity or classification is invalid")
    if roadmap_reference.get("document_id") != roadmap_id or roadmap_reference.get("status") != "Active":
        raise MaturityRecognitionError("canonical roadmap reference is not active")
    if state.get("roadmap_id") != roadmap_id or not isinstance(state.get("next_authorized_action"), str) or not state["next_authorized_action"].strip():
        raise MaturityRecognitionError("canonical roadmap state is conflicting or stale")
    approval = str(project_state.get("approval_status", "")).upper()
    if approval != "APPROVED":
        raise MaturityRecognitionError("canonical roadmap approval is not approved")
    adoption = str(roadmap_reference.get("status", "")).upper()
    executable = (
        roadmap.get("classification") == "AUTHORITATIVE_EXECUTABLE_ROADMAP"
        and state.get("executable_qualification", {}).get("result") == "PASS"
        and state.get("executable_qualification", {}).get("executable") is True
    )
    if not executable:
        raise MaturityRecognitionError("canonical roadmap is not executable")
    provenance = integration.get("source_provenance")
    if not isinstance(provenance, list):
        raise MaturityRecognitionError("C18 integration source provenance is missing")
    by_id = {item.get("id"): item for item in provenance if isinstance(item, Mapping)}
    expected_qualifications = {
        "SPEC-0015": "WOP-Q-01..WOP-Q-12-PASS",
        "SPEC-0016": "EENS-Q-01..EENS-Q-10-PASS",
    }
    for identity, path, actual in (("SPEC-0015", WOP, wop_digest), ("SPEC-0016", EENS, eens_digest)):
        entry = by_id.get(identity)
        if (not isinstance(entry, Mapping) or entry.get("path") != path
                or entry.get("sha256") != actual
                or entry.get("qualification") != expected_qualifications[identity]):
            raise MaturityRecognitionError(f"C18 provenance digest mismatch: {identity}")
    if integration.get("roadmap_id") != "ESC-ROADMAP-001":
        raise MaturityRecognitionError("C18 integration is not bound to ESC-ROADMAP-001")
    if qualification.get("roadmap", {}).get("roadmap_id") != "ESC-ROADMAP-001" or qualification.get("status") != "PASS":
        raise MaturityRecognitionError("C18 canonical qualification is not a PASS for ESC-ROADMAP-001")
    if review.get("decision") != "ACCEPT_REBASED_C06_BOUNDARY_AND_PERSIST_REVIEW":
        raise MaturityRecognitionError("accepted C06 boundary review is not resolvable")
    status = str(integration.get("status", "")).upper()
    authority = str(integration.get("execution_authority", "")).upper()
    accepted = status in {"ACCEPTED", "PUBLISHED"} and authority != "SEPARATE_AUTHORITY_REQUIRED"
    blockers = [] if accepted else ["C18_INTEGRATION_REMAINS_DRAFT_OR_SEPARATE_AUTHORITY_REQUIRED"]
    return {
        "result": "PASS", "projection": "CANONICAL_WOP_EENS_MATURITY_RECOGNITION",
        "roadmap": {"id": roadmap_id, "role": "CURRENT_CANONICAL_ENGINEERING_ROADMAP", "approval": approval, "adoption": adoption, "executable": executable,
                    "path": ROADMAP, "sha256": roadmap_digest, "state_sha256": state_digest,
                    "reference_sha256": roadmap_reference_digest, "project_state_sha256": project_state_digest},
        "wop": {"path": WOP, "sha256": wop_digest, "qualification": by_id["SPEC-0015"]["qualification"], "recognized": True},
        "eens": {"path": EENS, "sha256": eens_digest, "qualification": by_id["SPEC-0016"]["qualification"], "recognized": True},
        "integration": {"path": INTEGRATION, "sha256": integration_digest, "status": status, "recognized": True, "accepted": accepted},
        "qualification": {"path": QUALIFICATION, "sha256": qualification_digest, "status": "PASS", "recognized": True},
        "c06_review": {"path": C06_REVIEW, "sha256": review_digest, "consumed": True},
        "blockers": blockers, "next_authorized_action": state["next_authorized_action"],
        "authority": {"c18_separate_authority_required": not accepted, "cr48_execution_authorized": False, "c06_advancement_performed": False}, "read_only": True,
    }
