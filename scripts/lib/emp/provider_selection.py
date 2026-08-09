"""P5-G1 provider selection foundation.

This module adapts the existing integrity-bound execution-agent registry to
the canonical Beta mission chain.  It materializes only provider-selection
evidence; it never creates a session, dispatch, or execution.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.production_execution import ProductionExecutionError, validate_agent
from scripts.lib.emp.mission_verification_controller import verify as verify_mission
from scripts.lib.emp.repository_identity import resolve as repository_identity
from scripts.lib.eos.canonical_baseline import (
    resolve as resolve_baseline,
    resolve_commit_lineage,
    resolve_provenance_lineage,
)
from scripts.lib.eos import operational_beta
from scripts.lib.emp.runtime_paths import resolve_runtime


POLICY_ID = "ZEUS-P5-G1-PROVIDER-SELECTION"
POLICY_VERSION = "1"
REGISTRY_RELATIVE = Path("engineering/dispatch/execution-agent-registry.json")
STAGE_DIRS = {
    "provider_selection": "provider-selection",
    "selected_provider": "selected-providers",
    "provider_qualification": "provider-qualifications",
    "provider_selection_receipt": "provider-selection-receipts",
    "provider_selection_journal": "provider-selection-journals",
    "dispatch_readiness": "dispatch-readiness",
}
ARTIFACT_TYPES = {
    "provider_selection": "provider-selection-transaction",
    "selected_provider": "selected-provider",
    "provider_qualification": "provider-qualification",
    "provider_selection_receipt": "provider-selection-receipt",
    "provider_selection_journal": "provider-selection-journal",
    "dispatch_readiness": "dispatch-readiness",
}


class ProviderSelectionError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code = code
        self.message = message
        self.next_action = next_action
        super().__init__(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProviderSelectionError("PROVIDER_ARTIFACT_INVALID", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ProviderSelectionError("PROVIDER_ARTIFACT_INVALID", f"{path} is not an object")
    return value


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    data = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    if runtime_root:
        return Path(runtime_root).resolve()
    raw = os.environ.get("ZEUS_RUNTIME_ROOT")
    if raw:
        return Path(raw).resolve()
    return Path(resolve_runtime(root, require_writable=False)["root"]).resolve()


def _mission_artifacts(runtime: Path, mission_id: str) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    found: dict[str, list[tuple[Path, dict[str, Any]]]] = {key: [] for key in STAGE_DIRS}
    for key, directory in STAGE_DIRS.items():
        path = runtime / directory
        for item in sorted(path.glob("*.json")) if path.is_dir() else ():
            value = _load(item)
            if value.get("mission_id") == mission_id:
                found[key].append((item, value))
    return found


def _scoped_mission_artifacts(
    found: dict[str, list[tuple[Path, dict[str, Any]]]],
    expected: Mapping[str, Any],
) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    """Exclude preserved non-current sets without weakening target checks.

    Provider artifacts are append-only.  A same-mission artifact with a
    different WOP, receipt, admission/bootstrap chain, repository, or
    provenance baseline is historical/subordinate evidence.  The recorded
    current baseline is deliberately not a scoping key: it is immutable
    transition provenance and may be an ancestor of the live published
    baseline after later legitimate publications.  A target artifact that is
    missing one of the stable bindings remains in the current candidate set
    so ``_verify_set`` fails closed instead of silently accepting malformed
    state.
    """
    fields = (
        "mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id",
        "repository_identity", "mission_provenance_baseline",
    )
    scoped: dict[str, list[tuple[Path, dict[str, Any]]]] = {key: [] for key in found}
    for key, items in found.items():
        for path, value in items:
            missing = any(field not in value for field in fields)
            exact = not missing and all(value.get(field) == expected.get(field) for field in fields)
            if exact or missing:
                scoped[key].append((path, value))
    return scoped


def _validate_live_lineage(
    root: Path,
    anchor: Mapping[str, Any],
    *,
    live_lineage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate provider-selection provenance against the live publication.

    ``current_published_baseline`` in a provider-selection artifact records
    the publication observed when that transition was created.  It is not a
    frozen current-state authority.  The live projection is resolved from
    HEAD/origin/EOS and the artifact's recorded baseline must be a reachable
    ancestor of that live projection.  This preserves immutable provider
    evidence while allowing ordinary descendant publications.
    """
    provenance = str(anchor.get("mission_provenance_baseline") or "")
    recorded = str(anchor.get("current_published_baseline") or "")
    if not provenance or not recorded:
        raise ProviderSelectionError(
            "PROVIDER_PROVENANCE_MISSING",
            "provider selection is missing immutable provenance or recorded publication baseline",
        )

    live = dict(live_lineage or resolve_provenance_lineage(root, provenance))
    if live.get("result") != "PASS":
        raise ProviderSelectionError(
            "PROVIDER_LIVE_LINEAGE_INVALID",
            "current repository/EOS lineage is not valid for provider selection",
        )
    current = str(live.get("current_published_baseline") or "")
    recorded_lineage = resolve_commit_lineage(root, recorded, current)
    if recorded_lineage.get("result") != "PASS":
        raise ProviderSelectionError(
            "PROVIDER_RECORDED_BASELINE_INVALID",
            "provider-selection recorded baseline is not an ancestor of the live publication",
        )
    provenance_lineage = resolve_commit_lineage(root, provenance, recorded)
    if provenance_lineage.get("result") != "PASS":
        raise ProviderSelectionError(
            "PROVIDER_PROVENANCE_BASELINE_INVALID",
            "provider-selection provenance baseline does not validate to its recorded publication",
        )
    return {
        "result": "PASS",
        "provenance_baseline": provenance,
        "recorded_published_baseline": recorded,
        "current_published_baseline": current,
        "recorded_baseline_relationship": recorded_lineage.get("baseline_relationship"),
        "live_baseline_relationship": resolve_commit_lineage(root, provenance, current).get("baseline_relationship"),
    }


