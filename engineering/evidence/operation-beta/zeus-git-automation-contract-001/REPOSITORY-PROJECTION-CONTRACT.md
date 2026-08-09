# Repository Projection Contract

Command:

```text
scripts/zeus repository projection --json
```

The command is read-only, deterministic for a fixed live repository/EOS
position, and exit-code driven. Its JSON includes:

- repository identity, repository ID, root, remote, branch, and detached-head
  state;
- `head`, explicit `origin_main`, parity, ahead/behind counts, and both
  directional ancestry checks;
- index, tracked worktree, untracked, and aggregate worktree state;
- NUL-safe-derived staged, unstaged, and untracked path collections;
- EOS baseline, availability, identity, manifest consistency, and parity;
- `read_only`, `projection_source`, `result`, and explicit errors.

Exit code `0` means the required projection was resolved. A nonzero result is
returned for invalid repositories, unavailable required refs, or contradictory
available EOS state. A missing optional EOS workspace is reported as
`eos.available=false` and `eos_parity=null`; the repository projection remains
usable while an EOS-aware caller can require EOS separately.

Current consumers must prefer this projection, then receipt-backed derived
state, persisted source records, explicitly bounded compatibility fallback, and
only lastly a documented hardcoded fallback. The new surface does not mutate
Git, EOS, runtime receipts, or lifecycle state.
