# Codex Notification Regression Results

- Native environment with `rg` absent: PASS.
- Forced `grep -E` fallback: PASS.
- Isolated `rg`-available shim: PASS.
- Match-found, match-not-found, count, and notification-title assertions: PASS.
- Secret-material absence assertion: PASS.

No provider was launched and no live notification or runtime state was changed.
