# P4-G3 Legacy Test Classification

`scripts/tests/test-zeus-p4-g3-runtime-discovery.py` targets historical
`MISSION-BETA-562F443E16C69401` and expects
`BEGIN_CONTROLLED_MISSION_WORK`. The current runtime returns
`OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION` because the record is a
completed/reconciled legacy execution and its native current action is an
operator review boundary, not a live execution action.

Classification: `HISTORICAL_ONLY` / `LEGACY_COMPATIBILITY_EXPECTATION`.

The test was reproduced and failed only on that stale action expectation. It
was not changed merely to make Wave 2 pass. Changing it would require a
separate controlled reconciliation of historical P4-G3 semantics. The Wave 2
aggregate explicitly prevents stopped, superseded, or reconciled sessions
from exposing current execution readiness.
