# P4 Cardinality Analysis

## Root cause

`bootstrap_boundary._validate_bootstrap_artifacts` and
`bootstrap_verification.verify_bootstrap_replay` counted every JSON file in
each P4 directory. The canonical lifecycle resolver also selected P4 with a
mission-only/global cardinality helper. Append-only historical Beta P4 and
downstream provider artifacts were therefore treated as competing current
state.

## Classification

| P4 chain | Mission | WOP | Classification |
|---|---|---|---|
| `BOOTSTRAP-4e6bd7f6-4489-5378-92c4-e3ea42782ec4` | `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` | `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001` | `CURRENT_CANONICAL` |
| `BOOTSTRAP-4a0217a3-bd32-5e90-a203-2a1ba681e1c1` | `MISSION-BETA-562F443E16C69401` | `WOP-BETA-562F443E16C69401` | `HISTORICAL` |

Counts are two P4 chains total, one current, one historical, with zero
legacy-compatibility and zero superseded chains. Each P4 class contains one
current and one historical artifact. Historical Beta dispatch and provider
session records are also valid historical records bound to the Beta chain and
are excluded from the lifecycle mission's current downstream check.

## Contract

Current selection requires exact Mission ID, WOP ID, submission ID, admission
ID, bootstrap ID, and verified receipt/digest provenance. Zero current
candidates, duplicate current candidates, invalid artifacts, identity/digest
contradictions, or downstream records bound to the current chain fail closed.
Mismatched valid historical records remain immutable and subordinate.
