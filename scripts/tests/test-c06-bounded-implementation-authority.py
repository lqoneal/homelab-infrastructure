"""Focused C06 bounded incremental implementation authority tests."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.eos.convergence_roadmap import (
    project_bounded_implementation_authority,
    project_c06_bounded_implementation_authority,
)


ROOT = Path(__file__).resolve().parents[2]


def _transaction() -> dict:
    return {
        "transaction_id": "C06-BOUNDARY-MODEL-001",
        "gate_id": "C06",
        "scope": ["one explicitly scoped implementation increment"],
        "authorized_scope": ["one explicitly scoped implementation increment"],
        "prerequisites": {
            "roadmap": True,
            "dependency": True,
            "maturity": True,
        },
        "qualification": {"valid": True, "evidence": "C06-QUALIFICATION-001"},
        "blockers": [],
        "authority": {
            "bounded_implementation": True,
            "publication_owner": "ZEUS",
        },
        "successor_gate_execution_requested": False,
        "publication_requested": False,
    }


def test_eligible_bounded_increment_is_authorized():
    value = project_bounded_implementation_authority(ROOT, _transaction())
    assert value["bounded_implementation_authorized"] is True
    assert value["next_authorized_action"] == "EXECUTE_BOUNDED_IMPLEMENTATION_INCREMENT"


def test_generic_resolver_is_not_tied_to_c06():
    transaction = _transaction()
    transaction["gate_id"] = "C09"
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is True


def test_gate_policy_can_restrict_generic_resolver():
    transaction = _transaction()
    transaction["gate_id"] = "C09"
    value = project_bounded_implementation_authority(
        ROOT, transaction, policy={"required_gate_id": "C06"}
    )
    assert value["bounded_implementation_authorized"] is False
    assert "GATE_POLICY_MISMATCH" in value["blockers"]


def test_missing_prerequisite_fails_closed():
    transaction = _transaction()
    transaction["prerequisites"]["dependency"] = False
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False
    assert "PREREQUISITES_NOT_SATISFIED" in value["blockers"]


def test_explicit_blocker_fails_closed():
    transaction = _transaction()
    transaction["blockers"] = ["DEPENDENCY_PENDING"]
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False


def test_scope_expansion_fails_closed():
    transaction = _transaction()
    transaction["scope"].append("unrelated successor work")
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False
    assert "IMPLEMENTATION_SCOPE_EXCEEDS_TRANSACTION_BOUNDARY" in value["blockers"]


def test_qualification_is_required():
    transaction = _transaction()
    transaction["qualification"]["valid"] = False
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False


def test_publication_is_zeus_owned():
    value = project_bounded_implementation_authority(ROOT, _transaction())
    assert value["publication_authority_owner"] == "ZEUS"
    assert value["codex_publication_authority"] is False


def test_successor_work_is_not_implicitly_authorized():
    transaction = _transaction()
    transaction["successor_gate_execution_requested"] = True
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False


def test_incremental_authority_does_not_require_roadmap_completion():
    value = project_bounded_implementation_authority(ROOT, _transaction())
    assert value["bounded_implementation_authorized"] is True
    assert value["next_authorized_action"] != "COMPLETE_ROADMAP"


def test_implementation_authority_is_separate_from_successor_authority():
    value = project_bounded_implementation_authority(ROOT, _transaction())
    assert value["bounded_implementation_authorized"] is True
    assert value["successor_gate_execution_authorized"] is False


def test_qualification_is_separate_from_implementation_authority():
    transaction = _transaction()
    transaction["qualification"]["valid"] = False
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False
    assert "QUALIFICATION_ARTIFACT_INVALID_OR_MISSING" in value["blockers"]


def test_completion_does_not_authorize_another_increment():
    transaction = _transaction()
    transaction["state"] = "QUALIFIED"
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False


def test_missing_transaction_scope_fails_closed():
    transaction = _transaction()
    transaction.pop("scope")
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False


def test_projection_is_deterministic_and_replay_safe():
    transaction = _transaction()
    first = project_bounded_implementation_authority(ROOT, transaction)
    second = project_bounded_implementation_authority(ROOT, copy.deepcopy(transaction))
    assert first == second
    assert first["read_only"] is True


def test_persisted_first_increment_is_discovered_and_authorized():
    value = project_c06_bounded_implementation_authority(ROOT)
    assert value["transaction_recognized"] is True
    assert value["transaction_id"] == "C06-WOP-01-ROADMAP-AUTHORITY-001"
    assert value["bounded_implementation_authorized"] is True
    assert value["next_authorized_action"] == "EXECUTE_BOUNDED_IMPLEMENTATION_INCREMENT"


def test_unknown_persisted_transaction_fails_closed():
    from scripts.lib.eos.convergence_roadmap import RoadmapError

    try:
        project_c06_bounded_implementation_authority(ROOT, transaction_id="UNKNOWN-C06-TX")
    except RoadmapError as error:
        assert "unknown" in str(error)
    else:
        raise AssertionError("unknown transaction was accepted")


def test_transaction_gate_mismatch_fails_closed():
    transaction = _transaction()
    transaction["gate_id"] = "C07"
    value = project_c06_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False


def test_superseded_transaction_fails_closed():
    transaction = _transaction()
    transaction["state"] = "SUPERSEDED"
    value = project_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False


def test_altered_authority_provenance_fails_closed():
    transaction = _transaction()
    transaction["authority"]["provenance_reference"] = "FORGED"
    value = project_c06_bounded_implementation_authority(ROOT, transaction)
    assert value["bounded_implementation_authorized"] is False
