#!/usr/bin/env bash
pmct_assert() {
  local name="$1" observed="$2" expected="$3"
  if [[ "${observed}" == "${expected}" ]]; then
    printf 'PMCT_ASSERT=%s PASS\n' "${name}"
    return 0
  fi
  printf 'PMCT_ASSERT=%s FAIL observed=%s expected=%s\n' "${name}" "${observed}" "${expected}"
  return 1
}
