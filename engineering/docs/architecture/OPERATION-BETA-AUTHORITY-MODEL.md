# Operation Beta — Authority and Projection Model

Status: reconciled planning baseline; Beta-03G invariant governance candidate

Controller governance is normative in `ENGINEERING-PLATFORM-INVARIANTS.md` and
`ZEUS-CONTROLLER-GOVERNANCE.md`. These documents constrain projections and
ownership without creating a second authority.

Operation Beta preserves the Operational Alpha source ownership model. Beta adds generators and execution services as consumers or projections; it does not create a second mission, capability, lifecycle, or governance authority.

| Fact or artifact | Canonical owner | Beta consumers/projections |
| --- | --- | --- |
| Mission objectives, order, dependencies, readiness inputs | Mission Knowledge Model | Beta roadmap and controllers |
| Capability identity and state | Capability Registry | Capability and mission projections |
| Source revisions, bindings, and drift | EMM | Assessment and reconciliation |
| Qualification contract and gate semantics | PMCT / controlled gate authority | Mission contracts and validators |
| Synchronized platform state | EOS | ZDCL, EPE, and platform validation |
| Authorization and publication disposition | Engineering Governance | ZDCL and publication integration |
| Planning and orchestration | EMP | Mission selection and operational views |
| Event delivery | EENS | Session and execution lifecycle events |
| Execution mechanics and enforcement | Zeus / qualified agents | ZDCL and EPE runtime |

Derived artifacts must carry source identity, source revision or digest, generator identity, generation time, and qualification status. A source conflict, missing owner, stale digest, cycle, or unverifiable projection fails closed. Generation never silently repairs authority.

## Ownership and promotion rules

The canonical owner remains singular for each authority domain. Mission
Knowledge Model owns mission facts; Capability Registry owns capability facts;
EMM owns bindings and drift; PMCT and controlled gate authority own
qualification semantics; Engineering Governance owns approval and publication;
EOS owns synchronized operational state. ZDCL, CAGF, EPE, EMP, EENS, and Zeus
consume or project these records within their existing boundaries.

Generated artifacts are disposable projections and must identify their source,
revision or digest, generator version, and qualification result. Generation
cannot repair or override a source conflict. Beta promotion requires source
validation, independent qualification, reconciliation, governed publication,
canonical merge, EOS synchronization, platform validation, and a completion
receipt. Rollback returns to the last qualified Beta checkpoint or Alpha
baseline without rewriting historical records.

Authority and mission dependency graphs must be acyclic. Runtime event and
monitoring feedback may exist, but cannot create an authority edge back into
the source that generated the event or projection.

## Future knowledge audit policy

Beta shall classify each significant artifact as normative, canonical, generated,
runtime state, projection, historical evidence, or planning. Classification
does not change ownership. CAGF candidates are limited to deterministic,
source-bound projections and indexes; canonical mission, capability, binding,
approval, publication, lifecycle, and EOS records remain manually controlled
sources until a separately authorized design changes that boundary.
