# Zeus Git Publication Boundary Procedure

This procedure keeps prepublication work off canonical `main` and makes any
publication to `main` an explicit governed operation.

## Git automation contract

Machine consumers MUST use `scripts/zeus repository projection --json` for
current repository/EOS state where the projection covers the required facts.
The projection is read-only and derives live identity, explicit `HEAD` and
`origin/main`, parity, index/worktree state, and EOS parity. It uses
machine-oriented Git interfaces, exit-code boolean checks, NUL-safe path
collections, and explicit refs. Unattended Git operations use
`GIT_TERMINAL_PROMPT=0`; operator-interactive publication is not converted to
an unattended credential flow.

Lifecycle receipts retain immutable transition provenance. They do not become
hardcoded current repository authority. Current state is resolved from the
canonical live projection, then receipt-backed or persisted evidence, with
compatibility fallbacks explicitly bounded and subordinate. Conflicting or
unavailable live state fails closed.

## Repository baseline states during publication

Steady state is fully converged: `HEAD == origin/main == EOS`. The canonical
repository projection also recognizes two bounded transitional states, but
only from one repository-bound Zeus publication transaction with passing
integrity and an immutable receipt for its current milestone:

- `COMMIT_CREATED` / pre-push: `HEAD` is the transaction `commit_id`;
  `origin/main` and EOS remain the equal recorded starting baseline; the
  remote baseline is an ancestor of `HEAD`; branch, repository, mission, WOP,
  runtime, index, cohort, and receipt bindings all match. Its next action is
  `PUSH_PUBLICATION`.
- `REMOTE_PUBLISHED` / pre-EOS-sync: `HEAD == origin/main == commit_id`; EOS
  remains the recorded starting baseline; the passing `REMOTE_PUBLISHED`
  receipt binds the exact commit and `refs/heads/main`. Its next action is
  `SYNCHRONIZE_EOS`.
- `EOS_SYNCHRONIZED`: `HEAD == origin/main == EOS == commit_id`; the passing
  EOS synchronization receipt restores full baseline parity.

These classifications preserve the immutable provenance baseline of an
existing P3 admission. P3 is not recreated against each transient `HEAD`;
its provenance must remain reachable and ancestral while the current
divergence is independently authorized for the same mission and WOP.

An ahead commit, stale or unrelated transaction, wrong commit/identity,
missing receipt, invalid transaction integrity, non-ancestor branch movement,
EOS drift, mismatched mission/WOP, or contradictory transaction cardinality
remains invalid. Git ancestry by itself never grants publication authority.
Status and replay projections are read-only and must not push, synchronize
EOS, or rewrite lifecycle evidence merely to prove transitional validity.

Before committing, verify the canonical repository, non-`main` branch, active
publication WOP, intended file scope, and clean remote ancestry. Run:

```text
python3 scripts/zeus-publication-boundary-guard --operation commit --target-ref refs/heads/<candidate>
```

Before pushing, verify the exact refspec and branch again, then run:

```text
python3 scripts/zeus-publication-boundary-guard --operation push --target-ref refs/heads/<candidate>
git push origin HEAD:refs/heads/<candidate>
```

The guard rejects commits on `main`, pushes to `main` without the explicit
governed publication authority marker, detached HEAD, unexpected refspecs,
unresolved origin, and dirty push state. It does not infer authority from a
Codex session or a WOP identifier.

If a candidate reaches `main` accidentally, preserve the exact commit on a
dedicated branch before any correction, verify its authorized parent from EOS
and publication records, use a normal `git revert`, push the revert, synchronize
EOS, and record the incident. Never force-push, reset, conceal, or delete the
candidate. The preserved candidate remains unpublished and follows the normal
qualification and publication approval workflow.
