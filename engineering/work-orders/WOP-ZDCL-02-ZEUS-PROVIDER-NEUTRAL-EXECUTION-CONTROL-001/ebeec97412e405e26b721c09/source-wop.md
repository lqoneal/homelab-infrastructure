---
document_id: WOP-ZDCL-02-ZEUS-PROVIDER-NEUTRAL-EXECUTION-CONTROL-001
title: ZDCL-02 Zeus Provider-Neutral Execution Control
version: 2.1
status: Draft
owner: Engineering Governance
created: 2026-08-03
last_updated: 2026-08-03
phase: Operation Beta — ZDCL Continuation
domain: Operation Beta Development
classification: Implementation WOP
source_of_truth: false
repository_identity: homelab
repository_root: /data/engineering/repositories/homelab
qualified_repository_baseline: c775ad3d0636d34866cfc2949e270c82697ba587
protected_baselines:
  OA-v1.0.0: 73b22f44dd8ee4d70f0c943ed19e1569022f856a
  OB-PLAN-v1.0.0: b928c1541aa7ba42132f288927924818632f7cd2
execution_mode: DEVELOPMENT
governance_authority: Engineering Governance
effect_profile: DEVELOPMENT-INFRASTRUCTURE-NONPRODUCTION
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - STD-0003
  - STD-0004
  - PROC-0001
  - PROC-0004
  - PROC-0005
  - TPL-0001
  - TPL-0002
  - SPEC-0005
  - SPEC-0008
  - SPEC-0014
  - ENGINEERING-EXECUTION-INTERFACE
  - MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY
tags:
  - operation-beta
  - zdcl
  - zeus
  - execution-control
  - provider-neutral
  - work-order
---

# ZDCL-02 Zeus Provider-Neutral Execution Control

This is revision **2.1** of the Implementation WOP. The filename, document
identifier, frontmatter version, transaction revision, and revision history
are one identity. The v2.0 staging draft remains unchanged as review evidence;
this document supersedes it only if separately accepted and published.

## Submission Metadata

WOP ID: `WOP-ZDCL-02-ZEUS-PROVIDER-NEUTRAL-EXECUTION-CONTROL-001`

Mission ID: `ZDCL-02`

Title: `ZDCL-02 Zeus Provider-Neutral Execution Control`

Objective: `Establish a bounded, provider-neutral Zeus control contract for discovery, qualification, deterministic selection, non-live planning, identity, receipt inspection, and replay/forgery safeguards.`

Dependencies: `ZDCL-01 completed; published Beta controller convergence; current controlled WOP, execution, handoff, validation, evidence, persistence, and publication documents; existing engctl codex launcher.`

Protected Baselines: [OA-v1.0.0@73b22f44dd8ee4d70f0c943ed19e1569022f856a, OB-PLAN-v1.0.0@b928c1541aa7ba42132f288927924818632f7cd2]

## Gates

- repository and protected-baseline verification;
- metadata, authority, ETP, and admission dry-run verification;
- non-live provider qualification and deterministic selection;
- dispatch-plan, identity, receipt, replay, and forged-state verification;
- controlled-document, Registry, platform, and regression validation.

## Qualification Requirements

- controlled-document and Registry validation pass;
- exact WOP and metadata ownership mapping pass;
- provider-neutral selection and non-live plan evidence pass;
- missing-capability, ambiguity, replay, forged-receipt, and parity fixtures pass;
- no runtime, lifecycle, publication, or protected-baseline mutation.

## Completion Requirements

- all required evidence and Completion Report produced;
- controlled documentation reconciled;
- candidate remains uncommitted and unpublished;
- Governance Conformance Review complete;
- no unresolved authority, metadata, provider-neutrality, or scope finding.

## Transaction Identification

