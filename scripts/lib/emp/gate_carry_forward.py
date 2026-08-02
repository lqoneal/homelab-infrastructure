#!/usr/bin/env python3
"""Integrity-protected carry-forward of accepted gates across safe successors."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp.runtime_paths import runtime_path


PROTECTED_PATHS = {
    "scripts/lib/emp/gate_approval.py": "OA01_OPERATOR_EVIDENCE",
    "scripts/lib/emp/gate_decision.py": "OA01_OPERATOR_DECISION",
    "scripts/lib/emp/authority_resolution.py": "OA01_AUTHORITY_BINDING",
    "scripts/lib/emp/authority_publication.py": "OA01_AUTHORITY_PUBLICATION",
    "engineering/tests/zeus-operational-alpha/lib/pmct.py": "OA01_PMCT_QUALIFICATION",
    "engineering/tests/zeus-operational-alpha/PMCT-CONTRACT.md": "OA01_PMCT_CONTRACT",
}
PROTECTED_ZEUS_TOKENS = (
    "verify OA-01",
    "accept OA-01",
    "GateApprovalService",
    "gate_decision",
    "OA01_VERIFICATION",
    "OA01_ACCEPTANCE",
)


class GateCarryForwardError(RuntimeError):
    """A gate milestone cannot safely be carried forward."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise GateCarryForwardError(result.stderr.strip() or "Git inspection failed")
    return result.stdout.strip()


def record_path(root: Path, gate: str = "OA-01") -> Path:
    return runtime_path(root, "gate-carry-forward") / f"{gate}.json"


def assess_changes(root: Path, predecessor: str, successor: str) -> dict[str, Any]:
    if subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", predecessor, successor],
        check=False,
    ).returncode:
        raise GateCarryForwardError("accepted baseline is not an ancestor of successor")
    changed = tuple(
        line for line in _git(root, "diff", "--name-only", predecessor, successor).splitlines()
        if line
    )
    affected: list[str] = []
    for path in changed:
        criterion = PROTECTED_PATHS.get(path)
        if criterion:
            affected.append(criterion)
        if path == "scripts/zeus":
            patch = _git(root, "diff", predecessor, successor, "--", path)
            if any(token in patch for token in PROTECTED_ZEUS_TOKENS):
                affected.append("OA01_OPERATOR_INTERFACE")
    return {
        "changed_files": list(changed),
        "affected_oa01_criteria": sorted(set(affected)),
        "assessment_result": "AFFECTED" if affected else "UNAFFECTED",
    }


def create_record(root: Path, service: Any, binding: Any) -> tuple[dict[str, Any], bool]:
    receipts = service._valid_receipts("OA-01")
    ancestors = [
        (path, fields) for path, fields in receipts
        if not subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor",
             fields.get("approved_head", ""), binding.qualified_head],
            check=False, capture_output=True,
        ).returncode
    ]
    if not ancestors:
        raise GateCarryForwardError("no integrity-valid accepted OA-01 ancestor exists")
    prior_path, prior = ancestors[-1]
    assessment = assess_changes(root, prior["approved_head"], binding.qualified_head)
    pointer = json.loads(
        runtime_path(root, "authority", "active-publication.json").read_text()
    )
    material = {
        "schema_version": 1,
        "gate": "OA-01",
        "prior_accepted_receipt": str(prior_path),
        "prior_accepted_receipt_digest": hashlib.sha256(prior_path.read_bytes()).hexdigest(),
        "prior_accepted_publication": prior.get("authority_publication", "HISTORICAL"),
        "prior_accepted_baseline": prior["approved_head"],
        "successor_publication": pointer["transaction_id"],
        "successor_baseline": binding.qualified_head,
        "successor_pmct_run_id": binding.run_id,
        "successor_pmct_evidence_digest": binding.evidence_digest,
        "change_scope_assessment": assessment["changed_files"],
        "affected_gate_analysis": assessment["affected_oa01_criteria"],
        "impact_assessment": {
            "result": assessment["assessment_result"],
            "affected_acceptance_criteria": assessment["affected_oa01_criteria"],
            "justification": (
                "Successor changes do not modify an OA-01-controlled capability, "
                "contract, evidence basis, assumption, or safety property."
                if not assessment["affected_oa01_criteria"] else
                "Successor changes modify an OA-01-controlled acceptance basis."
            ),
        },
        "carry_forward_decision": (
            "REVALIDATION_REQUIRED"
            if assessment["affected_oa01_criteria"] else "CARRY_FORWARD"
        ),
        "oa01_revalidation_required": bool(assessment["affected_oa01_criteria"]),
        "assessed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    # `integrity_digest` is the controlled decision digest.  Assessment time is
    # deliberately excluded from replay comparison, but remains integrity bound.
    material["integrity_digest"] = _sha256_bytes(_canonical(material))
    path = record_path(root)
    if path.is_file():
        existing = json.loads(path.read_text())
        stable = {
            k: v for k, v in existing.items()
            if k not in {"assessed_at", "integrity_digest"}
        }
        wanted = {
            k: v for k, v in material.items()
            if k not in {"assessed_at", "integrity_digest"}
        }
        if stable == wanted:
            return existing, True
        if existing.get("successor_baseline") == binding.qualified_head:
            raise GateCarryForwardError("conflicting carry-forward record exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(json.dumps(material, indent=2, sort_keys=True).encode() + b"\n")
    temporary.replace(path)
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
    )
    return material, False


def resolve_record(root: Path, binding: Any) -> dict[str, Any] | None:
    path = record_path(root)
    checksum = path.with_suffix(path.suffix + ".sha256")
    if not path.is_file() or not checksum.is_file():
        return None
    if checksum.read_text().split()[0] != hashlib.sha256(path.read_bytes()).hexdigest():
        return None
    try:
        value = json.loads(path.read_text())
        digest = value.pop("integrity_digest")
    except (OSError, json.JSONDecodeError, KeyError):
        return None
    if digest != _sha256_bytes(_canonical(value)):
        return None
    value["integrity_digest"] = digest
    if (
        value.get("gate") != binding.gate
        or value.get("successor_baseline") != binding.qualified_head
        or value.get("successor_pmct_run_id") != binding.run_id
        or value.get("successor_pmct_evidence_digest") != binding.evidence_digest
        or value.get("carry_forward_decision") != "CARRY_FORWARD"
        or value.get("oa01_revalidation_required") is not False
    ):
        return None
    prior = Path(str(value.get("prior_accepted_receipt", "")))
    if not prior.is_file() or hashlib.sha256(prior.read_bytes()).hexdigest() != value.get(
        "prior_accepted_receipt_digest"
    ):
        return None
    try:
        pointer = json.loads(
            runtime_path(root, "authority", "active-publication.json").read_text()
        )
        if pointer.get("transaction_id") != value.get("successor_publication"):
            return None
        assessment = assess_changes(
            root,
            str(value.get("prior_accepted_baseline", "")),
            binding.qualified_head,
        )
    except (OSError, json.JSONDecodeError, GateCarryForwardError):
        return None
    if (
        assessment["changed_files"] != value.get("change_scope_assessment")
        or assessment["affected_oa01_criteria"]
        != value.get("affected_gate_analysis")
        or assessment["assessment_result"]
        != value.get("impact_assessment", {}).get("result")
    ):
        return None
    return value
