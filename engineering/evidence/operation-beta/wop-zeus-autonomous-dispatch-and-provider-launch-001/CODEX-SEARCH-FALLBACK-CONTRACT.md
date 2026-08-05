# Codex Search Fallback Contract

`codex_notification_search` prefers `rg` when it is available and otherwise invokes `grep -E`. The exercised options (`-n`, `-c`, and `-q`) retain match, count, quiet, and not-found exit semantics. Genuine tool errors remain nonzero under `set -Eeuo pipefail`; no assertion is converted into unconditional success.

`CODEX_NOTIFICATION_FORCE_GREP=1` provides deterministic coverage of the fallback path without installing or modifying the environment.
