# Git Automation Contract

This is the persisted evidence copy of the current normative contract. The
controlled architecture specification and Git publication procedure are the
normative owners.

Automation MUST prefer stable Git plumbing/porcelain interfaces over
human-oriented output. Current repository state MUST be resolved from live
projection rather than hardcoded current values.

Required rules:

- use explicit refs, including `refs/remotes/origin/main`;
- use exit codes for boolean status and ancestry checks;
- use `--porcelain=v2 -z` and NUL-delimited path primitives for machine paths;
- set `GIT_TERMINAL_PROMPT=0` for unattended Git operations;
- keep authentication/session setup separate from Git operations;
- use `git merge-base --is-ancestor` for lineage;
- do not parse normal human `status`, `log`, or `diff` output when a stable
  machine interface exists;
- preserve operator-interactive publication behavior where credential prompts
  are intentionally supported.

`zeus repository projection --json` is the canonical read-only consumer
surface. It fails closed for an invalid repository, unavailable required
refs, or contradictory available EOS projection. A valid projection may
report parity or worktree differences as explicit data; it never guesses a
current baseline.

