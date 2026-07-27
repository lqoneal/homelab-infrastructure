# PMCT Operator Guide

Qualification sequencing for commit and publication boundaries is defined in
`QUALIFICATION-PHASES.md`. In particular, a committed HEAD that has not yet
been published is expected to report a baseline mismatch and OA-01
`NOT_READY`; publication-dependent OA-01 qualification runs only after the
successor publication is activated.

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
8. Run `zeus approve OA-NN`; it prints the exact verification command and
   stops without requesting approval.
9. Run `zeus verify OA-NN`; retain its checksummed verification record.
10. Run `zeus approve OA-NN` again and explicitly confirm acceptance.

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

Operator-verification readiness is reported separately. `READY` means the
repository, authority, publication, and current HEAD prerequisites permit the
operator to run verification while evidence remains `ABSENT`. It is not a
PMCT demonstration `PASS`, operator verification `PASS`, or acceptance.
`NOT_READY` means those prerequisites are unsatisfied. A stale, failed,
malformed, or differently bound record is preserved but cannot suppress
`READY` when the current prerequisites are satisfied; it is treated as absent
for the current binding.

Return failed work to Codex with the run ID, report path, evidence directory,
failed assertions, and unchanged repository status. Do not paste secrets.

Normal operators do not manually supply those identifiers during successful
closeout. Zeus resolves them from authoritative PMCT and WOP state.
`bin/record-operator-approval` is an internal persistence primitive.
It creates a new versioned receipt for the binding resolved by Zeus and never
overwrites the legacy receipt or a prior successor. Gate eligibility verifies
the receipt checksum and requires its approved HEAD to equal the current
repository HEAD; mere receipt-file existence is not acceptance.

A verification remains valid only while gate, PMCT run ID, evidence and
evidence-manifest digests, qualified repository HEAD, operator identity, WOP
identity, WOP manifest digest, verification checksum, and clean tracked state
all match. Any mismatch requires a fresh `zeus verify OA-NN`.

For this check, “clean tracked state” includes one narrow authenticated
condition: the sole unstaged tracked delta may be
`engineering/runtime/pmct/capability-state.yaml` when Zeus reconstructs it
exactly from the selected integrity-valid PMCT run and the committed ledger
baseline. The file is not ignored. Staged changes, extra tracked changes, or
any non-derived ledger field fail verification.

Zeus considers only PMCT `PASS` runs whose repository, HEAD, implementation
baseline, published baseline, and active authority publication all match the
current binding. Older PASS evidence remains auditable but is not a candidate
for current verification.

Evidence is stored at `engineering/runtime/pmct/runs/<run-id>/`. Each completed
run atomically reconciles `engineering/runtime/pmct/capability-state.yaml`
with its run ID, completion time, result, overall result, and gate status.
Repository authority, project, qualification, dispatcher, execution, mission,
and operational decision state remain unchanged. Documented bounded
presentation telemetry such as operator-interface `invocation_count` may
advance. An interrupted run without
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

ZEUS-P2-021 implements the locked `zeus next-action` acceptance interface, and
ZEUS-P2-026 reconciles its post-publication precedence. OA-01 retains a Codex
PMCT demonstration result of `PASS`; the current publication matches
repository HEAD, operator-verification readiness is `READY`, verification
evidence is `ABSENT`, and operator acceptance is not recorded. The
authoritative next action is `RUN_OA-01_VERIFICATION`. Dispatcher commissioning
and OA-02 execution remain prohibited. OA-02 is blocked by
`OA-01_OPERATOR_ACCEPTANCE_REQUIRED`, overall PMCT remains `NOT_READY`, and
OA-02 through OA-30 have not been accepted.

OA-30 can pass only after OA-01 through OA-29 have passed and a separate
authorized declaration is observably performed and evidenced. Any earlier
regression prevents the later gate from passing.
