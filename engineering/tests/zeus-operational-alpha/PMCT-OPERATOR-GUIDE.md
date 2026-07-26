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

Return failed work to Codex with the run ID, report path, evidence directory,
failed assertions, and unchanged repository status. Do not paste secrets.

Evidence is stored at `engineering/runtime/pmct/runs/<run-id>/`. Repeating
read-only discovery is safe. An interrupted run without `COMPLETE` is
incomplete; rerun the same gate to create a new run and retain the interrupted
directory as evidence. A report can be retrieved with `pmct report OA-NN`.

State-changing gates are read-only unless the matrix marks the gate as a state
transition and the operator supplies `--authorized-transition`. The framework
then still requires separately resolved authority. P2-020 deliberately
contains no authorized production transition implementation.

## OA-01 copyable example

```bash
cd /data/engineering/repositories/homelab
engineering/tests/zeus-operational-alpha/bin/pmct inspect
engineering/tests/zeus-operational-alpha/bin/pmct show OA-01
engineering/tests/zeus-operational-alpha/bin/pmct run OA-01
engineering/tests/zeus-operational-alpha/bin/pmct report OA-01
```

ZEUS-P2-021 implements the locked `zeus next-action` acceptance interface.
OA-01 now demonstrates `PASS` while still recording the stale published
baseline, inactive dispatcher, empty agent registry, BETA mode, disabled
dispatch, and the correctly prioritized baseline-republication action.
The overall PMCT remains `NOT_READY`; OA-02 through OA-30 have not passed.

OA-30 can pass only after OA-01 through OA-29 have passed and a separate
authorized declaration is observably performed and evidenced. Any earlier
regression prevents the later gate from passing.
