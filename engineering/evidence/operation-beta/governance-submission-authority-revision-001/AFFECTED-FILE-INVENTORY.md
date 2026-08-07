# Affected-File Inventory and Classification

| Artifact | Classification | Disposition |
| --- | --- | --- |
| `scripts/lib/emp/stage1_runtime.py` | REVISE | Remove redundant authority gate; mark submission authority only. |
| `scripts/lib/emp/wop_schema.py` | REVISE/MIGRATE | Make governance authority legacy-compatible metadata. |
| `scripts/lib/emp/wop_validation.py` | REVISE | Preserve fail-closed identity/effect validation. |
| `engineering/authority/manual-governance-wop-authority-policy.yaml` | REVISE | Establish canonical submission invariants and field disposition. |
| `engineering/admission/*.schema.yaml` | REVISE | Submitter metadata optional; add invariant projection. |
| `engineering/docs/architecture/ZEUS-WOP-SUBMISSION-PROCEDURE.md` | REVISE | Canonical sequence and downstream boundary distinctions. |
| `engineering/docs/operations/ZEUS-*-MODE/LIFECYCLE*` | REVISE | Remove second-declaration requirement and separate authority layers. |
| `scripts/tests/test-zeus-development-mode-recovery.py` | REVISE | Positive and negative convergence coverage. |
| Existing historical evidence and completed mission records | HISTORICAL_EVIDENCE_ONLY | Not rewritten. |

No second authority or lifecycle engine was introduced.
