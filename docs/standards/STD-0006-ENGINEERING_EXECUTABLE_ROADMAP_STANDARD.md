---
document_id: STD-0006
title: Engineering Executable Roadmap Standard
version: 1.2
status: Active
owner: Engineering Governance
created: 2026-08-09
last_updated: 2026-08-09
phase: Engineering System Convergence C02 Corrective
domain: Engineering Platform Planning and Execution
classification: Engineering Standard
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Homelab Operator
approval_reference: EXECUTABLE ROADMAP STANDARDIZATION AND ESC-ROADMAP-001 HARDENING directive
approval_date: 2026-08-09
persistence_status: Pending
source_of_truth: true
semantic_validation_profile: Standard
declared_deferrals: []
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: SPEC-0001
  - type: related_to
    target: STD-0003
  - type: related_to
    target: STD-0004
  - type: implemented_by
    target: PROC-0009
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0006
  - type: related_to
    target: PROJ-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - roadmap
  - executable-planning
  - execution-contract
  - deterministic-resume
  - qualification
---

# Engineering Executable Roadmap Standard

## Purpose

This standard establishes the mandatory Engineering Platform requirements for
classifying, constructing, evaluating, maintaining, and resuming engineering
roadmaps. It prevents structural validity, named gates, coherent dependencies,
or a known next gate from being mistaken for execution sufficiency.

An executable roadmap is an execution contract. A qualified engineer or agent
with complete loss of conversational context shall be able to determine from
repository- or EOS-controlled authoritative inputs exactly what to inspect,
how to inspect it safely, how to prove coverage, how to classify observations,
what artifacts and evidence to produce, how to determine the result, how review
and state transition work, how persistence is verified, and what action is
authorized next.

This standard defines requirements. PROC-0009 owns the repeatable evaluation
method. STD-0003 and PROC-0001 continue to own mission-specific WOP authority
and work initiation/execution. PROC-0006 continues to own Governance
qualification. A roadmap never creates execution authority merely by being
executable.

## Scope

This standard applies to all future Engineering Platform roadmaps and to any
existing roadmap proposed as executable, implementation-ready, or a durable
recovery/resume authority. It applies to machine-readable roadmap indexes,
gate definitions, shared playbooks, artifact contracts, results, state,
bindings, evidence, and human-readable projections.

It does not:

- authorize any gate, mission, WOP, implementation, publication, or state
  transition;
- replace controlled lifecycle, publication, qualification, recovery, or WOP
  authorities;
- require a planning-only roadmap to become executable; or
- permit a validator to approve content or make a Governance decision.

## Governing Records and Authority Boundaries

Apply this standard with CHAR-0001, POL-0001, STD-0000 through STD-0004,
SPEC-0001, PROC-0001, PROC-0005, PROC-0006, and PROC-0009.

Roadmap planning authority owns objectives, sequence, dependencies, gate
contracts, and roadmap state within its delegated scope. Mission-specific
authority, lifecycle approval, publication, acceptance, and implementation
authority remain with their existing controlled owners. An executable
qualification is evidence that the roadmap is sufficiently deterministic; it
is not evidence that its current gate has been authorized or executed.

## Roadmap Classes

Every roadmap shall declare exactly one class or a repository-controlled
equivalent with the same semantics.

| Class | Meaning | Executable qualification |
| --- | --- | --- |
| `PLANNING_ONLY` | Defines direction, objectives, sequencing, candidates, or dependencies but does not contain a complete execution contract. | Structurally valid is permitted; `EXECUTABLE=NO` is mandatory. |
| `EXECUTABLE` | Defines deterministic assessment or bounded engineering gates with complete playbooks, evidence, results, state transition, persistence, and resume behavior. | Every execution-significant criterion shall pass. |
| `IMPLEMENTATION` | An executable roadmap whose gates perform bounded implementation or migration under separate authority. | All `EXECUTABLE` requirements plus change, rollback, compatibility, and publication boundaries apply. |
| `RECOVERY_RESUME` | An executable roadmap or runbook sequence whose primary purpose is deterministic recovery, interruption handling, or context reconstruction. | All `EXECUTABLE` requirements plus recovery identity, precedence, replay, and non-mutation rules apply. |

A roadmap may describe future implementation while remaining `PLANNING_ONLY`.
Names, readiness labels, or a current gate shall not override the declared
class or evaluation result.

## Executable Qualification Principle

A roadmap qualifies as `EXECUTABLE` only when a qualified engineer or agent
with no conversational context can use only authoritative inputs referenced by
the roadmap to determine and safely perform the current gate, persist its
result, validate the state transition, prove cold resume, and identify the
next authorized action.

