# Operation Beta — Authority and Projection Model

Status: reconciled authority baseline; BETA-04 published active mission

## Zeus authority projection

The operator-facing authority projection resolves from the published
Operation Beta activation and current mission records. It validates the
activation binding, the five Operation Beta authority sources, and a
deterministic authority digest before reporting `authority_resolution: PASS`.
The projection reports `authority_framework: OPERATION_BETA`,
`active_operation: BETA`, and the current eligible Beta gate. Operational
Alpha and its historical manual-governance/EMM records remain available only
for explicit legacy reconciliation; they are not governing authority for the
current Beta path.

The current published mission is `BETA-04`. Its activation record is
`engineering/authority/operation-beta-beta04-activation.yaml`; the current
mission projection is `engineering/missions/operation-beta-current.yaml`.
This record does not grant capability implementation authority.

`BETA-04` is the Current Platform Mission. The receipt-backed canonical
lifecycle chain, not the planning catalog, owns Current Executable Mission.
The current value is `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`, bound to
`WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001` at
`READY_FOR_CONTROLLED_EXECUTION`. `CAGF-01` remains the Future Recommended
Mission and is deferred until lifecycle completion is independently qualified
and closed. Recommendation never substitutes for selection, admission, or
execution authority.

Current execution and future recommendation are distinct coordinates:

```text
CURRENT_EXECUTION != FUTURE_RECOMMENDATION
```

The lifecycle resolver owns mission/WOP identity, lifecycle state, work-start
flags, and lifecycle next action. The gate catalog owns only the deterministic
WOP/Operation capability crosswalk. Managed Codex status owns runtime liveness
and recovery disposition; its recovery action cannot replace the lifecycle
next action.

Repository baseline validity has one canonical resolver. It distinguishes
steady-state convergence from a receipt-backed publication transition without
changing authority ownership. During `COMMIT_CREATED`, the local publication
commit may be ahead of the equal remote/EOS starting baseline. During
`REMOTE_PUBLISHED`, the local and remote commit may be ahead of EOS. Both are
valid only when the authoritative Zeus transaction, current milestone receipt,
repository/runtime identity, mission/WOP, branch, ancestry, and transaction
integrity all match. Final `EOS_SYNCHRONIZED` restores full parity.

P3 admission validity remains provenance-based across those transitions. The
admission receipt is immutable; the current authorized transition is validated
separately for the same mission/WOP. Arbitrary divergence and receipt-less or
contradictory state fail closed and cannot be promoted by ancestry alone.

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
