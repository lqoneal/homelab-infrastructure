# Dispatch / Session Artifact Classification

The durable runtime contained five dispatch-family artifacts and five
provider-session-family artifacts, all bound to historical
`MISSION-BETA-562F443E16C69401`. The target lifecycle mission had zero current
dispatch artifacts and zero current session artifacts before and after this
corrective.

| Class | Target mission | Other missions |
|---|---:|---:|
| Current canonical dispatch | 0 | 0 |
| Current canonical provider session | 0 | 0 |
| Historical/compatibility dispatch | 0 | 5 |
| Historical/compatibility provider session | 0 | 5 |

Other-mission records are preserved and excluded from target cardinality.
Target-mission orphan records remain a fail-closed condition.