| Field | Declared value and owner |
|---|---|
| Engineering Operating System | `EOS`; EOS owns operational state and synchronization |
| Engineering Governance Authority | `Engineering Governance`; Governance owns authority and acceptance |
| Implementation Agent | Zeus-selected qualified Development execution agent; resolved at admission |
| Mission | `ZDCL-02` |
| Phase | `Operation Beta — ZDCL Continuation` |
| Implementation WOP | `WOP-ZDCL-02-ZEUS-PROVIDER-NEUTRAL-EXECUTION-CONTROL-001@2.1` |
| Revision | `2.1` |
| Title | `ZDCL-02 Zeus Provider-Neutral Execution Control` |
| Status | `Draft`; admission may resolve only the controlled lifecycle projection |
| Execution Mode | `DEVELOPMENT` |
| Effect Profile | `DEVELOPMENT-INFRASTRUCTURE-NONPRODUCTION` |
| Repository | `/data/engineering/repositories/homelab` (`homelab`) |
| Qualified baseline | `c775ad3d0636d34866cfc2949e270c82697ba587` (admission re-verifies) |
| Protected baselines | `OA-v1.0.0@73b22f44dd8ee4d70f0c943ed19e1569022f856a`; `OB-PLAN-v1.0.0@b928c1541aa7ba42132f288927924818632f7cd2` |
| Engineering Execution Interface | `engineering/execution/execution-interface.yaml@3`; owner `engctl` |

## Authority and resolution contract

This WOP does not self-authorize. It is a Development WOP under the active
`MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY@1.0` only when Zeus admission verifies
the exact EMM-registered identity, governance submission attestation,
delegation state, and allowlisted actions required by that policy. Admission
and registration are performed by Zeus; this document records the contract,
not the result.

| Artifact | State in this WOP | Producer and validation authority | Persistence |
|---|---|---|---|
| Authority Record | Not required for an allowlisted Development root action; required if policy validation fails | Governance/EMM resolver; Zeus verifies | EMM-controlled authority records |
| EMM resolution receipt | `REQUIRED_AT_ADMISSION` | Metadata Engine under SPEC-0014/EMM; Zeus consumes digest-bound receipt | EMM resolution receipt locator |
| Engineering Transaction Profile | `REQUIRED_AT_ADMISSION`; exact compatible active profile only | Authorization Kernel selects; SPEC-0008/PROC-0004 resolve | Frozen resolved manifest locator |
| Baseline binding | Declared above; admission re-verifies repository and protected tags | EOS/repository qualification | Resolution receipt and evidence |
| Compatibility result | `REQUIRED_AT_ADMISSION`; must be `COMPATIBLE` | ETP resolver and PROC-0004 | Frozen manifest |
| Authority preservation result | `REQUIRED_AT_ADMISSION`; must be `PRESERVED` | PROC-0004 authority-preservation validation | Handoff/resolution evidence |
| Implementation agent | `REQUIRED_AT_ADMISSION` | Zeus capability qualification and policy | Admission/execution record |

No value in this table grants authority merely by being present in the WOP.
Admission fails closed if a required resolver result is absent, ambiguous,
stale, incompatible, or digest-mismatched.

## Governing domain boundaries

| Domain/component | Owns | Does not own |
|---|---|---|
| Engineering Governance | authority, approval, controlled lifecycle, publication disposition | provider facts or runtime projections |
| Operation Beta | mission scope and roadmap context | constitutional authority or provider execution |
| Zeus Runtime | admission orchestration, lifecycle observation, verification, bounded planning, evidence projection | governance authority, EOS facts, EMM source ownership |
| Engineering Execution Interface | canonical routing and semantic owner bindings | a new provider or authority registry |
| ETP/SPEC-0008 | profile representation, compatibility, deterministic resolution | execution authority or activation |
| EOS | repository identity, operational state, freshness, synchronization | WOP authority or provider selection |
| EENS | append-only lifecycle event delivery | lifecycle approval or source replacement |
| EMM/Metadata Engine | registered entities and resolution receipts | runtime-generated authority or inferred scope |
| Managed provider adapter | provider capability facts and execution receipts | Zeus lifecycle transitions or authorization |

