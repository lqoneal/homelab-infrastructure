# ZH-AUTHORIZATION-BUNDLE-CONTRACT-001 Engineering Completion Record

Status: engineering evidence for repository changes; not an Engineering Work
Order, authorization decision, controlled-document publication, or lifecycle
transition.

## 1. Mission context and boundaries

The requested engineering outcome was to elevate the existing authorization
input manifest into one formal Authorization Bundle contract, route
Engineering Work Initiation consumers through it, preserve authorization
policy and the controlled dirty-tree baseline, test positive and negative
resolution behavior, and investigate controlled-document integration.

No commit, staging, push, publication, synchronization, reset, rebase,
approval replay, dispatch, or lifecycle action was performed. Work was limited
to input-contract definition, resolution integration, tests, architecture
documentation, evidence, and the baseline handoff allowlist.

## 2. Initial repository state — observed facts

- Branch: `main`, two commits ahead of `origin/main`.
- The index was empty.
- The working tree already contained 31 modified tracked paths and numerous
  untracked paths belonging to earlier work.
- The controlled baseline contract identified baseline commit
  `d0861dc62b8199de03230152c4ed3cfb687dd9a7`, 132 file-expanded baseline
  entries, and content digest
  `02539907905434ed91ecf600f1c55337a8dddcaa07b807f801a5ff0d57c6ef0e`.
- Existing authorization-input integration was already present in
  `scripts/lib/eos/platform.sh` and regression coverage was present in
  `scripts/tests/test-working-tree-baseline.py`.

These facts were observed before implementation. Existing changes were
preserved and were not attributed to this work.

## 3. Authorization-input inventory and dependency analysis

Observed authorization artifact inputs:

| Input | Required | Resolution before this work | Downstream consumer |
|---|---:|---|---|
| Admission record | yes | manifest plus independent admission environment | `wop-admissionctl verify-record` |
| Authority graph | yes | manifest or `EOS_SHADOW_AUTHORITY_GRAPH` | `AuthorityGraph` / evaluator |
| Immutable WOP | yes | manifest or `EOS_SHADOW_WOP`; separately parsed by shell for identity | admission and evaluator |
| Evaluation state | yes | manifest or `EOS_SHADOW_STATE` | `EvaluationState` / evaluator |
| Publication receipt | yes | manifest or `EOS_SHADOW_RECEIPT` | `PublicationReceipt` / evaluator |
| Execution lease | conditional | manifest or `EOS_SHADOW_LEASE` | `ExecutionLease` / evaluator |
| Revocation record | optional | manifest or `EOS_SHADOW_REVOCATION` | `RevocationRecord` / evaluator |
| Expected authority node | optional | manifest or `EOS_SHADOW_EXPECTED_AUTHORITY` | evaluator |

Evaluation configuration, not artifact input: authorization mode, evaluation
time, and ADR output directory. Those remain environment configuration because
they select evaluation/output behavior and are not authorization evidence.

The pre-change call path parsed the manifest twice:

1. `eos_platform_qualify` read admission and WOP locators and extracted
   `wop_id` with `awk`.
2. `eos_work_initiation_authorize` independently validated required keys and
   reread evaluator locators with `jq`.

The two paths had different completeness checks and could disagree about
malformed data. This was the confirmed architectural defect.

## 4. Investigation timeline, diagnostics, and rejected hypotheses

1. Captured branch, index, status, diff statistics, and local instruction-file
   inventory.
2. Searched authorization references across scripts, tests, engineering
   records, and fixtures.
3. Identified the earlier input-manifest correction and reconstructed its
   dependency trace from code and evidence.
4. Read the full shell call path, shadow evaluator CLI, enforcement regression,
   and controlled-baseline validator.
5. Confirmed duplicated parsing in two shell functions.
6. Implemented a resolver and initially required a complete legacy environment.
   Existing enforcement regression showed that this would suppress the
   historical validation-failure ADR when no WOP inputs exist. That experiment
   was rejected.
7. Changed legacy normalization to preserve incomplete legacy input, allowing
   existing admission/evaluator layers to retain fail-closed behavior.
8. The earlier incomplete canonical-manifest regression expected exit `77`.
   The canonical contract now consistently classifies structural resolution
   failure as resubmission-required exit `78`; the test was updated. This is an
   interface error-classification change, not an authorization-policy change.

Rejected hypotheses:

- The shadow evaluator itself needed modification. Rejected: it already
  consumes typed inputs and applies the required policy checks.
