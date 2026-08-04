# Platform Validation Report

Passed: `engctl eos sync-validate`, `engctl platform validate`, `engctl
registry validate`, `engctl validate`, `git diff --check`, Stage 1 runtime
regression tests (7), and disposable resolver tests (2).

Two broader pre-existing suites were not green in this dirty checkout:
`test-zeus-cli-command-consistency.py` expected `READY_FOR_REVIEW` but observed
`READY`, and `test-zeus-development-mode-recovery.py` was blocked by the
working-tree cleanliness guard. These failures are recorded rather than
attributed to the resolver.

Repository HEAD was `a638ea7221a025789c08c5fc1be4ac466b7041a6` (published short
identity `a638ea7`). Protected tags resolved to OA-v1.0.0
`73b22f44dd8ee4d70f0c943ed19e1569022f856a` and OB-PLAN-v1.0.0
`b928c1541aa7ba42132f288927924818632f7cd2`. Post-publication EOS
synchronization and live-transaction qualification are not claimed.
