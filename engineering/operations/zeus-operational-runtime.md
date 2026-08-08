# Zeus Operational Runtime

> **Current lifecycle projection rule:** Zeus resolves current lifecycle
> identity, receipt operands, repository baseline, mission/WOP binding,
> provider/session identity, next action, and verification state from live
> canonical projections first, receipt-backed derived projections second,
> authoritative persisted records third, and explicitly bounded compatibility
> fallbacks only thereafter. Hardcoded current-state authority is prohibited
> when the value is available live. Immutable constants, historical literals,
> test vectors, and documented legacy fallbacks are separate categories and
> cannot override a live projection.

## Architecture and ownership

The authoritative production ownership model is
`engineering/operations/authority-ownership-specification.md`. Lawrence O'Neal,
authenticated as principal `loneal`, is the sole ultimate engineering
authority for every Zeus Operational Alpha domain. The authenticated Zeus CLI
is the authoritative interface through which he exercises that authority.
The submitted WOP is the normal operational source of work authority. Zeus
resolves, validates, reconciles, and executes within that authority;
it is not an independent authority.

For the current receipt-backed P2/P3/P4 lifecycle, the repository-bound
user-state runtime resolved by `runtime_paths.py` is the authoritative mutable
runtime. The repository is the immutable source/control plane and EOS is the
published-baseline projection. The older repository-local orchestration store
described below remains an explicit OA/engineering compatibility surface; it
does not own current canonical mission discovery.

For that legacy orchestration surface, the repository root discovered from
`scripts/zeus` defines the compatibility runtime. Its orchestration store is:

`<repository>/.zeus/runtime/orchestration-state.json`

The Zeus operator owns the file and its lifecycle. The runtime is local,
mutable operational data and is intentionally excluded from Git. It is not an
authority source for the current P2/P3/P4 lifecycle: it records orchestration
state consumed by the existing
admission, selection, approval, dispatch, qualification, reconciliation, and
closeout services. Schema version 1 is owned by
`scripts/lib/emp/orchestration.py`.

The repository mount may be read-only. `ZEUS_RUNTIME_ROOT` explicitly selects
the mutable operator-owned runtime root. The canonical platform deployment is
`/home/loneal/.local/state/zeus/homelab`; operators shall export that value in
the service or login environment. Unset preserves the repository-local default
for writable installations only. There is no implicit fallback. Read-only
controller commands never create or lock runtime files. `submit`, `admit`,
`execute`, `publish`, and `synchronize` are the only runtime mutation classes
and fail closed when the selected root is unavailable or read-only. Published
evidence remains append-only and is never repaired in place.

Current-valid reconciliation receipts are generated from live repository,
origin, EOS, runtime, mission, WOP, and predecessor-receipt projections. The
receipt records both the immutable receipt-provenance baseline and the current
published baseline. Legitimate descendant publication is reconciled through a
durable lineage receipt; historical receipts are not rewritten. Non-descendant,
forged, mismatched, or ambiguous lineage fails closed.

`--state` and `ZEUS_STATE` are retained only as explicit engineering and test
overrides. Bootstrap refuses to initialize either override unless it resolves
to the authoritative location.

Operator orientation state is separately stored at
`.zeus/runtime/operator-interface-state.json` and is owned by
`scripts/lib/emp/operator_interface.py`. It is deliberately excluded from the
strict orchestration schema because presentation history is not mission,
approval, execution, qualification, or reconciliation state. Installation,
counting, suppression, and recovery are specified in
`engineering/operations/zeus-operator-interface.md`.

## Bootstrap and initialization

From the repository root, run:

```text
scripts/zeus bootstrap operational
scripts/zeus status
```

Bootstrap fails closed unless Git identifies this exact repository and HEAD
contains the qualified Mission O baseline
`a755aeb353639550eb2ffd197e30fc03bccac90b`. It then:

1. creates the canonical schema-version-1 empty state when no state exists;
2. validates any existing state instead of replacing it;
3. performs an atomic write and deterministic reload;
4. restricts the runtime directory and files to the operator;
5. records machine-readable evidence below the selected runtime root at
   `evidence/bootstrap-evidence.json`; and
6. reports `operational_readiness: READY`.

Repeated bootstrap is safe. It validates and rewrites the same logical state
without clearing missions or lifecycle records.

## Lifecycle, recovery, and troubleshooting

The state is created by `zeus bootstrap operational`, updated atomically by Zeus, and
retained across invocations. Never hand-edit it. Backups must preserve the
state file as a unit while Zeus is idle.

If no operational state exists, run `scripts/zeus bootstrap operational`; this is the
deterministic recovery path for an uninitialized runtime. Bootstrap does not
replace corrupted or incompatible state. Preserve the failed file for
investigation, restore a known-good whole-file backup, then rerun bootstrap.
If there is no trustworthy backup, move the failed file aside under operator
control and run bootstrap to create a new empty runtime; queued and historical
records must then be reconciled from their authoritative source records.

Common failures:

