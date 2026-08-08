# Runtime Convergence Report

The new resolver is read-only and is the common mission-view path for a
canonical P2 mission. It consumes existing boundary validators rather than
creating another lifecycle store:

```text
P2 submission receipt + admission request
        -> identity/digest verification
        -> optional P3 admission transaction/artifacts
        -> optional P4 bootstrap transaction/artifacts
        -> one canonical state/action projection
```

P3 and P4 artifacts must preserve Mission ID, WOP ID, submission ID, and the
preceding transaction identity. Duplicate canonical records are rejected.
Downstream evidence cannot make an absent P2 submission discoverable. Legacy
Stage 1 material is surfaced as compatibility evidence and excluded from
current lifecycle ownership.

No admission, bootstrap, provider, session, execution, or repository/EOS
mutation was performed for the parent mission.
