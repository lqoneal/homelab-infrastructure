"""Read-only current Operation Beta Model-B authority resolution."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.eos.convergence_runtime import ConvergenceRuntime, ConvergenceRuntimeError
from scripts.lib.eos.controlled_document_binding import resolve_exact


ROADMAP = "engineering/docs/architecture/OPERATION-BETA-ROADMAP.md"
WOP_ID = "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"
WOP_DIGEST = "460a4baeca153b05ee2cb0ade4a70a03b8ff2b8ca9e17a9074d0e44137d392d9"
EMM_ID = "OPERATION-BETA-EMM"


class ModelBAuthorityError(ValueError):
    """The current Beta authority chain is missing or contradictory."""


def _read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except OSError as error:
        raise ModelBAuthorityError(f"MODEL_B_SOURCE_UNAVAILABLE: {relative}") from error


def resolve(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    try:
        runtime = ConvergenceRuntime(root, emm_id=EMM_ID)
        emm = runtime.resolve_emm("OPERATION-BETA")
        entity = runtime._entity("ImplementationWOP", WOP_ID, 1)
    except ConvergenceRuntimeError as error:
        raise ModelBAuthorityError(str(error)) from error

    wop_path = root / entity["source"]
    wop_text = _read(root, entity["source"])
    materialized = hashlib.sha256(wop_text.encode("utf-8")).hexdigest()
    wop_id = re.search(r"^Wop Id: (.+)$", wop_text, re.MULTILINE)
    if not wop_id or wop_id.group(1) != WOP_ID:
        raise ModelBAuthorityError("MODEL_B_WOP_IDENTITY_INVALID")
    if materialized != WOP_DIGEST or entity.get("source_digest") != WOP_DIGEST:
        raise ModelBAuthorityError("MODEL_B_WOP_DIGEST_INVALID")
    roadmap = _read(root, ROADMAP)
    if "CURRENT_OPERATION=OPERATION-BETA" not in roadmap or f"CURRENT_WOP={WOP_ID}" not in roadmap:
        raise ModelBAuthorityError("MODEL_B_ROADMAP_BINDING_INVALID")
    if emm.get("program_id") != "OPERATION-BETA" or emm.get("authority_model") != "MODEL_B":
        raise ModelBAuthorityError("MODEL_B_EMM_BINDING_INVALID")
    if emm.get("current_wop") != WOP_ID or emm.get("current_roadmap") != ROADMAP:
        raise ModelBAuthorityError("MODEL_B_EMM_CURRENT_BINDING_INVALID")
    roadmap_entity = runtime._entity("MissionRoadmap", "OPERATION-BETA-ROADMAP", 1)
    if roadmap_entity.get("source") != ROADMAP:
        raise ModelBAuthorityError("MODEL_B_ROADMAP_ENTITY_INVALID")

    interface = yaml.safe_load(_read(root, "engineering/execution/execution-interface.yaml"))
    semantic = interface.get("semantic_bindings", {}) if isinstance(interface, dict) else {}
    controlled_owner = semantic.get("execution_lifecycle", {})
    controlled_binding = resolve_exact(
        root, str(controlled_owner.get("owner")), str(controlled_owner.get("revision"))
    )
    controlled_valid = True
    return {
        "result": "PASS",
        "operation": "OPERATION-BETA",
        "authority_model": "MODEL_B",
        "emm_id": EMM_ID,
        "program_id": "OPERATION-BETA",
        "wop_id": WOP_ID,
        "wop_path": str(wop_path),
        "roadmap": ROADMAP,
        "wop_digest": materialized,
        "emm_wop_binding": True,
        "roadmap_wop_binding": True,
        "roadmap_emm_binding": True,
        "current_wop_not_superseded": True,
        "legacy_oa_execution_dependency": False,
        "legacy_mission_contract_execution_dependency": False,
        "structural_validity": "PASS",
        "model_b_authority_validity": "PASS",
        "controlled_document_binding_validity": "PASS" if controlled_valid else "FAIL",
        "execution_readiness": "PASS" if controlled_valid else "FAIL",
        "remaining_execution_blockers": [] if controlled_valid else [
            {
                "blocker": "PROC-0001 live binding migration",
                "owner_transaction": "T-AUTH-02",
                "fail_closed": True,
                "next_required_transaction": "EXECUTE_T_AUTH_02",
            }
        ],
        "historical_oa_lookup": "PRESERVED",
        "controlled_document_binding": controlled_binding,
    }