- `operational state does not exist`: run `bootstrap operational`.
- `incompatible orchestration schema version`: use a compatible Zeus release
  or an explicitly qualified migration; bootstrap never guesses a migration.
- `invalid orchestration store`: preserve and restore the file; initialization
  will not overwrite corruption.
- `repository identity mismatch` or `does not contain qualified baseline`:
  use the qualified homelab checkout and baseline.
- `authoritative runtime path may not use symbolic links`: remove the path
  redirection and restore the repository-local runtime.

## Operational verification

After bootstrap, these commands discover the runtime without `--state`:

```text
scripts/zeus status
scripts/zeus show wop-template
scripts/zeus validate PACKAGE.json --repository /data/engineering/repositories/homelab
scripts/zeus explain rejection ADMISSION-RECORD.json
scripts/zeus converse status --context /tmp/zeus-context.json
scripts/zeus generate-wop INTENT --mission MISSION-ID --phase PHASE-ID \
  --repository /data/engineering/repositories/homelab --submitter OPERATOR \
  --approval-authority AUTHORITY --approval-reference REFERENCE \
  --approval-date 2026-07-25 --authority-node NODE --adr ADR \
  --immutable-wop WOP
```

Commands requiring packages or records must be supplied real qualified inputs;
runtime discovery does not relax their validation.

## Authority resolution and WOP generation modes

ZEUS-P2-003 adds two mutually exclusive generation paths.

Qualification mode is the backward-compatible default. Existing explicit
authority fields remain accepted, and omitted authority fields receive
unambiguous `PLACEHOLDER-*` values:

```text
scripts/zeus generate-wop "Qualification intent" \
  --mission ZEUS-QUALIFICATION \
  --repository /data/engineering/repositories/homelab
```

Every qualification result remains `review_required: true` and
`automatically_submitted: false`. It allocates no operational authority.

Operational mode accepts only mission/work selectors and an authenticated
principal selector:

```text
scripts/zeus generate-wop "Bounded operational intent" \
  --mode operational \
  --mission EMP-MISSION-ID \
  --work-item EMP-WORK-ID \
  --principal PRINCIPAL-ID \
  --repository /data/engineering/repositories/homelab
```

Operational mode rejects `--phase`, `--submitter`, `--approval-authority`,
`--approval-reference`, `--approval-date`, `--authority-node`, `--adr`, and
`--immutable-wop`. The Authority Resolution Runtime reads only the
integrity-qualified active publication selected by the repository-fixed
runtime contract. New publications are create-only directories below
`.zeus/runtime/authority/publications/`; the atomic
`.zeus/runtime/authority/active-publication.json` pointer binds the selected
state and artifact-manifest digests. The tracked
`engineering/authority/operational-authority-state.yaml` is a migration
fallback until the first runtime-store publication, not an activation target.

Operational resolution requires a complete mission/work item, repository
assertion, submitted-WOP binding, governing baseline, and authenticated
principal record. A signed operator approval is required only for a gate
explicitly declared by the submitted WOP. Tests may use an isolated source override only when
`ZEUS_TESTING=1`; production ignores the override.

The runtime validates ownership labels, lifecycle and qualification state,
approval scope, repository root and exact Git baseline, authority-DAG
resolution, governing-manifest digest, authentication state, placeholders,
provenance completeness, expiry, and the ARB seal. WOP rendering still requires
explicit review and performs no submission, admission, dispatch, approval, or
execution.

Because activation writes only ignored operational runtime state, publishing a
baseline does not modify the commit being published. Files are sealed `0444`
and directories `0555` after atomic promotion. The artifact set is create-only,
read-only after publication, integrity verified, and prohibited from
replacement by the publication runtime. It retains the signed envelopes,
detached signatures, activated state, and SHA-256 manifest, preserving
clean-worktree, reproducibility, auditability, and independent verification.

When authority is missing, stale, conflicting, incomplete, or invalid, Zeus
stops execution safely and reports an authority-resolution failure. Under
SPEC-0011 this is an authority restoration condition: affected controlled
records must be reconciled, the repository validated, and normal authority
resolution rerun before execution. The current runtime does not yet automate
that restoration sequence; bootstrapping never bypasses controlled
documentation.

## Unified mission admission

ZEUS-P2-007 preserves the historical admission state machine. Under the current
manual operating directive, Engineering Governance owns submission and the
admission decision. The runtime projects the Governance admission and evaluates
repository identity, repository integrity, and package integrity as independent
execution-readiness checks; it does not make a discretionary admission
decision:

```text
scripts/zeus admit-mission start --mode qualification \
  --intent "Qualification intent" --mission ZEUS-QUALIFICATION \
  --repository /data/engineering/repositories/homelab
```

Operational mode accepts mission, work-item, and principal selectors.
Execution safety is evaluated through Mission Contract resolution and
execution verification. A failure there stops execution without reversing
admission. Neither path automatically dispatches.
Stage evidence, interruption, resume, replay, failure categories, and recovery
are specified in
`engineering/operations/zeus-mission-admission-runtime.md`.

