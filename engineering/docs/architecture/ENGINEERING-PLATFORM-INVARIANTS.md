# Engineering Platform Invariant Specification

Status: BETA-04 normative governance baseline
Authority: Engineering Platform Governance Framework
Production baseline: `OA-v1.0.0`
Development baseline: Operation Beta

## Scope

These invariants govern Zeus, EMP, ZDCL, CAGF, EPE, EOS, EENS, mission
contracts, runtime records, controllers, and future Engineering Platform
work. They constrain ownership and projections; they do not authorize a
capability or lifecycle change.

## Normative invariants

1. **Canonical state ownership.** Every runtime datum shall have exactly one authoritative owner. A controller shall never become an owner by caching or reconstructing state.
2. **Canonical resolver.** Every controller shall consume the canonical resolver for mission, admission, execution, lifecycle, readiness, queue, and next-action state. Controller-specific inference is prohibited.
3. **Projection purity.** Runtime objects execute, evidence records history, documentation specifies authority, and controllers project. No layer shall perform another layer's responsibility.
4. **Active-state projection.** Active views shall expose only active state. Cancelled, superseded, completed, and failed records shall be available only through history, archive, evidence, qualification, or completion views.
5. **Historical immutability.** Historical runtime and evidence records shall be append-only. Correction shall use explicit supersession and shall not mutate the historical record.
6. **Freshness before idempotency.** Repository, authority, contract, WOP, approval, and lifecycle freshness shall be verified before an existing admission or execution is reused.
7. **Production isolation.** Development state shall not modify `OA-v1.0.0` or production EOS. Promotion shall be explicit, qualified, and governed.
8. **Single runtime truth.** Human-readable and JSON output shall render the same resolved projection object. Formatting shall not perform a second resolution.
9. **Deterministic resolution.** Identical authoritative inputs shall produce identical mission, admission, execution, queue, lifecycle, and controller projections.
10. **Fail closed.** Missing authority, ambiguous ownership, multiple active records, unknown lineage, invalid synchronization, or conflicting state shall stop the affected action.
11. **Recommendation capture.** Every architectural recommendation shall have an explicit disposition: mandatory invariant, roadmap enhancement, implementation optimization, deferred recommendation, or rejected.
12. **Future knowledge audit.** Every significant architectural change shall update the Future Knowledge Audit with ownership, classification, source, lifecycle, and generation suitability.
13. **Runtime boundary separation.** Repository evidence may be mounted read-only; read-only projections shall remain functional without runtime writes, while mutation paths shall use only the explicitly configured writable runtime root and fail closed when unavailable.

## Runtime ownership

| Record or concern | Sole owner | Consumers |
| --- | --- | --- |
| Mission facts and readiness inputs | Mission Knowledge Model | EMP, Zeus, controllers |
| Capability identity and lifecycle | Capability Registry | Mission and platform projections |
| Source bindings and drift | EMM | Validation and reconciliation |
| Qualification semantics | PMCT / controlled gate authority | WOPs and validators |
| Synchronized platform state | EOS | Zeus, ZDCL, EPE, validation |
| Approval and publication authority | Engineering Governance | Admission and publication |
| Submission | EMP/Zeus submission authority | Queue and admission |
| Admission | Zeus admission authority | Execution |
| Execution | Zeus / qualified agent | Status and qualification |
| Evidence and history | Evidence record authority | Controllers and audit |
| Presentation | Canonical projection resolver | Human and JSON renderers |

## Self-audit contract

The platform self-audit shall verify the invariants without mutating canonical state. A failed invariant shall identify the authoritative owner, conflicting projection, and required reconciliation boundary.
