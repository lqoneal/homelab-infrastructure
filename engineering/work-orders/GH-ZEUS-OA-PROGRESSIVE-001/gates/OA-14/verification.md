# OA-14 Operator Verification Guide

## Intent and implementation

This gate is intended to prove explicit authorization, rejection, expiration, and replay-safe dispatch authorization receipts.
The implementation procedure and evidence manifest describe the exact change made.
Every check is necessary to bind the observed behavior to the admitted package,
current repository, authority, agent, and cumulative predecessor state.

## Prerequisites

The package manifest and admission receipt must validate; `OA-14` must be the sole
active gate; the repository and EOS must be synchronized; gate implementation must
be complete; and the evidence directory must contain the generated manifest.

## Steps and expected results

1. Run `zeus gate show OA-14`. Expect JSON with `gate_id` equal to `OA-14` and the
   complete contract. Any missing field is FAIL.
2. Run `zeus gate objective OA-14`. Expect the objective in this guide. A different
   objective is FAIL.
3. Run `zeus gate evidence OA-14`. Expect the evidence template and runtime directory.
4. Run `zeus verify OA-14`. Expect all positive, negative, replay, recovery, and
   cumulative checks to report PASS and create `runtime/evidence/OA-14/VERIFIED`.
5. Run `scripts/engctl repository health`, `scripts/engctl eos sync-validate`,
   `scripts/engctl registry validate`, and `scripts/engctl validate`. Expect PASS.
6. Run `git status --short --branch` and `git rev-parse HEAD`. Expect the documented
   branch/commit and only the gate's authorized publication set.
7. Run `zeus explain OA-14` and inspect every file returned by
   `zeus gate evidence OA-14`. Confirm checksums, identities, timestamps, exit codes,
   assertions, reconciliation, and the `VERIFIED` marker.

PASS requires every expected result and no unexplained mutation. FAIL includes any
nonzero verification, absent evidence, checksum mismatch, stale authority, unexpected
working-tree path, reconciliation conflict, or later-gate activity.

## Decision and continuation

Reject with `zeus decline OA-14 --operator OPERATOR`; this persists a rejection and
stops fail closed. Accept only after PASS with
`zeus approve OA-14 --operator OPERATOR`. Confirm the receipt using
`zeus gate receipt OA-14`. Run `zeus resume`; the controller recognizes the receipt
and directly enables `OA-15` without a new mission authorization. After OA-30,
resume stops at declaration preparation and requests separate declaration/freeze authority.
