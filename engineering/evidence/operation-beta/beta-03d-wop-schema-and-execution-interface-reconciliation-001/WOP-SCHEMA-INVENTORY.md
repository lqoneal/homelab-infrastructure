# WOP Schema Inventory

| Consumer | Authority used | Prior drift | Reconciled rule |
|---|---|---|---|
| Package/mission resolver | Mission contract and published package | semantic package identity was valid here | canonical semantic WOP ID |
| Submission/admission | `engineering/admission/wop-submission.schema.yaml` and `wop_admission.py` | UUID-only regex; date required | semantic or legacy UUID; optional ISO date |
| Mission admission | `mission_admission_runtime.py` | generated canonical binding was not accepted by execution validator | same submission validator |
| Execution `VALIDATE_WOP` | `mission_execution_runtime.py` | inherited UUID/date-only rules | shared admission validator |
| Controllers | Beta roadmap plus runtime records | waiting execution was not projected | read-only execution projection |

The offline immutable WorkPackage model retains its UUID identity rule for its
separate legacy contract and fixtures; it is not used to validate the
published Beta submission contract.