- Admission verification should accept the package directory label as WOP
  identity. Rejected: admission is bound to the immutable internal `WOP-`
  identity.
- Mode, evaluation time, and ADR destination belong in the authorization
  artifact bundle. Rejected: they are runtime/evidence configuration and do
  not identify authorization evidence.

## 5. Engineering decisions and implementation

### Canonical contract

`engineering/authorization/authorization-bundle.schema.yaml` defines a closed,
versioned `ZeusAuthorizationBundle`. Five locators are required: admission
record, authority graph, WOP, state, and receipt. Lease, revocation, and
expected authority are optional. Unknown fields are rejected.

### Single resolver

`scripts/lib/work_initiation/authorization_bundle.py` owns:

- JSON/YAML mapping load and corruption handling;
- version, type, completeness, and unknown-field validation;
- relative-locator resolution against the bundle directory;
- regular-file availability checks;
- normalized absolute paths;
- WOP identity derivation;
- canonical-versus-legacy conflict detection;
- explicit legacy environment compatibility.

The resolver grants no authority and does not interpret admission or
authorization policy.

### Consumer routing

`eos_platform_qualify` resolves once, supplies the normalized admission locator
and derived WOP identity to admission verification, and passes the same
normalized object to `eos_work_initiation_authorize`. The authorization
function constructs the existing evaluator CLI arguments without reparsing the
source manifest.

### Fail-closed behavior

Canonical structural or ambiguity failures stop before admission with exit
`78`. Evaluator rejection remains exit `77`. No fallback from a selected,
invalid canonical bundle to legacy inputs is allowed.

## 6. File-by-file delta

| File | Change |
|---|---|
| `engineering/authorization/authorization-bundle.schema.yaml` | Added machine-readable canonical contract. |
| `scripts/lib/work_initiation/authorization_bundle.py` | Added the sole bundle/compatibility resolver. |
| `scripts/lib/eos/platform.sh` | Replaced duplicate parsing with one normalized resolution flow. |
| `scripts/tests/test-authorization-bundle.py` | Added seven contract-level regressions. |
| `scripts/tests/test-working-tree-baseline.py` | Added canonical type/version fixture fields and canonical incomplete-bundle exit expectation. |
| `engineering/docs/architecture/authorization-bundle-contract.md` | Added interface, dependency, compatibility, and failure documentation. |
| `engineering/execution/controlled-working-tree-baseline.json` | Added only this work's paths to the pre-existing handoff allowlist. |
| This record | Added reconstruction, evidence, debt, and integration analysis. |

No admission evaluator, authorization evaluator, WOP policy, authority graph,
publication receipt, lease, revocation, publication, synchronization,
lifecycle, replay, or enforcement-decision implementation was modified.

## 7. Compatibility assessment

Canonical producers must add `schema_version: 1` and
`document_type: ZeusAuthorizationBundle`. Relative locators are supported and
are now deterministic relative to the bundle file rather than caller working
directory.

Legacy `EOS_WOP_ADMISSION_RECORD` and `EOS_SHADOW_*` artifact variables remain
supported when no bundle is selected. When a bundle is selected, a populated
legacy variable must agree exactly with the normalized canonical value;
otherwise resolution fails closed. Incomplete legacy input is intentionally
passed onward so existing admission/evaluator failure behavior and ADR
generation remain intact.

Compatibility risk: canonical incomplete-bundle failures are uniformly exit
`78`; one prior missing-receipt test observed `77`. Consumers that improperly
depend on that inconsistent code must update to the formal distinction:
resolution/admission input defects are `78`, authorization rejection is `77`.

## 8. Validation evidence

The final validation commands and exact results are recorded after execution
in section 13. Required negative cases are permanent tests:

- valid bundle;
- incomplete bundle;
- canonical/legacy conflict;
- corrupted bundle;
- complete legacy compatibility;
- unavailable locator fail-closed;
- unknown field and invalid WOP identity;
- admission/WOP mismatch;
- authorized shadow/enforcement integration.

Each PASS in the final matrix is supported by the named command and test count
or exact decision output. A failed intermediate regression (legacy completeness
behavior) and the incomplete-bundle exit-code discrepancy are retained above.

## 9. Architecture impact

Ownership of input location and normalization moves from two shell consumers to
one Python boundary. Ownership of policy and evidence remains unchanged.
Dependency direction is now:

`bundle producer -> resolver -> admission + shadow/enforcement adapters -> existing evaluators`.

