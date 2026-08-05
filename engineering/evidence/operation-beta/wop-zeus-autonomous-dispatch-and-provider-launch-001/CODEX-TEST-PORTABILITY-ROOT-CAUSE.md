# Codex Test Portability Root Cause

The notification regression failed only because `scripts/tests/test-codex-notifications.sh` invoked `rg` directly at lines 232, 237, and 239–244. The active qualification image has `/usr/bin/grep` but no `rg`; the Codex wrapper and notification implementation were not implicated.

The assertions were preserved. The corrective is test-local and does not alter notification production behavior.
