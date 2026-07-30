# Architecture Convergence Report

Review ID: `ENGINEERING-CONVERGENCE-REVIEW-001`  
Assessment date: 2026-07-30

## Finding

The repository is converging toward one architecture, but the cutover has not
occurred. The intended architecture is technically credible and reuses the
strongest existing implementations. The unresolved issue is authority
composition: multiple components can independently reconstruct or evaluate
parts of the same execution decision.

## Architecture generations present

### 1. Foundation EMP/EOS architecture

This generation established controlled documentation, the EMP Work Registry,
context/resume, WOP lifecycle, admission, dispatch, oversight, reconciliation,
EOS runtime, and engineering control surfaces. It remains foundational and
should not be replaced.

### 2. Operational authority and pre-Progressive PMCT

This generation added owner enrollment, signed authority publications,
Authority Resolution, legacy gate approval, next action, agent qualification,
and the external PMCT package. It proved important behaviors but coupled live
runtime to an external WOP tree and created lifecycle semantics that no longer
match current Progressive records.

### 3. Canonical Progressive Operational Alpha

This generation introduced the repository-owned immutable WOP, locked OA
sequence, gate-specific verification, append-only decisions, runtime state,
and replay/supersedence protections. It is the current gate architecture.

### 4. Unified authority-pipeline architecture

The newest planning and working-tree implementation defines canonical
capabilities, policies, states, transitions, execution contracts, outcomes,
dependency rules, and repository constraints. It proposes a single resolved
execution context consumed by Progressive eligibility and EWI. This is the
correct convergence target, but publication and end-to-end integration remain
incomplete.

## Competing approaches

| Concern | Current approaches | Decision |
|---|---|---|
| Mission identity | Controlled Mission Contracts and execution mission YAML | Controlled Mission Contract is authoritative; execution representation becomes projection |
| Generic authority | Authority Graph, WOP compatibility state, ARS bundle, Controlled Mission Authority, Authorization Bundle | ARS owns the canonical resolved execution context |
| Progressive eligibility | PMA reconstructs upstream authority and gate facts | PMA accepts verified resolved context and only narrows |
| Terminal allow/deny | Compatibility evaluator, PMA, admission, EWI may appear decision-capable | EWI emits the one terminal initiation decision; upstream layers emit typed narrower decisions |
| Gate lifecycle | Legacy GateApprovalService and Progressive Gate Service | Progressive service owns current OA lifecycle |
| State | Repository, EOS, WOP, registry, runtime, progress prose | Each fact has one owner; all other copies are validated projections |
| Repository policy | Fixed `HEAD == origin/main` and newer phase-specific proposal | Preserve fail-closed current rule until phase-specific policy is adopted and qualified |

## Recommended canonical architecture

```text
Operator-approved intent
        |
        v
Exactly one Mission Contract
        |
        +-------------------------+
        |                         |
        v                         v
Immutable WOP + receipt      Owner publications
        |
        v
Accepted Admission Record
        |
        +----------- repository identity/freshness
        |                         |
        v                         v
Authority Resolution Service -> Resolved Execution Authority Context
                                      |
                                      v
                   Progressive Mission Authority (narrow only)
                                      |
                                      v
                   Engineering Work Initiation terminal decision
                                      |
                     +----------------+----------------+
                     |                                 |
                   deny                    supervised dispatch/execute
                                                       |
                                      typed effect/evidence receipts
                                                       |
                              qualification and reconciliation
                                                       |
                                      repository owners + EENS projection
```

### Ownership rules

- Mission Contract owner owns mission intent, identity, scope, and
  dependencies.
- WOP Service owns immutable WOP publication receipts.
- Admission Controller owns admission outcome only.
- Authority publication owners own signed owner facts.
- ARS owns generic resolution and the resolved-context digest.
- PMA owns Progressive-specific gate eligibility only.
- EWI owns the terminal initiation decision.
- Dispatcher and executor may act only on a current EWI allow bound to the same
  resolved-context digest.
- Evidence, qualification, reconciliation, and EENS records prove outcomes;
  they cannot manufacture prior authority.

## Canonical subsystem decisions

| Subsystem | Canonical implementation |
|---|---|
| Management state | EMP Work Registry |
| Controlled current project/phase | PROJ-0001 and PHASE-0001 within their scopes |
| Mission contract | `engineering/mission-contracts/contracts/` and EOS resolver |
| Work package | `scripts/lib/wop/contract.py` and repository immutable WOP |
| Authority publication | EMP owner enrollment/publication/resolution modules |
| Resolved authority | Evolve current authority-resolution bundle; no third schema |
| Progressive gates | `progressive_gate.py` and canonical WOP runtime |
| Initiation | EOS Engineering Execution Interface |
| Admission | WOP admission record consumed by mission admission |
| Execution | Supervised dispatcher, production agent, mission execution runtime |
| Evidence/qualification | EMP evidence qualification and execution oversight |
| Synchronization | Repository-to-EOS one-way projection |
| Notifications | EENS |

## Unresolved architectural decisions

1. Exact schema and lifecycle of the resolved execution context.
2. Producer, selector, expiry, revocation, and supersedence rules for the
   Authorization Bundle during migration.
3. Field mapping and retirement/projection rules for execution mission YAML.
4. One authoritative owner for each lifecycle and status fact.
5. Phase-specific Git cleanliness and authenticated remote-freshness policy.
6. Current mission applicability rules for authority publication generations.
7. Receipt-type schemas and explicit cross-type rejection.
8. Whether the narrowed standalone PMCT remains an installed operational tool.

## Documentation convergence

### Authoritative

- Approved/Active controlled documents in `docs/`, within their metadata scope
- DOC-0001 for controlled-document discovery
- PROJ-0001 for project resume and declared current project state
- PHASE-0001 for the bounded Operational Alpha phase
- Work Registry for EMP coordination facts
- Canonical Progressive WOP and its accepted runtime receipts for gate state

### Reference

- `engineering/operations/`
- `engineering/docs/cli/`
- current engineering architecture declarations and explanatory architecture
  documents
- service READMEs

### Historical

- completed EWOs, completion reports, evidence packages, and milestones
- superseded P2 assessments/corrections
- external WOP evidence
- prior publication evidence and frozen manifests after supersedence

### Duplicate or transitional

- legacy PMCT/gate approval documentation
- execution mission YAML as an independent contract
- repeated current-state prose across progress and evidence reports

### Pending reconciliation

- untracked architecture declarations and controlled revisions
- DOC-0001 semantic profile discrepancy
- controlled adoption of operational architecture records
- PU-01B/PU-01C publication sequence

## Convergence acceptance criteria

Architecture can be called converged when:

1. every execution attempt resolves exactly one Mission Contract;
2. exactly one WOP, publication receipt, and accepted Admission Record bind to
   it;
3. ARS is the only producer of generic resolved authority;
4. PMA consumes that exact context and cannot broaden it;
5. EWI is the only terminal allow producer;
6. legacy and compatibility paths cannot authorize;
7. repository and remote-freshness policy are phase-appropriate and
   deterministic;
8. tests use isolated fixtures and do not consume live OA state;
9. external duplicate trees have zero consumers;
10. the complete baseline reproduces from a clean checkout.

## Architecture recommendation

Adopt the existing authority-pipeline specification as the implementation
direction after a bounded architecture decision review. Do not create a new
framework or rewrite the platform. The convergence mission should be an
integration-and-retirement exercise centered on OA-06.

