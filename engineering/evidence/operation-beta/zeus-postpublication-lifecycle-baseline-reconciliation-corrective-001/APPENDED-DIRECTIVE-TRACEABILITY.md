# Appended Directive Traceability

This file records the later amendments that were added after the main
postpublication corrective request and shows their incorporation.

| Directive | Ledger IDs | Implementation/document owner | Verification | Evidence |
|---|---|---|---|---|
| Zeus status failures must be investigated and classified | R022 | `scripts/zeus`, status tests, status contract documentation | status human/JSON commands and status-contract tests | `STATUS-CONTRACT-RECONCILIATION.md` |
| Live Projection First priority order | R025, R027, R028 | canonical resolver and reconciliation receipt | payload operand inspection, resolver/native commands | `BASELINE-PROVENANCE-MODEL.md`, `TEST-RESULTS.md` |
| Hardcoding is last-resort only | R026 | affected runtime and current controlled docs | static audit and conflict/fallback tests | `HARDCODING-AUDIT.md` |
| Current receipts derive operands from live projections | R027, R028 | `lifecycle_baseline_reconciliation.py` and verifier | independent digest/lineage reproduction | `ZEUS-NATIVE-VERIFICATION.md` |
| Distinguish provenance baseline from current published baseline | R018, R019, R027 | baseline lineage helper and reconciliation receipt | identical/ancestor, non-descendant, identity mismatch, forged-record tests | `BASELINE-PROVENANCE-MODEL.md`, `TEST-RESULTS.md` |
| Persist the rule across all lifecycle areas | R029 | current Zeus architecture/procedure documents | controlled-document and semantic validation | `CONTROLLED-DOCUMENT-RECONCILIATION.md` |
| Reconstruct every session instruction and perform omission audit | R030 | ledger, coverage matrix, audit | all-available-message review and zero-unmapped assertions | `FINAL-OMISSION-AUDIT.md` |

No appended directive was dropped because it was secondary. Each is either
implemented in the bounded corrective, classified as an explicit
compatibility/historical boundary, or linked to a verification artifact.

