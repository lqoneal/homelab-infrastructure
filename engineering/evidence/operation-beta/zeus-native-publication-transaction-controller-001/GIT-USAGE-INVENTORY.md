# Git Usage Inventory

The existing `repository_projection.py` is the canonical live repository
projection. The new controller consumes it rather than reimplementing status,
identity, parity, or ancestry parsing.

The controller-owned operations use:

- `rev-parse --verify` for explicit commit identities;
- `status --porcelain=v2 --branch -z` and NUL-safe path primitives;
- `diff --quiet` and `diff --cached --quiet` for boolean state;
- `merge-base --is-ancestor` through the shared projection;
- explicit `origin` and `refs/heads/main` push targets;
- `GIT_TERMINAL_PROMPT=0` for unattended Git operations.

Legacy human-readable publication procedures and historical evidence remain
preserved. They are not current controller authority.
