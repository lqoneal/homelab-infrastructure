# Gate A Implementation Review Unit 1 — External WOP Test Fixture Isolation

Date: 2026-07-29

Mission: `ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001`

Gate: `A`

Status: `IN_PROGRESS — CONSUMER_REDIRECTION_REQUIRED`

Scope: test infrastructure only. No production module, production behavior,
Mission Contract, Progressive OA implementation, PMCT design, gate-approval
design, runtime state, implementation gate, or external-tree permission was
changed.

## Test Fixture Inventory

The pre-change fixed-string scan of executable test paths found exactly two
references to:

`/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP`

| Test | Reference | Classification | Required test behavior |
|---|---|---|---|
| `scripts/tests/test-zeus-next-action.py` | `bin/check-gate-eligibility` invocation | direct filesystem dependency | Distinguish conditionally eligible exit `0` from blocked exit `77`, and retain the expected lifecycle output assertions |
| `scripts/tests/test-zeus-gate-approval.py` | `shutil.copy2(.../bin/record-operator-approval)` | copied executable | Persist a binding-valid synthetic approval receipt and checksum inside the temporary WOP |

No test reference was an approval-receipt dependency, verification dependency,
or historical fixture. Existing approval and verification records in
`test-zeus-gate-approval.py` were already synthetic records created beneath
its `TemporaryDirectory`; they were not read or copied from the external
tree.

No additional executable test reference was found under `scripts` or
`engineering` after excluding Gate A evidence and historical evidence.

## Fixture Design Notes

### Next-action eligibility fixture

`test-zeus-next-action.py` now creates
`<TemporaryDirectory>/legacy-wop-fixture` with:

1. an empty `operator-approvals/` directory;
2. a synthetic `README.md`;
3. one executable `bin/check-gate-eligibility`.

The command accepts the existing `OA-02` argument and derives its result only
from the test-owned `FIXTURE_OA01_ACCEPTED` environment value:

- accepted: exit `0`, `ELIGIBILITY=CONDITIONALLY_ELIGIBLE`;
- absent: exit `77`, `OA-02_ELIGIBILITY=BLOCKED` and
  `BLOCKING_REASON=OA-01_OPERATOR_ACCEPTANCE_REQUIRED`.

The decision resolver runs against the test's existing temporary Git
repository with explicit synthetic OA-01 and OA-02 lifecycle results. It no
longer imports or calls the live `oa02_lifecycle` resolver and no longer
observes the current repository runtime. Cleanup is registered with
`unittest` and occurs on success or failure.

The fixture contains no authoritative approval, verification, decision,
manifest, or runtime record. It reproduces only the output and exit-code shape
required by the assertions.

### Gate-approval primitive fixture

`test-zeus-gate-approval.py` now writes a synthetic Python executable to:

`<TemporaryDirectory>/wop/bin/record-operator-approval`

The fixture primitive implements only the behavior exercised by the test:

1. validate the gate and confirmation mode;
2. resolve only explicit test-owned environment paths;
3. validate a synthetic predecessor digest when supplied;
4. validate the synthetic verification record and its checksum;
5. require the fixture repository HEAD to match the verification binding;
6. create the expected text receipt fields beneath the temporary WOP;
7. mark the receipt read-only;
8. create its SHA-256 sidecar.

It neither embeds nor copies authoritative external records or executable
content. The test's resume and eligibility commands remain independently
generated synthetic shell fixtures in the same temporary WOP.

## Test Conversion Report

### Conversion 1 — next action

Intent retained:

- the legacy decision remains observational;
- every file in the temporary repository remains byte-for-byte unchanged;
- dispatch remains disabled;
- lifecycle verification and acceptance vocabulary remains constrained;
- eligibility remains conditional after recorded acceptance;
- the same fixture also proves missing acceptance remains blocked with exit
  `77`.

Assertions and pass/fail semantics were retained. Only the command location and
explicit `ZEUS_GATE_WOP` binding changed.

Focused result:

```text
Ran 9 tests in 0.307s
OK
```

The immediately following fixed-string scan of the converted file returned
zero external-root references. Python compilation passed.

### Conversion 2 — gate approval

Intent retained:

- verification must precede approval;
- the receipt binds gate, PMCT run, repository, HEAD, evidence, operator,
  verification record/digest, confirmation mode, and predecessor;
- duplicate and conflicting operations fail;
- predecessor lineage remains integrity checked;
- receipt and verification tampering remains rejected;
- success reports conditional next-gate eligibility without execution.

All existing assertions and pass/fail semantics ran unchanged against the
synthetic primitive.

Focused result:

```text
Ran 35 tests in 1.864s
OK
```

The immediately following fixed-string scan of the converted file returned
zero external-root references. Python compilation passed.

Combined rerun after both conversions:

```text
test-zeus-next-action.py: 9 tests, OK
test-zeus-gate-approval.py: 35 tests, OK
```

## Verification Results

| Verification | Result |
|---|---|
| Complete executable test scan for exact external root | `0` references |
| External inventory `test_consumers` | `0` |
| External inventory `production_consumers` | `4` (unchanged and outside this review unit) |
| External inventory `service_consumers` | `0` |
| External inventory `active_process_users` | `0` |
| Next-action focused regression | `9/9 PASS` |
| Gate-approval focused regression | `35/35 PASS` |
| Python compilation of both modified tests | `PASS` |
| Diff whitespace validation | `PASS` |
| Next-action test SHA-256 | `9efdd19be66e4563613f4be5873588a022006001d0713cb6dcc13eb43f9a7593` |
| Gate-approval test SHA-256 | `6251087af13383feef825045cdc84d845042570c949446ceef355db21466201b` |
| External root mode | `0755` |
| External root device/inode | `2065 / 2362046` |
| External manifest SHA-256 | `fbf1e69b4acc7a223aab1f547adc8698ae025912eaf82fd7e85c5121e2cd1f69` |

The inventory command initially failed when its executable launcher could not
import the `scripts` package. It succeeded unchanged when rerun with the
repository explicitly supplied on `PYTHONPATH`. This is an existing launcher
packaging issue, not a fixture-isolation failure, and no production launcher
change was made.

The final production reference scan still reports only:

1. two lines in `scripts/lib/emp/oa02_lifecycle.py`;
2. one default in `scripts/lib/emp/gate_approval.py`;
3. one default in
   `engineering/tests/zeus-operational-alpha/lib/pmct.py`.

Those four production references match the prior Gate A inventory.

## Remaining Test Dependency List

None.

Historical mentions in evidence and planning remain provenance and are not
executable test dependencies.

## Scope and integrity conclusion

Files changed by this review unit:

1. `scripts/tests/test-zeus-next-action.py`;
2. `scripts/tests/test-zeus-gate-approval.py`;
3. this Gate A evidence record.

Production consumers were not edited by this review unit. Existing unrelated
worktree changes were preserved and are not claimed as review-unit changes.
The external WOP was not read by the converted test executions, copied,
executed, imported, or modified.

Gate A remains `IN_PROGRESS — CONSUMER_REDIRECTION_REQUIRED`. Freeze approval
is not requested. Gate B has not begun.

## Next review-unit recommendation

Proceed, under a separately bounded Gate A implementation review, with
complete retirement of the classified dead consumer
`scripts/lib/emp/oa02_lifecycle.py` and only its unreachable legacy routing.
Before removal, characterize default Progressive command routing and scan for
forced `ZEUS_PROGRESSIVE_OA=0` callers as required by the approved Gate A
plan. Do not begin transitional `GateApprovalService` narrowing in the same
review unit.
