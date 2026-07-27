# Engineering CLI Standard

First-class engineering tools shall provide a canonical executable on `PATH`,
repository-independent resolution, `--help`, `help`, contextual
`help <command>`, a Unix manual page, a Markdown user guide, examples,
documented exit codes, cross-references, and automated qualification.

Exit status `0` means success, `2` means command-line syntax error, and `78`
means a failed prerequisite or unavailable governed state. Evidence-producing
tools may use `1` for a completed non-PASS evaluation. Installation helpers use
`64` for invalid installer syntax. Installation must be idempotent and must refuse
to replace conflicting launchers. Help and manual rendering must not advance
an operational lifecycle.

Phase 1 conforming tools are `zeus` and `pmct`. Future first-class engineering
CLIs must satisfy this standard before being described as production commands.
