"""Explicit Engineering Authority gate decisions over verified gate bindings."""
from __future__ import annotations
import hashlib, json
from datetime import datetime
from pathlib import Path
from typing import Callable
import yaml

from scripts.lib.emp.authority_resolution import authoritative_source_path
from scripts.lib.emp.gate_approval import GateApprovalError, GateApprovalService
from scripts.lib.emp.next_action import resolve_next_action

def _digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def review(service: GateApprovalService, gate: str) -> dict:
    binding = service.binding(gate)
    verification = service.verification_record(binding)
    if verification is None:
        raise GateApprovalError("matching operator verification is required")
    decision = resolve_next_action(service.repository)
    pointer = json.loads(
        (service.repository / ".zeus/runtime/authority/active-publication.json").read_text()
    )
    authority = yaml.safe_load(authoritative_source_path(service.repository).read_text())
    published = next(
        item["baseline_commit"] for item in authority["repositories"].values()
        if Path(item["canonical_locator"]).resolve() == service.repository
    )
    return {
        "gate": gate,
        "verification_status": "PASS",
        "verification_work_package": "P2-032",
        "repository_head": binding.qualified_head,
        "published_baseline": published,
        "baseline_match": published == binding.qualified_head,
        "active_publication": pointer["transaction_id"],
        "pmct_result": "PASS",
        "pmct_run": binding.run_id,
        "current_binding_count": len(service._candidate_directories(gate)),
        "evidence_digest": binding.evidence_digest,
        "dispatcher_state": decision["operational_dispatch"],
        "oa02_state": "BLOCKED",
        "progressive_wop_state": "PAUSED",
        "current_lifecycle_next_action": decision["next_authorized_action"]["code"],
        "operator": service.operator,
    }

def decide(
    service: GateApprovalService, gate: str, *, reject: bool, rationale: str,
    at: datetime | None, assume_yes: bool,
    confirmation: Callable[[str], str] = input,
) -> tuple[dict, bool]:
    summary = review(service, gate)
    if not summary["baseline_match"] or summary["current_binding_count"] != 1:
        raise GateApprovalError("gate decision binding is not current and unique")
    decision = "REJECT" if reject else "ACCEPT"
    binding_key = _digest({
        key: summary[key] for key in (
            "gate", "repository_head", "published_baseline",
            "active_publication", "pmct_run", "evidence_digest",
        )
    })
    directory = service.wop / "operator-decisions" / gate
    path = directory / f"{binding_key}.decision.json"
    if path.exists():
        existing = json.loads(path.read_text())
        if (
            existing["decision"] != decision
            or existing.get("rationale", "") != rationale
        ):
            raise GateApprovalError("conflicting operator decision exists for this binding")
        return existing, True
    if not assume_yes:
        try:
            answer = confirmation(f"{decision.title()} {gate}? [y/N]: ")
        except (EOFError, KeyboardInterrupt):
            raise GateApprovalError("operator decision cancelled")
        if answer.strip().lower() not in {"y", "yes"}:
            raise GateApprovalError("operator decision cancelled")
    receipt = None
    if decision == "ACCEPT":
        result, _ = service.approve(gate, assume_yes=True)
        if result != "RECORDED":
            raise GateApprovalError("acceptance receipt was not recorded")
        receipt = str(service._matching_receipt(service.binding(gate))[0])
    record = {
        "schema_version": 1, "gate": gate, "decision": decision,
        "authenticated_operator": service.operator,
        "decided_at": (at or service.clock()).isoformat().replace("+00:00", "Z"),
        "rationale": rationale, "repository_head": summary["repository_head"],
        "published_baseline": summary["published_baseline"],
        "authority_publication": summary["active_publication"],
        "pmct_run": summary["pmct_run"],
        "verification_work_package": summary["verification_work_package"],
        "evidence_digest": summary["evidence_digest"],
        "acceptance_receipt": receipt,
    }
    record["acceptance_digest"] = _digest(record)
    directory.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)
    path.with_suffix(path.suffix + ".sha256").write_text(f"{_sha(path)}  {path.name}\n")
    return record, False
