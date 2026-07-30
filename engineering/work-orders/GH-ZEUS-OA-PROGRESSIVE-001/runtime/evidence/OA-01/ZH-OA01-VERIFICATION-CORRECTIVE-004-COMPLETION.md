# ZH-OA01-VERIFICATION-CORRECTIVE-004 Completion Report

## Identity and boundary

- Repository: `/data/engineering/repositories/homelab` (`homelab`)
- Branch: `main`
- Starting HEAD: `f79462bd837df51f12a103f2ebc69a071c27f45d`
- Ending HEAD: `f79462bd837df51f12a103f2ebc69a071c27f45d`
- Qualified baseline: `bcdd0b1a19045654d470bc65383c05a976bae2a6`
- Handoff: `ZH-OA01-VERIFICATION-CORRECTIVE-004`
- Operator acceptance recorded: **No**
- OA-02 enabled: **No**

The starting tree was the pre-existing modified mission tree reported in the
handoff initiation transcript. Its raw Git porcelain inventory digest was
`2ccf14068b0c4bc3af581bab9ed26f7f5d090688dbe2ed7823986097018c576c`.
The integrity-bound ending verification inventory contains 46 entries and has
canonical digest
`a9bd036a4cadc9b1d4de72bdaa0e0dc4018690de4b307bbafa08bea3b561d834`.
The complete ending inventory, including status, path, and file SHA-256, is in
`VERIFICATION.json`.

## Root cause and correction

The Progressive OA command dispatcher hard-coded `IMPLEMENTATION_REQUIRED` for
every `zeus verify` request. It never invoked an OA-01 verification assessor,
even when OA-01 was already `AWAITING_OPERATOR_VERIFICATION`.

The correction adds a production OA-01 assessor and routes only
`zeus verify OA-01` to it. The assessor validates package admission and
integrity, repository identity/root/remote/branch/HEAD/upstream/baseline,
Mission Contract authorization, sole-active-gate state, later-gate inactivity,
implementation-evidence integrity, deterministic Zeus observations, a
fail-closed negative selector, cumulative tests, repository health, EOS
synchronization, registry validation, aggregate validation, and complete
working-tree content inventory. Evidence and marker writes are atomic and
fsync-backed. Approval now validates the current marker rather than accepting
an empty or stale sentinel.

Stale attempts are preserved under `attempts/<marker-digest>/`; two development
attempts were preserved while the content-bound inventory and recovery test
were finalized. No historical evidence bytes were altered.

## Files changed by this corrective handoff

- `scripts/lib/emp/oa01_gate_verification.py`
- `scripts/lib/emp/progressive_oa.py`
- `scripts/zeus`
- `scripts/tests/test-zeus-oa01-verification.py`
- `scripts/tests/test-zeus-oa01-implementation.py`
- `scripts/tests/test-zeus-progressive-oa.py`
- this completion report

All other modified and untracked paths were present mission work and were
preserved.

## Verification results

The focused command ran 14 tests and passed:

`python3 -m unittest scripts/tests/test-zeus-oa01-verification.py scripts/tests/test-zeus-oa01-implementation.py scripts/tests/test-zeus-progressive-oa.py scripts/tests/test-zeus-stage1-runtime.py`

The final Zeus evidence records these exit codes:

| Check | Exit |
| --- | ---: |
| package integrity | 0 |
| gate show/objective/evidence, twice | 0 |
| mission show/readiness/blockers/next, twice | 0 |
| unknown mission negative test | 78 (expected fail closed) |
| focused cumulative regression | 0 |
| repository health | 0 |
| EOS synchronization | 0 |
| registry validation | 0 |
| aggregate `scripts/engctl validate` | 0 |

Replay returned the same evidence digest with `idempotent_replay: true` and
created no duplicate state transition, receipt, event, or marker. The recovery
test interrupted after durable evidence and before marker publication and
confirmed that partial evidence did not qualify.

## Integrity evidence

- Verification timestamp: `2026-07-29T10:02:43.069165+00:00`
- Canonical evidence digest:
  `3ba2ec4f077c4e02dee3eed29fbad10fdcbfe4fcbf0137b22ebbd3f059bd0750`
- `VERIFICATION.json` file SHA-256:
  `f78bca8c7df96296b4990c45fcee3f67fef5950d272fdc32033de6306a441ef4`
- `VERIFIED` file SHA-256:
  `43626172b97a478afa34f17c1a713e11365ae28f713310dd7dc1d29443c8944b`
- Marker canonical digest:
  `742c95dfead7256d375b0a0c1241e146e013c9a1f8498909a63cd78e5b0fadda`

The marker binds package, gate, repository identity/root, branch, exact HEAD,
authority source, evidence digest, timestamp, and PASS result.

## State and reconciliation

Before and after verification, OA-01 remained
`AWAITING_OPERATOR_VERIFICATION`, OA-02 remained `PENDING`, and there were no
accepted gates. The mission projection changed only from the verification
blocker to `OA-01_OPERATOR_ACCEPTANCE_REQUIRED`; its next authorized action
remains `VERIFY_AND_DECIDE_OA-01`. No acceptance receipt, operator consent,
dispatch, EENS event, baseline freeze, declaration, or later-gate activity was
created.

Repository, EOS, registry, package, runtime, Mission Contract, Project State,
Work Registry, and controlled-document validation all reconciled without
reported conflict. The working tree remains intentionally modified because the
authorized mission publication set and this corrective work are not committed.

## Remaining risk

The broader dirty mission tree predates this corrective handoff. Verification
binds its exact content inventory, but publication/commit of that larger set
remains a separate repository-owner action. Operator acceptance is deliberately
pending.
