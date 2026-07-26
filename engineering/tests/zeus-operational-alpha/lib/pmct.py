#!/usr/bin/env python3
"""Read-only, evidence-producing Progressive Manual Capability Test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
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
    source = REPOSITORY / "engineering/authority/operational-authority-state.yaml"
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
        repositories = value.get("repositories", {})
        for record in repositories.values():
            if Path(str(record.get("canonical_locator", ""))).resolve() == REPOSITORY:
                return record.get("baseline_commit")
    except (OSError, yaml.YAMLError, AttributeError):
        return None
    return None


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
    return {
        "repository": str(root), "repository_identity_valid": root == EXPECTED_REPOSITORY,
        "branch": branch, "head": head, "published_baseline": published_baseline(),
        "baseline_matches": published_baseline() == head,
        "working_tree": git("status", "--short"),
        "authority_operationally_configured": bool(
            yaml.safe_load((REPOSITORY / "engineering/authority/operational-authority-state.yaml").read_text()).get(
                "operationally_configured", False
            )
        ),
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
    missing_prerequisites = [
        prior for prior in prerequisites
        if capability_state["gates"][prior]["status"] != "PASS"
    ]
    if missing_prerequisites:
        return "BLOCKED", reasons + [
            "prerequisite gates have not passed: " + ", ".join(missing_prerequisites)
        ]
    # Manual review is always required before persistent PASS. A run may only
    # demonstrate PASS when every mandatory assertion succeeds and the command
    # interface exists; it never mutates capability-state automatically.
    if missing_required or failed:
        return "NOT_READY", reasons or ["capability demonstration incomplete"]
    return "PASS", ["observable demonstration completed; manual approval remains required"]


def load_state() -> dict[str, Any]:
    value = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PmctError("capability state is invalid")
    return value


def safe_runtime() -> Path:
    configured = os.environ.get("PMCT_RUNTIME_ROOT")
    root = Path(configured).resolve() if configured else DEFAULT_RUNTIME.resolve()
    if root == REPOSITORY or REPOSITORY not in root.parents:
        raise PmctError("PMCT runtime must be a scoped repository subdirectory")
    return root


def evaluate(gate: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    gate_id = gate["gate_id"]
    checks = [
        assertion("repository_identity", state["repository_identity_valid"],
                  f"repository={state['repository']}"),
        assertion("production_state_read_only", not gate["state_change"],
                  "gate requires authorized transition" if gate["state_change"]
                  else "read-only discovery"),
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
            gate_id == "OA-01",
            "gate-specific observable adapter is implemented"
            if gate_id == "OA-01" else
            f"{gate_id} functional adapter is expected at its locked implementation gate",
        ),
        assertion(
            "negative_path_adapter",
            gate_id == "OA-01",
            "OA-01 verifies that incomplete production prerequisites do not advance state"
            if gate_id == "OA-01" else
            f"{gate_id} negative-path adapter is not yet implemented",
        ),
        assertion(
            "idempotency_adapter",
            gate_id == "OA-01",
            "OA-01 repeats read-only repository discovery"
            if gate_id == "OA-01" else
            f"{gate_id} idempotency adapter is not yet implemented",
        ),
        assertion(
            "interruption_resume",
            not gate["state_change"],
            "NOT_APPLICABLE: read-only gate has no transition to interrupt"
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
            assertion("published_baseline_mismatch_observed", not state["baseline_matches"],
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
                "next_action_prioritizes_baseline",
                isinstance(state["next_action_probe"], dict)
                and state["next_action_probe"].get(
                    "next_authorized_action", {}
                ).get("code") == "PUBLISH_SIGNED_REPOSITORY_BASELINE",
                "repository baseline reconciliation precedes dispatcher and agent work",
            ),
            assertion(
                "dispatch_remains_disabled",
                isinstance(state["next_action_probe"], dict)
                and state["next_action_probe"].get("operational_dispatch") == "DISABLED",
                "read-only decision must not enable dispatch",
            ),
            assertion(
                "read_only_idempotency",
                all(state[key] == repeated[key] for key in stable_keys),
                "repeated discovery returned the same repository and production state",
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
            projected = dict(item)
            projected["assertion"] = f"regression:{prior_id}:{item['assertion']}"
            assertions.append(projected)
    result, reasons = classify(gate, state, assertions)
    completed = utc_now()
    command_availability = state.pop("command_availability")
    result_value = {
        "schema_version": 1, "contract_version": VERSION, "run_id": run_id,
        "gate": gate["gate_id"], "result": result, "reasons": reasons,
        "assertions": assertions, "manual_review_required": True,
        "state_changed": False,
    }
    manifest = {
        "schema_version": 1, "pmct_version": VERSION, "run_id": run_id,
        "gate": gate["gate_id"], "started_at": time_text(started),
        "completed_at": time_text(completed), "repository": str(REPOSITORY),
        "repository_identity": state["repository"], "branch": state["branch"],
        "head": state["head"], "published_baseline": state["published_baseline"],
        "operator_identity": os.environ.get("USER", "unavailable"),
        "host_identity": socket.gethostname(), "command_availability": command_availability,
        "result": result, "evidence_digest": None,
    }
    write_json(directory / "repository.json", state)
    write_json(directory / "command-discovery.json", command_availability)
    write_json(directory / "assertions.json", assertions)
    write_json(directory / "capability-result.json", result_value)
    commands = [
        {"command": "git rev-parse HEAD", "classification": "read-only"},
        {"command": "git status --short", "classification": "read-only"},
        {"command": "zeus --help", "classification": "read-only"},
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
    return 0 if result["result"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pmct")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect")
    sub.add_parser("list")
    show = sub.add_parser("show"); show.add_argument("gate")
    execute = sub.add_parser("run"); execute.add_argument("gate")
    execute.add_argument("--authorized-transition", action="store_true")
    report = sub.add_parser("report"); report.add_argument("gate")
    args = parser.parse_args(argv)
    try:
        value = matrix()
        gates = {gate["gate_id"]: gate for gate in value["gates"]}
        if args.command == "inspect":
            print(json.dumps(inspect_state(), indent=2, sort_keys=True))
            return 0
        if args.command == "list":
            current = load_state()
            for gate in value["gates"]:
                print(f"{gate['gate_id']}\\t{current['gates'][gate['gate_id']]['status']}\\t{gate['title']}")
            return 0
        gate_id = args.gate.upper()
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
