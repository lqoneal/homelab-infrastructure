#!/usr/bin/env python3
"""Generate the locked PMCT matrix and auditable gate procedure wrappers."""

from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
TITLES = [
    "Assessment recognition and controlled mission transition",
    "First-qualification authority lifecycle",
    "Dispatcher policy resolution",
    "Dispatcher activation",
    "Production execution-agent registry",
    "Production execution-agent qualification",
    "Dispatcher-to-agent invocation",
    "Admission-driven dispatch authorization",
    "Production CLI execution management",
    "Production EENS execution lifecycle",
    "Cryptographically signed execution evidence",
    "Independent evidence qualification",
    "Live authoritative reconciliation",
    "Authority restoration coordination",
    "Integrated production execution foundation",
    "Controlled-document reconciliation",
    "Production implementation commit",
    "Signed repository-baseline republication",
    "Dispatcher commissioning",
    "Production execution-agent activation",
    "Operational qualification mission authorization",
    "Complete operational WOP construction",
    "Admission with dispatch permitted",
    "Zeus dispatches a real operational WOP",
    "Qualified agent executes the WOP",
    "Independent evidence qualification passes",
    "Zeus reconciles authoritative project state",
    "Zeus closes the operational mission",
    "Operational Alpha capability qualification",
    "Operational Alpha declaration",
]
COMMANDS = [
    ["zeus status", "zeus next-action"],
    ["zeus authority status", "zeus authority work-lifecycle"],
    ["zeus dispatcher policy"],
    ["zeus dispatcher activation", "zeus dispatcher status"],
    ["zeus agent registry", "zeus agent status"],
    ["zeus agent qualify", "zeus agent status"],
    ["zeus invocation probe", "zeus agent select"],
    ["zeus admission evaluate", "zeus dispatcher probe"],
    ["zeus dispatcher status", "zeus agent select"],
    ["zeus eens status", "zeus eens self-test"],
    ["zeus evidence self-test"],
    ["zeus qualification self-test"],
    ["zeus reconciliation self-test"],
    ["zeus authority restoration"],
    ["zeus dispatcher probe", "zeus invocation probe"],
    ["zeus reconciliation self-test"],
    ["zeus status"],
    ["zeus authority status"],
    ["zeus dispatcher activation", "zeus dispatcher probe"],
    ["zeus agent qualify", "zeus agent status"],
    ["zeus authority work-lifecycle", "zeus next-action"],
    ["zeus admission evaluate"],
    ["zeus admission evaluate", "zeus dispatcher status"],
    ["zeus invocation probe"],
    ["zeus agent status", "zeus eens status"],
    ["zeus qualification self-test", "zeus evidence self-test"],
    ["zeus reconciliation self-test"],
    ["zeus status", "zeus next-action"],
    ["zeus qualification self-test"],
    ["zeus status", "zeus next-action"],
]


def gate(number: int) -> dict:
    gate_id = f"OA-{number:02d}"
    title = TITLES[number - 1]
    prior = [f"OA-{item:02d}" for item in range(1, number)]
    state_change = number in {4, 6, 18, 19, 20, 24, 25, 27, 28, 30}
    return {
        "gate_id": gate_id,
        "sequence": number,
        "title": title,
        "required_commands": COMMANDS[number - 1],
        "optional_commands": ["zeus status"] if "zeus status" not in COMMANDS[number - 1] else [],
        "prerequisites": [prior[-1]] if prior else [],
        "positive_demonstration": (
            f"Through the authoritative CLI, demonstrate {title.lower()} and "
            "capture the resulting production-observable state."
        ),
        "negative_demonstration": (
            f"Present a malformed, unauthorized, stale, mismatched, or incomplete "
            f"{gate_id} request and verify Zeus rejects it without advancing state."
        ),
        "idempotency_demonstration": (
            f"Repeat the {gate_id} observation or authorized request with the same "
            "identity and verify no duplicate state, event, evidence, or action."
        ),
        "interruption_demonstration": (
            "Read-only: verify repeatable discovery without mutation."
            if not state_change else
            "With explicit transition authority and a controlled object, interrupt "
            "after preflight and verify checkpointed resume without duplicate effects."
        ),
        "evidence_requirements": [
            "repository identity and exact HEAD",
            "command stdout, stderr, and return code",
            f"{gate_id} positive and negative assertions",
            "evidence integrity manifest and completion marker",
        ],
        "regression_gates": prior,
        "allowed_results": ["PASS", "FAIL", "BLOCKED", "NOT_READY"],
        "manual_review_required": True,
        "state_change": state_change,
    }


def main() -> None:
    gates = [gate(number) for number in range(1, 31)]
    value = {
        "test_name": "ZEUS_PROGRESSIVE_MANUAL_CAPABILITY_TEST",
        "contract_version": "1.0",
        "sequence_locked": True,
        "cumulative": True,
        "production_cli_contract": [
            command for commands in COMMANDS for command in commands
        ],
        "gates": gates,
    }
    value["production_cli_contract"] = list(dict.fromkeys(value["production_cli_contract"]))
    (ROOT / "PMCT-CAPABILITY-MATRIX.yaml").write_text(
        yaml.safe_dump(value, sort_keys=False, width=1000), encoding="utf-8"
    )
    gate_directory = ROOT / "gates"
    gate_directory.mkdir(parents=True, exist_ok=True)
    for item in gates:
        requirements = ", ".join(item["required_commands"])
        content = f"""#!/usr/bin/env bash
# Gate identity: {item['gate_id']}
# Capability statement: {item['title']}
# Current applicability: discovered at runtime; unavailable future interfaces produce NOT_READY.
# Required authority: controlled PMCT read-only authority; state changes require --authorized-transition.
# Required commands: {requirements}
# Required artifacts: run manifest, repository, discovery, assertions, result, report, hashes, COMPLETE.
# Preconditions: exact repository identity and prior gate PASS where required.
# Positive path: {item['positive_demonstration']}
# Negative path: {item['negative_demonstration']}
# Idempotency: {item['idempotency_demonstration']}
# Interruption/recovery: {item['interruption_demonstration']}
# Regression scope: {', '.join(item['regression_gates']) or 'none'}
# Evidence requirements: {'; '.join(item['evidence_requirements'])}
# PASS: all mandatory observable assertions pass and evidence is complete.
# FAIL: an available required capability behaves incorrectly or unsafely.
# BLOCKED: repository identity, authority, or prerequisite prevents evaluation.
# NOT READY: a mandatory acceptance interface or demonstration is unavailable.
# Manual review: inspect terminal result, report, assertions, and artifacts.sha256.
set -u
set -o pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${{BASH_SOURCE[0]}}")" && pwd -P)"
exec "${{SCRIPT_DIR}}/../bin/pmct" run "{item['gate_id']}" "$@"
"""
        path = gate_directory / f"{item['gate_id']}.sh"
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