## Purpose and expected outcome

Purpose: establish a bounded, provider-neutral Zeus control contract for
discovery, qualification, deterministic selection, non-live planning, identity,
receipt inspection, and replay/forgery safeguards.

Expected outcome: Zeus can inspect and qualify execution resources and produce
a canonical non-live dispatch plan without launching a provider, advancing a
mission, publishing, synchronizing EOS, or treating provider output as
authority.

## Mission classification and profile

Classification: `Category B — Local Engineering Environment Work`, subject to
PROC-0001 confirmation at admission. Selected ETP, components, compatibility,
and resolved manifest are admission-time outputs; no invented profile is
declared here. The transaction is non-live and has no external effects.

## Governing references

This WOP consumes, and does not redefine, `STD-0000@current`, `STD-0001@current`,
`STD-0002@current`, `STD-0003@2.2`, `STD-0004`, `PROC-0001@2.7`,
`PROC-0004@1.6`, `PROC-0005`, `TPL-0001@2.0`, `TPL-0002@2.0`,
`SPEC-0005@2.2`, `SPEC-0008@1.1`, `SPEC-0014@1.6`, and the
`ENGINEERING-EXECUTION-INTERFACE@3`. Exact revisions selected by controlled
resolution are recorded in the admission receipt.

## Scope

### In scope

- provider-neutral provider and agent capability abstractions;
- descriptive provider-resource registration using an existing authoritative
  registry or bounded qualification record;
- capability qualification and deterministic, read-only selection;
- non-live dispatch-plan construction and inspection;
- canonical execution/provider/agent/session/mission/WOP/handoff identities;
- provider-neutral receipt validation, replay rejection, and forged-state
  rejection;
- `engctl codex` as the first replaceable managed compatibility adapter;
- directly affected tests, documentation, and evidence.

### Out of scope

Live provider launch, live mission dispatch, autonomous selection or execution,
Codex-only architecture, authority or registry creation, CAGF implementation,
Operational Alpha redesign, publication, EOS synchronization, commit, push,
merge, tag, closeout, and completed-history modification.

## Explicit authority and effects

Authorized activities are repository inspection, metadata reconciliation,
non-live planning, read-only verification, bounded adapter qualification, and
focused tests. Authorized repository changes are limited to directly affected
Zeus controller/interface code, tests, controlled documentation, and evidence.
Authorized external effects: `None`.

The WOP cannot activate itself, create root authority, dispatch a provider,
change protected baselines, or advance lifecycle state from provider output.

## Dependencies and entry criteria

Dependency boundary: completed ZDCL-01; published Beta controller convergence; current
controlled WOP/execution/handoff/validation/evidence/persistence/publication
documents; existing `engctl codex` launcher for compatibility assessment.

Entry criteria: clean repository; exact repository identity and qualified
baseline; controlled-document review; current Beta and Zeus health; successful
admission-time EMM/ETP resolution; no live executor requirement.

Blocking conditions: unresolved metadata ownership; missing or ambiguous
authority; baseline drift; incompatible ETP; provider-specific architecture;
need for live dispatch; or any non-approved external effect.

## Metadata contract inventory and extension rule

The supporting `METADATA-FIELD-MAPPING.md` inventories WOP, mission, Mission
Contract projection, Authority Record, ETP, execution interface, provider,
agent, receipt, EOS, EENS, runtime, admission, and verification metadata. Each
field has one owner, producer, consumer set, lifecycle, persistence locator,
validation source, duplicate/conflict result, and compatibility mapping.
Zeus-specific fields are additive projections only; they cannot supersede a
controlled producer or create a new authority schema.

## Architecture and provider contract

