#!/usr/bin/env python3
"""Authoritative-state-preserving, evidence-producing capability test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

CONTROLLED_RESULTS = {
    "PASS", "FAIL", "BLOCKED", "NOT_READY",
    "EXPECTED_NOT_YET_IMPLEMENTED", "NOT_APPLICABLE",
}
TERMINAL_RESULTS = {"PASS", "FAIL", "BLOCKED", "NOT_READY"}
REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY))

from scripts.lib.emp.authority_resolution import authoritative_source_path  # noqa: E402
from scripts.lib.emp.gate_approval import (  # noqa: E402
    GateApprovalError,
    GateApprovalService,
)

PMCT_ROOT = REPOSITORY / "engineering/tests/zeus-operational-alpha"
MATRIX_PATH = PMCT_ROOT / "PMCT-CAPABILITY-MATRIX.yaml"
STATE_PATH = REPOSITORY / "engineering/runtime/pmct/capability-state.yaml"
DEFAULT_RUNTIME = REPOSITORY / "engineering/runtime/pmct"
EXPECTED_REPOSITORY = Path("/data/engineering/repositories/homelab")
VERSION = "1.0"


class PmctError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def time_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def run(command: list[str], cwd: Path = REPOSITORY) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command, "returncode": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
    }


def git(*arguments: str) -> str:
    result = run(["git", "-C", str(REPOSITORY), *arguments])
    if result["returncode"]:
        raise PmctError(result["stderr"].strip() or "git verification failed")
    return result["stdout"].strip()


def matrix() -> dict[str, Any]:
    value = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
    validate_matrix(value)
    return value


def validate_matrix(value: Any) -> None:
    if not isinstance(value, dict) or value.get("contract_version") != VERSION:
        raise PmctError("capability matrix contract version is invalid")
    gates = value.get("gates")
    if not isinstance(gates, list) or len(gates) != 30:
        raise PmctError("capability matrix must contain exactly 30 gates")
    expected = [f"OA-{number:02d}" for number in range(1, 31)]
    observed = [gate.get("gate_id") for gate in gates]
    if observed != expected:
        raise PmctError("capability sequence is not contiguous and locked")
    required = {
        "gate_id", "sequence", "title", "required_commands", "optional_commands",
        "prerequisites", "positive_demonstration", "negative_demonstration",
        "idempotency_demonstration", "interruption_demonstration",
        "evidence_requirements", "regression_gates", "allowed_results",
        "manual_review_required", "state_change",
    }
    for sequence, gate in enumerate(gates, 1):
        if set(gate) != required or gate["sequence"] != sequence:
            raise PmctError(f"{expected[sequence - 1]} metadata is incomplete")
        if set(gate["allowed_results"]) - CONTROLLED_RESULTS:
            raise PmctError("gate uses uncontrolled result vocabulary")
        if gate["regression_gates"] != expected[:sequence - 1]:
            raise PmctError(f"{gate['gate_id']} cumulative regression scope is invalid")
        script = PMCT_ROOT / "gates" / f"{gate['gate_id']}.sh"
        if not script.is_file():
            raise PmctError(f"gate procedure missing: {gate['gate_id']}")


def command_surface() -> dict[str, dict[str, Any]]:
    contracts = {
        "zeus status": ["status"],
        "zeus authority status": ["authority", "status"],
        "zeus authority work-lifecycle": ["authority", "work-lifecycle"],
        "zeus authority restoration": ["authority", "restoration"],
        "zeus dispatcher status": ["dispatcher", "status"],
        "zeus dispatcher policy": ["dispatcher", "policy"],
        "zeus dispatcher activation": ["dispatcher", "activation"],
        "zeus dispatcher probe": ["dispatcher", "probe"],
        "zeus agent registry": ["agent", "registry"],
        "zeus agent qualify": ["agent", "qualify"],
        "zeus agent status": ["agent", "status"],
        "zeus agent select": ["agent", "select"],
        "zeus admission evaluate": ["admission", "evaluate"],
        "zeus invocation probe": ["invocation", "probe"],
        "zeus eens status": ["eens", "status"],
        "zeus eens self-test": ["eens", "self-test"],
        "zeus evidence self-test": ["evidence", "self-test"],
        "zeus qualification self-test": ["qualification", "self-test"],
        "zeus reconciliation self-test": ["reconciliation", "self-test"],
        "zeus next-action": ["next-action"],
    }
    help_result = run([str(REPOSITORY / "scripts/zeus"), "--help"])
    top = set(re.findall(r"\{([^}]+)\}", help_result["stdout"])[0].split(",")) if (
        help_result["returncode"] == 0 and re.findall(r"\{([^}]+)\}", help_result["stdout"])
    ) else set()
    discovered: dict[str, dict[str, Any]] = {}
    for label, arguments in contracts.items():
        available = arguments[0] in top
        if available and len(arguments) > 1:
            probe = run([str(REPOSITORY / "scripts/zeus"), arguments[0], "--help"])
            available = probe["returncode"] == 0 and arguments[1] in probe["stdout"]
        discovered[label] = {
            "available": available,
            "classification": "AVAILABLE" if available else "UNAVAILABLE",
        }
    return discovered


def published_baseline() -> str | None:
    source = authoritative_source_path(REPOSITORY)
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
        repositories = value.get("repositories", {})
        for record in repositories.values():
            if Path(str(record.get("canonical_locator", ""))).resolve() == REPOSITORY:
                return record.get("baseline_commit")
    except (OSError, yaml.YAMLError, AttributeError):
        return None
    return None


def oa01_verification_state(*, head: str, prerequisites_ready: bool) -> dict[str, str]:
    wop = Path(os.environ.get(
        "ZEUS_GATE_WOP", "/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP"
    )).resolve()
    record = wop / "operator-verifications/OA-01.verification.json"
    checksum = record.with_suffix(record.suffix + ".sha256")
    if record.is_file() or checksum.is_file():
        try:
            service = GateApprovalService.configured(REPOSITORY)
            binding = service.binding("OA-01", require_clean=False)
        except GateApprovalError:
            binding = None
        if (
            binding is not None
            and binding.qualified_head == head
            and service.verification_record(binding) is not None
        ):
            return {"readiness": "PASS", "evidence": "PRESENT"}
        return {
            "readiness": "READY" if prerequisites_ready else "NOT_READY",
            "evidence": "ABSENT" if prerequisites_ready else "MISMATCHED",
        }
    return {
        "readiness": "READY" if prerequisites_ready else "NOT_READY",
        "evidence": "ABSENT",
    }


def inspect_state() -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    activation_path = REPOSITORY / "engineering/dispatch/dispatcher-activation.json"
    registry_path = REPOSITORY / "engineering/dispatch/execution-agent-registry.json"
    activation = json.loads(activation_path.read_text()) if activation_path.exists() else {}
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    commands = command_surface()
    next_probe: dict[str, Any] | None = None
    next_probe_error: str | None = None
    if commands["zeus next-action"]["available"]:
        probe = run([str(REPOSITORY / "scripts/zeus"), "next-action", "--json"])
        if probe["returncode"] == 0:
            try:
                next_probe = json.loads(probe["stdout"])
            except json.JSONDecodeError as error:
                next_probe_error = f"invalid JSON: {error}"
        else:
            next_probe_error = probe["stderr"].strip() or "command failed"
    authority_configured = bool(
        yaml.safe_load(authoritative_source_path(REPOSITORY).read_text()).get(
            "operationally_configured", False
        )
    )
    baseline_matches = published_baseline() == head
    verification = oa01_verification_state(
        head=head,
        prerequisites_ready=(
            root == EXPECTED_REPOSITORY and authority_configured and baseline_matches
        ),
    )
    pointer = REPOSITORY / ".zeus/runtime/authority/active-publication.json"
    if pointer.is_file():
        active_authority_publication = str(
            json.loads(pointer.read_text(encoding="utf-8")).get(
                "transaction_id", ""
            )
        )
    else:
        active_authority_publication = "TRACKED-AUTHORITY-FALLBACK"
    return {
        "repository": str(root), "repository_identity_valid": root == EXPECTED_REPOSITORY,
        "branch": branch, "head": head, "published_baseline": published_baseline(),
        "baseline_matches": baseline_matches,
        "implementation_baseline": head,
        "active_authority_publication": active_authority_publication,
        "working_tree": git("status", "--short"),
        "authority_operationally_configured": authority_configured,
        "oa01_operator_verification_readiness": verification["readiness"],
        "oa01_operator_verification_evidence": verification["evidence"],
        "dispatcher_status": activation.get("status", "MISSING"),
        "dispatcher_active": activation.get("status") == "ACTIVE",
        "production_agent_count": len(registry.get("agents", [])),
        "production_qualified_agent_count": sum(
            1 for agent in registry.get("agents", [])
            if agent.get("active") and agent.get("qualification_status") == "QUALIFIED"
        ),
        "command_availability": commands,
        "next_action_probe": next_probe,
        "next_action_probe_error": next_probe_error,
    }


def assertion(name: str, passed: bool, detail: str, mandatory: bool = True) -> dict[str, Any]:
    return {
        "assertion": name, "passed": bool(passed), "mandatory": mandatory,
        "detail": detail,
    }


def classify(gate: dict[str, Any], state: dict[str, Any], assertions: list[dict[str, Any]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not state["repository_identity_valid"]:
        return "BLOCKED", ["repository identity mismatch"]
    missing_required = [
        command for command in gate["required_commands"]
        if not state["command_availability"].get(command, {}).get("available")
    ]
    if missing_required:
        reasons.append("required command unavailable: " + ", ".join(missing_required))
    failed = [item for item in assertions if item["mandatory"] and not item["passed"]]
    reasons.extend(item["detail"] for item in failed)
    prerequisites = gate["prerequisites"]
    capability_state = load_state()
    missing_prerequisites = []
    for prior in prerequisites:
        prior_state = capability_state["gates"][prior]
        accepted = prior_state.get("operator_acceptance") == "RECORDED"
        if prior == "OA-01":
            try:
                service = GateApprovalService.configured(REPOSITORY)
                binding = service.binding("OA-01", require_clean=False)
                accepted = service._matching_receipt(binding) is not None
            except GateApprovalError:
                accepted = False
        if prior_state["status"] != "PASS" or not accepted:
            missing_prerequisites.append(prior)
    if missing_prerequisites:
        return "BLOCKED", reasons + [
            "prerequisite gate operator acceptance is not recorded: "
            + ", ".join(missing_prerequisites)
        ]
    # Manual review is always required after a demonstrated PASS. The sealed
    # run updates capability-state with its result but never records operator
    # verification or acceptance.
    if missing_required or failed:
        return "NOT_READY", reasons or ["capability demonstration incomplete"]
    return "PASS", ["observable demonstration completed; manual approval remains required"]


def load_state() -> dict[str, Any]:
    value = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PmctError("capability state is invalid")
    return value


def persist_capability_state(
    *, gate: str, run_id: str, result: str, reasons: list[str], updated_at: str
) -> None:
    state = load_state()
    gate_state = state["gates"].get(gate)
    if not isinstance(gate_state, dict):
        raise PmctError(f"capability state gate is unavailable: {gate}")
    gate_state["status"] = result
    gate_state["reason"] = "; ".join(reasons)
    if result == "PASS":
        gate_state["codex_validation"] = "PASS"
        if gate_state.get("operator_acceptance") != "RECORDED":
            gate_state["gate_status"] = "AWAITING_OPERATOR_VERIFICATION"
    state["last_run_id"] = run_id
    state["last_evaluated_gate"] = gate
    state["updated_at"] = updated_at
    state["overall_result"] = (
        "PASS"
        if all(
            value.get("status") == "PASS"
            for value in state["gates"].values()
        )
        else "NOT_READY"
    )
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=STATE_PATH.parent, prefix=".capability-state.", suffix=".yaml"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            yaml.safe_dump(state, stream, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, STATE_PATH)
    finally:
        if temporary.exists():
            temporary.unlink()


def safe_runtime() -> Path:
    configured = os.environ.get("PMCT_RUNTIME_ROOT")
    root = Path(configured).resolve() if configured else DEFAULT_RUNTIME.resolve()
    if root == REPOSITORY or REPOSITORY not in root.parents:
        raise PmctError("PMCT runtime must be a scoped repository subdirectory")
    return root


def completed_run(run_id: str) -> Path:
    if not re.fullmatch(r"PMCT-\d{8}T\d{6}Z-[0-9a-f]{12}", run_id):
        raise PmctError(f"invalid PMCT run ID: {run_id}")
    directory = safe_runtime() / "runs" / run_id
    if not directory.is_dir() or not (directory / "COMPLETE").is_file():
        raise PmctError(f"completed PMCT run not found: {run_id}")
    return directory


def evaluate(gate: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    gate_id = gate["gate_id"]
    checks = [
        assertion("repository_identity", state["repository_identity_valid"],
                  f"repository={state['repository']}"),
        assertion("authoritative_state_observation", not gate["state_change"],
                  "gate requires authorized transition" if gate["state_change"]
                  else "authoritative engineering and decision state preserved"),
    ]
    for command in gate["required_commands"]:
        available = state["command_availability"].get(command, {}).get("available", False)
        checks.append(assertion(
            f"required_command:{command}", available,
            f"{command} is {'available' if available else 'unavailable'}",
        ))
    checks.extend([
        assertion(
            "positive_path_adapter",
            gate_id in {"OA-01", "OA-02"},
            "gate-specific observable adapter is implemented"
            if gate_id in {"OA-01", "OA-02"} else
            f"{gate_id} functional adapter is expected at its locked implementation gate",
        ),
        assertion(
            "negative_path_adapter",
            gate_id in {"OA-01", "OA-02"},
            f"{gate_id} verifies that incomplete production prerequisites do not advance state"
            if gate_id in {"OA-01", "OA-02"} else
            f"{gate_id} negative-path adapter is not yet implemented",
        ),
        assertion(
            "idempotency_adapter",
            gate_id in {"OA-01", "OA-02"},
            f"{gate_id} repeats authoritative-state repository discovery"
            if gate_id in {"OA-01", "OA-02"} else
            f"{gate_id} idempotency adapter is not yet implemented",
        ),
        assertion(
            "interruption_resume",
            not gate["state_change"],
            "NOT_APPLICABLE: observation-only gate has no transition to interrupt"
            if not gate["state_change"] else
            "state-changing interruption/resume demonstration requires separate authority",
        ),
    ])
    if gate_id == "OA-01":
        repeated = inspect_state()
        stable_keys = (
            "repository", "branch", "head", "published_baseline",
            "dispatcher_status", "production_agent_count",
        )
        checks.extend([
            assertion("implementation_baseline_observed", bool(state["head"]),
                      f"HEAD={state['head']}"),
            assertion("published_baseline_current", state["baseline_matches"],
                      f"published={state['published_baseline']} HEAD={state['head']}"),
            assertion("dispatcher_inactive", not state["dispatcher_active"],
                      f"dispatcher={state['dispatcher_status']}"),
            assertion("agent_registry_empty", state["production_agent_count"] == 0,
                      f"agents={state['production_agent_count']}"),
            assertion("operational_alpha_not_claimed",
                      not state["dispatcher_active"] and
                      state["production_qualified_agent_count"] == 0,
                      "production prerequisites remain incomplete"),
            assertion(
                "next_action_executed",
                isinstance(state["next_action_probe"], dict)
                and not state["next_action_probe_error"],
                state["next_action_probe_error"] or
                "zeus next-action returned structured authoritative state",
            ),
            assertion(
                "beta_mode_reported",
                isinstance(state["next_action_probe"], dict)
                and state["next_action_probe"].get("zeus_mode") == "BETA",
                "current incomplete capability set must remain BETA",
            ),
            assertion(
                "next_action_prioritizes_oa01_verification",
                isinstance(state["next_action_probe"], dict)
                and state["next_action_probe"].get(
                    "next_authorized_action", {}
                ).get("code") == "RUN_OA-01_VERIFICATION",
                "current-baseline OA-01 verification precedes dispatcher and agent work",
            ),
            assertion(
                "oa01_verification_ready_not_executed",
                state["oa01_operator_verification_readiness"] == "READY"
                and state["oa01_operator_verification_evidence"] == "ABSENT",
                "OA-01 verification prerequisites are satisfied and evidence is absent",
            ),
            assertion(
                "dispatch_remains_disabled",
                isinstance(state["next_action_probe"], dict)
                and state["next_action_probe"].get("operational_dispatch") == "DISABLED",
                "observational decision must not enable dispatch",
            ),
            assertion(
                "read_only_idempotency",
                all(state[key] == repeated[key] for key in stable_keys),
                "repeated discovery returned the same repository and production state",
            ),
        ])
    if gate_id == "OA-02":
        repeated = inspect_state()
        next_action = (
            state["next_action_probe"].get("next_authorized_action", {}).get("code")
            if isinstance(state["next_action_probe"], dict) else None
        )
        try:
            service = GateApprovalService.configured(REPOSITORY)
            binding = service.binding("OA-01", require_clean=False)
            verification_pass = service.verification_record(binding) is not None
            acceptance_recorded = service._matching_receipt(binding) is not None
        except GateApprovalError:
            verification_pass = acceptance_recorded = False
        stable_keys = (
            "repository", "branch", "head", "published_baseline",
            "dispatcher_status", "production_agent_count",
            "active_authority_publication",
        )
        checks.extend([
            assertion(
                "oa02_repository",
                state["repository_identity_valid"] and state["baseline_matches"],
                f"repository={state['repository']} published={state['published_baseline']} "
                f"HEAD={state['head']}",
            ),
            assertion(
                "oa02_authority",
                state["authority_operationally_configured"]
                and bool(state["active_authority_publication"]),
                f"publication={state['active_authority_publication']}",
            ),
            assertion(
                "oa02_lifecycle",
                verification_pass and acceptance_recorded
                and next_action in {
                    "COMPLETE_OA02_PMCT",
                    "RUN_OA-02_PRE_EXECUTION_VERIFICATION",
                    "QUALIFY_PRODUCTION_AGENT",
                },
                "OA-01 current-binding verification and acceptance are required",
            ),
            assertion(
                "oa02_configuration",
                state["dispatcher_status"] == "PREPARED",
                f"dispatcher={state['dispatcher_status']}",
            ),
            assertion(
                "oa02_runtime",
                not state["dispatcher_active"]
                and isinstance(state["next_action_probe"], dict)
                and state["next_action_probe"].get("operational_dispatch") == "DISABLED",
                "dispatcher must remain prepared and operational dispatch disabled",
            ),
            assertion(
                "oa02_capabilities",
                state["production_qualified_agent_count"] == 0,
                "OA-02 PMCT qualifies pre-execution controls without qualifying an agent",
            ),
            assertion(
                "oa02_observational_idempotency",
                all(state[key] == repeated[key] for key in stable_keys),
                "repeated OA-02 discovery returned identical authoritative inputs",
            ),
        ])
    return checks


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True) + "\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def evidence_run(gate: dict[str, Any], *, authorized_transition: bool = False) -> tuple[dict[str, Any], Path]:
    if authorized_transition:
        raise PmctError(
            "this PMCT version contains no authorized state-changing gate implementation"
        )
    started = utc_now()
    run_id = "PMCT-" + started.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    directory = safe_runtime() / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    state = inspect_state()
    assertions = evaluate(gate, state)
    capability_state = load_state()
    for prior_id in gate["regression_gates"]:
        if capability_state["gates"][prior_id]["status"] != "PASS":
            continue
        prior_gate = next(
            item for item in matrix()["gates"] if item["gate_id"] == prior_id
        )
        for item in evaluate(prior_gate, inspect_state()):
            if item["assertion"] in {
                "next_action_prioritizes_oa01_verification",
                "oa01_verification_ready_not_executed",
            }:
                continue
            projected = dict(item)
            projected["assertion"] = f"regression:{prior_id}:{item['assertion']}"
            assertions.append(projected)
    result, reasons = classify(gate, state, assertions)
    completed = utc_now()
    command_availability = state.pop("command_availability")
    decision_material = {
        "gate": gate["gate_id"],
        "repository": state["repository"],
        "head": state["head"],
        "published_baseline": state["published_baseline"],
        "active_authority_publication": state["active_authority_publication"],
        "assertions": [
            {
                "assertion": item["assertion"],
                "passed": item["passed"],
                "mandatory": item["mandatory"],
                "detail": item["detail"],
            }
            for item in assertions
        ],
        "result": result,
        "reasons": reasons,
    }
    result_value = {
        "schema_version": 1, "contract_version": VERSION, "run_id": run_id,
        "gate": gate["gate_id"], "result": result, "reasons": reasons,
        "assertions": assertions, "manual_review_required": True,
        "state_changed": True,
        "decision_digest": sha256(canonical(decision_material)),
    }
    manifest = {
        "schema_version": 1, "pmct_version": VERSION, "run_id": run_id,
        "gate": gate["gate_id"], "started_at": time_text(started),
        "completed_at": time_text(completed), "repository": str(REPOSITORY),
        "repository_identity": state["repository"], "branch": state["branch"],
        "head": state["head"], "published_baseline": state["published_baseline"],
        "implementation_baseline": state["implementation_baseline"],
        "active_authority_publication": state["active_authority_publication"],
        "operator_identity": os.environ.get("USER", "unavailable"),
        "host_identity": socket.gethostname(), "command_availability": command_availability,
        "result": result, "evidence_digest": None,
    }
    write_json(directory / "repository.json", state)
    write_json(directory / "command-discovery.json", command_availability)
    write_json(directory / "assertions.json", assertions)
    write_json(directory / "capability-result.json", result_value)
    commands = [
        {"command": "git rev-parse HEAD", "classification": "authoritative-state-observation"},
        {"command": "git status --short", "classification": "authoritative-state-observation"},
        {"command": "zeus --help", "classification": "authoritative-state-observation"},
    ]
    write_json(directory / "commands.json", commands)
    repository_text = (
        f"repository={state['repository']}\nbranch={state['branch']}\n"
        f"head={state['head']}\npublished_baseline={state['published_baseline']}\n"
        f"baseline_matches={str(state['baseline_matches']).lower()}\n"
        f"working_tree:\n{state['working_tree']}\n"
    )
    (directory / "repository.txt").write_text(repository_text, encoding="utf-8")
    authority_text = (
        f"operationally_configured={str(state['authority_operationally_configured']).lower()}\n"
        f"dispatcher_status={state['dispatcher_status']}\n"
        f"dispatcher_active={str(state['dispatcher_active']).lower()}\n"
        f"production_agent_count={state['production_agent_count']}\n"
        f"production_qualified_agent_count={state['production_qualified_agent_count']}\n"
    )
    (directory / "authority.txt").write_text(authority_text, encoding="utf-8")
    discovery_text = "".join(
        f"{command}\t{details['classification']}\n"
        for command, details in sorted(command_availability.items())
    )
    (directory / "command-discovery.txt").write_text(discovery_text, encoding="utf-8")
    (directory / "commands.log").write_text(
        "".join(f"{item['classification']}\t{item['command']}\n" for item in commands),
        encoding="utf-8",
    )
    (directory / "stdout.log").write_text(
        f"repository={state['repository']}\nhead={state['head']}\n"
        f"dispatcher_status={state['dispatcher_status']}\n",
        encoding="utf-8",
    )
    (directory / "stderr.log").write_text("", encoding="utf-8")
    report = (
        f"# PMCT Capability Report\n\n"
        f"- Run: `{run_id}`\n- Gate: `{gate['gate_id']}`\n"
        f"- Result: `{result}`\n- HEAD: `{state['head']}`\n"
        f"- Published baseline: `{state['published_baseline']}`\n\n"
        "## Reasons\n\n" + "".join(f"- {reason}\n" for reason in reasons) +
        "\nImplementation artifacts alone do not satisfy this capability test.\n"
    )
    (directory / "capability-report.md").write_text(report, encoding="utf-8")
    evidence_files = sorted(
        path for path in directory.iterdir() if path.name not in {"run-manifest.json", "artifacts.sha256", "COMPLETE"}
    )
    hashes = "".join(f"{sha256(path.read_bytes())}  {path.name}\n" for path in evidence_files)
    (directory / "artifacts.sha256").write_text(hashes, encoding="utf-8")
    manifest["evidence_digest"] = sha256(hashes.encode())
    write_json(directory / "run-manifest.json", manifest)
    persist_capability_state(
        gate=gate["gate_id"],
        run_id=run_id,
        result=result,
        reasons=reasons,
        updated_at=time_text(completed),
    )
    (directory / "COMPLETE").write_text("PMCT_COMPLETION_MARKER=COMPLETE\n", encoding="utf-8")
    return result_value, directory


def emit_run(result: dict[str, Any], directory: Path) -> int:
    print(f"PMCT_RUN_ID={result['run_id']}")
    print(f"PMCT_GATE={result['gate']}")
    print(f"PMCT_RESULT={result['result']}")
    print(f"ZEUS_PROGRESSIVE_TEST_RESULT={result['result']}")
    print(f"PMCT_REPORT={directory / 'capability-report.md'}")
    print(f"PMCT_EVIDENCE={directory}")
    print("PMCT_COMPLETION_MARKER=COMPLETE")
    if result["gate"] == "OA-02":
        outcomes = {
            item["assertion"]: "PASS" if item["passed"] else "NOT_READY"
            for item in result["assertions"]
        }
        print(f"OA02_PMCT_RESULT={result['result']}")
        for label, assertion_name in (
            ("REPOSITORY", "oa02_repository"),
            ("AUTHORITY", "oa02_authority"),
            ("LIFECYCLE", "oa02_lifecycle"),
            ("CONFIGURATION", "oa02_configuration"),
            ("RUNTIME", "oa02_runtime"),
            ("CAPABILITIES", "oa02_capabilities"),
        ):
            print(f"OA02_PMCT_{label}={outcomes.get(assertion_name, 'NOT_READY')}")
        print(f"OA02_PMCT_DECISION_DIGEST={result['decision_digest']}")
    return 0 if result["result"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "help":
        argv = ["--help"] if len(argv) == 1 else [argv[1], "--help"]
    parser = argparse.ArgumentParser(prog="pmct")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument(
        "run_id", nargs="?",
        help="exact completed PMCT run ID; omit for current-state inspection",
    )
    sub.add_parser("list")
    show = sub.add_parser("show"); show.add_argument("gate")
    execute = sub.add_parser("run"); execute.add_argument("gate")
    execute.add_argument("--authorized-transition", action="store_true")
    report = sub.add_parser("report")
    report.add_argument("selector", help="gate ID or exact completed PMCT run ID")
    args = parser.parse_args(argv)
    try:
        value = matrix()
        gates = {gate["gate_id"]: gate for gate in value["gates"]}
        if args.command == "inspect":
            if args.run_id:
                directory = completed_run(args.run_id)
                inspected = {
                    "run_manifest": json.loads(
                        (directory / "run-manifest.json").read_text()
                    ),
                    "capability_result": json.loads(
                        (directory / "capability-result.json").read_text()
                    ),
                    "evidence_directory": str(directory),
                    "completion_marker": (directory / "COMPLETE").read_text().strip(),
                }
            else:
                inspected = inspect_state()
            print(json.dumps(inspected, indent=2, sort_keys=True))
            return 0
        if args.command == "list":
            current = load_state()
            for gate in value["gates"]:
                gate_state = current["gates"][gate["gate_id"]]
                lifecycle = gate_state.get("gate_status", "NOT_STARTED")
                print(
                    f"{gate['gate_id']}\\t{gate_state['status']}\\t"
                    f"{lifecycle}\\t{gate['title']}"
                )
            return 0
        selector = args.selector if args.command == "report" else args.gate
        if args.command == "report" and selector.startswith("PMCT-"):
            directory = completed_run(selector)
            print((directory / "capability-report.md").read_text(), end="")
            return 0
        gate_id = selector.upper()
        if gate_id not in gates:
            raise PmctError(f"unknown gate: {gate_id}")
        if args.command == "show":
            print(yaml.safe_dump(gates[gate_id], sort_keys=False).rstrip())
            return 0
        if args.command == "report":
            candidates = sorted(safe_runtime().glob(f"runs/PMCT-*/capability-result.json"))
            matching = [
                path for path in candidates
                if json.loads(path.read_text()).get("gate") == gate_id
            ]
            if not matching:
                raise PmctError(f"no completed PMCT run for {gate_id}")
            result_path = matching[-1]
            print((result_path.parent / "capability-report.md").read_text(), end="")
            return 0
        result, directory = evidence_run(
            gates[gate_id], authorized_transition=args.authorized_transition
        )
        return emit_run(result, directory)
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        print(f"PMCT_ERROR={error}", file=sys.stderr)
        print("PMCT_RESULT=BLOCKED")
        print("ZEUS_PROGRESSIVE_TEST_RESULT=BLOCKED")
        print("PMCT_COMPLETION_MARKER=COMPLETE")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