Two qualified evaluators using the same roadmap revision and the same system
state shall reach materially equivalent gate and overall results. Free-form
judgment may explain findings but shall not supply missing discovery,
classification, artifact, coverage, result, transition, or persistence rules.

## Requirements

### Structural Contract

The roadmap root shall provide a versioned identity, class, purpose, authority
model, repository identity, gate index, state locator, binding manifest,
evaluation authority, playbook catalog, schemas, and persisted evaluation
result. Every gate and dependency shall resolve uniquely. Roadmap order and
dependency order shall be deterministic.

Structural validity and execution sufficiency are separate results. A roadmap
can be structurally valid while not executable.

### Mixed-Generation and Provenance Contract

Roadmap revision does not retroactively rewrite a completed or current gate.
The roadmap index shall record explicit contract provenance for every gate:
immutable gate identity, roadmap order, lifecycle, validation schema, contract
generation, and standard applicability. Historical and activation-era gates
retain the schema and validation semantics applicable when they were created;
STD-0006 is prospective from the first declared prospective gate. A frozen
gate may be represented in a newer roadmap revision, but it shall not acquire
new required fields merely because a newer generic schema exists.

The canonical engineering queue remains `ESC-ROADMAP-001` with role `ACTIVE`
until a separately reviewed authority transition. Zeus staging is
`NOT_YET_ACTIVE` for queue ownership; it becomes authoritative only after it
exposes an equivalent durable queue contract, provenance, review, persistence,
and cold-resume behavior and the operator accepts the transfer.

Roadmap maintenance is pending-only: completed and current gate contracts,
results, evidence, and historical meaning are immutable. Historical records
are append-only and are never normalized, rewritten, or retrofitted. Maturity
gates and hardening requirements are prospective only. A gate's immutable
identity is separate from its numeric roadmap order, so a future maturity gate
may be inserted using a new identity and an unused order value without
renumbering existing gates. Dependencies and successor links are resolved by
identity and must advance order; pending contracts may evolve under a new
roadmap revision while active-contract defects are recorded and routed for
review rather than silently edited in place.

### Mandatory Gate Contract

Each executable gate shall define directly or by a resolvable shared contract:

- permanent gate identifier, title, gate type, lifecycle/status, purpose,
  problem statement, objective, and rationale;
- in-scope and out-of-scope work, dependencies, entry conditions, and
  authoritative inputs;
- exact discovery surfaces and inventory method;
- ordered assessment or execution procedure;
- safe or read-only operations and command classes where appropriate;
- prohibited operations and authority boundaries;
- exhaustive coverage rules and their evidence;
- bounded classification and severity vocabulary where classification occurs;
- structured artifact contracts and required outputs;
- required evidence, cross-checks, and objective completeness tests;
- result rules, acceptance criteria, and fail-closed conditions;
- stop boundary and operator or independent review procedure;
- result and evidence locations;
- successor gate or explicit terminal semantics;
- reviewed state-transition procedure;
- persistence verification and cold-resume verification; and
- exact resume instructions and next authorized action.

References to a schema-valid shared execution playbook are preferred to copied
boilerplate. A reference shall resolve to the same gate ID and the evaluator
shall inspect the resolved content as part of that gate's contract.

### Execution Playbook Contract

Every executable gate shall resolve an execution playbook containing at least:

```yaml
execution_playbook:
  discovery_surfaces: []
  inventory_method: []
  safe_operations: []
  prohibited_operations: []
  coverage_rules: []
  classification_required: true
  classification_vocabulary: {}
  artifact_contracts: []
  cross_checks: []
  completeness_tests: []
  result_rules: {}
  review_contract: CONTROLLED-REFERENCE
  state_transition_contract: CONTROLLED-REFERENCE
  persistence_contract: CONTROLLED-REFERENCE
  cold_resume_contract: CONTROLLED-REFERENCE
```

Discovery surfaces shall identify repository-relative paths, globs, safe
commands, controlled references, or explicitly dynamic future locations.
`REQUIRED` paths shall exist at evaluation. A dynamic location shall identify
what predecessor or procedure creates it; `DYNAMIC` is not a waiver for an
unknown input. Reference-only sources shall never be treated as current
authority or merged implicitly.

### Coverage Contract

Every assessment, analysis, design, planning, qualification, or implementation
gate shall state how exhaustive coverage is proven. Coverage rules shall use
enumeration, index/schema/registry reconciliation, unique-key accounting,
source-to-consumer tracing, graph endpoint checks, anti-joins, scenario
coverage, or another objective method appropriate to the subject.

