# Zeus Execution Lifecycle Submission Contract Investigation

Date: 2026-08-07

## Result

The failure is a submission-routing and contract-convergence defect, not
evidence that the lifecycle WOP requires a second generic approval.

The current lifecycle source is a valid legacy-compatible Development WOP. It
is not currently a canonical Phase-1 authored-WOP output because its adjacent
immutable traceability record is absent. Independently, the observed command
used `--repository`, which causes `scripts/zeus` to skip the newer P2 route
before it performs source classification. The command therefore enters the
legacy admission-record path, whose CLI guard requires `--approval`.

The preferred target is an identity-preserving canonicalization boundary for
new Development sources, selected before legacy argument handling. `zeus
submit` should deterministically promote a valid source into the canonical
Phase-1/P2 provenance contract, preserve the original source bytes and digest,
and stop at `ADMISSION_REQUESTED`. Historical legacy records remain supported
through an explicit compatibility path and are never rewritten.

## Verified starting state

- Repository root: `/data/engineering/repositories/homelab`.
- Repository identity: `git@github.com:lqoneal/homelab-infrastructure`;
  repository fingerprint `6bd83f9079d6fc5780ca2cb9a93060778a899cd97e82ef3d708f91a42dbda02d`.
- `HEAD == origin/main == 32796dffb43a47f4f9516a0936fe89f0bec0ee80`.
- Index is empty; all existing modified and untracked paths were preserved.
- EOS synchronization validation passed.
- Lifecycle source SHA-256 is
  `460a4baeca153b05ee2cb0ade4a70a03b8ff2b8ca9e17a9074d0e44137d392d9`.
- The lifecycle source is untracked pre-existing work. It was not edited.
- No lifecycle-specific submission, admission, or execution record was
  found. No CAGF-01 artifact was edited by this investigation.

Read-only commands `zeus wop validate`, `zeus wop lint`, and metadata
`zeus wop inspect` pass. `zeus wop identity`, `readiness`, `traceability`,
`snapshot`, and `verify` fail closed because
`source-wop.md.traceability.json` does not exist. This is the expected
distinction between schema-valid Development source and Phase-1 authored
output.

## Direct answers

1. **Is the lifecycle WOP currently a valid canonical authored WOP?**

   No. It is valid against `development-wop/1`, but it lacks the immutable
   Phase-1 authoring provenance required by `submission_boundary.py`.

2. **Why not?**

   The source has no adjacent traceability sidecar containing authoring output
   identity, Operation Beta, repository identity, source digest, template and
   context digests, output digest, readiness, validation, and source-to-output
   mapping. The P2 branch is selected only by sidecar presence, then verifies
   those facts.

3. **Is it valid only as a legacy Development source?**

   In the current implementation, yes. With no sidecar and no explicit legacy
   admission-record arguments, it follows source packaging and the current
   Development Stage-1 lifecycle. With `--repository`, it is not treated as a
   Development source at all; the CLI enters the older admission-record
   orchestration path.

4. **Does `zeus wop init` intentionally produce legacy-compatible input?**

   Yes. The CLI comment identifies `--wop-id/--mission-id` template mode as a
   compatibility path, and the `init` implementation writes only Markdown or
   DOCX. It does not invoke the structured authoring service and does not
   write a traceability sidecar.

5. **Is there a supported promotion command?**

   No supported `promote`, `canonicalize`, or `author-existing` command was
   found. `wop template <MISSION-SOURCE.yaml>` is an authoring operation that
   derives a new deterministic WOP/Mission identity; it is not an
   identity-preserving promotion of this source. `wop template --from` copies
   metadata but still does not emit the Phase-1 receipt.

6. **Should `zeus submit` adapt the source?**

   Yes, but only through a deterministic, explicit normalization contract that
   verifies all required semantic facts and preserves the source digest. It
   must not infer authority, invent approval, silently change identity, or
   bypass admission and downstream controls.

7. **Is the routing behavior intentional or incomplete?**

   The existence of a legacy compatibility path is intentional. The silent
   choice of that path based on the presence of `--repository` is incomplete
   convergence: it prevents a source WOP from reaching the canonical route and
   produces a misleading generic approval error.

## Preferred remediation

Implement Option 2 with an explicit classifier and compatibility guard:

1. Resolve the input source first.
2. Classify it as `CURRENT_AUTHORED`, `CURRENT_CANONICAL_PACKAGE`,
   `DEVELOPMENT_SOURCE_PROMOTABLE`, `LEGACY_SUPPORTED`, or `INVALID` using a
   complete contract—not merely sidecar existence.
3. For a current authored or promotable Development source, construct the
   Phase-1 provenance projection in an isolated deterministic workspace. Bind
   the existing WOP ID, Mission ID, repository identity, source digest,
   template/schema version, context digest, output digest, and semantic
   source-to-output mapping. Preserve the original source byte-for-byte.
4. Enter the existing P2 submission boundary and create one deterministic
   submission receipt plus one admission-request projection. Do not run
   Mission Admission or execution.
5. If legacy-only flags are supplied for a current source, either normalize
   only an explicitly matching repository value or fail with an actionable
   `LEGACY_ARGUMENTS_NOT_VALID_FOR_CURRENT_SOURCE` error. Do not silently route
   to the legacy path.
6. Keep the old admission-record path available only as an explicit
   compatibility path for actual legacy admission records.

The expected successful submission result is `submission_result=PASS`,
`submission_state=ADMISSION_REQUESTED`, a deterministic receipt, and
`next_action=EVALUATE_MISSION_ADMISSION`. It must not return an admission ID,
execution ID, provider/session identity, or generic approval request. A later
explicit admission command may produce `ADMISSION_COMPLETE` and
`EVALUATE_BOOTSTRAP_ELIGIBILITY`; that is outside this submission boundary.

## Remediation boundary

The original lifecycle source need not be regenerated or edited. The
canonicalizer must preserve its bytes and expected digest. A generated
canonical/provenance representation may exist in temporary or governed
derived storage, but it must retain the source as immutable provenance and
must preserve the declared WOP/Mission identities. Blindly running the
current structured authoring command would be incorrect because it derives a
new hash-based identity.

Historical WOPs, admission records, receipts, evidence, and runtime records
remain immutable. They may be read through a deterministic compatibility
adapter, but never rewritten or reclassified in place.

## Required completion boundary for the remediation

After implementation, Zeus-native verification should independently expose:

- the lifecycle Mission ID, WOP ID, and package/source digests;
- `SUBMITTED` / `ADMISSION_REQUESTED` lifecycle state;
- `operator-submitted WOP` authority;
- `NOT_REQUIRED_UNLESS_DECLARED_IN_WOP` approval state;
- any explicit in-WOP approval gate as a separate blocker;
- repository, baseline, source, output, and provenance checks;
- deterministic submission and replay identities;
- `EVALUATE_MISSION_ADMISSION` as the next action.

No submission, admission, dispatch, execution, publication, synchronization,
or CAGF-01 mutation was performed by this investigation.
