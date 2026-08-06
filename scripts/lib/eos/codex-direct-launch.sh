#!/usr/bin/env bash
# Shared low-level native Codex launcher.
# Callers own authority context, notifications, and qualification; this file
# only preserves direct terminal inheritance and replaces itself with Codex.
set -euo pipefail

if (($# == 0)); then
    printf 'ERROR: direct Codex launcher requires an executable.\n' >&2
    exit 64
fi

export CURRENT_TERMINAL_INHERITED=YES
export STDIN_DIRECT=YES
export STDOUT_DIRECT=YES
export STDERR_DIRECT=YES
export CODEX_NATIVE_TUI=YES
exec "$@"
