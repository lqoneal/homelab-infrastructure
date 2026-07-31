# Metadata Migration Runtime Architecture

Status: `PROPOSED LOGICAL EXECUTION CONTRACT — NON-AUTHORITATIVE`

| Phase | Execution behavior | Rollback/recovery |
|---|---|---|
| Plan | resolve source/target schema, mapping version, owners, consumer compatibility, and reversibility | reject incomplete or ambiguous plan |
| Snapshot | seal source input manifest and consumer adoption bindings | retained immutable recovery point |
| Transform | apply deterministic mapping into a successor fact or derived compatibility view | source remains unchanged |
| Validate/qualify | execute schema, ownership, lineage, compatibility, and projection checks | failed target is unpublished; evidence retained |
| Publish/adopt | publish qualified successor; consumers adopt explicitly in dependency order | no implicit consumer upgrade |
| Roll back | repoint consumer adoption to prior qualified compatible binding | published successor remains historical lineage |
| Restart/reconcile | replay transformation from sealed manifest; rebuild derived targets and compare digests | open discrepancy until expected manifests match |

Cross-major migration cannot proceed without an explicit qualified mapping. An irreversible migration permits recovery by replaying historical sources and adoption bindings, not by overwriting authoritative history.
