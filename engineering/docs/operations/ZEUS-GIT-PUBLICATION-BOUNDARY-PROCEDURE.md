# Zeus Git Publication Boundary Procedure

This procedure keeps prepublication work off canonical `main` and makes any
publication to `main` an explicit governed operation.

Before committing, verify the canonical repository, non-`main` branch, active
publication WOP, intended file scope, and clean remote ancestry. Run:

```text
scripts/zeus-publication-boundary-guard --operation commit --target-ref refs/heads/<candidate>
```

Before pushing, verify the exact refspec and branch again, then run:

```text
scripts/zeus-publication-boundary-guard --operation push --target-ref refs/heads/<candidate>
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