Every discovered object shall be accounted for exactly once or placed in an
explicit exclusion or unresolved-gap record. Every required source, store,
controller, producer, consumer, interface, authority claim, or dependency shall
be represented. A claim that no issues were found is not coverage evidence.

An unproven required coverage rule is execution-significant and produces
`BLOCKED` for a gate result or `NOT_EXECUTABLE` for roadmap qualification.

### Classification Contract

When a gate classifies observations, its playbook shall set
`classification_required: true` and define non-empty, bounded finding and
severity vocabularies. Records shall not introduce synonyms or arbitrary prose
states in controlled classification fields.

Vocabulary shall be specific to the gate where necessary. Assessment
vocabularies may include `CONSISTENT`, `STALE`, `CONFLICTING`, `DUPLICATE`,
`OVERLAPPING`, `OBSOLETE`, `UNCONSUMED`, `UNDOCUMENTED_IMPLEMENTATION`, and
`UNRESOLVED`, with severity values `INFORMATIONAL`, `LOW`, `MEDIUM`, `HIGH`,
and `CRITICAL`. Existing controlled vocabulary shall be reused when it owns
equivalent semantics.

### Artifact Contract

Every structured output shall have a machine-readable artifact contract. A
contract shall identify artifact ID, title, representation format, purpose,
minimum record fields, and one or more completeness keys. Title-only output
lists do not qualify.

Artifact fields shall fit the gate subject. Each artifact shall be testable for
schema or field completeness, key uniqueness, referential integrity, bounded
classification, evidence linkage, and reconciliation to coverage counts.
Human-readable executive reports may summarize structured sources but shall
not replace them.

### Evidence Contract

Evidence shall prove discovery, coverage, classification, artifacts,
cross-checks, completeness, result, non-mutation or authorized mutation,
review, transition, persistence, and cold resume as applicable. Evidence shall
be attributable, repository-relative, reproducible, and integrity-protected
where the governing contract requires a digest.

Historical captured evidence remains digest-validated. Validators shall not
rewrite or whitespace-normalize historical evidence to make it conform.

### Result Contract

Assessment gate results use the existing convergence vocabulary:

| Result | Required meaning |
| --- | --- |
| `COMPLETE` | Required work and coverage are complete; no material finding affects the gate purpose. |
| `COMPLETE_WITH_FINDINGS` | Required work and coverage are complete; findings exist as controlled inputs to later work and do not block assessment completion. |
| `BLOCKED` | Required coverage, authority, integrity, identity, or safe operation cannot be established. |
| `FAILED` | The procedure, evidence integrity, or mandatory safety boundary failed. |

A subject finding is not automatically gate failure when discovery of findings
is the gate purpose. Result rules shall define each allowed result with
objective conditions. The result record shall be schema-valid and linked to
all artifacts, evidence, criteria, blockers, disposition, and next action.

### Terminal Gate Contract

`next_gate: null` is valid only when the gate explicitly declares itself
terminal and identifies both the external authority or process governing
continuation and the external continuation action. A terminal gate shall not
imply roadmap-wide execution authority. A non-terminal gate shall resolve one
deterministic successor and shall not declare external continuation.

### Review Contract

Every executable gate shall define qualified engineering review and operator
review boundaries. Review shall verify coverage totals, key uniqueness,
unresolved gaps, evidence links, artifact conformance, result rules, scope,
blockers, and proposed successor action. Review shall occur before state
transition. A validator result never substitutes for operator acceptance where
the gate requires it.

### State-Transition Contract

A reviewed completion transition shall, as applicable:

1. validate current roadmap and state;
2. validate gate result and evidence;
3. record required operator review;
4. update gate status;
5. update `STATE.yaml` sets, pointers, and successor status;
6. update Project State binding and roadmap version when required;
7. update the binding manifest and EMM digests;
8. validate the complete roadmap;
9. persist through separately authorized governed repository publication;
10. verify `HEAD`, `origin`, and required EOS relationship under current
    authority;
11. perform cold-resume verification; and
12. expose only the reviewed successor action.

The contract may be defined before system-authority convergence is complete.
It shall not be used to repair EOS or Registry state without separate
authority.

### Persistence Contract

Each gate shall persist artifacts, evidence, coverage proof, and result under
declared repository locations. Bindings and digests shall cover all roadmap
execution-contract sources required to reproduce qualification. Uncommitted
working-tree records shall report persistence as pending. A successful local
evaluation does not prove commit, push, publication, or EOS synchronization.

### Cold-Resume Contract

An executable roadmap shall support fresh-shell resume with no conversation,
provider session, transport, thread, or volatile runtime identity. Cold resume
shall resolve repository provenance, roadmap identity and version, structural
and executable qualification, completed/current/blocked gates, current gate
playbook, evidence, first incomplete objective, stop boundary, and exact next
authorized action.

