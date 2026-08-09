# Controlled-Document Reconciliation

The previous controlled text described stopped/non-authoritative runtime repair
as wrapper supersession and successor creation. That language encoded the same
transport/thread conflation as the implementation.

Minimum authoritative changes were made to:

- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`
- `engineering/docs/cli/ZEUS-USER-GUIDE.md`
- `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md`

The documents now define Zeus execution identity, ephemeral Codex transport
identity, persisted native thread identity, native resume/fork semantics,
new-thread authority, fail-closed behavior, remote recovery, replay, and the
single managed `codex resume` recovery command. Historical evidence was not
rewritten.
