# Recommended Remediation

## Defect classification

`SUBMISSION_ROUTING_AND_AUTHORED_PROVENANCE_CONVERGENCE_DEFECT`

It has two coupled manifestations:

1. A valid hand-authored Development source is not promotable to the current
   Phase-1/P2 contract through a supported identity-preserving command.
2. `scripts/zeus` selects the P2 route only when `--repository` is absent.
   Supplying repository/baseline/impact/resource options silently forces the
   legacy admission-record path and reports a generic approval requirement.

The legacy approval check is not evidence that the lifecycle WOP declares an
approval gate.

## Authoritative target behavior

`zeus submit SOURCE` must:

1. Resolve the source and repository identity.
2. Validate the complete Development WOP contract.
3. Classify the input using complete provenance and identity checks.
4. Promote a valid source deterministically to the canonical Phase-1/P2
   representation in isolated storage, preserving source bytes and digest.
5. Preserve the declared WOP ID, Mission ID, seven gates, scope, authority
   wording, baseline, and all execution/evidence/closeout requirements.
6. Enter the existing `submit_wop_boundary`.
7. Produce exactly one deterministic submission receipt and one admission
   request with:

   ```text
   submission_result = PASS
   submission_state  = ADMISSION_REQUESTED
   next_action       = EVALUATE_MISSION_ADMISSION
   authority         = operator-submitted WOP
   approval_state    = NOT_REQUIRED_UNLESS_DECLARED_IN_WOP
   ```

8. Stop before Mission Admission, bootstrap, dispatch, provider session,
   execution, qualification, publication, synchronization, or closeout.

Supplying legacy-only options must not override this classification. Current
source plus inconsistent legacy identity/authority options must fail closed
with a specific conflict reason. Actual legacy admission records may continue
through an explicit compatibility adapter.

## Likely runtime files

The implementation owner should evaluate these files together:

- `scripts/zeus` — classify before option-dependent routing; remove silent
  `not a.repository` path selection; make legacy mode explicit and conflict
  checked.
- `scripts/lib/emp/wop_authoring.py` — add or expose an identity-preserving
  promotion contract; do not reuse hash-derived identity generation for this
  case.
- `scripts/lib/emp/wop_verification.py` — verify the complete promoted
  provenance envelope and replay content.
- `scripts/lib/emp/submission_boundary.py` — consume the normalized authored
  projection without weakening source/output/template/context/repository
  digest checks.
- `scripts/lib/emp/wop_validation.py` and
  `scripts/lib/emp/wop_packaging.py` — share normalized source facts and
  preserve source/package/tree digest distinctions.
- `scripts/lib/emp/stage1_runtime.py` — remain the derived package/lifecycle
  owner; consume the normalized authority snapshot and retain fail-closed
  admission, baseline, provider, and execution controls.
- `scripts/lib/emp/orchestration.py` — retain legacy behavior for actual
  admission records, but prevent its selection approval field from becoming
  the new-WOP authority contract.
- `scripts/lib/emp/wop_admission.py` — preserve explicit in-WOP approval gate
  validation and admission fail-closed behavior.

No CAGF-01 or lifecycle source file should be edited as part of this
remediation.

## Tests to add or correct

- valid hand-authored Development source is classified as promotable;
- complete Phase-1 provenance is generated deterministically in isolation;
- lifecycle source WOP/Mission identities are preserved exactly;
- source bytes and source digest remain unchanged;
- missing, stale, conflicting, or forged provenance fails closed;
- `zeus submit SOURCE` routes to P2;
- `zeus submit SOURCE --repository ...` does not silently route to legacy;
- legacy admission-record input still routes through compatibility behavior;
- no generic `required_approvals` is needed for submitted-WOP authority;
- a declared in-WOP approval gate remains required;
- source/package/tree/output digests remain distinct and bound;
- submission receipt and admission request are deterministic and idempotent;
- no admission, execution, provider, publication, or synchronization artifact
  is created by P2 submission;
- Zeus-native mission snapshot exposes identity, authority, state, blockers,
  receipts, and next action.

Existing P1 authoring, P2 boundary, authority-convergence, WOP admission,
Stage-1, replay, and controlled-document tests should remain green.

## Controlled documents requiring reconciliation

The following documents currently describe overlapping source-only, P1/P2,
canonical-package, and legacy behavior and should be reconciled in the same
authorized change:

- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`;
- `engineering/docs/operations/ZEUS-WOP-AUTHORING-GUIDE.md`;
- `engineering/docs/architecture/ZEUS-WOP-SUBMISSION-PROCEDURE.md`;
- `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md`;
- `engineering/docs/architecture/WOP-SCHEMA-AND-EXECUTION-INTERFACE.md`;
- the authoritative WOP/admission schemas and their semantic validation
  profiles.

They should state one rule: new Development sources are normalized through one
canonical submission boundary; historical admission records use an explicit
compatibility adapter; legacy selection approval is not generic execution
authority; only an approval gate declared in the WOP requires approval.

## Historical and migration handling

- Preserve historical WOPs, source files, package directories, submission and
  admission receipts, evidence, and runtime records byte-for-byte.
- Do not bulk-migrate historical records.
- On read, classify historical records as legacy-supported, legacy-read-only,
  superseded, or invalid using their existing identity and digest.
- New submissions must not depend on historical `required_approvals` semantics.
- The lifecycle source can remain byte-identical; only a deterministic derived
  canonical/provenance projection is needed.

## Zeus-native verification after implementation

The operator should verify, without using an execution command:

```text
zeus wop identity SOURCE --json
zeus wop traceability SOURCE --json
zeus wop readiness SOURCE --json
zeus wop verify SOURCE --json
zeus submit SOURCE --json
zeus submit SOURCE --json
zeus mission snapshot ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission blockers ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission next ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
```

Expected independent observations are one stable WOP/Mission identity, one
stable submission receipt, first result `PASS`, replay `IDEMPOTENT`, state
`ADMISSION_REQUESTED`, no admission/execution identity, authority
`operator-submitted WOP`, explicit-gate blockers only when declared, and next
action `EVALUATE_MISSION_ADMISSION`.

## Boundary and status

This report is a recommendation only. The lifecycle WOP was not submitted,
admitted, dispatched, executed, published, synchronized, or closed. CAGF-01
was not modified or executed.
