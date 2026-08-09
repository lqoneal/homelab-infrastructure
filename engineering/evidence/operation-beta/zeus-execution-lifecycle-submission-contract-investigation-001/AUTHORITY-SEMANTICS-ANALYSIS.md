# Legacy Approval and Submitted-WOP Authority Analysis

## Normative distinction

The shared WOP contract states that the operator-submitted WOP is the work
authority for the bounded work it contains. It separately requires mission,
repository, baseline, provider, lifecycle, admission, integrity, and
qualification controls. It says an approval is required only when the
submitted WOP declares that approval gate.

The lifecycle source declares explicit authority and does not declare an
approval gate. Its authority section explicitly says no second generic
corrective, implementation, execution, or WOP authorization grant is required.

## What `required_approvals` means in the legacy path

In `scripts/zeus`, `--approval` is passed as `required_approvals` to
`MissionOrchestrator.submit`. The orchestrator stores it in a legacy mission
record. During `evaluate`, an empty list produces
`REQUIRED_APPROVAL_CONFIGURATION_MISSING`. During `select`, the orchestrator
creates an `approval_request`; `approve` changes the legacy mission to an
authorized state and creates a lifecycle handoff record.

Therefore the legacy field is a combination of:

1. **Legacy admission-record metadata**: it is part of the input required by
   `MissionOrchestrator.submit`.
2. **Mission-selection approval configuration**: it is used to decide whether
   a queued legacy mission is eligible and to create the selection approval
   request.
3. **Legacy authorization transition input**: the later `approve` operation
   changes the legacy queue state.

It is not, by itself, proof of an approval gate declared in the WOP. It is not
the P2 submission receipt's authority, and it is not the explicit approval
semantics enforced by `AdmissionController`.

## What the canonical path does

`Stage1Runtime.submit_development` records:

```text
governance_authority = operator-submitted WOP
wop_authority        = operator-submitted WOP
approval_state       = NOT_REQUIRED_UNLESS_DECLARED_IN_WOP
```

The current authority-convergence tests prove that this authority is enough
for bounded workspace-writing execution and that no generic second approval is
needed. A separate test proves an explicit in-WOP approval gate still yields
`OPERATOR_APPROVAL_REQUIRED`. This is the correct semantic split.

`wop_admission.py` independently checks an `approval` object or an explicit
approval gate in the submitted WOP. If an approval gate is declared and no
approval is supplied, admission fails closed. That control must remain.

## Recommendation on controls

Do not remove approval controls globally. Instead:

- remove the accidental dependency of new Development source submission on
  legacy `required_approvals`;
- retain legacy `required_approvals` for actual legacy admission-record input
  until compatibility retirement is governed;
- expose legacy approval as selection-compatibility metadata, not as generic
  execution authority;
- preserve all explicit WOP approval gates;
- preserve admission, repository, baseline, provider, session, evidence,
  publication, synchronization, and scope controls.

## Fail-closed rules for the target

The target must reject or block on missing/ambiguous/conflicting:

- WOP/Mission identity;
- source/output/template/context digests;
- repository identity or baseline;
- explicit approval-gate satisfaction;
- package/manifest integrity;
- admission and execution receipts;
- provider/session/evidence/publication/synchronization state.

It must never manufacture a generic `--approval` value to make a legacy
branch pass.
