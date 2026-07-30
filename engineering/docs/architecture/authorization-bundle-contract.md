# Authorization Bundle Contract

Status: engineering architecture interface; not a controlled-document
publication or authorization decision.

## Purpose

The Authorization Bundle is the single canonical input interface used by
Engineering Work Initiation to locate every artifact needed for admission,
shadow authorization, and enforcement authorization. It changes input
resolution only. It does not grant authority and does not change evaluator,
admission, baseline, policy, publication, lifecycle, replay, synchronization,
or enforcement semantics.

The machine-readable schema is
`engineering/authorization/authorization-bundle.schema.yaml`. The resolver is
`scripts/lib/work_initiation/authorization_bundle.py`.

## Contract

Every canonical bundle is a JSON or YAML mapping with:

| Field | Requirement | Consumer |
|---|---|---|
| `schema_version` | Required; integer `1` | Bundle resolver |
| `document_type` | Required; `ZeusAuthorizationBundle` | Bundle resolver |
| `admission_record` | Required non-empty file locator | Admission verifier |
| `authority_graph` | Required non-empty file locator | Compatibility evaluator |
| `wop` | Required non-empty file locator | Admission verifier and evaluator |
| `state` | Required non-empty file locator | Compatibility evaluator |
| `receipt` | Required non-empty file locator | Compatibility evaluator |
| `lease` | Optional non-empty file locator | Compatibility evaluator |
| `revocation` | Optional non-empty file locator | Compatibility evaluator |
| `expected_authority` | Optional non-empty authority-node identifier | Compatibility evaluator |

Unknown fields are rejected. Relative locators resolve against the directory
containing the bundle. Every locator is normalized to an absolute path and
must identify an existing regular file. The WOP must expose a `WOP-` identity;
that identity is derived by the resolver and supplied to admission
verification, so callers cannot independently select a different identity.

## Resolution and dependency trace

1. `eos_platform_qualify` invokes `eos_authorization_bundle_resolve` once.
2. The Python resolver validates and normalizes either the selected canonical
   bundle or the documented legacy environment inputs.
3. The normalized admission locator and resolver-derived WOP identity are
   supplied to `eos_wop_admission_require`.
4. Admission verification validates the accepted record and its repository and
   WOP bindings.
5. Legacy repository qualification, including controlled working-tree
   baseline validation, runs unchanged.
6. The same normalized object is passed to
   `eos_work_initiation_authorize`; it is not reparsed.
7. The authority graph, WOP, evaluation state, receipt, optional lease,
   optional revocation, and optional expected authority are passed unchanged
   to `work-initiation-shadow`.
8. Existing shadow/enforcement selection determines the shell result.

## Compatibility

When `EOS_AUTHORIZATION_INPUT_MANIFEST` is set, the canonical bundle is the
authority for input selection. A populated legacy variable is accepted only
when its value exactly agrees with the normalized bundle value; disagreement
is rejected as ambiguous.

When no canonical bundle is selected, the following compatibility inputs are
resolved by the same resolver:

| Legacy variable | Canonical field |
|---|---|
| `EOS_WOP_ADMISSION_RECORD` | `admission_record` |
| `EOS_SHADOW_AUTHORITY_GRAPH` | `authority_graph` |
| `EOS_SHADOW_WOP` | `wop` |
| `EOS_SHADOW_STATE` | `state` |
| `EOS_SHADOW_RECEIPT` | `receipt` |
| `EOS_SHADOW_LEASE` | `lease` |
| `EOS_SHADOW_REVOCATION` | `revocation` |
| `EOS_SHADOW_EXPECTED_AUTHORITY` | `expected_authority` |

Incomplete legacy inputs remain incomplete after normalization so the existing
admission or authorization layer produces its established fail-closed result
and, where applicable, its immutable validation-failure ADR. This path is
deprecated as an input interface but remains supported for compatibility.

`EOS_AUTHORIZATION_MODE`, `EOS_SHADOW_EVALUATION_TIME`, and
`EOS_SHADOW_ADR_DIR` configure evaluation behavior/output rather than identify
authorization artifacts and are intentionally outside the bundle.

## Failure contract

Canonical-bundle selection fails before admission with resubmission-required
exit `78` for an unreadable/corrupt bundle, wrong version/type, missing or
unknown field, invalid/unavailable locator, invalid WOP identity, or conflict
with a legacy locator. Evaluator rejection remains enforcement failure exit
`77`. No resolution failure is converted into authorization.

## Ownership and lifecycle

The Engineering Work Initiation component owns resolution and the resolved
object. Producers own the referenced artifacts; their existing schemas,
signatures, digests, lifecycle rules, and authorities remain unchanged.
Bundle creation, replacement, retention, and any future controlled-document
status require separately established lifecycle and authority.
