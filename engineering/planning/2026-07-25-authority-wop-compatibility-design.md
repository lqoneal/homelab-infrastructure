# Authority/WOP Compatibility Specification

Date: 2026-07-25
Status: Offline verification implementation; no execution authority
Mission: Zeus Operational Alpha Mission F

## Boundary

The compatibility layer is a pure, offline adapter between the Mission D
Authority Resolution Engine and Mission E Immutable Work Package model. It
accepts already constructed typed inputs and returns one immutable terminal
decision. It does not read repositories, modify files, acquire leases, create
sessions, contact services or execute effects.

## Compatibility rules

The WOP authority-node binding is resolved through the validated single-parent
Authority DAG. Each authorized-effect `kind` names its required authority
capability. Every such capability must be present in the node's effective
capability set. Requested effect identifiers must remain inside the WOP effect
manifest, and explicit prohibited identifiers override manifest membership.

Authority graph validation preserves parent uniqueness, strict rank descent,
cycle rejection and capability monotonicity before WOP evaluation.

Publication receipts, leases and revocations remain external immutable records
bound to WOP identity and payload digest. A caller-supplied signature verifier
is mandatory. The provided digest verifier recognizes only deterministic
Mission F fixtures and is not a production trust implementation.

## Terminal decisions and precedence

Every evaluation emits exactly one of the required decision codes. When inputs
contain multiple failures, deterministic precedence selects structural WOP and
graph failures first, then binding, signature, receipt, temporal and lease
conditions, context, prerequisites, dependencies, capabilities, prohibited
effects, unauthorized effects and general validation failure. A valid input
emits `AUTHORIZED`.

Detailed reasons are sorted and deduplicated. Authority chains, capabilities
and effects are sorted or retain deterministic traversal order. An input digest
covers canonical graph, WOP, evaluation state, lifecycle records, expected
binding and reference time. Identical canonical inputs therefore produce
byte-equivalent serialized decisions.

## Offline interface

```text
scripts/authority-wop-compatctl GRAPH WOP STATE RECEIPT
  --lease LEASE [--revocation REVOCATION]
  [--expected-authority NODE] --at TIMESTAMP
```

Exit zero means `AUTHORIZED`; any fail-closed terminal decision exits one.
Mission F creates no live consumer.
