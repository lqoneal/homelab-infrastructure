# Zeus Runtime Discovery Specification

Zeus has one runtime resolver: `scripts/lib/emp/runtime_paths.py`. Every
runtime consumer uses it; no controller may select a second state directory.

Resolution precedence is command-line `--runtime-root`, `ZEUS_RUNTIME_ROOT`,
`.zeus/config.yaml` `runtime.root`, the user-state default
`~/.local/state/zeus-runtime/<repository-id>`, then an explicitly configured
system root. The repository ID is a stable digest of canonical repository path
and origin identity. Candidates are normalized, checked for repository-local or
protected-baseline containment, and checked for a foreign binding marker.

Read-only resolution does not create files. The first mutating command calls
`initialize_runtime`, which creates the selected root, standard subdirectories,
and `runtime-identity.json`. Initialization is deterministic and idempotent.
Existing stores are never moved, merged, or silently adopted when ownership
cannot be proven. Explicit override rejection is fail-closed.

The repository-bound user-state runtime is authoritative for current Zeus
operation; repository-local `.zeus/runtime` content is historical or explicit
legacy compatibility state unless adopted through the native transaction. The
legacy operational `active-publication.json` pointer is not a prerequisite for
canonical P2/P3/P4 submission, admission, or mission discovery. An explicit
`--state` orchestration override is an isolated engineering/test surface and
must remain independent of that historical OA pointer.
## Legacy runtime adoption

An existing valid Zeus runtime is adopted or migrated only through the native
transactional command `zeus runtime adopt`. It verifies repository binding,
bootstrap evidence, schema, history, EENS records, protected tags, and
collision state before writing a generated `runtime-binding.yaml`. `--dry-run`
performs the complete verification without mutation. Operators never edit
runtime identity JSON or copy/delete runtime directories manually.
