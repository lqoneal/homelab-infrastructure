# ZH-OA04 Acceptance Replay Corrective Evidence

Date: 2026-07-29  
Handoff: `ZH-OA04-ACCEPTANCE-REPLAY-CORRECTIVE-001`  
Package: `GH-ZEUS-OA-PROGRESSIVE-001`  
Disposition: `CORRECTED — VERIFIED_AWAITING_OPERATOR_ACCEPTANCE`

## Work initiation

The work was classified as Category A repository engineering work. The
canonical repository was `/data/engineering/repositories/homelab`, identity
`homelab`, branch `main`, HEAD
`f79462bd837df51f12a103f2ebc69a071c27f45d`, upstream `origin/main`, and
ahead/behind `0/0`. The remote was
`git@github.com:lqoneal/homelab-infrastructure.git`. Contract baseline
`d25d144312b73fc8230113c99f5d0368037b4483` and qualified WOP baseline
`bcdd0b1a19045654d470bc65383c05a976bae2a6` were ancestors of HEAD.

The pre-existing modified working tree was inventoried and preserved. No
reset, checkout, cleanup, deletion, staging, commit, or historical-artifact
rewrite was performed. Repository health, controlled-document validation,
registry validation, package integrity, admission integrity represented in
the corrected OA-04 authority evidence, EOS synchronization, and integrated
platform validation passed. The mission-specific execution snapshot returned
no repository Mission Contract for the corrective handoff and failed closed;
the handoff itself bounded this correction to the OA-04 approval defect. It
did not authorize dispatch, execution, acceptance, declaration, or freeze.

## Root cause and affected path

The operator path is:

```text
scripts/zeus approve OA-XX --operator OPERATOR
  -> scripts.lib.emp.progressive_oa.decide()
  -> receipt lookup/persistence
  -> runtime/state.json transition
```

The former first durable branch in `decide()` constructed the fixed path
`runtime/decisions/OA-XX/accepted.json`. If that file existed, it parsed the
file, checked only `receipt["decision"] == "ACCEPTED"`, and immediately
returned `(receipt, True)`. This happened before loading or enforcing the
current gate lifecycle, active-gate identity, runtime `acceptance_receipt`
pointer, VERIFIED marker, corrected evidence digest, operator, supersedence,
or receipt digest.

`verify_receipt()` already rejected OA-04 because runtime did not mark OA-04
accepted or reference the flat path, but approval replay did not call it.
`verify_receipt()` was itself fixed-path-specific, and
`ControlledMissionAuthority` used fixed prior-gate paths. The combined design
made `accepted.json` existence act as decision currency even when the receipt
was superseded and no longer current.

Prior unsafe observation:

```text
OA-04 state: AWAITING_OPERATOR_VERIFICATION
runtime acceptance_receipt: null
historical accepted.json: present
supersedence record: present
approve result: historical receipt with idempotent_replay=true
state transition: none
```

## Corrected approval algorithm

Approval now applies these ordered rules:

1. Load the current package state and gate.
2. Treat a request as replay only if the gate is `ACCEPTED`.
3. Require the runtime `acceptance_receipt` locator and resolve that exact path
   inside the package decision-history root.
4. Require the referenced receipt to exist.
5. Validate the current VERIFIED marker mapping, package/gate/result, canonical
   marker digest, corresponding VERIFICATION record, and canonical evidence
   digest.
6. Validate receipt canonical digest, decision, package, gate, package-manifest
   binding for schema 2, operator compatibility, marker-file SHA-256,
   marker digest, and evidence digest.
7. Search supersedence records by historical path and receipt digest; reject a
   match.
8. Only after all checks return the referenced current receipt with
   `idempotent_replay: true`.
9. For a new explicit decision, require OA-04 to be the sole active gate in
   `AWAITING_OPERATOR_VERIFICATION`, require an operator, and validate the
   current corrected marker/evidence before constructing the receipt.
10. Persist an immutable unique receipt, read and validate it, bind state to
    that exact path, transition OA-04, and advance exactly to OA-05.

The current corrected OA-04 bindings are:

- evidence digest:
  `4a4262f465844f7965b0ab95e0b3091fd17fda90fe89e5270f9a5995c7ecd214`
- marker digest:
  `8996960699a4970b2fda196eecc043ddcda1608ffd3321ee90531cc5c55091e3`
- VERIFIED file SHA-256:
  `e16b0a1a48be91f5dc4ef9af5db1068ee687eb069e055bef9b05a650aa2f01dc`
- package: `GH-ZEUS-OA-PROGRESSIVE-001`
- gate: `OA-04`

## Receipt storage decision and recovery

The fixed `accepted.json` path cannot preserve more than one acceptance
decision without overwrite. New receipts therefore use:

```text
runtime/decisions/OA-XX/accepted-RECEIPT_DIGEST.json
```

The receipt digest is a unique immutable identity. Runtime
`acceptance_receipt` is the deterministic current index. Consumers resolve
that pointer rather than infer currency from a conventional filename.
Supersedence remains explicit, historical receipts remain append-only, and
current lookup fails closed when state and receipt disagree.