Zeus remains the lifecycle observer/orchestrator. Provider selection is
capability-, authority-, environment-, availability-, and policy-bound and
fails closed on ambiguity. A provider adapter supplies capability facts and
receipts through the common contract; it cannot approve, qualify, publish, or
advance Zeus state. `engctl codex` is the initial managed adapter and is not
the execution model or sole supported provider.

## Transaction-specific execution sequence

1. Verify repository, identity, protected baselines, and clean tree.
2. Resolve the exact WOP, Development authority policy, EMM identity, and ETP.
3. Freeze the digest-bound resolved manifest and record metadata mappings.
4. Inventory existing execution-interface, provider, runtime, event, receipt,
   and test paths.
5. Implement only non-live provider-neutral registration, qualification,
   selection, planning, identity, receipt, and inspection components.
6. Qualify `engctl codex` as a replaceable adapter without live dispatch.
7. Run replay, forged-state, missing-capability, ambiguity, parity, and
   regression tests.
8. Reconcile controlled documentation and produce evidence.
9. Stop at the uncommitted, unpublished operator-review boundary.

Authorized workflow deviations: `None`.

## Deliverables and evidence

Deliverables are the provider-neutral implementation, adapter binding,
non-live plan/receipt contracts, tests, controlled-document reconciliation,
and Completion Report. Required evidence includes:

- `METADATA-RECONCILIATION-REPORT.md`
- `METADATA-FIELD-MAPPING.md`
- `METADATA-GAP-ANALYSIS.md`
- `METADATA-EXTENSION-COMPATIBILITY-REPORT.md`
- `METADATA-OWNERSHIP-MATRIX.md`
- `GOVERNING-DOMAIN-BOUNDARY-REPORT.md`
- `AUTHORITY-RESOLUTION-MATRIX.md`
- `ARCHITECTURE-RECONCILIATION-REPORT.md`
- provider selection, missing-capability, ambiguity, replay, forged-receipt,
  non-live-plan, and human/JSON parity evidence;
- `CONTROLLED-DOCUMENTATION-RECONCILIATION-REPORT.md`.

## Success, validation, and stop conditions

Success requires metadata and admission dry-run compatibility, provider
neutrality, non-live plan inspection, receipt integrity, replay/forgery
rejection, focused/regression tests, and unchanged Beta/Operational Alpha
behavior. Controlled-document, Registry, platform, metadata, ownership,
traceability, version, and `git diff --check` validation must pass. Repository–
EOS synchronization may be deferred only because this candidate is
unpublished, and that exception must be reported.

Stop on authority excess, baseline drift, unresolved metadata, provider
specificity, live-dispatch requirement, external effect, integrity failure, or
any non-synchronization validation failure. Resume requires re-verifying this
exact WOP revision/digest, repository/baseline, authority, ETP, and first
incomplete step.

## Publication and completion

Publication is a separate operator-authorized transaction. Synchronization
targets are none during this WOP. Required repository history action before
review is none. Completion follows TPL-0002/STD-0003 and begins exactly with
`# Completion Report`; Governance Conformance Review is mandatory.

## Final certification

Question: Does the candidate establish Zeus-controlled provider-neutral,
non-live execution planning and inspection while preserving controlled
metadata, authority, lifecycle, and provider independence?

Allowed answer set: `YES | NO`.

## Engineering Governance review

Disposition: `Pending independent review`.

Acceptance: `Requires Revision or Approval`.

Approved by/date: `Pending`.

## Revision history

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-03 | Initial provider-neutral execution-control draft. |
| 1.1 | 2026-08-03 | Established Zeus lifecycle ownership and Codex adapter boundary. |
| 1.2 | 2026-08-03 | Added metadata reconciliation and evidence requirements. |
| 2.0 | 2026-08-03 | Added metadata-contract inventory expansion; retained as prior review input. |
| 2.1 | 2026-08-03 | Corrected revision identity, domain/authority boundaries, immutable baseline binding, ownership mappings, admission-time resolution semantics, and non-live provider constraints. |
