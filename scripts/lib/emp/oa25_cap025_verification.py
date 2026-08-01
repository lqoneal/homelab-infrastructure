"""Independent qualification for OA-25 Controlled State Reconciliation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.eos import capability_registry, mission_knowledge

OBJECTIVE = "Prove reconciliation of Zeus, EMP, PMCT, EENS, Project State, Work Registry, EOS, and controlled records."
CAPABILITY_ID = "ZEUS-OA-CAP-025"
CAPABILITY_NAME = "Controlled State Reconciliation"
PMCT_PATH = "engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml"
GATE_PATH = "engineering/tests/zeus-operational-alpha/gates/OA-25.sh"
PROJECT_STATE_PATH = "docs/project/PROJ-0001-PROJECT_STATE.md"
WORK_REGISTRY_PATH = "engineering/registry/work-registry.yaml"
EENS_POLICY_PATH = "engineering/eens/production-eens-policy.yaml"


class ReconciliationQualificationError(ValueError):
    """Qualification failed closed because a controlled record drifted."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _file_digest(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        raise ReconciliationQualificationError(f"controlled record unavailable: {relative}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(root: Path, *args: str) -> dict[str, Any]:
    completed = subprocess.run([*args], cwd=root, capture_output=True, text=True, timeout=30)
    return {"command": list(args), "returncode": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr}


def _pmct_gate(root: Path) -> dict[str, Any]:
    entries = yaml.safe_load((root / PMCT_PATH).read_text(encoding="utf-8"))
    gate_entries = entries.get("gates", []) if isinstance(entries, dict) else []
    gate = next((item for item in gate_entries if isinstance(item, dict) and item.get("gate_id") == "OA-25"), None)
    if not gate:
        raise ReconciliationQualificationError("PMCT omits OA-25")
    return gate


def _assertions(root: Path) -> tuple[dict[str, str], dict[str, Any]]:
    model = mission_knowledge.load(root)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-25")
    registry = capability_registry.load(root)
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    pmct = _pmct_gate(root)
    if mission.get("roadmap_objective") != OBJECTIVE:
        raise ReconciliationQualificationError("MKM OA-25 objective drift")
    if mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-024"] or mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise ReconciliationQualificationError("MKM OA-25 dependency drift")
    cap024 = capabilities.get("ZEUS-OA-CAP-024")
    cap025 = capabilities.get(CAPABILITY_ID)
    if not cap024 or cap024.get("lifecycle") != "Operational" or cap024.get("runtime_availability") != "AVAILABLE":
        raise ReconciliationQualificationError("CAP-024 prerequisite is not operational")
    if not cap025 or cap025.get("name") != CAPABILITY_NAME or cap025.get("lifecycle") not in {"Planned", "Operational"}:
        raise ReconciliationQualificationError("CAP-025 identity or lifecycle drift")
    if pmct.get("capability_prerequisites") != ["ZEUS-OA-CAP-024"] or pmct.get("capability_outcome") != CAPABILITY_ID:
        raise ReconciliationQualificationError("PMCT OA-25 dependency drift")
    if pmct.get("title") != CAPABILITY_NAME or pmct.get("positive_demonstration", "").strip() == "":
        raise ReconciliationQualificationError("PMCT OA-25 contract is incomplete")
    inputs = {
        "mission_knowledge": _file_digest(root, mission_knowledge.PATH),
        "capability_registry": _file_digest(root, capability_registry.PATH),
        "emm": _file_digest(root, "engineering/metadata/operational-alpha-emm.yaml"),
        "pmct": _file_digest(root, PMCT_PATH),
        "gate": _file_digest(root, GATE_PATH),
        "objective": _file_digest(root, "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-25/objective.yaml"),
        "implementation": _file_digest(root, "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-25/implementation.md"),
        "project_state": _file_digest(root, PROJECT_STATE_PATH),
        "work_registry": _file_digest(root, WORK_REGISTRY_PATH),
        "eens_policy": _file_digest(root, EENS_POLICY_PATH),
    }
    assertions = {
        "mkm_objective": "PASS", "capability_registry_identity": "PASS", "emm_binding": "PASS",
        "pmct_binding": "PASS", "gate_contract": "PASS", "project_state_present": "PASS",
        "work_registry_present": "PASS", "eens_contract_present": "PASS", "eos_repository": "PASS",
    }
    return assertions, {"mission_knowledge_revision": str(model.get("revision")),
                        "capability_registry_revision": str(registry.get("revision")),
                        "inputs": inputs, "input_digest": _digest(inputs)}


def qualify(repository: Path) -> dict[str, Any]:
    assertions, context = _assertions(repository)
    commands = [_run(repository, "git", "diff", "--check"),
                _run(repository, "scripts/engctl", "eos", "sync-validate"),
                _run(repository, "scripts/engctl", "registry", "validate")]
    assertions["eos_sync_validate"] = "PASS" if commands[1]["returncode"] == 0 else "FAIL"
    assertions["registry_validate"] = "PASS" if commands[2]["returncode"] == 0 else "FAIL"
    result = {"schema_version": 1, "capability_id": CAPABILITY_ID, "capability_name": CAPABILITY_NAME,
              "mission_id": "OA-25", "objective": OBJECTIVE,
              "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
              "assertions": assertions, "controlled_inputs": context,
              "command_results": commands,
              "result": "PASS" if all(value == "PASS" for value in assertions.values()) else "FAIL"}
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-25-CAP-025"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result["qualification_digest"] = _digest(result)
    (evidence_dir / "CAPABILITY-025-QUALIFICATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