Missing, malformed, stale, conflicting, unknown, unbound, or contradictory
inputs shall fail closed without mutation. Repeated cold resume over identical
authoritative inputs shall produce materially identical semantic output.

### Maintenance and Invalidation

Any material change to roadmap procedure, scope, dependencies, entry or
acceptance conditions, artifacts, evidence, classification, coverage, result
rules, authority, state transition, persistence, terminal behavior, or cold
resume invalidates prior execution-sufficiency qualification. Roadmap version
shall advance and PROC-0009 evaluation shall be repeated before
`EXECUTABLE=YES` is restored.

Editorial changes proven not to affect execution may retain qualification only
when the evaluation result records that determination and all source bindings
remain coherent.

## Evaluation Dimensions

PROC-0009 shall evaluate and report these independent dimensions:

1. structural completeness;
2. procedural sufficiency;
3. discovery sufficiency;
4. coverage determinism;
5. classification determinism;
6. artifact determinism;
7. evidence sufficiency;
8. result determinism;
9. authority boundaries;
10. fail-closed behavior;
11. review boundary;
12. state-transition determinism;
13. persistence; and
14. cold resume.

Every execution-significant dimension and gate shall pass. Warnings may record
non-determinism-neutral observations, but no warning may conceal an
execution-significant ambiguity. Such ambiguity produces `NOT_EXECUTABLE`.

## Machine-Readable Evaluation Result

Every evaluation shall persist a schema-valid result containing roadmap ID and
version, standard and procedure revisions, evaluation time, each dimension,
per-gate criterion results, warnings, blockers, overall result, and boolean
`executable`. The result shall use `PASS`, `FAIL`, and `NOT_APPLICABLE` for
criteria and `PASS` or `NOT_EXECUTABLE` overall.

The live generic evaluator remains authoritative for current sufficiency. A
persisted result is qualification evidence bound to one roadmap version; it
shall not override current source drift or a live failure.

## Validation

Conformance requires at minimum:

- schema validation of roadmap, state, gates, results, playbooks, artifacts,
  evidence manifests, and evaluation result;
- unique gate and dependency resolution;
- terminal-gate validation;
- non-empty structured procedure validation;
- discovery surface resolution or explicit dynamic/reference semantics;
- classification and artifact-contract resolution;
- coverage, cross-check, completeness, result, review, transition,
  persistence, and cold-resume checks;
- negative tests for missing or ambiguous execution-significant contracts;
- structurally valid `PLANNING_ONLY` behavior with `EXECUTABLE=NO`;
- contradiction and unknown-dependency fail-closed tests;
- generic CLI result exposure; and
- fresh-shell, non-mutating cold resume.

The canonical operator interface shall expose structural validity, execution
sufficiency, and executable status separately. Commands declared by a roadmap
shall document syntax, read/write class, expected outputs, and nonzero failure
behavior. Evaluation commands are read-only and return nonzero when structure
is invalid or executable qualification is requested and fails.

## Compliance

A roadmap complies as `EXECUTABLE` only when:

- all mandatory root, gate, and playbook contracts resolve;
- all execution-significant evaluation dimensions pass;
- all required gates pass individually;
- terminal semantics are unambiguous;
- warnings do not undermine determinism;
- the persisted evaluation matches the exact roadmap version;
- bindings detect drift;
- cold resume is deterministic and non-mutating; and
- separate execution authority remains explicit.

`PLANNING_ONLY` is compliant when its class is truthful and it does not claim
`EXECUTABLE=YES`. An executable roadmap with a missing classification contract,
artifact schema, completeness test, result rule, transition, persistence
check, cold-resume check, or terminal continuation is noncompliant and shall
fail closed as `NOT_EXECUTABLE`.

## Evidence and Acceptance

Required conformance evidence includes the machine-readable evaluation result,
gate results, negative-test results, schema validation, binding validation,
cold-resume transcript, and read-only proof. Engineering Governance or the
operator reviews controlled authority establishment; roadmap-specific review
follows its own review contract.

Acceptance of this standard does not accept any roadmap gate result or perform
any roadmap state transition.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-08-09 | Established the reusable executable-roadmap execution contract, evaluation dimensions, gate/playbook/artifact/coverage/result/terminal/transition/persistence/cold-resume requirements, maintenance invalidation, and fail-closed qualification rule. |

## Lifecycle Transition History

