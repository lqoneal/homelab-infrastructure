# Repository–EOS State Synchronization

## Authority

`engineering/eos/repository-eos-authority.yaml` is the machine-readable
authority matrix for repository–EOS integration. It assigns exactly one owner
and one classification to every synchronized record.

The repository owns engineering state. EOS does not independently author
project, registry, execution-interface, approval, or controlled-document
state. EOS projects repository state for runtime consumption.

EOS is therefore a derived projection, never an authority over repository
state. A repository working-tree change, commit, or push does not implicitly
invoke synchronization. Synchronization is a separate, explicitly authorized
operation and always flows from repository sources to EOS.

The canonical mutable EOS workspace for this read-only repository deployment
is `/home/loneal/.local/state/zeus/eos-workspace`, selected explicitly with
`EOS_WORKSPACE`. Its `repositories/homelab` entry resolves to the immutable
repository checkout; only derived EOS state, caches, checkpoints, and atomic
pointers persist in the writable workspace. `/data/engineering/eos` is a
legacy read-only projection and is not a synchronization target on this host.

## Projection semantics

- **Working-tree projection:** the EOS bytes that would be rendered from the
  currently selected repository working tree; a validation-only view until an
  authorized synchronization occurs.
- **Committed projection:** the EOS bytes that would be rendered from the
  selected local commit and its repository-authoritative records.
- **Published projection:** the EOS bytes that would be rendered from the
  repository baseline that completed its authorized publication operation.
- **Synchronized EOS projection:** the EOS bytes actually persisted by an
  authorized `engctl eos synchronize` operation and verified against the
  selected authoritative repository baseline.

These states may legitimately differ between publication and synchronization
boundaries. Neither a working-tree nor an EOS runtime view supersedes committed
or published repository content.

## Publication synchronization boundaries

Every publication procedure shall identify these boundaries before execution:

1. **Initial Validation Boundary:** read-only repository identity, baseline,
   health, registry, package, diff, and EOS comparison before publication.
2. **Publication Boundary:** the exact authorized repository transaction. EOS
   synchronization is not part of this boundary unless separately authorized.
3. **Synchronization Boundary:** the separately authorized point at which a
   selected committed or published repository baseline may project to EOS.
4. **Final Validation Boundary:** read-only verification of the final
   repository baseline and, when synchronization was authorized and performed,
   exact verification of the synchronized EOS projection.

Publication may contain multiple commits and one later Synchronization
Boundary. Drift between an intermediate repository commit and the last
synchronized EOS projection is expected and shall not be repaired merely to
make an intermediate validation green.

## Drift classification and operator action

| Classification | Meaning | Required operator action |
| --- | --- | --- |
| `EXPECTED_PUBLICATION_DRIFT` | Repository authority advanced inside an authorized publication sequence, but the declared Synchronization Boundary has not been reached. | Record compared baselines, continue only within the approved plan, and do not synchronize. |
| `SYNCHRONIZATION_REQUIRED` | The declared Synchronization Boundary has been reached and the authorized repository baseline is ready to project. | Stop publication advancement and obtain or verify explicit synchronization authority and prerequisites. |
| `SYNCHRONIZATION_FAILURE` | An authorized synchronization was attempted but did not complete or its exact post-check failed. | Stop, preserve repository authority and evidence, diagnose EOS projection/runtime state, and retry only under applicable authority. |
| `AUTHORITATIVE_SOURCE_FAILURE` | Repository identity, source schema, source content, registry, package, diff, or required repository validation failed. | Stop; correct the repository-authoritative source under separate change authority. Do not use EOS to repair the repository. |
| `RUNTIME_STATE_FAILURE` | Repository sources and deterministic projection validate, but EOS runtime, checkpoint, cache, or persistence validation fails. | Stop runtime-dependent work; preserve repository state and repair only the affected EOS runtime record under operational authority. |

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
derived projection is repairable by synchronization only at an authorized
Synchronization Boundary. Repository authority is never replaced from EOS.

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

Outside an active publication sequence, resume may execute the same
verification sequence and automatically repair only derived/cache drift when
its invocation carries the established operational synchronization authority.
Publication procedures shall not use an auto-repairing resume command for
boundary validation. A failure in repository authority or runtime evidence
stops resume.

## Synchronization authority and prerequisites

EOS synchronization may be invoked only by the operator or automation identity
explicitly named by the active handoff, Work Order, publication authorization,
or Engineering Platform operational authority. Repository write, commit,
push, publication, validation, or executor authority does not imply EOS
synchronization authority.

Before invocation, record and verify:

1. repository identity and selected full commit;
2. completion of all publication units assigned before the Synchronization
   Boundary;
3. repository health, registry validity, required package verification, and
   diff or committed-path verification;
4. absence of an authoritative-source failure; and
5. the exact project and EOS projection targets.

After invocation, run read-only synchronization validation, EOS state and
persistence validation, and the applicable integrated platform validation.
Record exact repository and synchronized projection identities. A post-check
failure is `SYNCHRONIZATION_FAILURE` or `RUNTIME_STATE_FAILURE`, not permission
to modify repository authority.
