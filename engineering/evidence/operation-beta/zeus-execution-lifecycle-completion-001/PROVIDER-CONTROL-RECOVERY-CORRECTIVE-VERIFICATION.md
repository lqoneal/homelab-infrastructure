# Provider-control recovery corrective verification

Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`  
Corrective: `ZEUS_MANAGED_PROVIDER_CONTROL_OWNERSHIP_AND_RESET_RECOVERY`  
Verification boundary: `OPERATOR_REVIEW`  
Real mission turn: **not performed**

## Root cause

The managed STDIO broker collapsed a provider-side `ConnectionResetError` into
the generic `BROKER_START_FAILED` marker. The adapter then had no phase,
provider-exit, or endpoint-owner evidence and treated the historical
handshake receipt as sufficient launch state. It did not actively probe the
control endpoint before the bounded thread/turn transaction. A stopped or
foreign endpoint could therefore reach provider control as
`PROVIDER_CONTROL_FAILED` without a safe, explicit runtime recovery result.

## Corrective

The broker now records launch phase, provider identity/exit diagnostics,
session-bound endpoint ownership, and a local `zeus/transport/probe`. The
adapter verifies the endpoint after launch and immediately before
`thread/start` and `turn/start`; it rejects missing handshakes, dead providers,
stale/foreign sockets, and missing thread/turn IDs. A predecessor endpoint is
verified stopped before supersession. The predecessor and event journal remain
preserved, while one deterministic successor owns a new control endpoint.
Thread acknowledgement is durably retained as a pending attempt for
interruption/resume, but no work flag is projected until turn acknowledgement.
Lifecycle next action and runtime recovery action are emitted separately.

## Verification result

```text
MISSION_ID=ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01
EXECUTION_ID=EXECUTION-START-03e0a183-23a4-5dc7-b6dc-bc62c1a9a1ae
EXECUTION_SESSION_ID=EXECUTION-SESSION-13637768-524b-5587-8d01-1cce5f301b80
PROVIDER_SESSION_ID=PROVIDER-SESSION-309031db-d38a-5bf9-8db3-b871ed2ddfd1
PROVIDER_ID=zeus-local-loneal-01
BOUND_CODEX_SESSION_ID=CODEX-SESSION-8e97324a-cdd7-5189-acaf-a37682cb24ee
LIFECYCLE_STATE=READY_FOR_CONTROLLED_EXECUTION
NEXT_LIFECYCLE_ACTION=BEGIN_CONTROLLED_MISSION_WORK
RUNTIME_CLASSIFICATION=STALE_ORPHANED_RUNTIME
RUNTIME_RECOVERY_ACTION=SUPERSEDE_CODEX_SESSION
MISSION_WORK_STARTED=NO
REPOSITORY_WORK_STARTED=NO
SUPERSESSION_RECOVERY_VERIFIED=YES_IN_DISPOSABLE_AND_FOCUSED_COVERAGE
REAL_MISSION_TURN=NO
STATUS=AWAITING_OPERATOR_REVIEW
```

The authoritative read-only runtime still has the supplied stopped-session
boundary. No authoritative runtime mutation was performed during this
verification.

## Tests

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/tests/test-zeus-p5-g6-codex-adapter.py        PASS (32 tests, 2 skipped by Unix-socket sandbox)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/tests/test-zeus-p5-g6-session-supersession.py PASS (17 tests)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/tests/test-zeus-execution-lifecycle-completion-corrective.py PASS (7 tests)
python -m py_compile scripts/lib/emp/codex_adapter.py scripts/lib/emp/codex_app_server_broker.py scripts/zeus PASS
```

The skipped tests require host Unix-domain socket binding; no real provider
turn was substituted for them.

## Operator acceptance command

After review, the exact Zeus command that performs the real bounded transition
is:

```text
scripts/zeus execution-start begin ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --approve --json
```

Do not run this command as engineering verification: it launches/replaces the
managed provider as needed and sends the real bound `thread/start` and
`turn/start` requests.
