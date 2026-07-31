# Architecture Traceability Updates

Status: `PROPOSED INTEGRATION UPDATE — NON-AUTHORITATIVE`

| HF-009 trace boundary | Remediated execution evidence | Responsible contract |
|---|---|---|
| Decision/Authority → metadata | resolved identity, active owner, schema/revision, publication/qualification binding | `01`, `03`, `07` |
| Metadata → capability/interface | versioned request/response, correlation, input manifest, receipt/error | `02` |
| Metadata → generated artifact | topologically resolved manifest, generator/output digest, provenance, qualified publication | `04`, `07` |
| Source → synchronization target | idempotency key, dependency set, checkpoint, target digest, completion/discrepancy receipt | `06` |
| Version transition | source snapshot, mapping version, adoption bindings, successor/rollback/reconciliation receipts | `05`, `07` |
| Verification/qualification → gate/project state/closeout | sealed criteria/result and provenance-bearing status projection | `02`, `06`, `07` |

This adds executable evidence expectations to HF-009’s reference matrix. It does not modify the HF-005 gates or state transitions to which that matrix refers.
