---
document_id: CHAR-0001
title: Engineering Charter
version: 1.2
status: Active
owner: Engineering Governance
created: 2026-07-10
last_updated: 2026-07-26
phase: Governance Foundation
domain: Engineering Governance
classification: Foundational Governance Charter
source_of_truth: true
related_documents:
  - GEN-0001
  - POL-0001
  - STD-0000
  - EDR-0002
  - SPEC-0011
tags:
  - engineering
  - charter
  - governance
  - authority
  - foundational
---

# Engineering Charter

## Purpose

This Charter establishes the origin of engineering authority for the Engineering Operating System.

It defines the relationship between the ultimate engineering authority, the authenticated production principal, Zeus, Engineering Governance, and repository-controlled records.

The Charter provides the foundational authority upon which all subordinate engineering governance is established.

This Charter does not prescribe engineering implementation, document formats, technical standards, or execution procedures. Those responsibilities are delegated to subordinate controlled records.

---

## Scope

This Charter governs:

- the origin of engineering authority;
- delegation of engineering authority;
- governance hierarchy;
- repository authority;
- foundational engineering principles.

This Charter does not directly govern engineering implementation.

---

## Origin of Engineering Authority

For the production Zeus environment, engineering authority originates solely
with Lawrence O'Neal, the Ultimate Engineering Authority.

Principal `loneal` is the authenticated production identity representing that
authority. The authenticated Zeus CLI is the authoritative interface through
which Lawrence O'Neal exercises engineering authority.

Engineering Governance is the controlled governance function through which
that authority is recorded and administered. It is not an independent person,
organization, committee, or competing source of authority.

Repository-controlled records derive their authority ultimately from Lawrence
O'Neal. They are the normal operational source of execution authority after
authentication, publication, validation, and authority resolution.

Repository-controlled records do not constitute the ultimate origin of
engineering authority, and the Zeus system does not originate authority.

---

## Engineering Governance

Engineering Governance is responsible for:

- establishing engineering governance;
- approving policies;
- approving standards;
- approving specifications;
- approving procedures;
- authorizing engineering work;
- accepting engineering work;
- establishing engineering baselines;
- qualifying engineering baselines;
- designating operational baselines;
- improving the Engineering Operating System.

Engineering Governance may delegate execution responsibility but retains governance responsibility.

### Transitional Engineering Handoff Governance

Engineering Governance recognizes that Engineering Handoff generation is presently a manual engineering activity.

Until Engineering Handoff generation has been established as an operational automated capability through the controlled engineering lifecycle, every Engineering Handoff issued by Engineering Governance shall be considered approved by Engineering Governance.

During this transitional period:

- Engineering Handoffs constitute the authoritative expression of Engineering Governance intent.
- Engineering Handoffs provide the constitutional authority required to initiate subordinate engineering governance processes.
- The authority, scope, limitations, deliverables, prohibitions, success criteria, and certification requirements for each engineering mission shall remain defined by the individual Engineering Handoff.
- Subordinate controlled documentation shall interpret and execute Engineering Handoffs consistent with this Charter.

This transitional authority shall not eliminate, merge, bypass, or diminish any subsequent governance activity established by subordinate controlled documentation, including:

- Engineering Work Order construction;
- Engineering Work Order review;
- lifecycle transitions;
- publication;
- qualification;
- activation;
- implementation authorization;
- repository modification controls;
- evidence requirements; or
- any other governance responsibility established by subordinate controlled documentation.

This transitional provision exists solely to remove circular authority dependencies while Engineering Handoff generation remains a manual engineering activity.

This transitional provision shall terminate automatically upon activation of an automated Engineering Handoff generation capability through the controlled engineering lifecycle.

---

## Repository Authority

The engineering repository is a governed system.

It is not the originating governing authority.

Repository-controlled records become authoritative through the governance processes established by Engineering Governance.

Repository-controlled records govern engineering activity within the authority delegated to the repository.

They do not create or originate engineering authority.

---

## Delegation Hierarchy

Engineering authority is expressed and resolved through the following
hierarchy:

1. Lawrence O'Neal, Ultimate Engineering Authority
2. Authenticated production principal `loneal`
3. Zeus CLI, Authoritative Instruction Interface
4. Authority Resolution Runtime
5. Controlled repository governance and engineering records
6. Authorized engineering execution
7. Engineering evidence, qualification, completion, and reconciliation

Each level shall remain consistent with the authority delegated by the level above it.

No subordinate record may contradict a superior governing record.

---

## Engineering Principles

### Evidence Before Assumption

Engineering decisions shall be based upon observable evidence.

Repository state shall not be inferred.

Authority shall not be assumed.

### Deterministic Engineering

Engineering processes shall be repeatable, deterministic, and reproducible.

Equivalent inputs shall produce equivalent engineering outcomes.

### Explicit Authority

Every engineering activity requiring repository modification shall possess explicit engineering authority.

Engineering authority shall not be implied.

### Traceability

Every engineering decision shall be traceable to its governing authority.

Every repository-controlled record shall possess discoverable relationships to governing records.

### Historical Integrity

Engineering history shall be preserved.

Superseded engineering decisions and records shall remain reconstructable.

### Continuous Improvement

The Engineering Operating System shall continually evaluate and improve its engineering processes.

Process deficiencies identified during initiation, execution, validation, or qualification shall become controlled engineering improvement candidates.

---

## Bootstrap Authority

Lawrence O'Neal possesses ultimate engineering authority independent of
repository state and exercises it through authenticated principal `loneal` and
the Zeus CLI.

Bootstrapping authority exists only to restore authoritative repository state
when controlled documentation cannot authorize execution. It authorizes
reconciliation of controlled documentation before operational execution
proceeds; it never authorizes a bypass of controlled documentation, policy,
authentication, provenance, validation, or auditing.

Zeus shall first attempt normal authority resolution. Missing, stale,
conflicting, incomplete, or invalid authority shall be handled according to the
Authority Restoration Principle in SPEC-0011. Deterministic reconciliation
that requires no human engineering decision shall be performed automatically.
An explicit authenticated decision shall be requested only when reconciliation
requires Lawrence O'Neal to exercise ultimate engineering authority.

After reconciliation, Zeus shall validate the repository and re-run normal
authority resolution. Execution may proceed only under restored
controlled-document authority.

---

## Relationship to Subordinate Documents

This Charter delegates operational governance to subordinate controlled documents.

Policies define governance objectives and constraints.

Standards define mandatory engineering rules.

Specifications define engineering models and architectures.

Procedures define repeatable engineering workflows.

Engineering Work Orders authorize bounded engineering execution.

No subordinate controlled document may conflict with this Charter.

---

## Amendment

This Charter may be amended only by Engineering Governance.

Every amendment shall:

- preserve a traceable authority chain;
- preserve engineering history;
- be published as a controlled revision;
- trigger reconciliation of affected subordinate records.

Until all affected subordinate controlled documentation has been reconciled, this Charter shall govern in the event of conflict between this Charter and subordinate controlled documentation.

Reconciliation shall restore consistency without diminishing the authority established by this Charter.

---

## Effective Authority

This Charter becomes the highest foundational governing record within the Engineering Operating System upon activation by Engineering Governance.

All subordinate repository-controlled governance derives authority through this Charter.