This reduces ambiguity, makes provenance observable through the resolved
object's `source`, and provides a stable interface for future producers. It
does not introduce dispatch, execution, approval, publication, or persistence
capability.

## 10. Controlled Documentation Integration Investigation

This section is an implementation-ready investigation only. It does not create,
revise, approve, activate, or publish a controlled document.

### Affected controlled documents

| Candidate document | Proposed integration | Owner/authority |
|---|---|---|
| `PROC-0001` Engineering Work Order Execution Procedure | Reference the Authorization Bundle as the exclusive canonical artifact-input interface at initiation and define the legacy transition rule. | Existing procedure owner and Engineering Governance authority. |
| `TPL-0001` Engineering Work Order template | Add a reference/locator field for the bundle where machine initiation is applicable; do not embed authorization evidence. | Existing template owner and Engineering Governance authority. |
| Controlled document model/specification | Define whether a bundle is a controlled record, execution record, or transient resolved manifest and its retention/integrity requirements. | Existing specification owner and Engineering Governance authority. |
| Execution interface specification | Define producer/consumer responsibilities, exit `77` versus `78`, and bundle handoff. | Zeus execution-interface owner under its existing authority. |

No revision is recommended until the governing owners classify the bundle.

### Proposed new controlled document

A new controlled interface specification, tentatively “Authorization Bundle
Interface Specification,” is recommended only if the existing execution
interface specification cannot own the schema without mixing unrelated
concerns. It would normatively own field definitions, producer obligations,
integrity/provenance requirements, compatibility lifecycle, error taxonomy,
and conformance tests. The repository-native YAML schema would remain the
machine-readable subordinate artifact.

### Hierarchy, placement, and dependencies

Recommended hierarchy:

1. Engineering Governance/Charter establishes authority boundaries.
2. `PROC-0001` establishes the initiation process and requires the interface.
3. The execution-interface or new Authorization Bundle specification defines
   the normative data contract.
4. The YAML schema is the machine-readable conformance artifact.
5. Architecture documentation explains implementation.
6. Evidence records demonstrate qualification without granting approval.

Recommended normative placement is under the existing controlled
specification hierarchy; the machine schema should remain at
`engineering/authorization/authorization-bundle.schema.yaml` or move only
during an authorized migration with all references reconciled.

Dependencies include admission-record, authority-graph, immutable-WOP,
evaluation-state, receipt, lease, and revocation schemas; `PROC-0001`; the
execution interface; the controlled-document model; and baseline
qualification.

### Lifecycle and reconciliation

Proposed lifecycle: Draft -> technical review -> Governance qualification ->
approval -> controlled publication -> Active -> superseded/retired through
existing controlled-document procedures. Schema revision must be monotonic;
resolver support must precede producer migration; removal of legacy variables
requires usage evidence and separately authorized deprecation.

Reconciliation must compare normative prose, YAML schema, resolver constants,
CLI behavior, user guidance, fixtures, tests, and any WOP/template references.
The controlled-document manifest and immutable locators must be updated only
through separately authorized publication.

### Migration and adoption sequence

1. Classify the bundle record and assign a controlled owner.
2. Decide whether the execution-interface specification or a new specification
   owns the normative contract.
3. Draft controlled text and cross-document changes.
4. Qualify schema/prose equivalence and negative cases.
5. Publish under existing approval and publication procedures.
6. Update bundle producers to version/type fields.
7. Measure legacy-variable usage.
8. Announce deprecation and remove compatibility only under separate authority.

### Risks

- Divergence between controlled prose, YAML schema, and resolver constants.
- Treating a bundle as authorization rather than a locator contract.
- Persisting secrets if future inputs contain sensitive material.
- Relative-path relocation changing provenance unless the bundle is immutable.
- Premature removal of legacy inputs.
- Publication of references before schema ownership is established.

## 11. Engineering framework and process improvements

Implemented improvements directly aligned with scope:

- one typed normalization boundary;
- strict closed-schema behavior;
- deterministic relative-path resolution;
- explicit source provenance;
- canonical/legacy ambiguity rejection;
- WOP identity derived once from the selected artifact;
- distinct resolution and authorization error classes;
- negative tests retained as first-class evidence.

Reusable process improvements:

- Require every cross-language shell/Python contract to have one parser and a
  machine-readable schema.
- Test corrupted, incomplete, conflicting, unknown, and unavailable inputs in
  addition to semantic denial.
