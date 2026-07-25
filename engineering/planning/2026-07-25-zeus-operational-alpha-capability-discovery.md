# Zeus Operational Alpha Capability Discovery

Date: 2026-07-25  
Status: Planning evidence — no implementation authority  
Baseline: `e0d024a1e40a68b57422193c089ae560a495feed`  
Authority: PHASE-0001 and PROJ-0001

## Scope and method

This report inventories repository-controlled capabilities and interfaces that
Zeus may reuse. It is based on controlled records, `scripts/engctl`, EOS and EMP
libraries, registry state, tests, and the imported EENS source. It does not
assert that an external service is currently available unless an authoritative
record says so, and it does not authorize implementation.

## Zeus Capability Inventory

| Domain | Existing reusable capability | Principal source | Readiness | Gap for Zeus |
| --- | --- | --- | --- | --- |
| Repository control | Root discovery, branch/commit/status, integrity, upstream, publication readiness | `scripts/lib/eos/repository.sh`, `operations.sh` | Reusable | Atomic multi-repository transaction and remote divergence policy |
| Controlled documents | Metadata, lifecycle and relationship validation; deterministic index discovery | `scripts/validate_controlled_documents.py`, DOC-0001, SPEC-0001 | Reusable | Authority-parent cardinality and complete DAG validation |
| Project authority | Current mission, phase, next action and historical boundary | PHASE-0001, PROJ-0001 | Reusable | Machine-readable mission contract separate from narrative fields |
| Work registry | YAML schema, CRUD, transitions, queues, dependency/deferral/milestone management, context | EMP-0001, SPEC-0006, SERVICE-0002, `scripts/lib/emp` | Reusable as projection | Must never originate authority; source freshness and authority-parent checks missing |
| Resume | Project/registry context, repository/checkpoint status, conflict detection | SPEC-0004, STD-0004, `context.sh` | Reusable | Structured result API, complete authority-chain display and stable error codes |
| Recovery | Evidence identity, preservation, imaging, verification, restoration prohibition | PROC-0003 | Reusable procedure | Automated recovery remains separately authorized |
| Checkpoints | Append-only capture, active pointer, applicability, commit/root identity, retention | `checkpoint.sh`, EOS-0003 | Reusable where EOS state exists | Host baseline currently lacks required EOS state/checkpoint records |
| Work Initiation | Repository qualification, wrapper gate, mission/resume summary, integrity tests | PROC-0001, `platform.sh`, `codex.sh` | Partially reusable | One deterministic authorization decision object; authority DAG validation |
| Evidence qualification | Evidence packages, Completion Reports, PROC-0006 nine-stage qualification | PROC-0006, STD-0003, TPL-0002 | Reusable workflow | Machine-readable finding/decision contracts and independent verifier identity |
| Governance stabilization | Twelve-stage reconciliation, external qualification and decision routing | PROC-0007 | Reusable conceptually | Current authority relationship model is cyclic and multi-parent |
| Publication | Six-stage controlled publication and verification | PROC-0005 | Reusable workflow | Authorized effect manifest and idempotent publication receipt |
| Handoff construction | Authority-kernel intake and deterministic construction | PROC-0004, TPL-0001, SPEC-0008 | Reusable | Typed authority-parent field and frozen resolved manifest |
| Command supervision | Governed Codex wrapper, timeout, lifecycle notifications | `codex.sh` | Reusable | Durable execution lease, revocation and crash recovery |
| Event model | Immutable validated events, canonical JSON, SHA-256 fingerprint, idempotency key | `services/eens/src/eens/events.py` | Reusable | Producer identity/authentication and schema/version registry |
| Event persistence | SQLite WAL, append-only sequence, idempotent acceptance, replay | `store.py` | Reusable | Authorization ledger is not implemented and must not be inferred from event storage |
| Event consumption | Named durable consumer checkpoints, ordered pending/acknowledge | `consumer.py` | Reusable | Delivery obligation/attempt records and dead-letter policy |
| Lifecycle production | Handoff started/completed/failed events and wrapped-command events | `lifecycle.py`, `runtime.py` | Reusable as evidence | Events cannot activate or alter authority |
| Notification | ntfy HTTP adapter and continuous systemd user service | `notify.py`, `systemd/eens-notify.service` | Qualified EENS foundation | Provider registry, authentication, advanced routing and full HNS remain deferred |
| Security | Wrapper-bypass detection, protected SSH-agent use, value-blind notification configuration | EOS scripts and EENS configuration | Partial | Principal identity, signed grants, least privilege, secrets isolation, audit integrity |

## Interface Inventory

### Command interfaces

- `engctl resume|status|validate|platform|repository|eos|checkpoint|context`
- `engctl registry|portfolio|project|queue|milestone|dependency|defer`
- `engctl codex --ewo ...` and the wrapper marker enforced at initiation
- EENS CLI entry point `python -m eens`, including server, lifecycle, replay,
  notify and continuous-service operations

### File and data interfaces

