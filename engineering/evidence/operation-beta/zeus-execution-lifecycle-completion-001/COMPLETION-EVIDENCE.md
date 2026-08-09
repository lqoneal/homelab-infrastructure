# Zeus Execution Lifecycle Completion Corrective Evidence

Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`
Corrective: `ZEUS_MANAGED_RUNTIME_RESOLUTION_AND_MACHINE_CONTRACT_INTERFACE`
Execution mode: `BOUNDED_CORRECTIVE`
Stop boundary: `OPERATOR_REVIEW`

## Result

```text
MISSION_ID=ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01
EXECUTION_ID=EXECUTION-START-03e0a183-23a4-5dc7-b6dc-bc62c1a9a1ae
EXECUTION_SESSION_ID=EXECUTION-SESSION-13637768-524b-5587-8d01-1cce5f301b80
PROVIDER_SESSION_ID=PROVIDER-SESSION-309031db-d38a-5bf9-8db3-b871ed2ddfd1
CODEX_SESSION_ID=CODEX-SESSION-8e97324a-cdd7-5189-acaf-a37682cb24ee
ROOT_CAUSE=global managed --active/--latest had no canonical selector and fell through to the historical Beta mission default
CORRECTIVE_IMPLEMENTED=PASS
CANONICAL_RUNTIME_RESOLUTION=mission-qualified live authoritative binding > live execution/provider/session state > historical/reconciled records; equal authority fails closed
MISSION_SCOPED_RESOLUTION=PASS
ACTIVE_RESOLUTION=PASS in regression coverage; current host native observation is NO_LIVE_MANAGED_RUNTIME because recorded PIDs are stopped
LATEST_RESOLUTION=PASS
HISTORICAL_SUPERSESSION_PREVENTED=PASS
MACHINE_WORK_CONTRACT_INTERFACE=scripts/zeus codex resume <MISSION_ID> --approve --work-contract PATH --json
WORK_CONTRACT_SCHEMA_VALIDATION=PASS
WORK_CONTRACT_PROVENANCE=PASS; source digest, payload digest, binding snapshot, and append-only acceptance event persisted
WORK_CONTRACT_REPLAY=IDEMPOTENT
ZEUS_MANAGED_EXECUTION_OWNERSHIP=PASS
CONTROLLED_DOCUMENT_VALIDATION=PASS; default validator 2897 checks passed, 0 failed
SEMANTIC_VALIDATION=PASS for applicable conformance/assurance layers; targeted docs have no registered semantic profile
INTEGRATED_VALIDATION=PASS; Zeus platform verification has no defects
REPOSITORY_EOS_VALIDATION=PASS; repository/EOS projection and parity pass
STAGED_COUNT=0
CONTROLLED_MISSION_WORK_STARTED=NO
PUBLICATION_PERFORMED=NO
PUSH_PERFORMED=NO
EOS_PUBLICATION_SYNCHRONIZATION_PERFORMED=NO
UNRELATED_WORKTREE_CHANGES_PRESERVED=YES
NEXT_AUTHORIZED_ACTION=CONTINUE_CONTROLLED_MISSION_WORK
STATUS=AWAITING_OPERATOR_REVIEW
```

## Root cause and implementation

Mission-qualified `codex status` already used the managed adapter with its
mission identity. Global `--active` and `--latest` instead selected the
hard-coded historical Beta mission because the CLI had no global managed
resolver. The corrective adds a shared managed-runtime resolver and routes
global managed selectors through it. It resolves exact execution/provider/
session bindings, checks liveness and reconciliation state, and uses stable
authority-first ordering; timestamps and filesystem order cannot promote
historical state over live state.

The machine work contract is defined by
`engineering/oversight/work-contract.schema.yaml` and implemented by
`scripts/lib/emp/managed_work_contract.py`. `codex resume` validates the
structured contract before continuation, requires approval, persists its
source and normalized payload digests and binding provenance in the
Zeus-managed runtime, and returns structured JSON. Replay of the same
contract/binding is idempotent. It never converts arbitrary prose into an
unrelated `codex exec` call.

## Verification record

Focused corrective coverage:

```text
7 tests: PASS
MISSION_SCOPED_RESOLUTION=PASS
ACTIVE_RESOLUTION=PASS
LATEST_RESOLUTION=PASS
HISTORICAL_SESSION_DOES_NOT_SUPERSEDE_LIVE_SESSION=PASS
MACHINE_WORK_CONTRACT_VALIDATION=PASS
MISSION_BINDING_VALIDATION=PASS
EXECUTION_BINDING_VALIDATION=PASS
PROVIDER_SESSION_BINDING_VALIDATION=PASS
STALE_BINDING_FAIL_CLOSED=PASS
CONTRACT_DIGEST_PERSISTED=PASS
CONTRACT_REPLAY=IDEMPOTENT
STRUCTURED_JSON_RESULT=PASS
```

The native mission-qualified selector returned the exact IDs above. The
corrected global `--latest` selector resolved the same Zeus mission rather
than historical Beta. The current host’s `--active` read-only result was
`NO_LIVE_MANAGED_RUNTIME`; this conflicts with the operator-supplied live
observation and was not repaired by starting, replacing, or terminating any
provider/session.

Existing Codex adapter, supersession, handoff, runtime discovery, platform
sync, controlled-document, conformance, assurance, and relationship checks
were run. No controlled mission work, CAGF01 execution, publication staging,
commit, push, or EOS publication synchronization was performed.
