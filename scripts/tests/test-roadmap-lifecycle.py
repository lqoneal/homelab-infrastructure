#!/usr/bin/env python3

from scripts.lib.eos.roadmap_lifecycle import (
    AdvancementBinding,
    LifecycleError,
    LifecycleState,
    OperatorDecision,
    ResultClass,
    ResultFacts,
    ReviewBinding,
    apply_operator_decision,
    classify_replay,
    classify_result,
    complete_accepted_gate,
    pending_review_transition,
    result_recorded_transition,
)


def expect_error(fn):
    try:
        fn()
    except LifecycleError:
        return
    raise AssertionError("expected LifecycleError")


def review_binding():
    return ReviewBinding(
        roadmap_id="ESC-ROADMAP-TEST",
        roadmap_version="1.0.0",
        gate_id="C01",
        gate_definition_digest="a" * 64,
        result_digest="b" * 64,
        operator_identity="operator",
        transaction_id="tx-review-1",
    )


def advancement_binding():
    return AdvancementBinding(
        roadmap_id="ESC-ROADMAP-TEST",
        roadmap_version="1.0.0",
        gate_id="C01",
        gate_definition_digest="a" * 64,
        result_digest="b" * 64,
        acceptance_receipt_id="receipt-1",
        acceptance_receipt_digest="c" * 64,
        transaction_id="tx-advance-1",
    )


def test_result_classification():
    assert classify_result(
        ResultFacts(exists=False)
    ) is ResultClass.ABSENT

    assert classify_result(
        ResultFacts(
            exists=True,
            identity_valid=True,
            schema_valid=True,
            evidence_valid=True,
            final=True,
        )
    ) is ResultClass.VALID_FINAL

    assert classify_result(
        ResultFacts(
            exists=True,
            identity_valid=True,
            schema_valid=True,
            evidence_valid=True,
            final=True,
            stale=True,
        )
    ) is ResultClass.STALE

    assert classify_result(
        ResultFacts(
            exists=True,
            identity_valid=True,
            schema_valid=True,
            evidence_valid=True,
            final=True,
            conflicting=True,
        )
    ) is ResultClass.CONFLICTING


def test_result_does_not_imply_acceptance():
    state = result_recorded_transition(
        LifecycleState.CURRENT,
        ResultClass.VALID_FINAL,
    )

    assert state is LifecycleState.RESULT_RECORDED

    state = pending_review_transition(
        state,
        ResultClass.VALID_FINAL,
    )

    assert state is LifecycleState.AWAITING_OPERATOR_REVIEW


def test_explicit_accept_reject():
    accepted = apply_operator_decision(
        LifecycleState.AWAITING_OPERATOR_REVIEW,
        ResultClass.VALID_FINAL,
        OperatorDecision.ACCEPT,
        review_binding(),
    )

    rejected = apply_operator_decision(
        LifecycleState.AWAITING_OPERATOR_REVIEW,
        ResultClass.VALID_FINAL,
        OperatorDecision.REJECT,
        review_binding(),
    )

    assert accepted is LifecycleState.ACCEPTED
    assert rejected is LifecycleState.REJECTED


def test_rejected_cannot_complete():
    expect_error(
        lambda: complete_accepted_gate(
            LifecycleState.REJECTED,
            advancement_binding(),
            successor_gate="C02",
            terminal=False,
        )
    )


def test_acceptance_does_not_execute_successor():
    state, successor = complete_accepted_gate(
        LifecycleState.ACCEPTED,
        advancement_binding(),
        successor_gate="C02",
        terminal=False,
    )

    assert state is LifecycleState.COMPLETED
    assert successor == "C02"


def test_terminal_does_not_fabricate_successor():
    state, successor = complete_accepted_gate(
        LifecycleState.ACCEPTED,
        advancement_binding(),
        successor_gate=None,
        terminal=True,
    )

    assert state is LifecycleState.COMPLETED
    assert successor is None

    expect_error(
        lambda: complete_accepted_gate(
            LifecycleState.ACCEPTED,
            advancement_binding(),
            successor_gate="C99",
            terminal=True,
        )
    )


def test_nonterminal_requires_successor():
    expect_error(
        lambda: complete_accepted_gate(
            LifecycleState.ACCEPTED,
            advancement_binding(),
            successor_gate=None,
            terminal=False,
        )
    )


def test_exact_replay():
    assert classify_replay(
        transaction_id_matches=True,
        gate_matches=True,
        result_matches=True,
        receipt_matches=True,
        pre_state_matches=True,
        committed=False,
    ) == "RESUME_EXACT_TRANSACTION"

    assert classify_replay(
        transaction_id_matches=True,
        gate_matches=True,
        result_matches=True,
        receipt_matches=True,
        pre_state_matches=True,
        committed=True,
    ) == "ALREADY_APPLIED"


def test_conflicting_replay_fails_closed():
    expect_error(
        lambda: classify_replay(
            transaction_id_matches=True,
            gate_matches=True,
            result_matches=False,
            receipt_matches=True,
            pre_state_matches=True,
            committed=False,
        )
    )


def test_invalid_result_cannot_enter_review():
    expect_error(
        lambda: result_recorded_transition(
            LifecycleState.CURRENT,
            ResultClass.INVALID,
        )
    )


def main():
    tests = [
        test_result_classification,
        test_result_does_not_imply_acceptance,
        test_explicit_accept_reject,
        test_rejected_cannot_complete,
        test_acceptance_does_not_execute_successor,
        test_terminal_does_not_fabricate_successor,
        test_nonterminal_requires_successor,
        test_exact_replay,
        test_conflicting_replay_fails_closed,
        test_invalid_result_cannot_enter_review,
    ]

    for test in tests:
        test()
        print("PASS", test.__name__)

    print(f"TESTS={len(tests)}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()
