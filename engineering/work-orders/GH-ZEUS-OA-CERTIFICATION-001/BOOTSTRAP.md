# GH-ZEUS-OA-CERTIFICATION-001 Historical Bootstrap

Status: Retired and non-executable.

This package is preserved as historical engineering evidence. It was
superseded by `GH-ZEUS-OA-PROGRESSIVE-001`; none of its gate sequencing,
PMCT mappings, admission state, or instructions may be used to resolve current
Operational Alpha work.

This directory was the execution package for Zeus Operational Alpha
certification. `submission.yaml`, its ACCEPTED admission record, and
`immutable-wop.yaml` establish eligibility; none of them records OA execution,
operator acceptance, a PMCT transition, baseline freeze, or OA-30 completion.

## Historical binding order

The following is retained only to explain the superseded package. It is not an
active execution procedure.

1. Verify repository identity, `main`, exact admitted baseline, clean worktree,
   `origin/main` alignment, EOS synchronization, Project State, PMCT state, Work
   Registry integrity, package checksums, and the ACCEPTED admission record.
2. Execute gates OA-01 through OA-30 strictly in numeric order using
   `engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml`,
   `PMCT-CONTRACT.md`, and `PMCT-OPERATOR-GUIDE.md`.
3. For every gate, collect the evidence in `templates/gate-evidence.yaml`;
   reruns with the same run identity must be observational or return the
   existing result and must never duplicate decisions or transitions.
4. OA-01 requires an independent human operator to run and witness verification,
   then create either an ACCEPT or REJECT record from
   `templates/operator-decision.yaml`. A PMCT PASS is not acceptance.
5. OA-02 through OA-30 are ineligible until every preceding gate has current,
   integrity-valid PASS evidence and required acceptance. Manual demonstrations
   and witnessed tests use the matrix positive, negative, idempotency, safety,
   and regression criteria without substitution.
6. A controlled PMCT mutation is permitted only by the repository PMCT/Zeus
   command named by the current operator guide, after pre-state evidence is
   persisted. Never hand-edit capability state, run records, verification
   records, approvals, receipts, or authority publications.
7. A failure, rejection, ambiguity, stale baseline, missing witness, checksum
   mismatch, interrupted write, or reconciliation conflict stops progression.
   Preserve evidence and generate a separately authorized corrective work item
   using `templates/corrective-work.yaml`; corrective work cannot be executed
   under this WOP.
8. After each accepted gate, reconcile controlled documents, Project State,
   Work Registry, EOS, and checkpoint only through their owning procedures and
   commands. Conflicts fail closed; do not rewrite history.
9. On interruption, do not infer completion. Re-run `verify-package.sh`, inspect
   the last durable completion marker and PMCT state, verify checksums, and
   resume at the first gate lacking complete accepted evidence.
10. After OA-01 through OA-29 are accepted and OA-30 passes its own witnessed
    criteria, prepare—but do not make—the OA-30 completion declaration. OA-30
    completion declaration requires separate, explicit authorization.
11. Final OA baseline freezing is a distinct post-certification transaction.
    Prepare the candidate inventory and manifest, then stop. A separately
    authorized action must freeze, tag, publish, or activate it.

## Evidence persistence

Evidence is append-only beneath the repository evidence location selected by
the PMCT runtime. Each gate bundle must include exact repository SHA, authority
and publication bindings, commands, stdout, stderr, exit status, timestamps,
witness identity, assertions, before/after state, reconciliation results,
SHA-256 manifest, and an atomic completion marker. Secrets and credentials must
not be captured.

## Rollback and recovery

There is no rollback by deletion or state editing. If a command fails before
its atomic completion marker, retain the partial run, classify it incomplete,
restore only through the owning recovery procedure, and rerun with a new run
identity. If a controlled transition completed but reconciliation did not,
freeze further progression and reconcile from the durable authoritative record.
Any unsafe or unexplained state requires operator escalation and corrective
work authorization.

## Completion boundary

This WOP completes only when every gate has valid accepted evidence, controlled
records agree, a completion report exists, and separate authority has declared
OA-30 completion and frozen the final baseline. Admission alone merely makes
GH-ZEUS-OA-CERTIFICATION-001 eligible to begin.
