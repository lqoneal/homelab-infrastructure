# Canonical WOP Package to Zeus Lifecycle Integration Assessment

Assessment only. This record does not submit, admit, select, dispatch, execute,
qualify, publish, commit, push, or synchronize `WOP-OB-CAGF-G01-CANONICAL-001`.

## Result and provenance

```text
INTEGRATION_DIAGNOSTIC_RESULT=PASS_WITH_INTEGRATION_GAP
REPOSITORY=/data/engineering/repositories/homelab
REPOSITORY_ID=homelab-6bd83f9079d6fc57
BRANCH=main
HEAD=73bd1547d377cba66ecd470de8ae2caf95ad6d69
ORIGIN_MAIN=73bd1547d377cba66ecd470de8ae2caf95ad6d69
BASELINE_PARITY=PASS
WORKTREE_ENTRY_STATE=DIRTY_PRE_EXISTING_WORK_PRESERVED
TARGET_WOP=WOP-OB-CAGF-G01-CANONICAL-001
TARGET_PACKAGE=engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-wop-package.yaml
PACKAGE_SCHEMA=canonical-wop-package/1
CANONICAL_PACKAGE_DIGEST=c7a90c8854c170474d21059463bda616b93cd1886ee372a2fa1c4ab4ebc1b85c
RAW_FILE_SHA256=70efd25355a8364dd748cbde9376fcf718d6a992f29fbbb982c54c67c539fac2
PUBLISHED_GIT_BLOB=646efd271527956f00af88b41d9c8a1c32013a65
PACKAGE_CONTENT_PARITY=PASS
```

The two SHA-256 values are different by design. `package_digest` is computed
over canonicalized package content without `integrity`; the raw hash covers
the serialized YAML. Neither difference is corruption.

## Native diagnostic

| Interface | Result | Finding |
|---|---|---|
| `zeus wop validate <canonical-wop-package.yaml>` | FAIL / RC 78 | Existing source classifier accepts package directories, Markdown, and DOCX only. |
| `zeus wop inspect <canonical-wop-package.yaml>` | FAIL / RC 78 | Same source-format boundary; no package-directory projection is present. |
| `zeus wop verify <canonical-wop-package.yaml>` | FAIL / RC 78 | Authored-WOP verifier searches for `<source>.traceability.json`. |
| direct `canonical_package.load/validate` | PASS | 12 requirements, CAGF extension, digest, and non-executable result validate. |

This is an integration/interface defect. It is not a CAGF requirement defect,
package-integrity defect, or authority record.

## Existing authoritative source model

The current canonical Zeus flow is:

```text
Markdown or DOCX authored source
  -> wop_packaging.extract / wop_validation.validate_source
  -> atomic Stage 1 package directory
  -> stage1_runtime.validate_package
  -> Stage 1 registration/provenance and lifecycle record
  -> submission boundary / admission / execution services
```

An already-materialized Stage 1 package directory is also supported. Its
required shape is `mission.yaml`, `bootstrap.md`, `roadmap.md`, `gates.yaml`,
`manifests/immutable-manifest.yaml`, and the declared source document. The
package-directory validator owns structural package validation; Stage 1 owns
registration, package-tree identity, runtime provenance, and lifecycle
resolution. The existing example
`engineering/work-orders/WOP-ZDCL-02-ZEUS-PROVIDER-NEUTRAL-EXECUTION-CONTROL-001/ebeec97412e405e26b721c09`
passes this path.

The public lifecycle remains:

```text
mission authority -> WOP resolution/qualification -> submission
-> queue projection -> admission -> execution
```

Submission revalidates the source/package, freezes the Stage 1 package
identity, and records the existing registration/provenance and receipt chain.
Admission resolves the Mission Contract and WOP package; it does not regenerate
the WOP. Provider, execution, evidence, recovery, qualification, publication,
reconciliation, and closeout remain downstream Zeus owners. The WOP is not an
authority source.

## Traceability model and owner

There are two established traceability forms:

1. For authored Markdown/DOCX, `scripts/lib/emp/wop_authoring.py` writes the
   adjacent immutable `<source>.traceability.json`; `wop_verification.py`
   verifies its output digest, readiness, and replay content. This is the owner
   of the authored-source traceability sidecar.
2. For a package directory, `stage1_runtime.py` validates the package and owns
   the registration, validation evidence, package-tree digest, provenance,
   receipts, and lifecycle record. A source-sidecar is not required.

