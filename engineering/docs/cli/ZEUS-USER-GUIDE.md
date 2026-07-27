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
`zeus approve OA-NN`; verification never implies acceptance.

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
