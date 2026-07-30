# Authority Integration Roadmap, Risks, and Verification

Mission: `ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001`

Status: implementation plan for operator review. All gates below require
separate execution authorization.

## 1. Conflict and issue register

| Issue / root cause | Target and immediate correction | Migration / validation / rollback | Dependencies and completion evidence | OA-06 |
|---|---|---|---|---|
| Missing Authorization Bundle producer, selector, lifecycle | Assign temporary producer/owner; define one indexed active ARS-input manifest; fail on none/multiple | Migrate callers from env; validate create/select/supersede/revoke/expiry; rollback keeps old path deny-only | Gate B/C; schema, lifecycle tests, producer ownership record | blocker |
| Missing current graph/state/WOP receipt set | Do not manufacture fixtures; legitimate owners publish WOP receipt and owner facts; EWI observations replace state | Compatibility artifacts remain fixtures; validate provenance and exact WOP binding; rollback disables new generation | WOP Service and publication owners; signed/digest-bound evidence | blocker while old EWI is production |
| No ARS–PMA–EWI bridge | ARS emits REAC; PMA consumes it; EWI orchestrates both | Dual-run comparison is observational only; cut over after zero unexplained divergence; rollback returns fail-closed, never old allow | Gates B–F; cumulative decision matrix and trace | blocker |
| Multiple Mission Contract stores | designate `engineering/mission-contracts/contracts` sole authority | map execution-mission fields; generate read-only projection or retire; preserve historical files | consumer inventory, ambiguity tests, no direct writers | blocker |
| Unclear precedence | conjunctive narrowing; revocation/supersedence and mismatch dominate; ARS sole generic resolver | encode terminal-state precedence and all-diagnostic reporting | approved contract and negative matrix | blocker |
| Hard-coded package/admission discovery | immutable package index by WOP ID+digest and exactly-one active Admission Record | support old fixed path read-only during migration; mismatch/ambiguity tests | Gate C/E; index rebuild test | blocker if selected record cannot be proven |
| Stale P2-014 publication | preserve history; legitimately publish/activate mission-scoped current owner facts | append-only new generation; rollback points only to previously valid applicable generation, otherwise none | canonical synchronized baseline and owners; activation evidence | blocker |
| `HEAD`/upstream ambiguity | phase-specific policy; current Progressive equality remains | add remote freshness observation; no policy relaxation in migration | policy decision, tests with stale tracking ref | blocker at current boundary |
| Tests coupled to live OA gate | isolated repositories and explicit OA state/observations | remove live defaults from unit tests; retain production integration test read-only | Gate F; repeatability at OA-02/OA-06 fixtures | blocker |
| Insufficient preflight diagnostics | read-only, non-ADR preflight with full missing/stale/owner report | keep EWI fail-closed; snapshot diagnostic schema | Gate E/F; golden negative outputs | blocker for safe qualification |
| Multiple trees/derived drift | canonical-root enforcement, freeze legacy OA tree, one-way projections | manifest/reconcile/quarantine; rollback restores read-only consumer routing, not independent editing | Gates A/D; writer/consumer scans and EOS rebuild | blocker |
| Runtime pointer is integrity-valid but applicability-stale | selector must include mission/work/WOP/repository generation and freshness | reject inapplicable generation instead of accepting “active” globally | ARS selector negative tests | blocker |
| Receipt type confusion | six type-specific schemas and explicit non-substitutability | inventory historical types; adapters only for verified same semantics | Gate C; cross-type rejection suite | blocker |

## 2. Gated roadmap

### Gate A — Canonical repository and state inventory

Entry: planning approval. Actions: capture all roots, writers, consumers,
runtime paths, Git/worktree identities, manifests, and divergence; freeze
external Homelab editing without deletion. Exit: signed-off inventory has no
unclassified path and records recovery needs. Rollback: restore service access
only to its prior mode; keep evidence. OA-06 remains blocked.

### Gate B — Authority topology decision

Approve this layered model; assign named role owners/producers; designate the
Mission Contract store, ARS/REAC, precedence, and compatibility sunset.
Exit evidence: decision record and responsibility/RACI mapping. No authority
publication is implied by architecture approval.

### Gate C — Contract and schema reconciliation

Version REAC, WOP publication, activation, admission, gate acceptance,
execution, reconciliation, package-index, and Initiation Decision schemas.
Specify discovery, signatures/digests, freshness, expiry, revocation,
supersedence, retention, and error precedence. Exit: schema tests and migration
mapping; every field has one owner.

### Gate D — Repository consolidation

Quarantine/freeze duplicate trees; redirect consumers; create one-way,
manifest-bound projections; rebuild EOS; reconcile runtime/project/registry
state without importing copied authority. Exit: one canonical writer root,
zero unexplained divergence, restore drill, and duplicate-tree scan passing.

### Gate E — Authority integration implementation

Implement mission/WOP/admission indices, current owner publications, ARS REAC,
PMA adapter, and EWI orchestrator. Compatibility runs shadow-only. Exit: a
single production allow path; none/ambiguous/stale inputs deny before effects.

