# Negative and Fail-Closed Qualification

| Case | Expected result | Result |
|---|---|---|
| Missing admission-request projection | `ADMISSION_REQUEST_PROJECTION_MISSING`, exit 78 | PASS |
| Tampered receipt digest | `CANONICAL_RECEIPT_DIGEST_MISMATCH`, exit 78 | Covered by resolver validation |
| Contradictory receipt next action | `CANONICAL_NEXT_ACTION_CONTRADICTION`, exit 78 | PASS |
| Multiple receipts for one mission | `MISSION_IDENTITY_AMBIGUOUS`, exit 78 | PASS |
| Identity-chain mismatch | `CANONICAL_IDENTITY_CHAIN_MISMATCH`, exit 78 | Covered by focused resolver tests |
| Unsupported lifecycle state | `CANONICAL_STATE_UNSUPPORTED`, exit 78 | Covered by resolver validation |
| Unrelated mission | `MISSION_NOT_FOUND` | PASS |

No fallback to historical execution, Stage 1 compatibility, or Operation Beta
recommendation is used to make a failed canonical read pass.