| Revision | Date | Previous State | New State | Authority |
| --- | --- | --- | --- | --- |
| STD-0006@1.0 | 2026-08-09 | Draft | Review | Executable Roadmap Standardization operator directive |
| STD-0006@1.0 | 2026-08-09 | Review | Approved | Homelab Operator |
| STD-0006@1.0 | 2026-08-09 | Approved | Active | Homelab Operator; persistence remains Pending because commit and push are prohibited |

## Human-Readable Gate Completion Record

An executable roadmap gate MUST persist both a machine-readable completion
record and a human-readable historical summary.

The minimum completion record is:

- `RESULT.yaml` or the roadmap's equivalent machine-readable result;
- required machine-readable evidence;
- validation evidence;
- `SUMMARY.md` or an equivalent explicitly declared human-readable gate
  completion record.

The human-readable summary MUST identify:

1. gate identifier and title;
2. execution result;
3. objective and achieved outcome;
4. material actions completed;
5. material findings and decisions;
6. validation/qualification result;
7. authoritative artifacts created or changed;
8. prohibited mutations confirmed absent;
9. blockers or unresolved matters;
10. next authorized roadmap action.

The summary is a projection of authoritative result/evidence and MUST NOT
silently introduce new execution authority or contradict machine-readable
records.

A roadmap SHOULD maintain a human-readable cumulative execution history that
references each completed gate's summary.

For manually executed roadmaps, a gate MUST NOT advance until its human-readable
summary and cumulative history entry have been persisted.

### Roadmap Versioning

Every authoritative modification to a roadmap definition MUST update the
roadmap version.

Version changes MUST be persisted in the roadmap itself and must distinguish
the prior and current version sufficiently for later provenance and resume.

At minimum:

- patch version: recordkeeping, clarification, or compatible planning change;
- minor version: executable scope, gate-contract, or compatible lifecycle
  capability expansion;
- major version: incompatible roadmap semantics, sequencing, authority, or
  lifecycle change.

Historical completed or active gate definitions remain immutable according to
their frozen execution generation; roadmap version advancement does not rewrite
their historical contracts.

## Pre-Creation Conflict Verification

Before any controlled document, roadmap artifact, gate record, human-readable
summary, cumulative history record, controlled-document-like evidence artifact,
or other repository document is created, copied, or introduced, the proposed
artifact MUST pass a pre-creation conflict verification.

The verification MUST occur before the artifact exists in the repository.

The verification sequence is:

1. declare the proposed artifact identity, type, purpose, authority, and
   intended repository location;
2. attempt Zeus-native discovery and verification first wherever Zeus exposes
   the required capability;
3. search authoritative document registration and indexing surfaces for the
   proposed identifier and equivalent purpose;
4. search existing controlled documentation for overlapping or conflicting
   authority, scope, terminology, or responsibility;
5. verify repository information-architecture placement;
6. verify that creation will not duplicate a controlled identifier or cause an
   existing controlled document to be rediscovered as a second authority;
7. verify applicable lifecycle, authority, and versioning constraints;
8. record a deterministic PRE_CREATE_VERIFICATION result;
9. create the artifact only after PRE_CREATE_VERIFICATION=PASS.

### Zeus-First Verification

Zeus is the preferred verification and discovery interface.

Where Zeus provides a native capability for document, registry, authority,
roadmap, artifact, identifier, placement, or conflict verification, that
capability MUST be attempted before lower-level repository inspection.

A Zeus capability failure MUST NOT be silently ignored.

If Zeus is unavailable or does not yet expose the required verification
surface:

- the missing capability MUST be identified explicitly;
- the condition MUST be preserved as a convergence/capability finding where
  applicable;
- repository-native controlled-document validation and authoritative index
  inspection MAY serve as a temporary fallback;
- the fallback MUST be visible in the verification result.

Zeus unavailability alone does not authorize bypassing conflict verification.

### Existing-Document Preference

When an authoritative controlled document already owns the proposed subject,
the default action is to evaluate modification of that existing document
rather than create another document.

Creation of a new document requires evidence that:

- no existing document already owns the authority or purpose;
- the identifier is unique;
- the repository location is valid;
- the relationship to existing authority is explicit.

### Controlled Documents in Evidence

A raw copy of a controlled document containing its live controlled identifier
MUST NOT be stored in a repository location where controlled-document discovery
can interpret that copy as another authoritative document.

Pre-change evidence SHOULD use digest provenance, Git object identity, patches,
or explicitly non-controlled representations instead.

### Failure Semantics

Any unresolved identifier collision, authority overlap, placement conflict,
duplicate-document discovery, or ambiguous ownership causes
PRE_CREATE_VERIFICATION=FAIL.

No artifact may be created while the result is FAIL or indeterminate.