### Gate F — Test isolation and qualification

Use temporary Git repositories and deterministic clocks/keys/state. Test every
layer alone and the cumulative path, including cross-store ambiguity,
cross-receipt substitution, stale remote refs, revocation during execution,
partial publication, replay, crash recovery, and concurrent selection. Exit:
all focused/integrated tests pass repeatedly independent of live OA state.

### Gate G — EWI qualification

Run read-only preflight first, then explicitly non-dispatching EWI
qualification. Verify exact mission, contract, WOP, publication receipt,
Admission Record, REAC, principal, repository, remote freshness, capability,
gate, and runtime binding. Preserve evidence; ensure no dispatch or gate
transition. Exit: one deterministic qualifying result and reproducible
negative results.

### Gate H — OA-06 resume authorization

An operator reviews Gates A–G and issues a separate OA-06 resume handoff if
appropriate. This plan cannot satisfy Gate H and does not resume OA-06.

## 3. Verification strategy

Contract tests validate schemas, canonicalization, unknown fields, ownership,
signatures, digests, time boundaries, lifecycle, and migration mappings.
Resolver tests cover zero/one/many candidates and every precedence class.
Repository tests cover wrong root/remote, multiple worktrees, dirty policies,
divergence, stale tracking refs, projection edits, symlink escapes, and
external duplicates. Receipt tests attempt every cross-type substitution.

Integration tests assert:

1. identical inputs always yield the same decision/digest;
2. no subsystem besides EWI emits the terminal initiation allow;
3. PMA can only narrow the REAC;
4. compatibility divergence cannot affect enforcement;
5. execution refuses a changed/expired/revoked REAC;
6. interruption before an atomic pointer/receipt write leaves no partial
   current state;
7. replay is idempotent and conflicting replay fails;
8. reconciliation never accepts an edited projection as authored truth.

Qualification evidence must include command/version, fixture or repository
identity, input and output digests, clock, remote-freshness evidence, test
counts, negative matrix, and proof that no dispatch/protected effect occurred.

## 4. Risk register

| Risk | Likelihood / impact | Control | Residual acceptance |
|---|---|---|---|
| Architecture document is mistaken for authority | medium / critical | banner, schema/type separation, EWI ignores planning path | zero use in resolvers |
| Migration temporarily creates two allow paths | high / critical | shadow-only compatibility, feature cutover invariant, one terminal emitter | no unexplained divergence |
| Legitimate historical evidence lost during consolidation | medium / high | hash inventory, read-only quarantine, restore drill, separate retirement approval | owner review |
| Runtime facts copied into Git become stale authority | medium / high | typed receipts/pointers, freshness/expiry, owner publications | bounded lifetime |
| Stale `origin/main` falsely appears synchronized | high / high | authenticated remote observation with timestamp/max age | phase policy met |
| PMA reintroduces generic resolution | medium / high | API accepts REAC; architectural dependency tests | code ownership review |
| Receipt substitution | medium / critical | distinct schemas/type IDs and negative suite | zero accepted substitutions |
| Live OA state contaminates tests | high / medium | isolated fixtures and explicit observations | repeatable suite |
| Hidden clone remains writable | medium / high | writer/process/config scans and canonical path enforcement | declared scan boundary |
| Revocation races with execution | medium / critical | boundary revalidation, short REAC expiry, durable checkpoints | fail closed/reconcile |

## 5. OA-06 unblock criteria

OA-06 remains blocked until all are true:

- Gates A–G have accepted completion evidence;
- the canonical root is the sole maintained Homelab tree and the external OA
  WOP tree has no writer/consumer;
- repository/registry/project/EOS/Progressive state have no unexplained drift;
- exactly one applicable active Mission Contract resolves from the canonical
  store and binds the Progressive WOP;
- exactly one immutable WOP, valid WOP publication receipt, and accepted
  Admission Record resolve by ID and digest;
- an applicable, fresh authority publication generation exists through its
  legitimate owners; the P2-014 generation is not reused;
- ARS emits one valid REAC bound to current mission, WOP, admission, principal,
  capabilities, repository, and requested OA-06 effect;
- PMA returns eligible for OA-06 while consuming that exact REAC;
- the current Progressive `HEAD == origin/main` boundary passes using fresh
  remote evidence, with a clean/allowed working tree and qualified baseline;
- compatibility and legacy locators cannot independently authorize;
- isolated and cumulative authority tests pass, including all ambiguity,
  revocation, stale, and receipt-substitution negatives;
- non-dispatching EWI qualification yields one deterministic allow and durable
  diagnostics, with no protected effect;
- an operator issues a new, separate OA-06 resume authorization.

OA-07 remains ineligible.

## 6. Nonblocking backlog

After the minimum unblock path: generic topology registry; automatic producer
ownership linting; package-index discovery across mission types; richer
structured diagnostics; automated receipt-type validator; immutable
reconciliation manifests; continuous duplicate-tree detection; projection
access telemetry; and automatic authenticated remote-ref freshness service.
