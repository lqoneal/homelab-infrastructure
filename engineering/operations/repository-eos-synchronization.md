# Repository–EOS State Synchronization

## Authority

`engineering/eos/repository-eos-authority.yaml` is the machine-readable
authority matrix for repository–EOS integration. It assigns exactly one owner
and one classification to every synchronized record.

The repository owns engineering state. EOS does not independently author
project, registry, execution-interface, approval, or controlled-document
state. EOS projects repository state for runtime consumption.

## Synchronization contract

`engctl eos synchronize [project]` performs a one-way projection:

1. validate the authority-matrix schema and all canonical sources;
2. render `EOS-ID.md` and `EOS-STATE.md` from repository identity and
   `PROJ-0001`;
3. render `EOS-MANIFEST.md` with exact source and projection SHA-256 digests;
4. atomically replace only changed derived projections;
5. refresh the EOS runtime cache; and
6. validate the synchronized result.

The projector uses temporary sibling files and atomic replacement. A repeated
run over unchanged inputs is byte-identical and reports no changes. Unsupported
schema versions, missing sources, invalid project metadata, or canonical
authority ambiguity fail before mutation.

`engctl eos sync-validate [project]` is read-only. It renders the expected
projection in memory and compares exact bytes and digests with EOS. Drift in a
derived projection is repairable by synchronization. Repository authority is
never replaced from EOS.

Checkpoint metadata, the active-checkpoint pointer, and retention configuration
remain EOS runtime records. They cannot override Project State or the Work
Registry. Checkpoints are append-only evidence bound to repository identity
and commit.

## Integrated qualification

Validation executes in this order:

1. repository validation;
2. repository–EOS synchronization validation;
3. EOS runtime and persistence validation;
4. integrated platform validation.

Resume executes the same verification sequence, automatically repairs only
derived/cache drift, and then renders repository mission context. A failure in
repository authority or runtime evidence stops resume.
