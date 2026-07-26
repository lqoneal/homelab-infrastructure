# ZEUS-P2-003 Authority Resolution Runtime Qualification Evidence

Date: 2026-07-26
Baseline: `5ebaa32` plus ZEUS-P2-002 working-tree architecture
Scope: repository-local runtime implementation and compatibility qualification

## Implemented components

| Component | Location |
| --- | --- |
| Authority Resolution Runtime | `scripts/lib/emp/authority_resolution.py` |
| Operational WOP finalizer | `scripts/lib/emp/wop_service.py` |
| Dual-mode operator interface | `scripts/zeus` |
| ARB schema | `engineering/authority/authority-resolution-bundle.schema.yaml` |
| Repository-fixed authority source | `engineering/authority/operational-authority-state.yaml` |
| Automated qualification | `scripts/tests/test-authority-resolution-runtime.py` |

## Positive evidence

An isolated, owner-labelled authority-state fixture resolves:

- mission, phase, work-item, and qualification identity;
- exact repository root and Git baseline;
- granted human approval bound to the work scope digest;
- a validated work-package node in the existing authority DAG;
- the active governing reference manifest;
- a verified authenticated principal; and
- deterministic WOP/ADR reservations.

The runtime produces a deterministic, sealed ARB with eight provenance entries.
The operational WOP finalizer derives approval, node, ADR, immutable WOP,
repository, mission, revision, governing references, and submitter values from
that bundle. The resulting WOP passes the unchanged Admission Controller.

The successful operational CLI invocation supplies no approval reference,
authority node, ADR identifier, or immutable WOP identifier. Output remains
`review_required: true` and `automatically_submitted: false`.

## Negative evidence

Automated cases prove rejection of:

- incomplete source collections;
- incorrect authoritative owner;
- superseded lifecycle state;
- approval/work scope disagreement;
- unverified principal;
- repository baseline disagreement;
- authority-graph resolution disagreement;
- operational placeholders;
- tampered bundle seal; and
- caller-supplied authority fields in operational mode.

The repository-default authority source has
`operationally_configured: false`. A live operational invocation therefore
fails closed until the designated owners publish complete records. This is an
activation safeguard, not a runtime limitation.

## Compatibility evidence

Qualification mode remains the CLI default. The legacy explicit fields remain
accepted. When omitted, clearly labelled placeholders are generated.
Qualification output remains review-required and never automatically
submitted. The pre-existing supervised reasoning and WOP-generation test suite
passes without modification.

## Governance and policy preservation

The implementation has no approval mutation, autonomous approval, submission,
admission decision, dispatch, or execution method. Mission Admission policy and
the Admission Controller validation contract are unchanged. Production source
selection is repository-fixed; only `ZEUS_TESTING=1` permits an isolated test
source.

## Qualification commands

```text
python3 scripts/tests/test-authority-resolution-runtime.py
python3 scripts/tests/test-conversational-reasoning.py
python3 scripts/validate_controlled_documents.py
python3 scripts/tests/test-controlled-document-relationships.py
bash scripts/verify.sh
git diff --check
```

Final aggregate results are recorded in the completion report.
