# Zeus OA-01 Mission-Centric Verification

Status: Operational Alpha verification specification

Handoff: ZH-OA01-VERIFICATION-001

## Scope and authority boundary

This specification augments verification of the already admitted OA-01
objective. It does not replace OA-01, change its implementation scope, alter
the OA-01 through OA-30 sequence, modify the Progressive WOP, activate a gate,
or modify Engineering Governance.

The controlled `ZEUS-OA-ROADMAP-002`, its immutable WOP, admission receipt,
Mission Contract, and runtime state remain unchanged. Governance Baseline
OA-1.0 is consumed from
`docs/project/milestones/2026-07-29-operational-alpha-governance-baseline-1.0.md`.
Mission authority is resolved by the existing EOS Mission Contract resolver.
Execution state is independently projected from the existing Progressive WOP
runtime. The Work Registry and Project State are read directly; this interface
does not create another state store.

## Mission-oriented acceptance

OA-01 operational acceptance requires Zeus itself to report:

- current mission and immutable identifiers;
- resolved Mission Contract and authority source;
- Governance State and Execution State as distinct fields;
- mission eligibility and execution readiness;
- unresolved blockers and required approvals;
- next authorized action;
- repository identity, root, branch, HEAD, working-tree state, and qualified
  baseline;
- source records used to create the projection.

The JSON output is deterministic for unchanged source state. A canonical
SHA-256 `projection_digest` binds the complete `zeus mission show` projection.
These observations do not accept OA-01 or advance the Progressive WOP.

## Authoritative verification interface

| Operator command | Observation |
| --- | --- |
| `zeus mission list` | Current mission identity, Governance State, Execution State, and eligibility |
| `zeus mission show` | Complete mission-centric OA-01 projection and source bindings |
| `zeus mission state` | Independent Governance State, Execution State, and mission status |
| `zeus mission readiness` | Readiness, blockers, and required approvals |
| `zeus mission eligibility` | Eligibility decision and blockers |
| `zeus mission blockers` | Deterministically ordered blocker set |
| `zeus mission contract` | Resolved Mission Contract identity, lifecycle, WOP, and resolution |
| `zeus mission authority` | Governance State, authority source, and required approvals |
| `zeus mission next` | Next authorized action and current blockers |

An optional selector may be supplied. `current`, the Mission Contract mission
ID, contract ID, Work Registry work-item ID, operational mission ID,
Progressive WOP ID, and package ID all resolve to the same OA-01 projection.
Unknown selectors fail closed.

## OA-01 capability matrix

| OA-01 objective | Existing subsystem | Zeus command | Verification evidence | Future OA dependency |
| --- | --- | --- | --- | --- |
| One identified repository | Git identity and Mission Contract repository binding | `zeus mission show` | `repository.identity`, `repository.root`, `current_mission` | OA-02 intended-repository authority |
| Synchronized authoritative state | Repository-to-EOS matrix, Project State, Work Registry | `zeus mission show` | `sources` and projection digest | OA-04 reconstruction; OA-25 reconciliation |
| Integrity-valid source state | Mission Contract resolver, immutable WOP locator, canonical projection | `zeus mission contract`; `zeus mission show` | authorized resolution, WOP binding, projection digest | OA-03 discovery; OA-08 WOP; OA-09 package integrity |
| Qualified baseline binding | Mission Contract baseline and observed Git HEAD | `zeus mission show` | `repository.qualified_baseline`, `repository.head`, Governance State | OA-02 current authority; all cumulative gates |
| Mission authority is observable | Existing Mission Contract resolver | `zeus mission authority` | authority source, Governance State, approvals | OA-02 authority; OA-03 discovery |
| Governance and execution are independent | Mission Contract resolution and Progressive WOP runtime | `zeus mission state` | separate state fields | OA-05 through OA-07 staging and selection |
| Incomplete work fails visibly | Progressive WOP and approval projection | `zeus mission readiness`; `zeus mission blockers` | readiness and ordered blockers | OA-06 classification; OA-18 approvals |
| Continuation is bounded | Progressive OA next-action resolver | `zeus mission next` | next action without execution or dispatch | OA-02 and immediate-successor rule |

## Operational verification scenarios

Run every command above twice against unchanged repository state. The JSON and
`projection_digest` must be identical. Confirm:

1. `mission list` and `mission show` identify the same current mission.
2. `mission state` contains separate Governance and Execution states.
3. `mission contract` reports the active resolver result and WOP locator.
4. `mission blockers` agrees exactly with `mission readiness`.
5. `mission next` reports an action but performs no transition.
6. An unknown mission selector exits fail closed.
7. `scripts/tests/test-zeus-oa01-verification.py` passes.

The existing OA-01 operator decision remains governed by the admitted
verification guide. This specification supplies operational evidence; it does
not manufacture its `VERIFIED` marker or operator acceptance receipt.

## Implementation completion integration

When the existing Progressive runtime reports OA-01
`IMPLEMENTATION_REQUIRED`, `zeus resume` invokes the fail-closed OA-01
implementation assessor. The assessor:

1. executes every mission-centric command twice and requires byte-identical
   valid JSON;
2. requires authorized Mission Contract resolution and OA-01 as the sole
   active gate;
3. executes the focused OA-01, Progressive OA, and Stage 1 tests;
4. validates the admitted package, repository, EOS synchronization, and Work
   Registry;
5. writes integrity-bound implementation evidence to
   `runtime/evidence/OA-01/IMPLEMENTATION.json`;
6. re-reads the existing runtime state and transitions only OA-01 to
   `AWAITING_OPERATOR_VERIFICATION`.

An idempotent replay validates and returns the same evidence without rewriting
state. The assessor never creates `VERIFIED`, records operator acceptance,
changes OA-02, or introduces a second operational state store.

## EENS boundary

No notification is emitted. A future read-only observation event may include
the mission identity, projection digest, Governance State, Execution State,
eligibility, blockers, and next action. Subscription, delivery, retry, and
notification dispatch remain owned by EENS and later OA gates.
