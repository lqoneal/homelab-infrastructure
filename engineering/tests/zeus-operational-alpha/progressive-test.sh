#!/usr/bin/env bash
# Copyable cumulative test entry point. Intentionally does not use `set -e`.
set -u
set -o pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
gate="${1:-OA-01}"
shift || true
"${SCRIPT_DIR}/bin/pmct" run "${gate}" "$@"
exit $?
