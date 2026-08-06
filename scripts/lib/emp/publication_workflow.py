"""Read-only Zeus publication and reconciliation verification.

This module owns the publication *observation* contract.  Repository and EOS
mutation remain with the governed publication procedure and ``engctl``.  The
controller deliberately invokes only supported operator commands or their
canonical read-only services; it never commits, pushes, synchronizes EOS, or
changes mission/runtime state.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from scripts.lib.emp.mission_verification_controller import verify as verify_mission
from scripts.lib.emp.provider_selection import verify as verify_provider
from scripts.lib.emp.dispatch_foundation import verify as verify_dispatch
from scripts.lib.emp.provider_session import verify as verify_provider_session
from scripts.lib.emp.provider_invocation import verify as verify_provider_invocation
from scripts.lib.eos import operational_beta
from scripts.lib.eos.canonical_baseline import resolve as resolve_baseline
from scripts.lib.eos.platform_sync_verification import verify as verify_platform
from scripts.lib.emp.runtime_paths import resolve_runtime


OBSOLETE_VALIDATION_PATHS = ("scripts/validate-engineering-platform.py",)
CANONICAL_COMMANDS = {
    "platform": "scripts/zeus platform verify",
    "authority": "scripts/zeus authority validate",
    "registry": "scripts/engctl registry validate",
    "integrated": "scripts/engctl validate homelab",
    "eos": "scripts/engctl eos validate homelab",
    "eos_sync_validate": "scripts/engctl eos sync-validate homelab",
    "mission": "scripts/zeus mission verify <MISSION_ID>",
    "provider": "scripts/zeus provider verify <MISSION_ID>",
    "provider_session": "scripts/zeus provider-session verify <MISSION_ID>",
    "provider_invocation": "scripts/zeus provider-invocation verify <MISSION_ID>",
}
AUTHORIZED_CANDIDATE_PATHS = frozenset({
    "engineering/docs/cli/ZEUS-USER-GUIDE.md",
    "engineering/evidence/operation-beta/p5-g2-provider-dispatch-foundation-completion-report.md",
    "scripts/zeus",
    "scripts/lib/emp/canonical_runtime_mission.py",
    "scripts/lib/emp/mission_verification_controller.py",
    "scripts/lib/emp/publication_workflow.py",
    "scripts/lib/emp/dispatch_foundation.py",
    "scripts/lib/emp/canonical_runtime_mission.py",
    "scripts/lib/emp/provider_session.py",
    "scripts/lib/emp/provider_invocation.py",
    "scripts/lib/eos/canonical_baseline.py",
    "scripts/tests/test-zeus-mission-verification-controller.py",
    "scripts/tests/test-zeus-p4-g3-runtime-discovery.py",
    "scripts/tests/test-zeus-p5-g1-provider-selection.py",
    "scripts/tests/test-zeus-p5-g2-dispatch-foundation.py",
    "scripts/tests/test-zeus-p5-g3-provider-session.py",
    "engineering/evidence/operation-beta/p5-g3-provider-session-foundation-completion-report.md",
    "scripts/zeus",
    "engineering/docs/cli/ZEUS-USER-GUIDE.md",
    "scripts/tests/test-zeus-p5-g4-provider-invocation.py",
    "scripts/tests/test-zeus-canonical-baseline-resolution.py",
    "engineering/evidence/operation-beta/p5-g4-provider-invocation-foundation-completion-report.md",
    "engineering/evidence/operation-beta/p5-g4-post-publication-invocation-baseline-reconciliation-completion-report.md",
})


def _command(root: Path, *args: str) -> dict[str, Any]:
    """Run one documented, read-only operator command and capture its result."""
    try:
        result = subprocess.run(
            [str(root / args[0]), *args[1:]],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return {"result": "FAIL", "returncode": 127, "stdout": "", "stderr": str(error), "error_code": "VALIDATION_ENTRY_POINT_MISSING"}
    return {
        "result": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": " ".join([str(root / args[0]), *args[1:]]),
    }


def _scope(root: Path) -> dict[str, Any]:
    result = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True, check=False)
    entries = [line[3:] if len(line) > 3 else line for line in result.stdout.splitlines() if line]
    unauthorized = sorted(set(entries) - AUTHORIZED_CANDIDATE_PATHS)
    valid = not unauthorized
    return {
        "result": "PASS" if valid else "FAIL",
        "clean": not entries,
        "paths": entries,
        "authorized": not unauthorized,
        "unauthorized_paths": unauthorized,
        "reason": "worktree is clean" if not entries else ("all candidate changes are within the accepted combined-publication scope" if valid else "unpublished changes are outside the accepted combined-publication scope"),
        "blocker": None if valid else "CANDIDATE_SCOPE_FAILURE",
    }


def _authority(root: Path) -> dict[str, Any]:
    """Resolve the published authority chain, never session-local authority."""
    try:
        value = operational_beta.authority(root)
    except Exception as error:  # authority service projects typed failures variably across generations
        return {"result": "FAIL", "authority_integrity": "FAIL", "authority_resolution": "FAIL", "reason": str(error)}
    valid = (
        value.get("result") == "PASS"
        and value.get("authority_framework") == "OPERATION_BETA"
        and value.get("active_operation") == "BETA"
        and value.get("authority_integrity") == "PASS"
        and value.get("authority_resolution") == "PASS"
        and value.get("authority_digest_validation") == "PASS"
        and value.get("oa_authority") == "SUPERSEDED"
    )
    return {**value, "result": "PASS" if valid else "FAIL", "authority_source": "published Operation Beta authority chain"}


def _validator_result(root: Path, name: str, command: tuple[str, ...]) -> dict[str, Any]:
    value = _command(root, *command)
    value["validator"] = name
    value["contract"] = CANONICAL_COMMANDS[name]
    if value.get("returncode") == 127:
        value["blocker"] = "VALIDATION_ENTRY_POINT_MISSING"
    elif value.get("result") != "PASS":
        value["blocker"] = {
            "registry": "INTEGRATED_VALIDATION_FAILURE",
            "integrated": "INTEGRATED_VALIDATION_FAILURE",
            "eos": "EOS_VALIDATION_FAILURE",
            "eos_sync_validate": "EOS_VALIDATION_FAILURE",
        }.get(name, "PRE_PUBLICATION_VALIDATION_FAILURE")
    return value


def _projection_schema(root: Path, mission_id: str) -> dict[str, Any]:
    """Validate each public projection against its own response schema."""
    commands = {
        "status": ("scripts/zeus", "mission", "status", mission_id, "--json"),
        "lifecycle": ("scripts/zeus", "mission", "lifecycle", mission_id, "--json"),
        "next": ("scripts/zeus", "mission", "next", mission_id, "--json"),
        "snapshot": ("scripts/zeus", "mission", "snapshot", mission_id, "--json"),
        "verify": ("scripts/zeus", "mission", "verify", mission_id, "--json"),
    }
    required = {
        "status": ("provider_session_created", "provider_invoked", "execution_started"),
        "lifecycle": ("lifecycle",),
        "next": ("next_authorized_action",),
        "snapshot": ("provider_session_id", "provider_invocation_id"),
        "verify": ("mission_verification",),
    }
    results: dict[str, Any] = {}
    blockers: list[dict[str, str]] = []
    for name, command in commands.items():
        observed = _command(root, *command)
        item: dict[str, Any] = {"result": observed.get("result"), "returncode": observed.get("returncode"), "command": observed.get("command")}
        if observed.get("returncode") != 0:
            item["reason"] = observed.get("stderr", "command failed").strip() or "command failed"
            blockers.append({"code": "PROJECTION_COMMAND_FAILURE", "message": f"{name}: {item['reason']}"})
        else:
            try:
                value = __import__("json").loads(observed.get("stdout", ""))
                missing = [key for key in required[name] if key not in value]
                if name == "verify" and value.get("mission_verification") != "PASS":
                    missing.append("mission_verification=PASS")
                if missing:
                    item["result"] = "FAIL"
                    item["missing"] = missing
                    blockers.append({"code": "PROJECTION_SCHEMA_FAILURE", "message": f"{name}: missing {', '.join(missing)}"})
                else:
                    item["result"] = "PASS"
            except (TypeError, ValueError) as error:
                item["result"] = "FAIL"
                item["reason"] = str(error)
                blockers.append({"code": "PROJECTION_JSON_FAILURE", "message": f"{name}: {error}"})
        results[name] = item
    return {"result": "PASS" if not blockers else "FAIL", "commands": results, "blockers": blockers}


def verify(root: Path | str, mission_id: str) -> dict[str, Any]:
    """Verify the current publication/reconciliation state without mutation."""
    root = Path(root).resolve()
    blockers: list[dict[str, str]] = []
    scope = _scope(root)
    if scope["blocker"]:
        blockers.append({"code": scope["blocker"], "message": scope["reason"]})

    try:
        runtime = resolve_runtime(root, require_writable=False)
        runtime_check = {"result": "PASS", "root": str(runtime["root"]), "identity": runtime["identity"]}
        baseline = resolve_baseline(root, Path("/data/engineering"), "homelab", runtime_identity=runtime["identity"])
    except Exception as error:
        runtime_check = {"result": "FAIL", "reason": str(error)}
        baseline = {"result": "FAIL", "errors": [{"code": "RUNTIME_REPOSITORY_BINDING_MISMATCH", "message": str(error)}], "current_head": None, "published_head": None, "eos_baseline": None, "publication_parity": "FAIL", "eos_parity": "FAIL", "runtime_binding": "FAIL"}
    for error in baseline.get("errors", []):
        blockers.append({"code": error["code"], "message": error["message"]})

    authority = _authority(root)
    if authority.get("result") != "PASS":
        blockers.append({"code": "AUTHORITY_INTEGRITY_FAILURE", "message": authority.get("reason", "published authority chain failed")})

    platform = verify_platform(root, Path("/data/engineering"), "homelab")
    if platform.get("result") != "PASS":
        blockers.append({"code": "POST_SYNC_PLATFORM_FAILURE", "message": "; ".join(platform.get("defects", []))})
    mission = verify_mission(root, mission_id)
    if mission.get("result") != "PASS":
        blockers.extend({"code": item.get("code", "POST_SYNC_MISSION_FAILURE"), "message": item.get("message", "mission verification failed")} for item in mission.get("blockers", []))
    provider = verify_provider(root, mission_id)
    if provider.get("result") != "PASS":
        blockers.append({"code": "POST_SYNC_STAGE_FAILURE", "message": "provider verification failed"})
    dispatch = verify_dispatch(root, mission_id)
    if dispatch.get("result") != "PASS":
        blockers.append({"code": "POST_SYNC_STAGE_FAILURE", "message": "dispatch verification failed"})
    provider_session = verify_provider_session(root, mission_id)
    if provider_session.get("result") != "PASS":
        blockers.append({"code": "POST_SYNC_STAGE_FAILURE", "message": "provider-session verification failed"})
    provider_invocation = verify_provider_invocation(root, mission_id)
    if provider_invocation.get("result") != "PASS" and provider_invocation.get("provider_invocation_created") is not False:
        blockers.append({"code": "POST_SYNC_STAGE_FAILURE", "message": "provider-invocation verification failed"})
    projection_schema = _projection_schema(root, mission_id)
    blockers.extend(projection_schema.get("blockers", []))

    validators = {
        "registry": _validator_result(root, "registry", ("scripts/engctl", "registry", "validate")),
        "integrated": _validator_result(root, "integrated", ("scripts/engctl", "validate", "homelab")),
        "eos": _validator_result(root, "eos", ("scripts/engctl", "eos", "validate", "homelab")),
        "eos_sync_validate": _validator_result(root, "eos_sync_validate", ("scripts/engctl", "eos", "sync-validate", "homelab")),
    }
    for value in validators.values():
        if value.get("result") != "PASS":
            blockers.append({"code": value.get("blocker", "INTEGRATED_VALIDATION_FAILURE"), "message": value.get("stderr", "canonical validator failed").strip() or value.get("validator", "validator") + " failed"})

    obsolete = {path: not (root / path).exists() for path in OBSOLETE_VALIDATION_PATHS}
    if any(not missing for missing in obsolete.values()):
        blockers.append({"code": "UNSUPPORTED_VALIDATION_COMMAND", "message": "obsolete validation entry point exists"})

    all_pass = not blockers
    candidate_present = bool(scope["paths"])
    return {
        "schema_version": 1,
        "result": "PASS" if all_pass else "FAIL",
        "read_only": True,
        "mission_id": mission_id,
        "publication_state": ("READY_TO_PUBLISH" if candidate_present else "PUBLICATION_RECONCILED") if all_pass else "PUBLICATION_VERIFICATION_FAILED",
        "publication_replay": "IDEMPOTENT" if all_pass and not candidate_present else ("NOT_APPLICABLE" if all_pass else "NOT_ESTABLISHED"),
        "push_required": candidate_present,
        "eos_sync_required": False if baseline.get("eos_parity") == "PASS" else True,
        "repository": {
            "current_head": baseline.get("current_head"),
            "published_baseline": baseline.get("published_head"),
            "origin_main": baseline.get("published_head"),
            "eos_baseline": baseline.get("eos_baseline"),
            "publication_parity": baseline.get("publication_parity"),
            "eos_parity": baseline.get("eos_parity"),
            "runtime_binding": baseline.get("runtime_binding"),
        },
        "candidate_scope": scope,
        "authority": authority,
        "runtime": runtime_check,
        "validators": validators,
        "platform_verification": platform.get("result"),
        "mission_verification": mission.get("result"),
        "stage_verification": "PASS" if provider.get("result") == "PASS" and dispatch.get("result") == "PASS" and provider_session.get("result") == "PASS" and provider_invocation.get("result") == "PASS" else "FAIL",
        "dispatch_verification": dispatch.get("result"),
        "provider_session_verification": provider_session.get("result"),
        "provider_invocation_verification": provider_invocation.get("result"),
        "final_projection_schema_verification": projection_schema.get("result"),
        "mission": {"result": mission.get("result"), "next_authorized_action": mission.get("next_authorized_action"), "blockers": mission.get("blockers", [])},
        "provider": {"result": provider.get("result"), "provider_id": provider.get("provider_id"), "provider_selected": provider.get("provider_selected"), "dispatch_created": provider.get("dispatch_created"), "execution_started": provider.get("execution_started"), "next_authorized_action": provider.get("next_authorized_action")},
        "dispatch": {"result": dispatch.get("result"), "dispatch_id": dispatch.get("dispatch_id"), "dispatch_state": dispatch.get("dispatch_state"), "dispatch_created": bool(dispatch.get("dispatch_id")), "provider_session_created": dispatch.get("provider_session_created"), "provider_invoked": dispatch.get("provider_invoked"), "execution_started": dispatch.get("execution_started"), "next_authorized_action": dispatch.get("next_authorized_action")},
        "provider_session": {"result": provider_session.get("result"), "provider_session_id": provider_session.get("provider_session_id"), "provider_session_created": provider_session.get("provider_session_created"), "provider_session_authorized": provider_session.get("provider_session_authorized"), "provider_invoked": provider_session.get("provider_invoked"), "execution_started": provider_session.get("execution_started"), "next_authorized_action": provider_session.get("next_authorized_action")},
        "provider_invocation": {"result": provider_invocation.get("result"), "provider_invocation_id": provider_invocation.get("provider_invocation_id"), "provider_invocation_state": provider_invocation.get("provider_invocation_state"), "provider_invoked": provider_invocation.get("provider_invoked"), "provider_acknowledged": provider_invocation.get("provider_acknowledged"), "execution_started": provider_invocation.get("execution_started"), "next_authorized_action": provider_invocation.get("next_authorized_action")},
        "final_projection": projection_schema,
        "obsolete_entry_points": obsolete,
        "canonical_commands": CANONICAL_COMMANDS,
        "blockers": blockers,
        "next_authorized_action": ("REVIEW_AND_PUBLISH_COMBINED_CANDIDATE" if all_pass and candidate_present else mission.get("next_authorized_action")) if all_pass else "Resolve the reported publication verification blocker",
    }


def render(value: dict[str, Any]) -> str:
    repository = value.get("repository", {})
    validators = value.get("validators", {})
    provider = value.get("provider", {})
    blockers = value.get("blockers", [])
    return "\n".join((
        "Zeus Publication Verification", "------------------------------",
        f"Result                 : {value.get('result')}",
        f"Publication state      : {value.get('publication_state')}",
        f"Current baseline       : {repository.get('current_head')}",
        f"Origin/main            : {repository.get('origin_main')}",
        f"EOS baseline           : {repository.get('eos_baseline')}",
        f"Publication parity     : {repository.get('publication_parity')}",
        f"EOS parity             : {repository.get('eos_parity')}",
        f"Candidate scope        : {value.get('candidate_scope', {}).get('result')}",
        f"Platform verification  : {value.get('platform_verification')}",
        f"Registry validation    : {validators.get('registry', {}).get('result')}",
        f"Integrated validation  : {validators.get('integrated', {}).get('result')}",
        f"Mission verification   : {value.get('mission_verification')}",
        f"Provider verification  : {value.get('stage_verification')}",
        f"Provider selected      : {'YES' if provider.get('provider_selected') else 'NO'}",
        f"Dispatch verification  : {value.get('dispatch_verification', 'NOT_RUN')}",
        f"Provider invocation     : {value.get('provider_invocation_verification', 'NOT_RUN')}",
        f"Projection schemas      : {value.get('final_projection_schema_verification', 'NOT_RUN')}",
        f"Dispatch created       : {'YES' if value.get('dispatch', {}).get('dispatch_created') else 'NO'}",
        f"Execution started     : {'YES' if value.get('dispatch', {}).get('execution_started') else 'NO'}",
        f"Replay                 : {value.get('publication_replay')}",
        f"Blockers               : {'NONE' if not blockers else ', '.join(item['code'] for item in blockers)}",
        f"Next action            : {value.get('next_authorized_action')}",
        "Read-only              : YES",
    ))