def _baseline(root: Path, runtime: Path, provenance: str) -> dict[str, Any]:
    marker = _load(runtime / "runtime-identity.json")
    result = resolve_baseline(root, Path(os.environ.get("EOS_WORKSPACE", "/data/engineering")),
                             mission_provenance_baseline=provenance, runtime_identity=marker)
    if result.get("result") != "PASS":
        code = result.get("errors", [{}])[0].get("code", "CURRENT_BASELINE_MISMATCH")
        raise ProviderSelectionError(code, "canonical baseline resolution failed")
    return result


def _inventory(root: Path, baseline: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    path = root / REGISTRY_RELATIVE
    if not path.is_file():
        raise ProviderSelectionError("PROVIDER_INVENTORY_MISSING", str(path))
    value = _load(path)
    if value.get("schema_version") != 2 or not isinstance(value.get("agents"), list):
        raise ProviderSelectionError("PROVIDER_INVENTORY_INVALID", "execution-agent registry shape is invalid")
    unsigned = {key: item for key, item in value.items() if key != "registry_digest"}
    if value.get("registry_digest") != _digest(unsigned):
        raise ProviderSelectionError("PROVIDER_INVENTORY_DIGEST_MISMATCH", "execution-agent registry digest mismatch")
    candidates: list[dict[str, Any]] = []
    for item in sorted(value["agents"], key=lambda candidate: str(candidate.get("agent_id", ""))):
        agent = dict(item)
        reasons: list[str] = []
        agent_id = agent.get("agent_id")
        try:
            validate_agent(agent, mission_class="engineering", repository=str(root))
        except ProductionExecutionError as error:
            reasons.append("QUALIFICATION_INVALID")
        if agent.get("active") is not True:
            reasons.append("PROVIDER_INACTIVE")
        if agent.get("qualification_status") != "QUALIFIED":
            reasons.append("PROVIDER_NOT_QUALIFIED")
        if str(root) not in {str(Path(entry).resolve()) for entry in agent.get("repository_access_scope", [])}:
            reasons.append("REPOSITORY_SCOPE_MISMATCH")
        if "engineering" not in agent.get("supported_mission_classes", []):
            reasons.append("MISSION_CAPABILITY_MISMATCH")
        required_tools = {"zeus-cli", "bounded-artifact-handler"}
        if not required_tools.issubset(set(agent.get("supported_tools", []))):
            reasons.append("TOOL_CAPABILITY_MISMATCH")
        if not agent.get("trust_binding") or not agent.get("eens_identity") or not agent.get("evidence_signing_identity"):
            reasons.append("AUTHENTICATION_READINESS_FAILURE")
        candidates.append({
            "provider_id": agent_id,
            "provider_type": agent.get("agent_type"),
            "eligible": not reasons,
            "exclusion_reasons": sorted(set(reasons)),
            "inventory_record": agent,
            "qualification_digest": (agent.get("qualification_evidence") or [None])[0],
        })
    return str(value["registry_digest"]), candidates


def _authority(root: Path) -> dict[str, Any]:
    value = operational_beta.authority(root, include_current_execution=False)
    if any(value.get(key) != expected for key, expected in {
        "authority_framework": "OPERATION_BETA", "active_operation": "BETA",
        "authority_integrity": "PASS", "authority_resolution": "PASS",
        "authority_digest_validation": "PASS", "authority_source": "Operation Beta",
        "oa_authority": "SUPERSEDED",
    }.items()):
        raise ProviderSelectionError("OPERATION_BETA_AUTHORITY_FAILURE", "published Operation Beta authority chain is invalid")
    if value.get("oa_authority") in {"ACTIVE", "FALLBACK"} or value.get("oa_fallback") == "PERMITTED":
        raise ProviderSelectionError("OA_ACTIVE_AUTHORITY", "Operational Alpha cannot be active or fallback authority")
    return {"framework": "OPERATION_BETA", "active_operation": "BETA", "integrity": "PASS", "oa_authority": "SUPERSEDED", "oa_fallback": "PROHIBITED", "source": "Operation Beta"}


def _common(mission: Mapping[str, Any], selection_id: str, provider_id: str, provider_type: str,
            policy: str, registry_digest: str, baseline: Mapping[str, Any], evaluation: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1, "mission_id": mission["mission_id"], "wop_id": mission["wop_id"],
        "submission_id": mission["submission_id"], "admission_id": mission["admission_id"],
        "bootstrap_id": mission["bootstrap_id"], "operation": "BETA",
        "authority_framework": "OPERATION_BETA", "oa_authority": "SUPERSEDED", "oa_fallback": "PROHIBITED",
        "repository_identity": baseline["identity"]["canonical_repository_identity"],
        "current_published_baseline": baseline["published_head"],
        "mission_provenance_baseline": baseline["mission_provenance_baseline"],
        "mission_baseline_relationship": baseline["mission_baseline_relationship"],
        "provider_selection_id": selection_id, "provider_id": provider_id, "provider_type": provider_type,
        "selection_policy": {"id": POLICY_ID, "version": POLICY_VERSION},
        "registry_digest": registry_digest, "candidate_evaluation": evaluation,
        "provider_selected": True, "provider_qualified": True,
        "dispatch_eligible": True, "provider_session_created": False,
        "dispatch_created": False, "execution_started": False,
    }


def _expected(runtime: Path, mission: Mapping[str, Any], baseline: dict[str, Any], registry_digest: str,
              evaluation: list[dict[str, Any]], selected: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    identity_material = {"mission_id": mission["mission_id"], "bootstrap_id": mission["bootstrap_id"],
                         "registry_digest": registry_digest, "policy": [POLICY_ID, POLICY_VERSION],
                         "candidate_evaluation": evaluation, "provider_id": selected["provider_id"]}
    selection_id = "PROVIDER-SELECTION-" + str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(identity_material, sort_keys=True, separators=(",", ":"))))
    common = _common(mission, selection_id, selected["provider_id"], selected["provider_type"], POLICY_ID, registry_digest, baseline, evaluation)
    selected_record = dict(common, artifact_type=ARTIFACT_TYPES["selected_provider"], provider=selected["inventory_record"])
    qualification = dict(common, artifact_type=ARTIFACT_TYPES["provider_qualification"], qualification_result="PASS",
                         qualification_checks={"identity":"PASS", "capability":"PASS", "authority":"PASS", "baseline":"PASS", "authentication":"PASS", "downstream_boundary":"PASS"})
    receipt = dict(common, artifact_type=ARTIFACT_TYPES["provider_selection_receipt"], result="PASS", receipt_type="provider-selection")
    journal = dict(common, artifact_type=ARTIFACT_TYPES["provider_selection_journal"], states=["PROVIDER_SELECTION_EVALUATING", "PROVIDER_SELECTED", "PROVIDER_QUALIFIED", "READY_FOR_PROVIDER_DISPATCH"], provisioned=[])
    readiness = dict(common, artifact_type=ARTIFACT_TYPES["dispatch_readiness"], readiness_state="READY_FOR_PROVIDER_DISPATCH", next_action="EVALUATE_PROVIDER_DISPATCH")
    transaction = dict(common, artifact_type=ARTIFACT_TYPES["provider_selection"], transaction_type="provider-selection", provider_selection_state="READY_FOR_PROVIDER_DISPATCH", provider_selection_result="PASS", next_action="EVALUATE_PROVIDER_DISPATCH")
    values = {"selected_provider": selected_record, "provider_qualification": qualification, "provider_selection_receipt": receipt, "provider_selection_journal": journal, "dispatch_readiness": readiness, "provider_selection": transaction}
    for key, value in values.items():
        value["artifact_digest"] = _digest(value)
    journal["provisioned"] = [values[key]["artifact_digest"] for key in ("provider_selection", "selected_provider", "provider_qualification", "provider_selection_receipt", "dispatch_readiness")]
    journal["artifact_digest"] = _digest({k: v for k, v in journal.items() if k != "artifact_digest"})
    transaction["artifacts"] = {key: {"path": str((runtime / STAGE_DIRS[key] / f"{selection_id}.json").resolve()), "digest": values[key]["artifact_digest"]} for key in values if key != "provider_selection"}
    transaction["artifact_digest"] = _digest({k: v for k, v in transaction.items() if k != "artifact_digest"})
    return values


