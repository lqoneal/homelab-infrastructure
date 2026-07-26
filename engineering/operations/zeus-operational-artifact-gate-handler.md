# Zeus Operational Artifact Gate Handler

## Purpose and boundary

ZEUS-P2-010 provides the first operational-grade handler implementation for the
P2-009 Gate Handler Framework. It executes bounded, declarative artifact gates
inside an isolated workspace. It does not execute shell commands, modify the
repository, allocate authority, approve WOPs, commission production, or expose
a production dispatcher.

The handler is operational-only. Qualification uses an isolated authoritative
fixture, temporary workspace, and an explicitly injected runtime boundary that
is unavailable from the Zeus CLI.

## Operational execution context

`OperationalExecutionContextService` builds an immutable context containing:

- execution and mission identity;
- repository identity and exact Git baseline;
- WOP submission digest;
- isolated workspace;
- validated gate plan and digest;
- execution authorization binding; and
- context digest.

The workspace must be outside the repository. Authorization must be explicitly
`AUTHORIZED` and bound to the execution identifier. Context or plan mutation
fails its digest check.

## Supported actions

Version 1.0 supports only:

- `create_artifact`: create-only UTF-8 text at a safe relative path; and
- `verify_artifact`: verify an existing artifact against its declared digest.

Absolute paths, traversal, duplicate action identifiers, unsupported actions,
missing content digests, repository workspaces, and conflicting existing files
fail closed.

This intentionally narrow contract excludes command execution, deletion,
overwrite, network access, package installation, service changes, and other
irreversible actions.

## Verification-first lifecycle

Before each gate the handler verifies:

1. context and gate-plan digests;
2. cancellation state;
3. runtime/WOP/execution binding;
4. exact repository HEAD;
5. explicit execution authorization;
6. gate definition and dependencies; and
7. durable action checkpoints.

It then determines pending actions, skips checkpointed actions, executes each
required action, records its checkpoint, and verifies every resulting artifact
and the complete checkpoint.

Each action result records disposition, artifact reference, and content digest.
The framework adds handler identity/version, verification-first trace,
disposition, retry diagnostics, and result verification to Mission Execution
evidence and EENS projection.

## Checkpoints, interruption, and resume

Action checkpoints are stored beneath the isolated workspace:

`<workspace>/.zeus-checkpoints/<execution-id>/<gate-id>.json`

Each checkpoint is digest protected and records action/result-digest pairs.
Resume reads the checkpoint and excludes completed actions. Conflicting
results, mutation, or incomplete post-verification fail closed.

The handler checks cancellation before each action. A `.cancel-requested`
sentinel in the isolated workspace provides the qualified cooperative
cancellation boundary. Mission-level waiting, suspension, resume, cancellation,
and gate checkpoints remain owned by Mission Execution Runtime.

## Capability and activation boundary

The manifest at `engineering/handlers/operational/artifact-handler.yaml`
declares operational mode, mutation, action checkpoints, artifact creation and
verification, and all required framework capabilities.

Registration and discovery do not enable execution. The default runtime still
stops with `OPERATIONAL_DISPATCH_DISABLED`, and no CLI option can change that.
A future commissioning transaction must provide authentic accepted admission,
execution context, handler framework, and explicitly enabled runtime boundary.

## Recovery

Preserve the execution state, evidence chain, EENS events, workspace,
artifacts, and checkpoint directory as one audit unit. Do not edit checkpoints
or artifacts to force resume. Resolve a dependency, cancellation, or integrity
failure through a new verified input or separately reviewed recovery action.

## Controlled-document disposition

This guide documents qualified software capability. It does not activate
production or authorize operational mission dispatch.
