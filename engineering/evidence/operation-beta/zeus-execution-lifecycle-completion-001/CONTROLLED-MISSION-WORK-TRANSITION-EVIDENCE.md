# Zeus Controlled Mission-Work Transition Evidence

Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`  
Corrective: `ZEUS_MANAGED_CONTROLLED_WORK_TRANSITION`  
Stop boundary: `OPERATOR_REVIEW`

## Implemented contract

`execution-start begin` now verifies the immutable execution-start boundary,
requires explicit controlled-work approval, and uses the exact mission, WOP,
execution, execution-session, provider-session, provider, and provider
invocation bindings already qualified by Zeus. A stopped session whose history
is non-authoritative is reconciled read-only and superseded through the
canonical receipt-backed session replacement path before provider launch. The
old Codex record and event history remain preserved.

Zeus sends the bounded `thread/start` and `turn/start` requests through the
bound managed provider broker. `mission_work_started` is projected only after
the provider acknowledges both a thread identity and a turn identity. The
active projection carries binding-specific response digests as
`CONTROLLED_MISSION_WORK_EVIDENCE`; its replay is idempotent. No transition in
this corrective sets `repository_work_started`; that flag remains false until
repository-specific authoritative evidence is recorded.

## Verification

```text
PYTHONPATH=. python scripts/tests/test-zeus-p5-g6-codex-adapter.py        PASS (30 tests, 1 skipped)
PYTHONPATH=. python scripts/tests/test-zeus-p5-g6-session-supersession.py PASS (17 tests)
PYTHONPATH=. python scripts/tests/test-zeus-execution-lifecycle-completion-corrective.py PASS (7 tests)
PYTHONPATH=. python scripts/tests/test-zeus-p5-g6-reconciliation.py       PASS (22 tests)
git diff --check                                                         PASS
```

The real mission provider turn was not invoked during engineering
verification. The repository remains at the operator-controlled boundary:

```text
MISSION_ID=ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01
EXECUTION_ID=EXECUTION-START-03e0a183-23a4-5dc7-b6dc-bc62c1a9a1ae
EXECUTION_SESSION_ID=EXECUTION-SESSION-13637768-524b-5587-8d01-1cce5f301b80
PROVIDER_SESSION_ID=PROVIDER-SESSION-309031db-d38a-5bf9-8db3-b871ed2ddfd1
CODEX_SESSION_ID=CODEX-SESSION-8e97324a-cdd7-5189-acaf-a37682cb24ee
LIFECYCLE_STATE=READY_FOR_CONTROLLED_EXECUTION
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
NEXT_AUTHORIZED_ACTION=BEGIN_CONTROLLED_MISSION_WORK
SESSION_REUSE_ALLOWED=NO
SESSION_SUPERSESSION_REQUIRED=YES
SESSION_REPLACEMENT_SAFE=YES
STATUS=AWAITING_OPERATOR_REVIEW
```

Operator acceptance is the next legitimate boundary. Run the Zeus-specific
commands in the completion handoff; do not infer mission-work completion from
this implementation evidence.