## Mission execution

ZEUS-P2-008 extends a decided admission into a persistent, checkpointed
execution state machine:

```text
scripts/zeus execute-mission start --admission-id MISSION-ADMISSION-ID
```

Qualification mode traverses validation, preparation, simulated execution, and
verification without side effects. Operational execution remains blocked at
the dispatch boundary because no commissioned execution handler is installed.
Evidence, EENS projection, idempotency, interruption, resume, cancellation,
and recovery are specified in
`engineering/operations/zeus-mission-execution-runtime.md`.

## Controlled authority publication

ZEUS-P2-004 introduces `scripts/authority-publishctl`. Publication uses
detached SSH signatures in the `zeus-authority-publication` namespace.
Production trusts only the repository-fixed policy and signer file:

```text
engineering/authority/owner-trust-policy.yaml
engineering/authority/allowed-signers
```

ZEUS-P2-014 enrolled Lawrence O'Neal's production key and `loneal` principal
through the supported enrollment action and installed registry-bound production
trust. The publication framework does not generate keys, sign envelopes, create
approvals, or authenticate a session by itself.

Review commissioning state without loading trust keys or changing files:

```text
scripts/authority-publishctl status
```

The command reports enrolled versus required ownership, allowed-signer count,
authority-source activation, required record collections, typed blockers, and
a deterministic assessment digest. After ZEUS-P2-014 activation it reports
`READY` with one enrolled owner, one signer, ten signed publications, and no
blockers.

Owner enrollment and unsigned publication preparation use:

```text
scripts/authority-ownerctl status
scripts/authority-ownerctl prepare-enrollment --help
scripts/authority-ownerctl publication-template --record-type RECORD-TYPE
scripts/authority-ownerctl prepare-publication --help
```

The complete workflow, lifecycle rules, operator approval boundary, and
recovery procedure are documented in
`engineering/operations/authority-owner-enrollment-procedure.md`.

The authenticated operator constructs each domain-specific envelope conforming to
`engineering/authority/authority-publication-envelope.schema.yaml`, calculates
the canonical payload digest and deterministic envelope identity, and signs the
canonical JSON envelope externally:

```text
ssh-keygen -Y sign -f OWNER_PRIVATE_KEY \
  -n zeus-authority-publication ENVELOPE.json
```

The private key never enters the repository or publication command. All
production envelopes use owner `Lawrence O'Neal` and signer principal `loneal`.

### Staging and readiness

```text
scripts/authority-publishctl initialize --transaction TRANSACTION
scripts/authority-publishctl stage --transaction TRANSACTION \
  --envelope ENVELOPE.json --signature ENVELOPE.json.sig
scripts/authority-publishctl verify --transaction TRANSACTION
```

`stage` verifies record-type ownership, the trusted `loneal` principal, detached
signature, revision, timestamp, payload digest, and envelope identity before a
create-only copy is accepted. Every readiness check rebuilds the candidate from
the signed envelopes; `candidate.yaml` is never trusted as input.

Readiness requires signed mission, phase, work-item, repository identity,
repository baseline, authority-node, approval, identity, governing-baseline,
and operational-configuration records. It then invokes the real Authority
Resolution Runtime against a provisional in-memory copy. Missing records,
ownership disagreement, invalid lifecycle, dependency failure, stale Git baseline,
invalid authority graph, unverified identity, or approval-scope mismatch
prevents readiness.

Authorization Decision Records use the same signed workflow but are not a
pre-WOP activation prerequisite because the authenticated operator creates one
only when an exact WOP is evaluated.

### Explicit activation

```text
scripts/authority-publishctl activate --transaction TRANSACTION
```

Activation reruns readiness, verifies that the candidate has not changed,
preserves the previous source bytes, atomically publishes the candidate, and
creates a digest-bound receipt. Only this command changes
`operationally_configured` to `true`. Staging, readiness, ARS, WOP generation,
and the runtime itself cannot enable it.

Production activation always targets
`engineering/authority/operational-authority-state.yaml`. Alternate policies
or targets are accepted only under `ZEUS_TESTING=1`.

### Rollback, revocation, and recovery

Rollback is valid only for the activation transaction while the active source
still matches its receipt:

```text
scripts/authority-publishctl rollback --transaction TRANSACTION
```

It atomically restores the exact pre-activation bytes and records a rollback
receipt. If the active bytes or saved snapshot digest changed, rollback stops
for investigation.

Revocation requires a separately signed `operational_revocation` envelope
owned by Mission Admission and bound to the activation transaction:

```text
scripts/authority-publishctl revoke \
  --envelope REVOCATION.json --signature REVOCATION.json.sig \
  --receipt REVOCATION-RECEIPT.yaml
```

Revocation sets `operationally_configured: false` without deleting published
records or history. Recovery requires a new complete signed publication
transaction; neither rollback nor revocation silently reactivates a prior
source.

Preserve the transaction directory, envelopes, signatures, readiness record,
source snapshot, and receipts as one audit unit. Never hand-edit an activated
source or transaction.