The canonical portable YAML is neither an authored Markdown/DOCX output nor a
Stage 1 directory. Therefore no existing traceability record can be resolved
for it, and Zeus correctly fails closed. A new standalone traceability store
would duplicate lifecycle ownership and is rejected.

Recommended traceability disposition: the canonical package remains the
portable source contract; a deterministic adapter supplies it to the existing
Stage 1 package-directory boundary. Stage 1 then generates its normal
validation evidence, registration, provenance, and lifecycle receipts. Any
canonical-package-specific facts are derived metadata bound to the adapter
projection, not a competing authority record.

## Identity and digest preservation

The following identities must remain distinct:

| Identity | Owner/meaning | Integration rule |
|---|---|---|
| `WOP_ID`, `MISSION_ID`, `GATE_ID`, `PACKAGE_ID` | Canonical portable package semantic identity | Preserve exactly from `canonical-wop-package/1`. |
| canonical `package_digest` | Digest of canonicalized package content excluding `integrity` | Preserve as immutable source provenance and never replace it with a raw-file hash. |
| raw YAML SHA-256 | Serialized source-file integrity fact | Record separately if needed for source-byte integrity. |
| Stage 1 package-tree digest | Zeus materialized package identity | Continue using the existing Stage 1 tree digest for registration/admission. |
| Stage 1 source/document digest | Existing source-preservation field | Extend its provenance to identify canonical digest semantics rather than relabeling the tree digest. |
| submission/admission/execution/receipt IDs | Zeus lifecycle identities | Generate only through existing lifecycle owners after authority permits. |

The adapter must carry at least `canonical_package_digest`, schema version,
source locator, raw source hash, and the canonical package identity into the
materialized package manifest/provenance. It must not overwrite Stage 1's tree
digest or invent a second semantic WOP identity.

## Ownership and consumers

| Concern | Canonical owner | Consumers |
|---|---|---|
| Portable package schema/digest | `canonical_package.py` and its schema | adapter, authoring/inspection tools, evidence |
| WOP meaning and shared identity | `WOP-SCHEMA-AND-EXECUTION-INTERFACE.md` | all WOP consumers |
| Source normalization and Stage 1 package creation | `wop_packaging.py` / Stage 1 boundary | Zeus submit and lifecycle |
| Package registration/provenance | `stage1_runtime.py` | submission, admission, recovery |
| Mission authority/Mission Contract | mission authority and existing resolver | admission/execution |
| Submission/admission | existing submission and admission boundaries | Zeus lifecycle |
| Runtime/execution/evidence/reconciliation | existing Zeus controllers | mission and WOP projections |
| Canonical package facts | adapter-derived metadata | Stage 1 manifest/provenance and read-only native views |

The package remains non-authoritative. Generated projections remain disposable
and non-authoritative. Mission authority is independent; no mission-to-mission
authority dependency is introduced.

## Integration options

### Recommended: deterministic adapter into the package-directory boundary

Add a source classifier and adapter for `canonical-wop-package/1` that:

1. calls the existing canonical package loader/validator;
2. maps only the universal WOP fields required by Stage 1;
3. preserves the complete canonical YAML as the immutable source copy;
4. writes the existing Stage 1 package shape in an isolated staging directory;
5. adds canonical schema/digest provenance to the existing manifest without
   changing Stage 1 tree-digest semantics;
6. passes the result through the existing `validate_package` and Stage 1
   submission path; and
7. exposes canonical-package identity and digest as read-only derived facts.

This is an adapter, not a parallel lifecycle. It reuses package validation,
registration, traceability/provenance, submission, admission, receipts,
recovery, and closeout.

### Rejected: direct canonical YAML lifecycle

Rejected because it would require a second validator-to-submission path,
duplicate registration/traceability/receipt handling, and risk allowing the
portable package to become an authority source.

### Rejected: authored-WOP traceability sidecar as the primary bridge

Rejected because a sidecar generated merely to satisfy `wop verify` would
duplicate the package's integrity/provenance contract and conflate authored
source traceability with Stage 1 package registration. A derived adapter view
may support inspection, but it must not own lifecycle state.

### Rejected: manual package-directory conversion

Rejected because it is not deterministic, not replay-safe, and would make the
operator reconstruct metadata outside the canonical package contract.

## Minimum implementation increment

The minimum increment before this WOP can be submitted is:

* a canonical-package source classifier and adapter at the existing WOP
  normalization/package boundary;
* a mapping contract for universal fields, including explicit fail-closed
  rejection when a canonical field cannot map to an executable Stage 1 field;
