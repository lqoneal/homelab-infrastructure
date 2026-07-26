#!/usr/bin/env bash
pmct_runtime_root() {
  printf '%s\n' "${PMCT_RUNTIME_ROOT:-${PMCT_REPOSITORY_ROOT}/engineering/runtime/pmct}"
}
