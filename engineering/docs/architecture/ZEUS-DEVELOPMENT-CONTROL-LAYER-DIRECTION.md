# Zeus Development Control Layer — Published Engineering Direction

Status: published engineering direction; planned subsystem; implementation deferred
Authority boundary: subordinate to Engineering Governance, EOS, EMP, and EENS

## Purpose

The Zeus Development Control Layer (ZDCL) is the planned engineering control
plane for governed development sessions. ZDCL will control session context,
execution boundaries, evidence, qualification preparation, and publication
preparation. It will not originate governance authority, replace EOS state, or
become an alternate mission or capability registry.

## Ownership and boundaries

| Concern | Owner | ZDCL relationship |
| --- | --- | --- |
| Governance authority and approval | Engineering Governance | Consumes verified authority; never originates it |
| Engineering operational state | EOS | Verifies and consumes EOS state |
| Portfolio and mission coordination | EMP | Resolves coordination inputs; does not duplicate them |
| Engineering event delivery | EENS | Publishes lifecycle facts through EENS contracts |
| Development execution | Codex and qualified agents | Executes a bounded, frozen session contract |
| Session control and evidence binding | ZDCL | Owns the technical session protocol |

## Responsibilities

The planned ZDCL responsibility set is:

- engineering session launch and classification;
- repository identity and qualified-baseline verification;
- EOS synchronization verification;
- mission and WOP resolution;
- execution identity and engineering-context generation;
- isolated execution workspaces;
- approval interception and fail-closed handling;
- engineering evidence capture and EENS integration;
- interruption recovery, qualification preparation, publication preparation,
  and engineering closeout.

Every session will bind mission, WOP, execution, repository, baseline,
authority, approval, evidence, and lifecycle identities. A missing, stale, or
ambiguous binding will prevent execution.

## Session classes

ZDCL will support three explicitly distinct session classes:

1. WOP Execution — a bounded session authorized by a controlled WOP.
2. Controlled Engineering — an authorized engineering session without direct
   mission execution authority.
3. Exploratory — a non-authoritative investigation session that cannot mutate
   controlled state or represent qualification.

The session class is part of the session identity and determines permitted
effects, evidence requirements, and recovery behavior.

## Progressive implementation roadmap

| Phase | Objective | Prerequisite | Qualification focus | Successor |
| --- | --- | --- | --- | --- |
| 1 | Native Zeus Launcher | Published direction | Identity and bounded launch | 2 |
| 2 | Session Classification | 1 | Correct class and effect profile | 3 |
| 3 | Mission/WOP Resolution | 2 | Authority-chain resolution | 4 |
| 4 | Engineering Context Generation | 3 | Complete immutable context | 5 |
| 5 | Repository Qualification | 4 | Identity, baseline, and cleanliness | 6 |
| 6 | EOS Qualification | 5 | Freshness and synchronization | 7 |
| 7 | Session Persistence | 6 | Durable recovery and replay safety | 8 |
| 8 | Controlled Workspaces | 7 | Isolation and bounded effects | 9 |
| 9 | Approval Management | 8 | Fail-closed approval interception | 10 |
| 10 | Evidence Capture | 9 | Complete attributable evidence | 11 |
| 11 | EENS Integration | 10 | Durable lifecycle event delivery | 12 |
| 12 | Qualification Integration | 11 | Independent qualification handoff | 13 |
| 13 | Publication Integration | 12 | Controlled publication preparation | 14 |
| 14 | Distributed Agent Support | 13 | Agent identity, capability, and recovery | 15 |
| 15 | Exclusive Engineering Execution Control | 14 | No bypass of ZDCL control plane | Complete |

Each phase requires its predecessor’s qualified boundary. No phase authorizes
implementation of a future phase, and this document itself authorizes none.

## Integration direction

- **EMP:** supplies operational coordination, node inventory, mission status,
  approvals as represented by authoritative sources, and engineering history
  projections.
- **EENS:** receives immutable lifecycle facts with identity, ordering,
  replay, and delivery obligations defined by EENS contracts.
- **EOS:** remains authoritative for engineering operational state,
  synchronization, freshness, and repository qualification inputs.
- **Engineering Governance:** owns authority, approval, controlled lifecycle,
  and publication disposition.
- **Codex and agents:** execute only the bounded session contract supplied by
  ZDCL; they cannot expand scope or create authority.
- **Distributed nodes:** participate through qualified execution envelopes,
  registered capabilities, isolated workspaces, and attributable evidence.

## Migration strategy

`engctl codex` is a temporary compatibility entry point. Future engineering
sessions will migrate to a Zeus-native interface, with the final command name
selected by a controlled interface decision (`zeus develop` or an equivalent
Zeus-native command).

Migration proceeds through compatibility redirect, native launcher, session
classification, context and workspace qualification, event/evidence
integration, and controlled cutover. Retirement requires equivalent or better
qualification coverage, operator acceptance, recovery evidence, and an
approved rollback path. Until those criteria are met, the compatibility path
remains available but cannot bypass the ZDCL boundaries defined here.

## Deferred status

ZDCL is a planned subsystem and architectural direction only. No launcher,
session controller, workspace manager, approval interceptor, distributed
agent service, or runtime behavior is implemented by this publication.
