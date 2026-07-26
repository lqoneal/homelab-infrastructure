# PMCT Operator Guide

## Purpose and timing

Run the PMCT in a separate Bash shell after each locked Operational Alpha gate
is implemented and before that gate is accepted. PMCT is a capability
demonstration, not a source inspection or automatic approval mechanism.

## Normal workflow

1. Enter `/data/engineering/repositories/homelab`.
2. Run `engineering/tests/zeus-operational-alpha/bin/pmct inspect`.
3. Run `.../bin/pmct list`.
4. Review a gate with `.../bin/pmct show OA-NN`.
5. Execute `.../bin/pmct run OA-NN`.
6. Read the terminal result and generated capability report.
7. Verify `artifacts.sha256` and the `COMPLETE` marker.
8. Approve or reject the gate through the separately controlled closeout
   process. PMCT never edits capability state automatically.

`PASS` means the observable demonstration and evidence completed. `FAIL`
means implemented behavior was wrong or unsafe. `BLOCKED` means identity,
authority, or prerequisites prevented evaluation. `NOT_READY` means a required
surface or demonstration is absent. Future commands are reported as
`EXPECTED_NOT_YET_IMPLEMENTED` during discovery, but become `NOT_READY` when
the selected gate requires them.

`PASS` does not mean the operator independently verified or accepted the gate.
The lifecycle is implementation complete, Codex validation PASS, operator
verification pending, operator acceptance not recorded, and gate awaiting
operator verification until the WOP receipt is created and reconciled.

Return failed work to Codex with the run ID, report path, evidence directory,
failed assertions, and unchanged repository status. Do not paste secrets.

Evidence is stored at `engineering/runtime/pmct/runs/<run-id>/`. Repeating
authoritative-state observation is safe: tracked repository, authority,
project, PMCT capability, qualification, dispatcher, execution, mission, and
operational decision state remain unchanged. Documented bounded presentation
telemetry such as operator-interface `invocation_count` may advance, and each
PMCT run creates a new evidence directory. An interrupted run without
`COMPLETE` is incomplete; rerun the same gate to create a new run and retain
the interrupted directory as evidence. Inspect and report an exact completed
run with `pmct inspect <PMCT-RUN-ID>` and `pmct report <PMCT-RUN-ID>`.
Gate-based `pmct report OA-NN` remains a latest-run convenience and shall not
be used when an exact run ID is available. Bare `pmct inspect` reports current
live state.

State-changing gates remain observation-only unless the matrix marks the gate
as a state transition and the operator supplies `--authorized-transition`.
The framework then still requires separately resolved authority. P2-020
deliberately contains no authorized production transition implementation.

## OA-01 copyable example

```bash
cd /data/engineering/repositories/homelab
engineering/tests/zeus-operational-alpha/bin/pmct inspect
engineering/tests/zeus-operational-alpha/bin/pmct show OA-01
engineering/tests/zeus-operational-alpha/bin/pmct run OA-01
engineering/tests/zeus-operational-alpha/bin/pmct report OA-01
```

ZEUS-P2-021 implements the locked `zeus next-action` acceptance interface.
OA-01 has a Codex PMCT demonstration result of `PASS` while still recording the stale published
baseline, inactive dispatcher, empty agent registry, BETA mode, disabled
dispatch, and the correctly prioritized baseline-republication action.
Independent operator verification is pending and operator acceptance is not
recorded. The OA-01 gate status is `AWAITING_OPERATOR_VERIFICATION`; OA-02 is
blocked by `OA-01_OPERATOR_ACCEPTANCE_REQUIRED`. The overall PMCT remains
`NOT_READY`; OA-02 through OA-30 have not been accepted.

OA-30 can pass only after OA-01 through OA-29 have passed and a separate
authorized declaration is observably performed and evidenced. Any earlier
regression prevents the later gate from passing.