def _verify_set(runtime: Path, found: dict[str, list[tuple[Path, dict[str, Any]]]]) -> dict[str, Any] | None:
    if not any(found.values()):
        return None
    if any(len(items) != 1 for items in found.values()):
        raise ProviderSelectionError("PROVIDER_SELECTION_CARDINALITY_CONFLICT", "provider-selection artifact cardinality conflicts")
    values = {key: items[0][1] for key, items in found.items()}
    if any(value.get("artifact_type") != ARTIFACT_TYPES[key] for key, value in values.items()):
        raise ProviderSelectionError("PROVIDER_SELECTION_ARTIFACT_MISMATCH", "provider-selection artifact type mismatch")
    for key, value in values.items():
        if value.get("artifact_digest") != _digest({k: v for k, v in value.items() if k != "artifact_digest"}):
            raise ProviderSelectionError("PROVIDER_SELECTION_DIGEST_MISMATCH", f"{key} digest mismatch")
    anchor = values["provider_selection"]
    selection_id = anchor.get("provider_selection_id")
    for key, items in found.items():
        if items[0][0].name != f"{selection_id}.json" or items[0][0].parent.name != STAGE_DIRS[key]:
            raise ProviderSelectionError("PROVIDER_SELECTION_PATH_INVALID", f"{key} canonical filename or path is invalid")
    for key, descriptor in anchor.get("artifacts", {}).items():
        if key not in found or descriptor.get("digest") != values[key].get("artifact_digest"):
            raise ProviderSelectionError("PROVIDER_SELECTION_ARTIFACT_MISMATCH", f"{key} descriptor is invalid")
        if Path(str(descriptor.get("path"))).resolve() != found[key][0][0].resolve():
            raise ProviderSelectionError("PROVIDER_SELECTION_PATH_INVALID", f"{key} descriptor path is invalid")
    for value in values.values():
        if any(value.get(field) != anchor.get(field) for field in ("mission_id", "bootstrap_id", "provider_selection_id", "provider_id", "registry_digest")):
            raise ProviderSelectionError("PROVIDER_SELECTION_IDENTITY_MISMATCH", "provider-selection identity chain mismatch")
    if anchor.get("provider_selection_state") != "READY_FOR_PROVIDER_DISPATCH" or not anchor.get("dispatch_eligible") or anchor.get("provider_session_created") or anchor.get("dispatch_created") or anchor.get("execution_started"):
        raise ProviderSelectionError("PROVIDER_SELECTION_BOUNDARY_FAILURE", "provider-selection chain crosses or omits the dispatch boundary")
    return {"result": "PASS", "replay": "IDEMPOTENT", "provider_selection_id": anchor["provider_selection_id"], "provider_id": anchor["provider_id"], "provider_selected": True, "provider_qualified": True, "provider_selection_state": anchor.get("provider_selection_state"), "provider_selection_result": anchor.get("provider_selection_result"), "dispatch_eligible": True, "provider_session_created": False, "dispatch_created": False, "execution_started": False, "artifacts": {key: {"path": str(items[0][0]), "digest": items[0][1]["artifact_digest"]} for key, items in found.items()}, "selection_policy": anchor.get("selection_policy"), "candidate_evaluation": anchor.get("candidate_evaluation")}