* preservation of the full canonical YAML and canonical digest in the
  materialized package manifest/provenance;
* Stage 1 validation and deterministic package-tree identity using existing
  code;
* read-only native projections for canonical package identity, canonical
  digest, source format, lifecycle disposition, and derived provenance;
* focused positive/replay tests and negative tests for malformed package,
  digest mismatch, unsupported extension, missing universal mapping,
  canonical/Stage 1 identity mismatch, and authority-dependency leakage; and
* documentation of the adapter ownership and digest distinction.

No change to the canonical package schema is currently required. No CAGF
requirement change is required. No WOP, Mission Contract, authority,
submission, admission, execution, or EOS mutation is part of this increment.

## Required tests

Positive tests must prove direct canonical validation, deterministic adapter
output, preservation of `WOP_ID`/`MISSION_ID`/`GATE_ID`, preservation of the
canonical package digest, Stage 1 package validation, and a single existing
submission lifecycle projection when later authorized.

Negative tests must prove fail-closed behavior for:

* canonical package integrity/digest mismatch;
* malformed YAML or unsupported schema version;
* unsupported typed extension;
* missing or ambiguous universal WOP mapping;
* Stage 1 identity mismatch;
* source/package digest mismatch;
* authority or mission-to-mission dependency leakage;
* duplicate/replayed adapter identity with different content; and
* missing/conflicting Mission Contract or authority at the existing boundary.

No submission or admission test should be run against the live target in this
assessment.

## Compatibility and authority impact

`CM`, `EENS`, `EMP`, and `ARCH` remain compatible because the adapter maps the
universal WOP contract and carries capability-specific data as package content
or typed extensions. It must not require CAGF-specific fields for non-CAGF WOPs.

The integration preserves existing authority semantics:

```text
MISSION_AUTHORITY_DEPENDENCIES=0
TECHNICAL_DEPENDENCIES=preserved and resolved by existing lifecycle contracts
RECOMMENDATION_CREATES_AUTHORITY=NO
ROADMAP_ORDER_CREATES_AUTHORITY=NO
GENERATED_PROJECTION_CREATES_AUTHORITY=NO
```

## Validation performed

```text
CANONICAL_WOP_PACKAGE_TESTS=PASS (7/7)
CANONICAL_PACKAGE_DIRECT_VALIDATION=PASS (12 requirements; non-executable)
ZEUS_WOP_VALIDATE_DIRECT_SOURCE=FAIL/RC78 (expected current integration blocker)
ZEUS_WOP_INSPECT_DIRECT_SOURCE=FAIL/RC78 (expected current integration blocker)
ZEUS_WOP_VERIFY_DIRECT_SOURCE=FAIL/RC78 (expected missing authored sidecar)
CONTROLLED_DOCUMENT_VALIDATION=PASS (--semantic-all)
REGISTRY_VALIDATION=PASS (native platform registry check)
ZEUS_PLATFORM_VERIFICATION=PASS
OPERATION_BETA_VERIFICATION=PASS
EOS_VALIDATION=PASS
REPOSITORY_EOS_VALIDATION=PASS
INTEGRATED_VALIDATION=PASS (platform verification)
GIT_DIFF_CHECK=PASS
MISSION_STATE_MUTATION=NO
EXECUTION_STATE_MUTATION=NO
AUTHORITY_MUTATION=NO
WOP_MUTATION=NO
EOS_MUTATION=NO
COMMIT=NOT_PERFORMED
PUSH=NOT_PERFORMED
EOS_SYNCHRONIZATION=NOT_PERFORMED
```

The worktree remains dirty from pre-existing unrelated changes. This
assessment adds only this evidence file and does not stage it.

## Disposition

```text
SCHEMA_CHANGE_REQUIRED=NO
CONTROLLED_DOCUMENT_CHANGE_REQUIRED=YES (adapter/source-type ownership and digest provenance documentation during implementation)
WOP_PACKAGE_CHANGE_REQUIRED=NO for the published target package
CAGF_REQUIREMENT_CHANGE_REQUIRED=NO
DUPLICATION_RISK=HIGH if direct lifecycle or sidecar authority is added; LOW with the Stage 1 adapter
WOP_SUBMISSION_READINESS=BLOCKED_PENDING_CANONICAL_PACKAGE_ADAPTER
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_CANONICAL_WOP_ZEUS_LIFECYCLE_INTEGRATION_ASSESSMENT
STATUS=AWAITING_OPERATOR_REVIEW
```
