# Mission Activation Architecture Inventory

Date: 2026-07-28

Status: Implementation inventory complete; implementation not yet started

## Observed Bootstrap State

- Repository: `homelab` at `/data/engineering/repositories/homelab`
- Branch: `main`
- Bootstrap implementation commits: `3b3d5c6`, `c3bcc2e`
- Upstream relation: local branch is two commits ahead of `origin/main`
- Mission Contract candidate: `MC-VALIDATION-ZEUS-PUBLICATION-001`
- Candidate lifecycle: `candidate`
- Resolver result: `NO_AUTHORIZED_WORK`
- Active Mission Contract count: zero
- Work Registry validation: pass
- EOS synchronization validation: drift in `EOS-STATE.md` and
  `EOS-MANIFEST.md`
- Corrective bootstrap lifecycle required by the continuation request:
  `ACTIVE`

The working tree contains pre-existing classified candidate changes. They must
be preserved and may not be overwritten by broad restoration or cleanup.

## Existing Capability

The existing bootstrap commits provide:

- a Mission Contract schema and store;
- contract loading, validation, digesting, resolution, and lifecycle
  transitions;
- WOP, repository, branch, baseline, role, approval, and dirty-tree checks;
- zero/one/multiple active-contract resolution;
- `engctl mission contract` routing;
- a resolver-backed `engctl resume` authority summary; and
- a resolver-backed execution snapshot special case.

## Architectural Gaps

The existing implementation does not provide:

1. An authoritative admission decision that returns `ADMIT` or `DENY` with
   stable reason codes.
2. Complete eligibility qualification for mission, WOP, repository, baseline,
   roles, approvals, dependencies, and scope.
3. A durable activation request with request identity, expected lifecycle,
   approval evidence, and idempotency key.
4. Approval verification independent from the mutable contract lifecycle.
5. A single activation service coordinating all canonical records.
6. An atomic multi-file activation transaction.
7. Pre-commit conflict and active-contract cardinality enforcement.
8. Durable transaction intent, completion, failure, and rollback evidence.
9. Recovery of an interrupted transaction.
10. Registry transition and binding reconciliation.
11. Project State activation projection and reconciliation.
12. EOS synchronization as a required activation outcome.
13. A shared authority result consumed identically by `engctl resume` and
    execution snapshots.
14. Regression coverage for each admission denial, duplicate/conflicting
    activation, rollback, interruption, invalid lifecycle, and terminal
    lifecycle enforcement.

## Implementation Inventory

### Admission

- `AdmissionDecision` result with deterministic check ordering and reason
  codes.
- Mission eligibility and lifecycle checks.
- WOP locator, digest, identity, lifecycle, work-item binding, repository,
  branch, and baseline checks.
- Repository identity, root, remote, branch, and HEAD checks.
- Role completeness and execution-agent/self-authorizer separation.
- Attributable activation approval record validation.
- Registry existence, lifecycle, mission/WOP binding, dependency, and scope
  checks.
- Dirty-tree policy and classified-scope validation.

### Activation

- Versioned activation-request schema and durable request records.
- Admission-before-activation pipeline.
- Expected-state compare-and-swap behavior.
- Repository lock and unique active-contract precondition.
- Atomic writes for the contract, Work Registry, Project State projection,
  and activation evidence.
- Transaction journal with before-images, intended digests, phase markers,
  rollback evidence, and idempotent recovery.
- Duplicate request replay and conflicting request rejection.
- Post-write reconciliation and resolver verification.
- EOS synchronization and validation before transaction completion.

### Operational Integration

- Work Registry transition from `ready` to `active` with attributable history.
- Project State activation projection naming the operational mission and
  Mission Contract.
- EOS regenerated only from reconciled repository sources.
- `engctl resume` and execution snapshot consuming the same resolver output.
- Exactly one active Mission Contract for the repository boundary.

### Validation and Evidence

- Unit fixtures for every qualification and denial class.
- Fault injection after each transaction phase.
- Rollback and interrupted-journal recovery tests.
- Normal activation of
  `VALIDATION-AND-ZEUS-CANDIDATE-PUBLICATION-001`, stopping immediately after
  operational activation and reconciliation.
- Updated bootstrap completion report retaining lifecycle `ACTIVE` and
  recording publication as pending.

## Transaction Boundary

The repository records are the canonical activation transaction. EOS is a
deterministic projection and must synchronize successfully before the
transaction is marked complete. If repository reconciliation or EOS
synchronization fails, repository before-images are restored and EOS is
regenerated from the restored sources. A transaction is operational only when
its completion evidence exists and resolver, registry, Project State, and EOS
all reconcile.

## Publication Boundary

Activation validation does not authorize execution of the publication
mission. Push, merge, release, publication, controlled-document activation,
bootstrap closeout, and bootstrap authority revocation remain excluded.
