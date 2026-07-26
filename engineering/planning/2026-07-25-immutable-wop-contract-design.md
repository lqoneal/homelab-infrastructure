# Immutable Work Package Authority Contract

Date: 2026-07-25
Status: Offline contract implementation; no execution authority
Mission: Zeus Operational Alpha Mission E

## Boundary

The Immutable Work Package (WOP) is a machine-readable authorization contract
for future engineering execution. During Mission E it is an offline model only.
No live subsystem consumes it and no fixture authorizes execution.

## Immutable contract

A WOP binds exactly one authority node, mission, phase and work item. It also
contains:

- a globally unique UUID-based WOP identity;
- repository, commit, branch and principal execution constraints;
- explicit assumptions;
- bounded authorized-effect entries with constraints;
- explicit prohibited-effect identifiers;
- prerequisite evidence requirements;
- required WOP dependencies;
- validity and expiration times;
- lease and revocation policies;
- canonical payload digest;
- signature interface fields.

The Python model is frozen. The persisted payload is protected by a canonical
SHA-256 digest. Any post-publication payload change invalidates the digest.

## External state objects

Publication, leasing and revocation are separate immutable objects bound to the
WOP identity and digest:

- **Publication Receipt** proves which immutable payload was published and when.
- **Execution Lease** binds a principal to a time-bounded use of that payload.
- **Revocation Record** terminates authorization without mutating the WOP.

This separation prevents lifecycle or execution state from rewriting the
authorization contract.

## Execution Context

Offline evaluation supplies observed prerequisite evidence, completed
dependencies, requested effects, principal, repository, baseline commit and
branch. These observations must exactly satisfy the immutable WOP constraints.

## Authorized Effect Manifest

Each authorized effect has a stable identifier, effect kind, target and at
least one constraint. Requested effects must be a subset of this manifest and
must not intersect the prohibited-effect manifest.

## Signature interface

The contract defines a `SignatureVerifier` protocol:

```python
verify(algorithm, key_id, signature, payload_digest) -> bool
```

No trust store or production cryptography is embedded. A future consumer must
supply a separately qualified verifier. Structural validation still requires
algorithm, key identity and signature value.

## Determinism and failure behavior

Serialization sorts mapping keys and emits canonical JSON or stable YAML.
Evaluation reasons and requested effects are sorted. Repeated evaluation of the
same WOP, receipt, state, lease, revocation and timestamp yields an identical
decision.

Missing bindings, malformed context, digest mismatch, unauthorized effects,
unsatisfied prerequisites/dependencies, absent/expired lease, expiration or
valid revocation produce a denied decision. Validation and evaluation fail
closed.

## Interfaces

```text
scripts/wopctl validate WOP
scripts/wopctl serialize WOP --format json|yaml
scripts/wopctl evaluate WOP STATE RECEIPT [--lease LEASE]
  [--revocation REVOCATION] --at TIMESTAMP
```

Future integration with the Authority Resolution Engine is reserved for
Mission F.