- Controlled Markdown/YAML frontmatter under `docs/`
- `engineering/registry/work-registry.yaml` and its declarative schema
- EOS state, runtime inventory, operational state and append-only checkpoints
- Git commit, branch, tag, remote and working-tree state
- EENS SQLite event store and separate SQLite consumer-checkpoint store
- EENS environment configuration and systemd user-unit contract

### Logical interfaces

- Project State supplies current mission, phase and next approved action.
- Controlled authority records supply permission and bounds.
- EMP consumes source references and supplies non-authoritative coordination.
- Resume consumes Project State, registry, EOS/checkpoint and Git observations.
- Work Initiation consumes resolved authority and fails closed.
- EENS accepts engineering lifecycle facts and owns accepted event/delivery
  state, not the authority behind those facts.
- Qualification consumes evidence and returns findings/recommendations; a
  separate authority makes disposition.

## Security and execution boundaries

1. Repository or runtime state cannot create Governance Authority.
2. Registry transitions cannot activate controlled work.
3. Resume output is a derived view and cannot authorize its recommendation.
4. EENS events prove recorded lifecycle facts, not authorization.
5. An implementation agent may consume only a frozen bounded work package.
6. Secrets must remain outside records, command output, events and logs.
7. Production mutation, deployment, remote approval and autonomous scheduling
   are absent from Mission C authority.
8. Git divergence, missing EOS state, unresolved identity, stale authority or
   graph disagreement are fail-closed conditions.

## External dependencies

| Dependency | Use | Boundary/risk |
| --- | --- | --- |
| Git and repository remotes | History, identity and publication evidence | Network/upstream availability; commits do not activate authority |
| Python 3 and PyYAML | Registry, validators and EENS | Version pinning and environment reproducibility |
| Bash and standard Unix tools | EOS/EMP controller | Shell environment and command availability |
| SQLite | EENS events and checkpoints | Local durability, locking, backup and corruption recovery |
| systemd user services | Continuous EENS consumer | Host-specific paths, user-session availability and supervision |
| ntfy HTTP service | Notification delivery | External availability, confidentiality and authentication |
| SSH agent/keys | Repository remote access | Principal identity and protected key handling |
| `/data/engineering/eos` | EOS state and checkpoints | Required base records are absent on the observed host |
| LOpi deployment | Qualified EENS operation | Repository source and deployed state are distinct |

## Assumptions requiring Mission D confirmation

- One repository commit can be treated as an immutable publication receipt, but
  not as approval.
- A work package will be a bounded child of exactly one mission authority.
- Identity, signature, revocation and concurrency contracts will be selected
  before autonomous execution.
- Existing EMP and EENS APIs remain consumers and evidence systems rather than
  sources of authority.
- EOS host-state prerequisites will be restored or explicitly waived through
  separate authority before relying on checkpoint/persistence gates.

## Capability Dependency Graph

```text
Charter authority
  -> governance decision
    -> frozen governance baseline
      -> mission authority
        -> bounded work package
          -> Work Initiation
            -> execution supervisor
              -> repository transaction
              -> evidence capture
                -> qualification
                  -> external disposition

Project State + Work Registry + EOS/Checkpoint + Git
  -> reconciliation
    -> resume (derived, fail-closed)
      -> Work Initiation

Execution lifecycle facts
  -> EENS append-only store
    -> durable consumers
      -> ntfy presentation
```

## Missing capabilities

Critical prerequisites:

1. Typed single-parent authority graph and validator.
2. Frozen machine-readable work-package contract.
3. Principal identity, signature, delegation and revocation model.
4. Idempotent authorized-effect manifest and publication receipt.
5. Durable execution lease with concurrency and crash-recovery semantics.
6. Structured Work Initiation decision and stable denial codes.
7. Evidence/qualification/disposition separation enforced by schema.
8. Complete EOS state/checkpoint baseline on the execution host.

Later capabilities:

- authorization ledger and audit query;
- provider-neutral notifications and delivery-attempt evidence;
- scheduling, dashboards, metrics and remote approval;
- multi-host coordination and policy distribution.

## Implementation Readiness Assessment

**Disposition: CONDITIONALLY READY FOR BOUNDED FOUNDATION WORK.**

The repository already supplies strong repository, registry, resume,
publication, evidence, event and notification primitives. It is not ready for
autonomous execution because authority is not yet represented as a distinct
single-parent DAG, identity/revocation are undefined, work packages are not
frozen machine contracts, and host EOS persistence prerequisites are missing.

The first implementation must therefore be an offline authority-graph model
and validator. It must not begin execution orchestration or production runtime.

## Deterministic implementation sequence

1. Define typed authority-node and authority-parent schemas.
2. Implement an offline authority DAG validator with fixtures only.
3. Define immutable work-package and resolved-manifest schemas.
4. Define identity, signature, delegation, expiry and revocation contracts.
5. Define authorized-effect manifest and publication-receipt contracts.
6. Extend Work Initiation to emit a structured allow/deny decision.
7. Implement an execution lease and local dry-run supervisor.
8. Integrate evidence capture and independent qualification.
9. Integrate EENS as an event sink without authority semantics.
10. Qualify recovery, concurrency, revocation and failure behavior.
11. Only after separate approval, evaluate production deployment.

