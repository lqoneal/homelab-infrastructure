# EMP Supervised WOP Dispatch

Date: 2026-07-25
Status: Supervised dispatch implementation
Mission: Zeus Operational Alpha Mission J

## Boundary

Mission J adds one controlled boundary crossing after Mission I. The lifecycle
manager continues to terminate at `Ready`. A separate dispatch ledger records
the single legal `Ready → Dispatched` transition after successful immutable
assignment delivery.

`Dispatched` is terminal for this subsystem. There is no execution, monitoring,
command streaming, execution lease, automatic retry, recovery, evidence
qualification, completion reconciliation, autonomous selection or autonomous
dispatch interface.

## Execution Assignment

The Execution Assignment (EA) is canonical JSON with a deterministic UUIDv5
identity and SHA-256 checksum. It binds the mission, WOP and WOP digest,
repository identity and baseline, authority chain, Zeus ADR digest, required
capabilities, intended agent, expected evidence, dispatch timestamp and human
approval reference.

Identical canonical inputs reproduce the same EA byte-for-byte. Assignments are
delivered with create-only semantics; a differing artifact at the same identity
fails closed.

## Agent qualification

The registry rejects duplicate identities and incomplete registrations. An
agent is dispatchable only when all of these match:

- qualification status is `qualified`;
- every required capability is declared;
- platform matches exactly;
- EA protocol version matches exactly.

Trust level is retained as qualification metadata. It does not independently
grant authorization.

## Human approval and authorization

Assignment preparation verifies a current Zeus `AUTHORIZED` ADR, `Ready`
lifecycle state, repository identity and baseline, and agent qualification.
Dispatch repeats every check and additionally requires a human approval record
whose approval reference and assignment checksum bind exactly to the EA.

Repository or resume state never grants authorization. A planning reservation
never becomes an execution lease. Legacy authorization cannot authorize
dispatch.

## Delivery and persistence

The filesystem outbox is a deliberately narrow delivery adapter: it writes the
EA and returns its artifact name. It cannot invoke an agent. The dispatch ledger
then records an immutable digest-protected event and exposes inspection-only
validation/status through `scripts/wop-dispatchctl`.
