#!/usr/bin/env bash
# Shared PMCT paths. Sourcing this file does not mutate repository state.
PMCT_SOURCE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
PMCT_REPOSITORY_ROOT="$(cd -- "${PMCT_SOURCE_ROOT}/../../.." && pwd -P)"