def verify(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve(); mission_id = str(mission_id).upper(); runtime = _runtime(root, runtime_root)
    blockers: list[dict[str, str]] = []
    try:
        base = verify_mission(root, mission_id, runtime_root=runtime)
        if base.get("result") != "PASS":
            raise ProviderSelectionError("MISSION_VERIFICATION_FAILURE", "canonical mission verification is not PASS")
        if base.get("authority", {}).get("framework") != "OPERATION_BETA" or base.get("authority", {}).get("oa_authority") != "SUPERSEDED":
            raise ProviderSelectionError("OPERATION_BETA_AUTHORITY_FAILURE", "Operation Beta authority is not valid")
        lifecycle = base.get("lifecycle", {})
        if lifecycle.get("bootstrap_state") != "READY_FOR_EXECUTION_PROVIDER" or lifecycle.get("provider_ready") is not True:
            raise ProviderSelectionError("PROVIDER_READINESS_INVALID", "mission is not ready for provider selection")
        expected = {
            "mission_id": mission_id,
            "wop_id": base.get("wop_id"),
            "submission_id": base.get("submission_id"),
            "admission_id": base.get("admission_id"),
            "bootstrap_id": base.get("bootstrap_id"),
            "repository_identity": str(root),
            "mission_provenance_baseline": base.get("repository", {}).get("mission_provenance_baseline"),
            "current_published_baseline": base.get("repository", {}).get("published_baseline"),
        }
        found = _scoped_mission_artifacts(_mission_artifacts(runtime, mission_id), expected)
        existing = _verify_set(runtime, found)
        if existing:
            provider_path = Path(existing["artifacts"]["provider_selection"]["path"])
            provider_anchor = _load(provider_path)
            lineage = _validate_live_lineage(root, provider_anchor)
            return {**existing, "schema_version": 1, "mission_id": mission_id, "read_only": True, "result": "PASS", "blockers": [], "next_authorized_action": "EVALUATE_PROVIDER_DISPATCH", "provider_selection_lineage": lineage}
        provenance = base.get("repository", {}).get("mission_provenance_baseline")
        baseline = _baseline(root, runtime, provenance)
        registry_digest, candidates = _inventory(root, baseline)
        eligible = [item for item in candidates if item["eligible"]]
        if not eligible:
            raise ProviderSelectionError("NO_ELIGIBLE_PROVIDER", "provider inventory contains no eligible provider")
        eligible.sort(key=lambda item: (str(item["provider_id"]), str(item["provider_type"])))
        selected = eligible[0]
        if len(eligible) > 1 and len({(item["provider_id"], item["provider_type"]) for item in eligible}) != len(eligible):
            raise ProviderSelectionError("AMBIGUOUS_PROVIDER_SELECTION", "provider ranking is not unique")
        return {"schema_version": 1, "result": "PASS", "read_only": True, "mission_id": mission_id,
                "provider_selected": False, "provider_qualified": False, "dispatch_eligible": False,
                "selection_policy": {"id": POLICY_ID, "version": POLICY_VERSION}, "registry_digest": registry_digest,
                "candidate_evaluation": candidates, "eligible_provider": selected["provider_id"], "blockers": [],
                "next_authorized_action": "MATERIALIZE_PROVIDER_SELECTION"}
    except ProviderSelectionError as error:
        blockers.append({"code": error.code, "message": error.message})
        return {"schema_version": 1, "result": "FAIL", "read_only": True, "mission_id": mission_id,
                "provider_selected": False, "provider_qualified": False, "dispatch_eligible": False,
                "blockers": blockers, "next_authorized_action": error.next_action}


def select(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve(); runtime = _runtime(root, runtime_root); mission_id = str(mission_id).upper()
    preview = verify(root, mission_id, runtime_root=runtime)
    if preview.get("result") != "PASS":
        return preview
    base = verify_mission(root, mission_id, runtime_root=runtime)
    expected = {
        "mission_id": mission_id,
        "wop_id": base.get("wop_id"),
        "submission_id": base.get("submission_id"),
        "admission_id": base.get("admission_id"),
        "bootstrap_id": base.get("bootstrap_id"),
        "repository_identity": str(root),
        "mission_provenance_baseline": base.get("repository", {}).get("mission_provenance_baseline"),
        "current_published_baseline": base.get("repository", {}).get("published_baseline"),
    }
    found = _scoped_mission_artifacts(_mission_artifacts(runtime, mission_id), expected)
    existing = _verify_set(runtime, found)
    if existing:
        provider_path = Path(existing["artifacts"]["provider_selection"]["path"])
        provider_anchor = _load(provider_path)
        lineage = _validate_live_lineage(root, provider_anchor)
        return {**existing, "read_only": False, "duplicate_provider_selection": "IDEMPOTENT", "next_authorized_action": "EVALUATE_PROVIDER_DISPATCH", "provider_selection_lineage": lineage}
    baseline = _baseline(root, runtime, base["repository"]["mission_provenance_baseline"])
    registry_digest, candidates = _inventory(root, baseline)
    eligible = sorted((item for item in candidates if item["eligible"]), key=lambda item: (str(item["provider_id"]), str(item["provider_type"])))
    if not eligible:
        return {"schema_version": 1, "result": "FAIL", "read_only": False, "mission_id": mission_id, "blockers": [{"code": "NO_ELIGIBLE_PROVIDER", "message": "provider inventory contains no eligible provider"}], "next_authorized_action": "STOP_FAIL_CLOSED"}
    selected = eligible[0]
    mission = {key: base[key] for key in ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id")}
    values = _expected(runtime, mission, baseline, registry_digest, candidates, selected)
    found = _scoped_mission_artifacts(_mission_artifacts(runtime, mission_id), expected)
    if any(found.values()):
        _verify_set(runtime, found)
    for key, value in values.items():
        path = runtime / STAGE_DIRS[key] / f"{value['provider_selection_id']}.json"
        if path.exists() and _load(path) != value:
            raise ProviderSelectionError("CONFLICTING_PROVIDER_SELECTION", f"existing artifact conflicts: {path}")
        if not path.exists():
            _write_immutable(path, value)
    result = _verify_set(runtime, _scoped_mission_artifacts(_mission_artifacts(runtime, mission_id), expected))
    if not result:
        raise ProviderSelectionError("PARTIAL_PROVIDER_SELECTION", "provider-selection artifact set is incomplete")
    provider_path = Path(result["artifacts"]["provider_selection"]["path"])
    lineage = _validate_live_lineage(root, _load(provider_path))
    return {**result, "read_only": False, "duplicate_provider_selection": "NO", "next_authorized_action": "EVALUATE_PROVIDER_DISPATCH", "provider_selection_lineage": lineage}
