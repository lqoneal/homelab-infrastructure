"""Receipt-backed canonical lifecycle resolution for the Zeus mission views.

This module is intentionally read-only.  It consumes the immutable P2/P3/P4
artifacts that already exist, verifies their identity and digest chain, and
projects the furthest contiguous canonical lifecycle state.  Stage 1 and
other historical stores remain compatibility evidence; they cannot advance or
replace the canonical chain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.bootstrap_boundary import BootstrapBoundaryError, _verify_admission
from scripts.lib.emp.bootstrap_verification import verify_bootstrap_replay
from scripts.lib.emp.canonical_authority_receipt import AuthorityReceiptError, resolve as resolve_authority_receipts
from scripts.lib.emp.submission_boundary import SubmissionError, mission_view as p2_mission_view
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.emp.lifecycle_baseline_reconciliation import verify_current, LifecycleBaselineReconciliationError


class CanonicalLifecycleResolutionError(ValueError):
    """Canonical lifecycle evidence is missing, ambiguous, or contradictory."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CanonicalLifecycleResolutionError("CANONICAL_ARTIFACT_INVALID", f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise CanonicalLifecycleResolutionError("CANONICAL_ARTIFACT_INVALID", f"{path} is not an object")
    return value


def _records(directory: Path, mission_id: str) -> list[tuple[Path, dict[str, Any]]]:
    if not directory.is_dir():
        return []
    result = []
    for path in sorted(directory.glob("*.json")):
        try:
            value = _load(path)
        except CanonicalLifecycleResolutionError:
            # A malformed artifact cannot identify a requested mission. It is
            # excluded from this mission's candidate set; a malformed
            # artifact whose identity is later supplied through a canonical
            # descriptor is rejected by the boundary verifier.
            continue
        if str(value.get("mission_id", "")).upper() == mission_id:
            result.append((path, value))
    return result


def _one(directory: Path, mission_id: str, label: str) -> tuple[Path, dict[str, Any]] | None:
    found = _records(directory, mission_id)
    if len(found) > 1:
        raise CanonicalLifecycleResolutionError(
            "CANONICAL_TRANSITION_CARDINALITY_CONFLICT",
            f"{label} has {len(found)} canonical records for {mission_id}",
        )
    return found[0] if found else None


def _current_p4(directory: Path, mission_id: str, canonical_identity: Mapping[str, Any],
                admission_id: str) -> tuple[tuple[Path, dict[str, Any]] | None, dict[str, int]]:
    """Select P4 by the active P2/P3 identity, preserving historical P4 sets."""
    found = _records(directory, mission_id)
    current = [
        item for item in found
        if all(item[1].get(field) == canonical_identity.get(field)
               for field in ("mission_id", "wop_id", "submission_id"))
        and item[1].get("admission_id") == admission_id
    ]
    if len(current) > 1:
        raise CanonicalLifecycleResolutionError(
            "CANONICAL_TRANSITION_CARDINALITY_CONFLICT",
            f"more than one current P4 bootstrap resolves {mission_id}",
        )
    if not current and found:
        raise CanonicalLifecycleResolutionError(
            "CANONICAL_P4_CURRENT_MISSING",
            f"P4 bootstrap records exist for {mission_id}, but none bind to the current P2/P3 chain",
        )
    return (current[0] if current else None,
            {"current": len(current), "historical": len(found) - len(current)})


def _current_p3(directory: Path, mission_id: str, canonical_identity: Mapping[str, Any]) -> tuple[tuple[Path, dict[str, Any]] | None, dict[str, int]]:
    """Select the P3 set linked to the active P2 submission identity.

    P3 directories preserve records across missions and historical revisions.
    For a requested mission, only the set carrying the exact current P2
    mission/WOP/submission identity is current.  Same-mission records with a
    different submission or WOP remain historical/superseded evidence.  More
    than one exact current set is an ambiguity and is rejected.
    """
    found = _records(directory, mission_id)
    current = [
        item for item in found
        if all(item[1].get(field) == canonical_identity.get(field)
               for field in ("mission_id", "wop_id", "submission_id"))
    ]
    if len(current) > 1:
        raise CanonicalLifecycleResolutionError(
            "CANONICAL_TRANSITION_CARDINALITY_CONFLICT",
            f"more than one current P3 admission resolves {mission_id}",
        )
    if not current and found:
        raise CanonicalLifecycleResolutionError(
            "CANONICAL_P3_CURRENT_MISSING",
            f"P3 admission records exist for {mission_id}, but none bind to the current P2 submission",
        )
    return (current[0] if current else None,
            {"current": len(current), "historical": len(found) - len(current)})


