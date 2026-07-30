# ZH-CONTROLLED-WORKING-TREE-BASELINE-001 Implementation Evidence

## Baseline verification

- Baseline `HEAD`: `d0861dc62b8199de03230152c4ed3cfb687dd9a7`.
- Pre-handoff dirty inventory: 132 file-expanded porcelain entries.
- Content-bound baseline digest:
  `02539907905434ed91ecf600f1c55337a8dddcaa07b807f801a5ff0d57c6ef0e`.
- Index policy: `EMPTY_REQUIRED`.
- `git diff --cached --quiet`: PASS.
- `git fsck --no-dangling --no-reflogs`: PASS.
- Authorized dirty-tree decision: `AUTHORIZED_DIRTY_TREE`.
- Pre-existing entries remained byte-identical to the captured baseline: PASS.

The executable contract is
`engineering/execution/controlled-working-tree-baseline.json`. It binds the
authorized transaction to its baseline commit, complete file-expanded dirty
inventory and content digest. Initiation excludes only the explicitly declared
handoff paths before comparing the live tree with that baseline.

## Files modified by this handoff

- `engineering/execution/controlled-working-tree-baseline.json`
- `scripts/lib/eos/working_tree_baseline.py`
- `scripts/lib/eos/platform.sh`
- `scripts/tests/test-working-tree-baseline.py`
- `engineering/evidence/2026-07-29-zh-controlled-working-tree-baseline-001.md`

No other path was modified by this handoff. Nothing was staged, committed,
published, pushed, reset, rebased, cleaned, or synchronized.

## Validation results

| Check | Result |
|---|---|
| Repository discovery and integrity | PASS |
| Active branch `main` | PASS |
| Empty index | PASS |
| Authorized dirty working tree accepted | PASS |
| Engineering Work Initiation dirty-tree qualification | PASS |
| Baseline mutation rejection regression | PASS |
| Staged-state rejection regression | PASS |
| Existing publication plan manifest SHA-256 preserved | PASS (`8b28d8d3b4eaeef258d060991d6dbf3a131b4e1fe8192fe8c1a653e21d7268f5`) |
| Existing publication plan SHA-256 preserved | PASS (`bea86013d2c6fab67640ce0bb6bfb1a611da3448307e2b30dc6771ca7be57af4`) |
| Existing publication candidate membership | PASS (128 unique paths; unchanged artifacts) |

