#!/usr/bin/env bash
pmct_state_path() {
  printf '%s/engineering/runtime/pmct/capability-state.yaml\n' "${PMCT_REPOSITORY_ROOT}"
}