def _identity_matches(expected: Mapping[str, Any], observed: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    mismatches = [field for field in fields if expected.get(field) != observed.get(field)]
    if mismatches:
        raise CanonicalLifecycleResolutionError(
            "CANONICAL_IDENTITY_CHAIN_MISMATCH",
            f"{label} differs from the canonical chain: {', '.join(mismatches)}",
        )


def _legacy_projection(runtime: Path, mission_id: str) -> dict[str, Any]:
    """Describe legacy Stage 1 material without allowing it to own state."""
    records = _records(runtime / "stage1", mission_id)
    return {
        "count": len(records),
        "classification": "LEGACY_COMPATIBILITY_PROJECTION" if records else "NONE",
        "current_state_authority": "EXCLUDED_FROM_CANONICAL_CHAIN",
        "paths": [str(path) for path, _ in records],
    }


def _fail(mission_id: str, code: str, message: str, *, chain: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "result": "FAIL",
        "mission_id": mission_id,
        "canonical_lifecycle_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
        "canonical_transition_resolution": "FAIL",
        "blockers": [{"code": code, "message": message}],
        "lifecycle_chain": chain or [],
        "read_only": True,
    }


def resolve(repository: Path | str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Resolve one mission from the contiguous P2/P3/P4 receipt chain.

    The resolver stops at the furthest verified canonical boundary.  It does
    not invoke admission, bootstrap, provider, session, execution, or Stage 1
    mutation, and it never treats a downstream projection as evidence that an
    upstream transition occurred.
    """
    root = Path(repository).resolve()
    mission = str(mission_id).upper()
    try:
        runtime = Path(runtime_root).resolve() if runtime_root is not None else Path(resolve_runtime(root, require_writable=False)["root"]).resolve()
        p2 = p2_mission_view(runtime / "submissions", mission, "snapshot")
    except (OSError, SubmissionError, CanonicalLifecycleResolutionError) as error:
        return _fail(mission, getattr(error, "code", "CANONICAL_RESOLUTION_FAILED"), str(error))

    try:
        p3, p3_cardinality = _current_p3(runtime / "admissions", mission, {
            "mission_id": p2.get("mission_id"),
            "wop_id": p2.get("wop_id"),
            "submission_id": p2.get("submission_id"),
        })
        p4_records = _records(runtime / "bootstraps", mission)
        p4 = None
    except CanonicalLifecycleResolutionError as error:
        return _fail(mission, error.code, str(error))
    downstream_exists = bool(p3 or p4_records or _records(runtime / "stage1", mission))
    if p2.get("result") == "MISSION_NOT_FOUND":
        if downstream_exists:
            return _fail(mission, "CANONICAL_SUBMISSION_MISSING", "downstream lifecycle evidence exists without a canonical P2 submission receipt")
        return p2
    if p2.get("result") != "PASS":
        # Pre-convergence P2-shaped records may coexist with a complete
        # historical P4 runtime.  They have no canonical authority envelope
        # and are therefore an explicit compatibility class, not a current
        # P2 transition.  Let the legacy P4 verifier handle that record; a
        # current canonical receipt with an authority conflict still fails
        # closed below.
        receipt_descriptor = p2.get("submission_receipt")
        legacy_shaped = False
        if isinstance(receipt_descriptor, Mapping) and receipt_descriptor.get("path"):
            try:
                legacy_receipt = _load(Path(str(receipt_descriptor["path"])))
                legacy_shaped = not isinstance(legacy_receipt.get("authority"), Mapping)
            except CanonicalLifecycleResolutionError:
                legacy_shaped = False
        if legacy_shaped and downstream_exists:
            return {"result": "MISSION_NOT_FOUND", "mission_id": mission, "read_only": True,
                    "legacy_p2_projection": "EXPLICIT_COMPATIBILITY_RECORD"}
        p2["canonical_transition_resolution"] = "FAIL"
        p2["canonical_lifecycle_owner"] = "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN"
        return p2

    chain = [{
        "stage": "SUBMITTED",
        "state": p2.get("lifecycle_state"),
        "receipt": p2.get("submission_receipt"),
        "next_action": p2.get("next_authorized_action"),
    }]
    base = dict(p2)
    base.update({
        "canonical_transition_resolution": "PASS",
        "canonical_lifecycle_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
        "canonical_state_source": "P2_SUBMISSION_RECEIPT",
        "historical_projections": "PRESERVED_AND_EXCLUDED_FROM_CURRENT_STATE",
        "legacy_stage1_projection": _legacy_projection(runtime, mission),
        "lifecycle_chain": chain,
        "p3_cardinality": p3_cardinality,
    })
    p2_receipt = _load(Path(p2["submission_receipt"]["path"]))
    canonical_identity = {
        "mission_id": p2_receipt.get("mission_id"),
        "wop_id": p2_receipt.get("wop_id"),
        "submission_id": p2_receipt.get("submission_id"),
    }
    try:
        authority = resolve_authority_receipts(
            [("P2_SUBMISSION_RECEIPT", p2_receipt)],
            expected=canonical_identity,
        )
    except AuthorityReceiptError as error:
        return _fail(mission, error.code, str(error), chain=chain)
    base["authority"] = authority
    base["canonical_authority_receipt"] = {
        "contract": authority["contract"],
        "classification": authority["classification"],
        "source": authority["source"],
        "receipt_digest": authority.get("receipt_digest"),
        "authority_snapshot_digest": authority.get("authority_snapshot_digest"),
        "compatibility": authority.get("compatibility"),
    }

    if p3 is None:
        return base
    admission_path, admission = p3
    try:
        admission_facts = _verify_admission(admission_path, runtime, root)
        admission = admission_facts["transaction"]
        _identity_matches(canonical_identity, admission, ("mission_id", "wop_id", "submission_id"), "P3 admission")
    except (BootstrapBoundaryError, CanonicalLifecycleResolutionError) as error:
        return _fail(mission, getattr(error, "code", "CANONICAL_P3_CHAIN_INVALID"), str(error), chain=chain)

    base.update({
        "admission_id": admission.get("admission_id"),
        "admission_state": admission.get("admission_state"),
        "admission_result": admission.get("admission_result"),
        "lifecycle_state": "ADMITTED",
        "readiness": "ADMITTED",
        "eligibility": "BOOTSTRAP_EVALUATION_PENDING",
        "next_authorized_action": "EVALUATE_BOOTSTRAP_ELIGIBILITY",
        "next_action": "EVALUATE_BOOTSTRAP_ELIGIBILITY",
        "canonical_state_source": "P3_ADMISSION_RECEIPT",
        "admission_transaction": {"path": str(admission_path), "digest": admission.get("transaction_digest")},
        "repository_lineage": admission_facts.get("repository_lineage"),
    })
    chain.append({
        "stage": "ADMITTED",
        "state": "ADMITTED",
        "receipt": {"path": str(admission_path), "digest": admission.get("transaction_digest")},
        "next_action": "EVALUATE_BOOTSTRAP_ELIGIBILITY",
    })

    try:
        p4, p4_cardinality = _current_p4(runtime / "bootstraps", mission, canonical_identity,
                                          admission.get("admission_id"))
    except CanonicalLifecycleResolutionError as error:
        return _fail(mission, error.code, str(error), chain=chain)
    base["p4_cardinality"] = p4_cardinality

    if p4 is None:
        base["lifecycle_chain"] = chain
        return base
    bootstrap_path, bootstrap = p4
    try:
        replay = dict(bootstrap)
        replay["duplicate_bootstrap"] = "IDEMPOTENT"
        verification = verify_bootstrap_replay(
            bootstrap,
            replay,
            runtime_root=runtime,
            repository=root,
            allow_current_wave2_downstream=True,
        )
        _identity_matches(canonical_identity, bootstrap, ("mission_id", "wop_id", "submission_id"), "P4 bootstrap")
        if bootstrap.get("admission_id") != admission.get("admission_id"):
            raise CanonicalLifecycleResolutionError("CANONICAL_IDENTITY_CHAIN_MISMATCH", "P4 bootstrap admission identity differs from P3 admission")
    except (BootstrapBoundaryError, CanonicalLifecycleResolutionError, ValueError) as error:
        return _fail(mission, getattr(error, "code", "CANONICAL_P4_CHAIN_INVALID"), str(error), chain=chain)

    lineage = admission_facts.get("repository_lineage") or {}
    if lineage.get("baseline_relationship") in {"IDENTICAL", "ANCESTOR"}:
        try:
            # Git/EOS live projections own the current baseline.  A
            # reconciliation receipt is supplemental transition evidence, not
            # a per-publication authority record.  Matching receipts are
            # validated by verify_current; routine descendants therefore
            # resolve even when no new receipt was authored.
            base["postpublication_reconciliation"] = verify_current(
                root,
                runtime,
                expected={
                    "mission_id": canonical_identity.get("mission_id"),
                    "wop_id": canonical_identity.get("wop_id"),
                    "submission_id": canonical_identity.get("submission_id"),
                    "admission_id": admission.get("admission_id"),
                    "bootstrap_id": bootstrap.get("bootstrap_id"),
                    "receipt_provenance_baseline": admission.get("repository_baseline"),
                },
                current_published_baseline=str(lineage.get("current_published_baseline")),
            )
        except LifecycleBaselineReconciliationError as error:
            return _fail(mission, error.code, str(error), chain=chain)

    base.update({
        "bootstrap_id": bootstrap.get("bootstrap_id"),
        "bootstrap_state": bootstrap.get("bootstrap_state"),
        "bootstrap_result": bootstrap.get("bootstrap_result"),
        "provider_ready": bootstrap.get("provider_ready"),
        "provider_selected": bootstrap.get("provider_selected"),
        "dispatch_created": bootstrap.get("dispatch_created"),
        "execution_started": bootstrap.get("execution_started"),
        "lifecycle_state": "AWAITING_EXECUTION_DISPATCH",
        "readiness": "READY_FOR_EXECUTION_PROVIDER",
        "eligibility": "PROVIDER_EVALUATION_PENDING",
        "next_authorized_action": "EVALUATE_EXECUTION_PROVIDER",
        "next_action": "EVALUATE_EXECUTION_PROVIDER",
        "canonical_state_source": "P4_BOOTSTRAP_RECEIPT",
        "bootstrap_transaction": {"path": str(bootstrap_path), "digest": bootstrap.get("transaction_digest")},
        "bootstrap_verification": verification,
    })
    chain.append({
        "stage": "AWAITING_EXECUTION_DISPATCH",
        "state": "AWAITING_EXECUTION_DISPATCH",
        "receipt": {"path": str(bootstrap_path), "digest": bootstrap.get("transaction_digest")},
        "next_action": "EVALUATE_EXECUTION_PROVIDER",
    })

    # Provider selection is the first canonical boundary after P4.  Consume
    # the shared provider-selection verifier here so every mission-native
    # surface projects the same receipt-backed position.  Other-mission and
    # historical artifacts are already excluded by the provider controller's
    # mission-scoped discovery; a malformed or ambiguous target set remains
    # fail-closed.  This stage never creates dispatch/session/execution state.
    try:
        from scripts.lib.emp import provider_selection

        provider_expected = {
            **canonical_identity,
            "admission_id": admission.get("admission_id"),
            "bootstrap_id": bootstrap.get("bootstrap_id"),
            "repository_identity": str(root),
            "mission_provenance_baseline": admission.get("repository_baseline"),
            "current_published_baseline": (lineage or {}).get("current_published_baseline"),
        }
        provider_found = provider_selection._scoped_mission_artifacts(
            provider_selection._mission_artifacts(runtime, mission), provider_expected
        )
        provider_stage = provider_selection._verify_set(runtime, provider_found)
        if provider_stage:
            provider_path = Path(provider_stage["artifacts"]["provider_selection"]["path"])
            provider_anchor = _load(provider_path)
            _identity_matches(
                {**canonical_identity, "admission_id": admission.get("admission_id"), "bootstrap_id": bootstrap.get("bootstrap_id")},
                provider_anchor,
                ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id"),
                "P5 provider selection",
            )
            if provider_anchor.get("repository_identity") != str(root):
                raise CanonicalLifecycleResolutionError(
                    "PROVIDER_REPOSITORY_BINDING_MISMATCH",
                    "provider selection is bound to a different repository",
                )
            if provider_anchor.get("mission_provenance_baseline") != admission.get("repository_baseline"):
                raise CanonicalLifecycleResolutionError(
                    "PROVIDER_PROVENANCE_MISMATCH",
                    "provider selection provenance differs from the admitted lifecycle baseline",
                )
            try:
                provider_lineage = provider_selection._validate_live_lineage(
                    root, provider_anchor, live_lineage=lineage
                )
            except provider_selection.ProviderSelectionError as error:
                raise CanonicalLifecycleResolutionError(
                    error.code,
                    str(error),
                ) from error
            base.update({
                "provider_selected": True,
                "provider_qualified": bool(provider_stage.get("provider_qualified")),
                "provider_id": provider_stage.get("provider_id"),
                "provider_selection_id": provider_stage.get("provider_selection_id"),
                "dispatch_eligible": bool(provider_stage.get("dispatch_eligible")),
                "provider_selection_state": provider_stage.get("provider_selection_state"),
                "provider_selection_result": provider_stage.get("provider_selection_result"),
                "provider_selection": provider_stage,
                "provider_selection_lineage": provider_lineage,
                "lifecycle_state": "AWAITING_EXECUTION_DISPATCH",
                "readiness": "READY_FOR_PROVIDER_DISPATCH",
                "eligibility": "PROVIDER_DISPATCH_PENDING",
                "next_authorized_action": "EVALUATE_PROVIDER_DISPATCH",
                "next_action": "EVALUATE_PROVIDER_DISPATCH",
                "canonical_state_source": "P5_PROVIDER_SELECTION_RECEIPT",
            })
            chain.append({
                "stage": "READY_FOR_PROVIDER_DISPATCH",
                "state": "READY_FOR_PROVIDER_DISPATCH",
                "receipt": {"path": provider_path.__str__(), "digest": provider_anchor.get("artifact_digest")},
                "provider_id": provider_stage.get("provider_id"),
                "next_action": "EVALUATE_PROVIDER_DISPATCH",
            })
    except (provider_selection.ProviderSelectionError, CanonicalLifecycleResolutionError, OSError) as error:
        return _fail(mission, getattr(error, "code", "CANONICAL_PROVIDER_SELECTION_INVALID"), str(error), chain=chain)
    # The provider-selection record is not the end of the canonical chain.
    # Later P5 records are immutable, receipt-backed transitions too; when
    # they exist, validate each set in order and project the furthest
    # contiguous position.  Do not use directory presence as evidence: every
    # stage below is accepted only after its own cardinality, digest, path,
    # identity, binding, and boundary verifier succeeds.
    from scripts.lib.emp import dispatch_foundation, execution_start, provider_invocation, provider_session

    def _anchor(stage: Mapping[str, Any], key: str, label: str) -> dict[str, Any]:
        descriptor = (stage.get("artifacts") or {}).get(key)
        if not isinstance(descriptor, Mapping) or not descriptor.get("path"):
            raise CanonicalLifecycleResolutionError("CANONICAL_DOWNSTREAM_RECEIPT_MISSING", f"{label} receipt descriptor is missing")
        return _load(Path(str(descriptor["path"])))

    def _bind(stage: Mapping[str, Any], key: str, expected: Mapping[str, Any], fields: tuple[str, ...], label: str) -> dict[str, Any]:
        observed = _anchor(stage, key, label)
        _identity_matches(expected, observed, fields, label)
        return observed

    def _has_artifacts(found: Mapping[str, list[Any]]) -> bool:
        return any(found.values())

    dispatch_found = dispatch_foundation._found(runtime, mission)
    session_found = provider_session._found(runtime, mission)
    invocation_found = provider_invocation._found(runtime, mission)
    execution_found = execution_start._found(runtime, mission)
    later_found = _has_artifacts(session_found) or _has_artifacts(invocation_found) or _has_artifacts(execution_found)

    try:
        dispatch_stage = dispatch_foundation._verify_set(runtime, dispatch_found)
        if dispatch_stage is None:
            if later_found:
                raise CanonicalLifecycleResolutionError(
                    "CANONICAL_DOWNSTREAM_CHAIN_GAP",
                    "provider-session, invocation, or execution-start evidence exists without a verified dispatch",
                )
            base["lifecycle_chain"] = chain
            return base
        dispatch_anchor = _bind(
            dispatch_stage,
            "dispatch_transaction",
            {**canonical_identity, "admission_id": admission.get("admission_id"), "bootstrap_id": bootstrap.get("bootstrap_id"),
             "provider_selection_id": provider_stage.get("provider_selection_id"), "provider_id": provider_stage.get("provider_id")},
            ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id", "provider_selection_id", "provider_id"),
            "P5 dispatch",
        )
        base.update({
            "dispatch_id": dispatch_stage.get("dispatch_id"),
            "dispatch_state": dispatch_stage.get("dispatch_state"),
            "dispatch_result": dispatch_stage.get("dispatch_result"),
            "dispatch_authorized": dispatch_stage.get("dispatch_authorized"),
            "dispatch": dispatch_stage,
            "lifecycle_state": "DISPATCHED",
            "readiness": "READY_FOR_PROVIDER_SESSION",
            "eligibility": "PROVIDER_SESSION_PENDING",
            "next_authorized_action": "ESTABLISH_PROVIDER_SESSION",
            "next_action": "ESTABLISH_PROVIDER_SESSION",
            "canonical_state_source": "P5_DISPATCH_RECEIPT",
        })
        chain.append({
            "stage": "DISPATCHED", "state": dispatch_stage.get("dispatch_state"),
            "receipt": (dispatch_stage.get("artifacts") or {}).get("dispatch_receipt"),
            "dispatch_id": dispatch_stage.get("dispatch_id"), "next_action": "ESTABLISH_PROVIDER_SESSION",
        })

        dispatch_fields = {**canonical_identity, "admission_id": admission.get("admission_id"), "bootstrap_id": bootstrap.get("bootstrap_id"),
                           "dispatch_id": dispatch_stage.get("dispatch_id"), "provider_selection_id": provider_stage.get("provider_selection_id"),
                           "provider_id": provider_stage.get("provider_id")}
        session_stage = provider_session._verify_set(runtime, session_found)
        if session_stage is None:
            if _has_artifacts(invocation_found) or _has_artifacts(execution_found):
                raise CanonicalLifecycleResolutionError(
                    "CANONICAL_DOWNSTREAM_CHAIN_GAP",
                    "provider invocation or execution-start evidence exists without a verified provider session",
                )
            base["lifecycle_chain"] = chain
            return base
        session_anchor = _bind(
            session_stage, "provider_session", dispatch_fields,
            ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id", "dispatch_id", "provider_selection_id", "provider_id"),
            "P5 provider session",
        )
        if session_stage.get("provider_session_id") != session_anchor.get("provider_session_id"):
            raise CanonicalLifecycleResolutionError("CANONICAL_DOWNSTREAM_BINDING_MISMATCH", "provider session projection differs from its receipt")
        base.update({
            "provider_session_id": session_stage.get("provider_session_id"),
            "provider_session_state": session_stage.get("session_state"),
            "provider_session_authorized": session_stage.get("provider_session_authorized"),
            "provider_session_created": session_stage.get("provider_session_created"),
            "provider_session": session_stage,
            "lifecycle_state": "PROVIDER_BOUND",
            "readiness": "READY_FOR_PROVIDER_INVOCATION",
            "eligibility": "PROVIDER_INVOCATION_PENDING",
            "next_authorized_action": "INVOKE_PROVIDER",
            "next_action": "INVOKE_PROVIDER",
            "canonical_state_source": "P5_PROVIDER_SESSION_RECEIPT",
        })
        chain.append({
            "stage": "PROVIDER_BOUND", "state": session_stage.get("session_state"),
            "receipt": (session_stage.get("artifacts") or {}).get("provider_session_receipt"),
            "provider_session_id": session_stage.get("provider_session_id"), "next_action": "INVOKE_PROVIDER",
        })

        session_fields = {**dispatch_fields, "provider_session_id": session_stage.get("provider_session_id")}
        invocation_stage = provider_invocation._verify_set(runtime, invocation_found)
        if invocation_stage is None:
            if _has_artifacts(execution_found):
                raise CanonicalLifecycleResolutionError(
                    "CANONICAL_DOWNSTREAM_CHAIN_GAP",
                    "execution-start evidence exists without a verified provider invocation",
                )
            base["lifecycle_chain"] = chain
            return base
        invocation_anchor = _bind(
            invocation_stage, "provider_invocation_transaction", session_fields,
            ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id", "dispatch_id", "provider_session_id", "provider_id"),
            "P5 provider invocation",
        )
        if invocation_stage.get("provider_invocation_id") != invocation_anchor.get("provider_invocation_id"):
            raise CanonicalLifecycleResolutionError("CANONICAL_DOWNSTREAM_BINDING_MISMATCH", "provider invocation projection differs from its receipt")
        base.update({
            "provider_invocation_id": invocation_stage.get("provider_invocation_id"),
            "provider_invocation_state": invocation_stage.get("provider_invocation_state"),
            "provider_invocation_authorized": invocation_stage.get("provider_invocation_authorized"),
            "provider_invoked": invocation_stage.get("provider_invoked"),
            "provider_acknowledged": invocation_stage.get("provider_acknowledged"),
            "provider_invocation": invocation_stage,
            "lifecycle_state": "PROVIDER_INVOKED",
            "readiness": "READY_FOR_EXECUTION_START",
            "eligibility": "EXECUTION_START_PENDING",
            "next_authorized_action": "START_EXECUTION",
            "next_action": "START_EXECUTION",
            "canonical_state_source": "P5_PROVIDER_INVOCATION_RECEIPT",
        })
        chain.append({
            "stage": "PROVIDER_INVOKED", "state": invocation_stage.get("provider_invocation_state"),
            "receipt": (invocation_stage.get("artifacts") or {}).get("provider_invocation_receipt"),
            "provider_invocation_id": invocation_stage.get("provider_invocation_id"), "next_action": "START_EXECUTION",
        })

        invocation_fields = {**session_fields, "provider_invocation_id": invocation_stage.get("provider_invocation_id")}
        execution_stage = execution_start._verify_set(runtime, execution_found)
        if execution_stage is None:
            base["lifecycle_chain"] = chain
            return base
        execution_anchor = _bind(
            execution_stage, "execution_start_transaction", invocation_fields,
            ("mission_id", "wop_id", "provider_invocation_id", "provider_session_id", "provider_id", "dispatch_id"),
            "P5 execution start",
        )
        if execution_stage.get("execution_id") != execution_anchor.get("execution_id"):
            raise CanonicalLifecycleResolutionError("CANONICAL_DOWNSTREAM_BINDING_MISMATCH", "execution-start projection differs from its receipt")
        if execution_stage.get("mission_work_started") is not False or execution_stage.get("repository_work_started") is not False:
            raise CanonicalLifecycleResolutionError("CANONICAL_EXECUTION_BOUNDARY_FAILURE", "execution-start evidence crosses the controlled mission-work boundary")
        base.update({
            "execution_id": execution_stage.get("execution_id"),
            "execution_session_id": execution_stage.get("execution_session_id"),
            "execution_start_state": execution_stage.get("execution_start_state"),
            "execution_state": execution_stage.get("execution_start_state"),
            "execution_start_result": execution_stage.get("execution_start_result"),
            "execution_start_authorized": execution_stage.get("execution_start_authorized"),
            "execution_session_created": execution_stage.get("execution_session_created"),
            "execution_started": execution_stage.get("execution_started"),
            "provider_process_bound": execution_stage.get("provider_process_bound"),
            "mission_work_started": execution_stage.get("mission_work_started"),
            "repository_work_started": execution_stage.get("repository_work_started"),
            "execution_monitoring_active": execution_stage.get("execution_monitoring_active"),
            "completion_reported": execution_stage.get("completion_reported"),
            "execution_start": execution_stage,
            "lifecycle_state": "READY_FOR_CONTROLLED_EXECUTION",
            "readiness": "READY_FOR_CONTROLLED_EXECUTION",
            "eligibility": "CONTROLLED_MISSION_WORK_READY",
            "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK",
            "next_action": "BEGIN_CONTROLLED_MISSION_WORK",
            "canonical_state_source": "P5_EXECUTION_START_RECEIPT",
        })
        chain.append({
            "stage": "READY_FOR_CONTROLLED_EXECUTION", "state": execution_stage.get("execution_start_state"),
            "receipt": (execution_stage.get("artifacts") or {}).get("execution_start_receipt"),
            "execution_id": execution_stage.get("execution_id"),
            "execution_session_id": execution_stage.get("execution_session_id"),
            "next_action": "BEGIN_CONTROLLED_MISSION_WORK",
        })
    except (dispatch_foundation.DispatchFoundationError, provider_session.ProviderSessionError,
            provider_invocation.ProviderInvocationError, execution_start.ExecutionStartError,
            CanonicalLifecycleResolutionError, OSError) as error:
        return _fail(mission, getattr(error, "code", "CANONICAL_DOWNSTREAM_CHAIN_INVALID"), str(error), chain=chain)

    base["lifecycle_chain"] = chain
    return base


def view(repository: Path | str, action: str, mission_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Return the same canonical chain for every read-only mission surface."""
    value = resolve(repository, mission_id, runtime_root=runtime_root)
    value["view"] = action
    return value


def submitted_missions(repository: Path | str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    """List missions discovered from the canonical P2 submission store.

    The Operation Beta roadmap is a planning projection and does not own
    discovery of submitted Development missions.  This read-only index keeps
    the CLI list surface on the same receipt-backed path as mission show and
    the other native mission views.  Invalid or ambiguous receipts are
    represented as blocked entries rather than silently omitted.
    """
    root = Path(repository).resolve()
    runtime = (Path(runtime_root).resolve() if runtime_root is not None
               else Path(resolve_runtime(root, require_writable=False)["root"]).resolve())
    receipts = runtime / "submissions" / "receipts"
    candidates: dict[str, list[Path]] = {}
    if receipts.is_dir():
        for path in sorted(receipts.glob("*.json")):
            try:
                record = _load(path)
            except CanonicalLifecycleResolutionError:
                continue
            mission = str(record.get("mission_id", "")).strip().upper()
            if mission:
                candidates.setdefault(mission, []).append(path)

    missions: list[dict[str, Any]] = []
    for mission in sorted(candidates):
        resolved = resolve(root, mission, runtime_root=runtime)
        if resolved.get("result") == "PASS":
            missions.append({
                "mission_id": mission,
                "wop_id": resolved.get("wop_id"),
                "lifecycle": resolved.get("lifecycle_state"),
                "lifecycle_state": resolved.get("lifecycle_state"),
                "readiness": resolved.get("readiness"),
                "eligibility": resolved.get("eligibility"),
                "authority": resolved.get("authority"),
                "next_authorized_action": resolved.get("next_authorized_action"),
                "submission_id": resolved.get("submission_id"),
                "canonical_lifecycle_owner": resolved.get("canonical_lifecycle_owner"),
                "read_only": True,
            })
        else:
            missions.append({
                "mission_id": mission,
                "lifecycle": "UNRESOLVED",
                "lifecycle_state": "UNRESOLVED",
                "resolution": "BLOCKED",
                "blockers": resolved.get("blockers", [{
                    "code": "CANONICAL_RESOLUTION_FAILED",
                    "message": "canonical submission could not be resolved",
                }]),
                "read_only": True,
            })

    return {"result": "PASS", "missions": missions, "read_only": True,
            "canonical_lifecycle_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
            "source": str(receipts), "mission_count": len(missions)}
