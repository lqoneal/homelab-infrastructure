# CR12 — Define Interruption and Replay

## Result

**COMPLETE**

## Objective

Define deterministic recovery behavior when roadmap lifecycle processing is
interrupted or an already-started lifecycle transaction is replayed.

## Outcome

CR12 established an explicit interruption model covering the lifecycle from
gate execution through result recording, operator review, operator acceptance,
atomic completion, and successor activation.

Recovery does not infer acceptance or completion merely because an artifact
exists.

## Material Decisions

- Every interruption point has a deterministic classification.
- Recovery uses validated authoritative artifacts and exact identity bindings.
- Exact replay is resumable or returns `ALREADY_APPLIED`.
- Conflicting replay fails closed.
- `validate`, `evaluate`, `status`, and `resume` remain read-only.
- Mutating recovery requires an explicit mutation interface.
- Recovery may finish only the interrupted lifecycle transaction.
- Recovery never executes successor work automatically.
- EOS synchronization, EOS refresh, commit, push, and publication remain
  explicit external actions.

## Zeus Development Opportunities

CR12 reinforces several future Zeus capabilities:

- native roadmap and corrective discovery;
- lifecycle interruption classification;
- replay-identity inspection;
- deterministic recovery recommendation;
- read-only recovery visibility through Zeus status/resume interfaces.

These opportunities are inputs to future roadmap maintenance. They do not
authorize implementation during CR12.

## Implementation

Controller modified: **NO**

engctl modified: **NO**

Implementation authorized: **NO**

## Validation

Interruption classification: **PASS**

Replay semantics: **PASS**

Fail-closed conflicting replay: **PASS**

Read-only recovery boundary: **PASS**

Successor execution boundary: **PASS**

## Next Authorized Item

**CR13**