- Treat backward compatibility as a named path with a removal criterion.
- Make controlled dirty-tree allowlists transaction-scoped and update them
  before introducing paths.
- Add schema/prose/implementation reconciliation to qualification checklists.

Potential WOP/EOS/EMP/EENS/Zeus follow-ons, not implemented:

- WOP templates should reference a bundle, not duplicate its locators.
- EOS should expose a diagnostic command that prints sanitized resolver
  provenance and contract version.
- EMP should produce bundles atomically after admission artifacts exist.
- EENS may record a digest/event for bundle resolution, but must not interpret
  that event as authorization.
- Zeus assurance could compare the schema field set with resolver constants.

## 12. Technical debt and future recommendations

Resolved:

- High-impact duplicated manifest parsing and inconsistent validation.
- Working-directory-dependent relative bundle locators.
- Unspecified canonical/legacy conflict behavior.

Discovered:

| Priority | Debt | Impact and remediation |
|---|---|---|
| P1 | No cryptographic digest/signature for the bundle itself | Referenced artifacts retain their controls, but locator substitution is not bundle-bound. Decide record classification, then add integrity/provenance without treating it as authorization. |
| P1 | Schema and resolver field sets can drift | Add an automated schema-to-constant conformance test. |
| P2 | Legacy environment usage is not observable centrally | Add sanitized telemetry/evidence and define a deprecation threshold. |
| P2 | Exit-code taxonomy is shell-local documentation | Define it in the controlled execution interface after authorization. |
| P3 | `expected_authority` is a scalar while future multi-root cases may emerge | Preserve v1; evaluate only with concrete requirements and a versioned migration. |

Introduced:

- A second representation exists between YAML schema and Python constants.
  Tests reduce but do not eliminate drift risk.
- Canonical incomplete bundles consistently return `78`, requiring callers
  that depended on the former inconsistent `77` to adjust.

Prioritized future recommendations, not authorized work:

1. P1 — controlled classification, ownership, and integrity design.
2. P1 — schema/resolver conformance automation.
3. P2 — migrate all producers to canonical bundles and measure compatibility
   path use.
4. P2 — add redacted bundle-resolution evidence to EENS with explicit
   non-authorization semantics.
5. P3 — remove legacy variables only after evidence, notice, and separate
   authorization.

## 13. Final validation and closeout

| Requirement | Evidence | Result |
|---|---|---|
| Repository integrity | `scripts/engctl repository health homelab`; `git fsck --no-dangling --no-reflogs` | PASS; health reported repository discovery/integrity and active `main`; fsck exit 0 |
| Controlled working-tree baseline | `working_tree_baseline.py --repository . --contract ...` | PASS; `AUTHORIZED_DIRTY_TREE`, 132 baseline paths, baseline HEAD/digest/index/preserved-artifact checks all true |
| Authorization Bundle contract resolution | `test-authorization-bundle.py` | PASS, 7/7 |
| Valid bundle and initiation integration | `test-working-tree-baseline.py` | PASS, 5/5; generated ADR recorded Zeus and enforcement `AUTHORIZED` |
| Admission verification | `test-wop-admission.py` | PASS, 10/10 |
| Shadow authorization | `test-work-initiation-shadow.py` | PASS, 11/11 |
| Enforcement authorization | `test-work-initiation-enforcement.py` | PASS, 13/13 |
| Existing authorization semantics | Unmodified evaluators plus shadow/enforcement/admission suites above | PASS within tested scope |
| Existing broad regression suite | `bash scripts/verify.sh` | PASS; summary 20 passed, 0 warnings, 0 failures |
| Shell syntax | `bash -n scripts/lib/eos/platform.sh` | PASS |
| Empty index | `git diff --cached --quiet` | PASS |

The broad verifier printed expected negative-fixture `FAIL:` lines during
semantic-validation tests; the enclosing tests passed and the verifier's final
result was 20/0/0. Those lines are test evidence, not repository failures.

Observed health context retained: repository state modified with 94
file-expanded paths and upstream state ahead 2/behind 0. This is consistent
with the pre-existing controlled working tree plus this handoff and is not a
clean-tree claim.

Final disposition: the requested engineering implementation and evidence are
complete within the non-publication repository scope. The canonical resolution
path, compatibility path, positive authorization flow, corruption,
incompleteness, conflict, admission mismatch, unavailable locator, invalid
identity, and fail-closed behavior are covered. No authorization decision was
made by this report.
