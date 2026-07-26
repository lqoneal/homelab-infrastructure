# Zeus Operational Runtime

## Architecture and ownership

The repository root discovered from `scripts/zeus` defines the Zeus runtime.
Its only authoritative orchestration store is:

`<repository>/.zeus/runtime/orchestration-state.json`

The Zeus operator owns the file and its lifecycle. The runtime is local,
mutable operational data and is intentionally excluded from Git. It is not an
authority source: it records orchestration state consumed by the existing
admission, selection, approval, dispatch, qualification, reconciliation, and
closeout services. Schema version 1 is owned by
`scripts/lib/emp/orchestration.py`.

`--state` and `ZEUS_STATE` are retained only as explicit engineering and test
overrides. Bootstrap refuses to initialize either override unless it resolves
to the authoritative location.

Operator orientation state is separately stored at
`.zeus/runtime/operator-interface-state.json` and is owned by
`scripts/lib/emp/operator_interface.py`. It is deliberately excluded from the
strict orchestration schema because presentation history is not mission,
approval, execution, qualification, or reconciliation state. Installation,
counting, suppression, and recovery are specified in
`engineering/operations/zeus-operator-interface.md`.

## Bootstrap and initialization

From the repository root, run:

```text
scripts/zeus bootstrap
scripts/zeus status
```

Bootstrap fails closed unless Git identifies this exact repository and HEAD
contains the qualified Mission O baseline
`a755aeb353639550eb2ffd197e30fc03bccac90b`. It then:

1. creates the canonical schema-version-1 empty state when no state exists;
2. validates any existing state instead of replacing it;
3. performs an atomic write and deterministic reload;
4. restricts the runtime directory and files to the operator;
5. records machine-readable evidence at
   `.zeus/evidence/bootstrap-evidence.json`; and
6. reports `operational_readiness: READY`.

Repeated bootstrap is safe. It validates and rewrites the same logical state
without clearing missions or lifecycle records.

## Lifecycle, recovery, and troubleshooting

The state is created by `zeus bootstrap`, updated atomically by Zeus, and
retained across invocations. Never hand-edit it. Backups must preserve the
state file as a unit while Zeus is idle.

If no operational state exists, run `scripts/zeus bootstrap`; this is the
deterministic recovery path for an uninitialized runtime. Bootstrap does not
replace corrupted or incompatible state. Preserve the failed file for
investigation, restore a known-good whole-file backup, then rerun bootstrap.
If there is no trustworthy backup, move the failed file aside under operator
control and run bootstrap to create a new empty runtime; queued and historical
records must then be reconciled from their authoritative source records.

Common failures:

- `operational state does not exist`: run bootstrap.
- `incompatible orchestration schema version`: use a compatible Zeus release
  or an explicitly qualified migration; bootstrap never guesses a migration.
- `invalid orchestration store`: preserve and restore the file; initialization
  will not overwrite corruption.
- `repository identity mismatch` or `does not contain qualified baseline`:
  use the qualified homelab checkout and baseline.
- `authoritative runtime path may not use symbolic links`: remove the path
  redirection and restore the repository-local runtime.

## Operational verification

After bootstrap, these commands discover the runtime without `--state`:

```text
scripts/zeus status
scripts/zeus show wop-template
scripts/zeus validate PACKAGE.json --repository /data/engineering/repositories/homelab
scripts/zeus explain rejection ADMISSION-RECORD.json
scripts/zeus converse status --context /tmp/zeus-context.json
scripts/zeus generate-wop INTENT --mission MISSION-ID --phase PHASE-ID \
  --repository /data/engineering/repositories/homelab --submitter OPERATOR \
  --approval-authority AUTHORITY --approval-reference REFERENCE \
  --approval-date 2026-07-25 --authority-node NODE --adr ADR \
  --immutable-wop WOP
```

Commands requiring packages or records must be supplied real qualified inputs;
runtime discovery does not relax their validation.
