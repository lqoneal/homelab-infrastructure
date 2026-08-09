# Command Contract

All commands support deterministic JSON output and use nonzero exit status for
failure, blocker, or unresolved state.

```text
zeus publication inspect <MISSION_ID> --json
zeus publication classify <MISSION_ID> --json
zeus publication prepare <MISSION_ID> --json
zeus publication verify <PUBLICATION_ID> --json
zeus publication stage <PUBLICATION_ID> --json
zeus publication commit <PUBLICATION_ID> --json
zeus publication push <PUBLICATION_ID> --json
zeus publication synchronize <PUBLICATION_ID> --json
zeus publication qualify <PUBLICATION_ID> --json
zeus publication status <PUBLICATION_ID> --json
zeus publication resume <PUBLICATION_ID> --json
zeus publication abort <PUBLICATION_ID> --json
zeus publication run <MISSION_ID> [--approve] --json
```

`run` without `--approve` performs read-only inspection and stops at
`APPROVE_PUBLICATION`. The explicit `--manifest` option is available for a
qualified machine-readable candidate manifest.
