# P3 Cardinality Analysis

## Defect

The P3 admission verifier and canonical resolver counted append-only artifact
files globally. The durable runtime contained two complete P3 sets: the
current lifecycle admission and a preserved historical `MISSION-BETA-*`
admission. Global `exactly one` rejected valid current state.

## Set inventory

| Classification | Admission | Mission | WOP | Result |
|---|---|---|---|---|
| CURRENT_CANONICAL | `ADMISSION-264c5bc0-4812-54d5-8f03-353d0cd0a899` | `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` | `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001` | selected |
| HISTORICAL | `ADMISSION-495901e4-4598-55a1-8dfd-38aadcbe92ff` | `MISSION-BETA-562F443E16C69401` | `WOP-BETA-562F443E16C69401` | preserved/excluded |

Each set has five P3 class artifacts (`packages`, `mission-contracts`,
`execution-authority`, `receipts`, and `journals`). Thus the runtime contains
`P3_ARTIFACT_SET_COUNT=2`, ten class files, one current canonical set, and one
historical set. There are no separately classified legacy or superseded sets
for this request.

## Correct contract

Resolution now scopes candidates to the exact admission identity and checks
mission, WOP, submission, provenance, and repository-bound transaction
identity. Historical, compatibility, or superseded records remain readable
evidence but cannot compete with current state. Zero current candidates and
more than one exact current candidate fail closed.

No historical file was deleted, rewritten, moved, suppressed, or invalidated.