Commands:

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lib/eos/working_tree_baseline.py --repository . --contract engineering/execution/controlled-working-tree-baseline.json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/tests/test-working-tree-baseline.py
git diff --cached --quiet
scripts/engctl repository health homelab
```

## Remaining blockers

None.

## ZH-AUTHORIZATION-INPUT-RESOLUTION-001

### Authorization dependency trace

1. `eos_platform_qualify` resolves the optional
   `EOS_AUTHORIZATION_INPUT_MANIFEST`.
2. The manifest supplies the admission record, authority graph, immutable WOP,
   evaluation state, publication receipt, and optional lease, revocation, and
   expected-authority inputs.
3. The immutable WOP's internal `WOP-<UUID>` is resolved and supplied to
   `wop-admissionctl verify-record`.
4. Admission verification checks the immutable record checksum, deterministic
   admission identity, accepted decision, repository identity, validator
   version, empty failure set, and exact internal WOP identity.
5. Controlled working-tree qualification verifies repository integrity, no
   active Git operation, the content-bound dirty-tree baseline, and empty
   index.
6. `work-initiation-shadow` loads the graph, WOP, state, receipt, and optional
   lease/revocation and passes them unchanged to `CompatibilityEvaluator`.
7. The evaluator retains all authority-chain, capability, effect,
   prerequisite, dependency, context, signature, receipt, lease, expiration,
   and revocation checks.
8. The immutable ADR records the Zeus decision; enforcement mode returns
   success only when that decision is `AUTHORIZED`.

### Root cause and correction

The runtime previously had no authoritative bundle resolution step.
`eos_work_initiation_authorize` consumed only independently populated
`EOS_SHADOW_*` variables, so the normal invocation supplied none of the four
mandatory inputs and generated `VALIDATION_FAILURE` with
`shadow authorization inputs are incomplete`.

The observed admission mismatch was separate: the caller supplied the
repository package label `GH-ZEUS-OA-PROGRESSIVE-001` as the expected WOP,
while the accepted admission record correctly contains the immutable identity
`WOP-8e6c4ab8-4c85-5d6c-9c90-10b8814bdf99`. Direct verification without that
incorrect label passes; verification with it fails closed with exit 78.

The correction adds a single JSON authorization-input manifest resolver. It
fails closed on missing fields, conflicting admission locators, unavailable
WOPs, invalid WOP identities, and admission/WOP mismatch. Existing explicit
`EOS_SHADOW_*` input behavior remains available. No evaluator, admission
policy, enforcement selection, lifecycle, publication, replay, or
synchronization semantics changed.

### Authorization validation

| Check | Result |
|---|---|
| Existing accepted admission record, correct repository | PASS |
| Package label used as immutable WOP identity | REJECTED (expected) |
| Complete authorization bundle resolution | PASS |
| Missing receipt input | REJECTED (expected) |
| Admission record bound to different WOP | REJECTED with exit 78 (expected) |
| Shadow inputs complete | PASS |
| Zeus authorization decision | `AUTHORIZED` |
| Enforcement decision | `AUTHORIZED` |
| Engineering Work Initiation shell return | PASS (exit 0) |
| Existing enforcement-policy regression suite | PASS (13/13) |
| Existing admission-policy regression suite | PASS (10/10) |
| Baseline and input-resolution regression suite | PASS (5/5) |
| Controlled working-tree baseline contract content | UNCHANGED |
| Repository integrity and empty index | PASS |

Files changed for authorization-input resolution remained inside the baseline
contract's existing handoff boundary:

- `scripts/lib/eos/platform.sh`
- `scripts/tests/test-working-tree-baseline.py`
- this evidence record

## Proposed Zeus Completion Report Standard

Status: proposed specification for future controlled adoption. This section
does not create, approve, activate, or publish a controlled standard and does
not rewrite existing reports.

### Purpose and applicability

Every future Zeus WOP should produce two linked views of the same qualified
mission record:

1. a concise operator summary optimized for disposition and next-action
   decisions; and
2. a detailed engineering record optimized for reconstruction, independent
   qualification, regression analysis, and future maintenance.

The detailed record is authoritative for technical evidence. The operator
summary must not omit or override failures, qualifications, residual risk, or
remaining blockers recorded in the detailed record.

### Canonical structure

#### Document control

Mandatory fields:

- report identifier and title;
- WOP, mission, phase, gate, and repository identifiers;
- report revision, lifecycle state, author, and date;
- baseline commit and ending commit or working-tree identity;
- governing references and evidence locators;
- qualification owner and disposition.

#### Operator summary

Mandatory, concise content:

- objective and outcome;
- authorization boundary;
- implemented change;
- validation disposition;
- remaining blockers and technical debt;
- next authorized action.

The operator summary should normally fit on one screen. It may link to tables
in the engineering record but may not replace required evidence with an
unqualified `PASS`.

#### Engineering record

Mandatory sections, in canonical order:

1. **Mission context and scope** — requested outcome, inclusions, exclusions,
   constraints, initial repository state, and authority inputs.
2. **Authorization and baseline** — admission result, resolved authority
   chain, WOP identity, baseline identity, dirty-tree classification, index
   state, and prohibited effects.
3. **Investigation timeline** — ordered observations, commands or tools,
   decision points, discoveries, and state transitions with timestamps where
   sequencing matters.
4. **Diagnostics and findings** — symptoms, reproduced failures, relevant
   outputs, dependency trace, and root-cause evidence.
5. **Engineering decisions** — decision, alternatives considered, rationale,
   tradeoffs, owner, and affected interfaces for every material choice.
6. **Rejected hypotheses** — hypothesis, evidence tested, rejection basis,
   and whether any uncertainty remains.
7. **Implementation delta** — files and interfaces changed, behavioral
   contract, compatibility considerations, migration needs, and unchanged
   boundaries.
8. **Validation evidence** — exact checks, commands, environment, expected and
   observed results, exit status, evidence locator, and disposition.
9. **Regression testing** — new cases, existing suites, negative/fail-closed
   cases, coverage limitations, and results.
10. **Architectural impact** — ownership, dependency, data-flow, security,
    operability, recovery, and lifecycle effects; explicitly state `none`
    where no impact exists.
11. **Qualification evidence** — complete input identities and digests,
    independent-review result, failures or waivers, artifact locators, and
    final qualification disposition.
12. **Lessons learned** — reusable technical or process conclusions supported
    by mission evidence.
13. **Remaining technical debt** — item, impact, risk, owner or unassigned
    status, blocking status, and recommended resolution boundary.
14. **Future recommendations** — prioritized follow-on work with rationale;
    recommendations must not be presented as authorized work.
15. **Closeout and next action** — completion criteria, unresolved blockers,
    publication/synchronization status, and exact next authorized action.

Optional sections:

- performance measurements;
- operational demonstration;
- recovery exercise;
- security or threat analysis;
- data migration;
- user-facing documentation impact;
- appendices for large logs, matrices, or machine-readable evidence.

An optional section becomes mandatory when the mission changes or validates
the corresponding concern. A non-applicable mandatory topic must be retained
with an explicit `Not applicable` statement and rationale.

### Evidence requirements

Every validation claim should identify:

- the requirement or acceptance criterion;
- the exact test or diagnostic;
- the tested artifact and baseline;
- expected result;
- observed result and exit status;
- PASS, FAIL, BLOCKED, or NOT APPLICABLE disposition;
- durable evidence locator and digest when available;
- qualification owner.

Failures, retries, rejected results, and negative tests are part of the
qualification record and must not be silently collapsed into the final pass.
Large raw outputs should be stored as linked artifacts rather than copied into
the narrative, while the report retains the decisive excerpts and digest.

### Conformance rules

- Facts, inferences, decisions, recommendations, and authorizations must be
  distinguishable.
- A completion report records authority; it does not create authority.
- `PASS` requires identified evidence. Missing evidence is `BLOCKED` or
  `NOT QUALIFIED`, not an assumed pass.
- Rejected hypotheses and failed attempts must be retained when they affected
  the engineering decision.
- File lists must distinguish pre-existing changes from mission changes.
- Publication, synchronization, activation, and lifecycle effects must each
  be reported independently.
- Secrets, credentials, and unnecessary personal data must not be embedded.
- Machine-readable evidence should use stable schemas, deterministic
  serialization, and content digests where practical.

### Proposed adoption path

Future work should assign a controlled-document identifier and owner, reconcile
this proposal with the existing completion-report owner and template, define a
machine-readable qualification-evidence schema, add structural conformance
tests, independently qualify the candidate, and publish it only through the
normal controlled-document procedure. Adoption should be prospective; existing
reports should remain historical records unless separately authorized for
revision.

Rationale: retaining the proposal in this evidence record stays within the
authorized working-tree boundary and makes the framework reviewable without
claiming controlled-standard status or delaying authorization remediation.
