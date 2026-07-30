# ZH-OA05 Mission Count Investigation

Date: 2026-07-29  
Handoff: `ZH-OA05-MISSION-COUNT-INVESTIGATION-001`  
Disposition: `CORRECT_ZERO_COUNT — STRUCTURAL_VALIDATION_HARDENED`

## Engineering Work Initiation

- Repository: `/data/engineering/repositories/homelab`
- Identity: `homelab`
- Branch / upstream: `main` / `origin/main`, aligned `0/0`
- HEAD: `f79462bd837df51f12a103f2ebc69a071c27f45d`
- Qualified WOP baseline:
  `bcdd0b1a19045654d470bc65383c05a976bae2a6`, ancestor of HEAD
- Package: `GH-ZEUS-OA-PROGRESSIVE-001`, 30-gate integrity PASS
- Registry validation: PASS
- EOS synchronization validation: PASS
- Repository health: PASS; existing modified working tree preserved
- OA-01 through OA-05: `ACCEPTED`, current receipts integrity PASS
- OA-06: sole active gate, `PENDING`
- OA-07 through OA-30: `PENDING`

No live mission was submitted. No dispatch, execution, OA-06 acceptance,
Operational Alpha declaration, or baseline freeze was performed.

## Complete status path

The production path is:

```text
scripts/zeus status --json
  -> Stage1Runtime(ROOT, ROOT/.zeus/runtime/stage1)
  -> Stage1Runtime.status()
  -> Stage1Store.all()
  -> sorted .zeus/runtime/stage1/missions/*.json
  -> Stage1Store.load_path() for each record
  -> integrity and structural validation
  -> derived mission_count and per-state counts
  -> value["mission_admission"]
  -> JSON output
```

`ZEUS_STAGE1_STATE` is an explicit test-state override. Production uses
`.zeus/runtime/stage1`.

## Authoritative sources

| Output | Authoritative source |
| --- | --- |
| `mission_count` | Number of successfully loaded and validated persisted `missions/*.json` records |
| `states.VALIDATING` | Count of those records with `state == VALIDATING` |
| `states.REJECTED` | Count of those records with `state == REJECTED` |
| `states.ADMITTED` | Count of those records with `state == ADMITTED` |
| `states.STAGED` | Count of those records with `state == STAGED` |
| `schema_version` | Version 1 of the derived `mission_admission` status response contract |

There is no separately persisted count file and no cached aggregate. Counts
are reconstructed on every invocation. The output zeros are dictionary
initializers only for supported categories; `mission_count` and every
nonzero value derive from loaded records.

## Live-state conclusion

The production `.zeus/runtime/stage1/missions` directory contains zero files.
Therefore:

```json
{
  "mission_count": 0,
  "schema_version": 1,
  "states": {
    "ADMITTED": 0,
    "REJECTED": 0,
    "STAGED": 0,
    "VALIDATING": 0
  }
}
```

is correct. OA-05 qualification used isolated repositories and intentionally
did not create a live mission. OA-05 acceptance advances the gate lifecycle;
it does not retroactively submit a Stage 1 candidate.

## Proven defect and correction

Digest corruption already failed closed. However, an attacker or faulty writer
could construct a structurally inconsistent record and recompute its digest.
Before correction, an unsupported state increased `mission_count` but matched
none of the four state buckets, allowing an internally inconsistent summary.
A filename that did not match `instance_id`, or a missing mission/WOP identity,
was likewise accepted by generic store loading.

`Stage1Store.load_path()` now requires:

- a valid canonical `state_digest`;
- non-empty string `instance_id`, `mission_id`, and `wop_id`;
- `instance_id` equal to the persisted filename stem; and
- exactly one supported state: `VALIDATING`, `REJECTED`, `ADMITTED`, or
  `STAGED`.

`Stage1Runtime.status()` additionally asserts that the sum of per-state counts
equals `mission_count`. Any violation raises `Stage1Error`; `scripts/zeus`
reports `FAIL` and exits 78.

## Isolated verification

Focused tests created one integrity-valid persisted record in each supported
state and proved:

- `mission_count == 4`;
- every state count equals one;
- the sum of state counts equals `mission_count`;
- a new runtime instance reconstructs identical counts after restart;
- an empty store deterministically reconstructs all zeros;
- digest corruption fails closed;
- a recomputed-digest unknown state fails closed;
- a recomputed-digest instance/path mismatch fails closed; and
- the `zeus status` CLI exits 78 for the corrupt override store.

Results:

```text
mission count focused suite: 7 PASS
Stage 1 runtime regression: 7 PASS
OA-05 staging and cumulative lifecycle: 12 PASS
```

Final independent validation:

| Validation | Result |
| --- | --- |
| Live `scripts/zeus status --json` | PASS — OA-01..OA-05 accepted, OA-06 pending, mission count 0 |
| Current OA-05 acceptance receipt integrity | PASS |
| Repository health | PASS — existing modified tree preserved |
| Repository–EOS synchronization | PASS |
| Work Registry validation | PASS — revision 85 |
| Integrated Engineering Platform validation | PASS |
| Independent `scripts/verify.sh` | PASS — 20 checks, 0 failures |
| Python compilation | PASS |
| `git diff --check` | PASS |

## Reconciliation

Reconciled:

- Stage 1 runtime architecture;
- Zeus CLI operator documentation;
- Project State `PROJ-0001@9.9`;
- Work Registry revision 85;
- Operational Alpha progress tracking;
- focused regression tests; and
- EOS repository projection.

## Final state

```text
OA-01..OA-05 = ACCEPTED
OA-06 = PENDING
OA-07..OA-30 = PENDING
Live mission count = 0
No live mission submission
No dispatch
No mission execution
No Operational Alpha declaration
No baseline freeze
```
