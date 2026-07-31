# Engineering Interface Contract Specification

Status: `PROPOSED LOGICAL EXECUTION CONTRACT — NON-AUTHORITATIVE`

All messages have `contract_version`, `correlation_id`, producer/consumer owner references, exact input manifest, output digest, and status. A receiver accepts only a compatible contract/schema version and records a receipt. Common failures are `NOT_FOUND`, `PRECONDITION_FAILED`, `INCOMPATIBLE_VERSION`, `INTEGRITY_FAILURE`, `RETRYABLE_DELIVERY_FAILURE`, and `QUALIFICATION_FAILED`.

| Interface | Responsibility; input → output | Preconditions → postconditions | Failure / ownership |
|---|---|---|---|
| Governance ↔ EMP | decision source → sealed planning applicability result | valid authority and compatible baseline → attributable planning receipt | reject invalid/missing source; Governance owns decision, EMP owns planning result |
| EMP ↔ Zeus | planning snapshot → selection/decision projection | sealed compatible snapshot → version-pinned response/receipt | reject mismatch; EMP owns snapshot, Zeus owns its decision facts |
| Zeus ↔ EOS | declared decision/event checkpoint → state projection | accepted event/manifest → idempotent checkpoint receipt | retry/replay target; Zeus owns source fact, EOS owns projection state |
| Zeus ↔ EENS | event emission → durable append receipt | sequence/digest valid → append-only event record | retry keyed by event identity; Zeus owns event source, EENS owns event store |
| Zeus ↔ Metadata Engine | resolution request → provenance-bearing resolved revision | exact/range request valid → single resolution receipt | structured resolution failure; source owner retains fact ownership |
| Metadata Engine ↔ Generator | source manifest → generated projection/provenance block | all inputs published/qualified/compatible → output digest | refuse or rebuild; metadata owners own inputs, generator owns execution/output process |
| Generator ↔ Qualification Engine | generation manifest/output → qualification result | reproducible output and criteria present → sealed result | fail blocks publication; generator owns output, qualifier owns result |
| Qualification Engine ↔ EOS | qualification result → qualified status projection | sealed applicable result → idempotent checkpoint | retry/replay target; qualifier owns result, EOS owns projection |

No interface writes a consumer’s response back into a producer’s authoritative record. A failed request emits an attributable receipt/event but does not manufacture a substitute fact.
