# Zeus User Guide

## Architecture and lifecycle role

`zeus` is the operator interface to the Zeus engineering platform. Its launcher
resolves the authoritative repository and invokes `scripts/zeus`. Zeus observes
authority publication, PMCT evidence, gate approval, Work Registry, EENS,
Engineering Work Orders, dispatch, and resume state without weakening their
separate contracts.

## Commands and workflows

Use `zeus --help`, `zeus help`, or `zeus help <command>`. Common observational
commands are `zeus status`, `zeus next-action`, and `zeus dispatcher status`.
The governed gate workflow is `zeus verify OA-NN` followed later by
`zeus accept OA-NN`; verification never implies acceptance. Use
`zeus accept OA-NN --reject` for the alternate explicit decision. Operator
identity is derived from the authenticated account; no operator option exists.

`zeus verify OA-02` performs the pre-execution readiness evaluation without
authorizing dispatch. Status and next-action resolve the integrity-protected
OA-02 record automatically. Current-binding PMCT qualification is reported
separately from OA-02-specific PMCT readiness; `NOT_READY` therefore identifies
the missing OA-02 demonstration or another ordered prerequisite without
invalidating the accepted OA-01 PMCT PASS.

Complete the separate OA-02 demonstration with `pmct run OA-02`. `zeus status`
and `zeus next-action` resolve its integrity-valid current-binding evidence
automatically. With no qualified production agent, a PASS advances only the
derived next action to `QUALIFY_PRODUCTION_AGENT`; the dispatcher remains
prepared and inactive and operational dispatch remains disabled.

`zeus authority status` and `zeus authority work-lifecycle` are observational
JSON surfaces used by PMCT to demonstrate publication and gate-lifecycle
resolution. They never publish authority or record a gate decision.

## Production agent qualification

`zeus agent status` and `zeus agent registry` display the integrity-validated
runtime registry. `zeus agent qualify` evaluates the authenticated local
agent's identity, repository access, current published baseline and authority,
OA-01 decision, OA-02 PMCT binding, runtime dependencies, security, EENS, and
execution capabilities. Successful qualification is append-only and
idempotent for the same binding. `zeus agent revoke AGENT-ID` appends a
revocation linked to the preserved qualification; it never overwrites history.

The tracked empty registry is the schema/bootstrap baseline. Mutable
qualification and effective-registry records live beneath
`.zeus/runtime/agents/` so qualification cannot change repository HEAD or
create a publication loop. A stale qualification remains historical evidence
but is ineligible when HEAD, published baseline, authority publication, or
PMCT run changes. Qualification does not authorize dispatch.

Authority baselines are managed by `scripts/authority-publishctl`. PMCT supplies
gate evidence. Work Registry records controlled engineering work. EENS and
dispatch remain unavailable until independently qualified. Resume commands
continue only from recorded lifecycle state.

## Troubleshooting and evidence

Exit `2` indicates invalid command syntax; `78` indicates a failed prerequisite or
governed-state error. Run `scripts/install-engineering-cli verify` when command
discovery fails. Runtime evidence is beneath `.zeus/runtime/`; PMCT evidence is
beneath `engineering/runtime/pmct/runs/`. See the PMCT User Guide and
Engineering CLI Standard in this directory.