Receipt creation uses exclusive create plus flush and `fsync`. Interruption
before persistence leaves no receipt and no state advance. Interruption after
receipt persistence but before state transition leaves an orphan audit record;
a retry recovers only when exactly one unique receipt matches the same current
package, gate, marker, evidence, and operator. Multiple valid orphans stop
fail closed. Recovery does not report idempotent replay until state is
actually accepted and references the receipt.

Historical files were preserved unchanged:

- `runtime/decisions/OA-04/accepted.json`
  - receipt digest:
    `fd578e57b4d67f6eb7102fed3951e682653263efee701f7d42b15c629612d08d`
  - historical marker-file binding:
    `49d132fd8df157dd4576dbff588c41e613f4072603d177b53ea8fb3a78705869`
- `runtime/decisions/OA-04/superseded-by-contract-correction.json`
  - explicitly identifies the historical receipt and digest

## Test matrix

The focused 17-test suite covers:

| Case | Result |
| --- | --- |
| No receipt creates a new unique receipt | PASS |
| Current matching receipt replays | PASS |
| Superseded receipt is rejected | PASS |
| Historical different-evidence receipt is not replayed | PASS |
| Receipt exists while gate is not accepted | PASS, new decision path only |
| Runtime lacks a receipt reference | PASS, current lookup fails closed |
| Receipt digest mismatch | PASS, fails closed |
| Marker digest mismatch | PASS, fails closed |
| Operator mismatch | PASS, fails closed |
| Historical receipt and supersedence preservation | PASS |
| New acceptance advances exactly one gate | PASS |
| OA-05 remains pending before acceptance | PASS |
| Corrected current receipt replays after acceptance | PASS |
| No dispatch, execution, declaration, or freeze | PASS |
| Interruption before receipt persistence | PASS |
| Interruption after persistence before transition | PASS |
| Controller remains single-gate and idempotent | PASS |

All mutating acceptance cases ran in temporary fixture repositories. The live
command `zeus approve OA-04` was not executed.

## Validation results

- focused Progressive OA approval/receipt tests: 17 PASS
- OA-01 implementation and verification: 5 PASS
- OA-02 controlled authority and lifecycle: 16 PASS
- OA-03 Mission Contract discovery: 5 PASS
- OA-04 context reconstruction and mission resolution: 11 PASS
- OA-05 Mission Staging Contract: 9 PASS
- combined authority/context/resolution regression: 39 PASS
- Operational Alpha independent inventory: PASS, including recursive
  hyphenated suite execution
- state-protection and result/discovery tests: PASS
- Progressive OA package verification: PASS, 30 gates
- Work Registry schema, serialization, identifiers, hierarchy, ordering,
  state, dependency, and authority boundary: PASS
- repository health: PASS; modified working tree preserved
- repository controlled-document validation: PASS
- EOS synchronization: synchronized and PASS
- integrated Engineering Platform validation: PASS
- independent `scripts/verify.sh`: 20 checks PASS, 0 failures
- `git diff --check`: PASS

## Lifecycle before and after

Before correction:

```text
OA-01..OA-03: ACCEPTED
OA-04: AWAITING_OPERATOR_VERIFICATION
OA-04 current acceptance_receipt: null
OA-04 historical accepted.json: present and superseded
OA-05..OA-30: PENDING
approval software: unsafe historical replay
```

After correction and verification:

```text
OA-01..OA-03: ACCEPTED
OA-04: VERIFIED_AWAITING_OPERATOR_ACCEPTANCE
OA-04 current acceptance_receipt: absent
OA-04 historical accepted.json: preserved and superseded
OA-05..OA-30: PENDING
approval software: ready for a new explicit corrected decision
execution agent dispatch: none
mission execution: none
Operational Alpha declaration: none
baseline freeze: none
```

No live state transition was performed. `zeus gate receipt OA-01` through
`OA-03` pass integrity validation. `zeus gate receipt OA-04` returns
`FAIL: current acceptance receipt does not exist for OA-04` with exit 78.

## Reconciliation and remaining risks

Approval semantics, append-only receipt lifecycle, supersedence, replay rules,
operator CLI documentation, Project State, Work Registry revision 83, OA
progress tracking, current-receipt consumers, tests, and this corrective
evidence were reconciled. Historical verification evidence was not edited to
appear current.

Remaining risk is bounded to operator action and future schema evolution. The
next operator must independently review and explicitly decide OA-04. Schema 1
receipts remain supported for already accepted OA-01 through OA-03 using their
integrity digest, package/gate identity, operator, and exact current marker-file
SHA-256; all new receipts use schema 2 with explicit evidence, marker, and
package-manifest digests. Any future decision-history schema must preserve
exclusive path resolution, explicit current state binding, and fail-closed
supersedence checks.

Final disposition:

```text
CORRECTED — VERIFIED_AWAITING_OPERATOR_ACCEPTANCE
```
