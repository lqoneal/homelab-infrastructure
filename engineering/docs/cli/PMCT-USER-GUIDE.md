# PMCT User Guide

## Architecture and qualification role

`pmct` is the Progressive Manual Capability Test interface. Its canonical
launcher resolves the repository-native PMCT implementation. PMCT creates
sealed, integrity-manifested gate evidence and reconciles its authenticated
runtime ledger; it does not record operator acceptance.

## Commands and workflows

Use `pmct --help`, `pmct help`, or `pmct help <command>`.
`pmct run OA-NN` executes one gate, `pmct inspect [RUN-ID]` inspects state or
exact evidence, `pmct report RUN-ID` renders a report, `pmct list` lists gates,
and `pmct show OA-NN` shows a matrix entry.

Run evidence is stored at `engineering/runtime/pmct/runs/<RUN-ID>` with a
completion marker and `artifacts.sha256`. Zeus gate verification selects only
evidence matching repository HEAD, active publication, and WOP identity.

## Troubleshooting and related systems

Nonzero results preserve diagnostic evidence. A `NOT_READY` result means
prerequisites remain incomplete. Use Authority Publication to reconcile a
baseline gap; use Zeus for next-action, verification, approval, dispatch, and
resume decisions. Work Registry, EENS, and Engineering Work Orders retain
their independent authority boundaries.
