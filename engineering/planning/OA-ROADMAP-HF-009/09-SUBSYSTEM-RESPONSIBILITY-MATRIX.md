# Subsystem Responsibility Matrix

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

| Subsystem | Ownership / inputs → outputs | Direction, validation, failure behavior |
|---|---|---|
| Governance | owns decision and authority facts; decision → Authority Record | publishes outward; scope/lineage validation; successor correction on failure |
| EMP | owns planning/evaluation facts; authority/baseline → sealed planning snapshot | source-to-Zeus; applicability/digest; reconcile planning source |
| Zeus | owns its declared decision facts and consumes compatible metadata; inputs → read-only verification/decision projections | never becomes source owner of consumed facts; version negotiation; structured incompatibility |
| EOS | owns projection-state records; source checkpoints → state view | source-to-EOS; checkpoint/freshness; replay target |
| EENS | owns durable event-store records; event inputs → event stream | append-only; sequence/digest; retry/recover store |
| Documentation Generator | owns generated output process, not source facts; manifests → documents | source-to-target; graph/schema; refuse or rebuild output |
| Metadata Engine | owns schema registry/validation process, not entity facts; candidates → validation/version bindings | contract validation; reject candidate, retain evidence |
| Qualification Engine | owns qualification process/results; evidence/criteria → Qualification | receipt/criteria; fail blocks publication/adoption |
| Engineering Information API | owns access/projection interface, not underlying facts; exact revisions → provenance-bearing responses | explicit negotiation; report unsupported/mismatch |

Each subsystem exposes a stable logical interface independent of implementation. Any transfer of a fact’s authority must be a separately authored, versioned relationship; operating a projection does not imply authority over its source.
