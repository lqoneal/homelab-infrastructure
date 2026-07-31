# Generated Documentation Architecture

Status: `PROPOSED — NON-AUTHORITATIVE`

## Gate Catalog composition

| Catalog content | Classification | Canonical source |
|---|---|---|
| Purpose, Engineering Objective, Architectural Rationale | Authored | controlled gate package and roadmap owner |
| Zeus Capability Evolution, Operator Guidance | Authored | capability/documentation owner |
| Lifecycle State Model, Transition and Dependency Matrices | Generated | gate metadata, state/transition declarations |
| Reachability, Cycle, and Ownership Analysis | Generated | dependency graph and ownership metadata |
| Capability Matrix, Verification Command Index, Cross References | Generated | capability and verification metadata |
| Qualification Status | Generated view of Historical records | receipts, evidence, qualification records |

The generator must label every generated block with generator version, source
manifest digest, generated-at time, and output digest. Human edits to a
generated block are drift and must be replaced on regeneration; edits belong
in the source metadata or authored section.

## Required authored metadata

```yaml
artifact_id: OA-XX
classification: Authoritative | Derived | Runtime | Historical
authoritative_owner: subsystem-or-role
source_artifacts: [stable-identities]
synchronization:
  direction: source-to-target
  mechanism: generator | event | pull | checkpoint-replay
  owner: subsystem-or-role
  trigger: source-revision
  verification: digest-and-semantic-predicate
  drift_detection: source-target-manifest-comparison
  reconciliation: source-owner-corrects-then-regenerates
  recovery: rebuild-from-last-valid-source-manifest
canonical_zeus_interface: [zeus, gate, show]
```

The schema is a future target; existing hand-authored documents remain
transitional until their metadata is present and a generator is qualified.
