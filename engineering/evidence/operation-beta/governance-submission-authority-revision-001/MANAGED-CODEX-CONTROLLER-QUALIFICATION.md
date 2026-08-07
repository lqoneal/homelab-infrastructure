# Managed Codex Controller Qualification

The canonical normal operator interface is:

```text
zeus codex handoff HANDOFF.md
cat HANDOFF.md | zeus codex handoff -
```

The resolver is read-only. It extracts labeled semantic assertions, resolves
repository and Operation Beta context, derives mission/WOP/gate/baseline from
authoritative records, verifies admission and execution bindings, validates
authority, and resolves the managed session. Handoff text is never an
authority source.

Session decisions are deterministic: compatible active sessions are reused,
compatible stopped sessions are resumed, no compatible session produces a
create plan, immutable incompatible sessions are not reused, and unresolved
multiple candidates block with `HANDOFF_RESOLUTION_AMBIGUOUS`.

The historical fixture `MISSION-BETA-562F443E16C69401` was preserved and was
not selected for unrelated handoff work. No provider was contacted and no
session, mission, execution, admission, or WOP state was mutated.

Focused qualification: `25/25 PASS`, including file/stdin paths, automatic
metadata resolution, active/resumable/create session paths, contradiction and
ambiguity blockers, prose non-authority, admission boundary, historical
session non-reuse, duplicate prevention, and approval convergence.

`HANDOFF_INVOCATION_REQUIRES_REDUNDANT_APPROVAL=NO` applies only to the
authoritative handoff invocation. Downstream protected approvals remain
required for separately governed admission, execution, production effects,
publication, acceptance, and closeout transitions.
