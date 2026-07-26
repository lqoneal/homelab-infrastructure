#!/usr/bin/env bash
# Hyphenated filenames match the locked repository layout; execute each directly.
set -u
set -o pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
failures=0
for test_file in "${SCRIPT_DIR}"/test-*.py; do
  python3 "${test_file}"
  status=$?
  if [[ ${status} -ne 0 ]]; then
    failures=$((failures + 1))
  fi
done
if [[ ${failures} -ne 0 ]]; then
  printf 'PMCT_SELF_TEST_RESULT=FAIL failures=%s\n' "${failures}"
  exit 1
fi
printf 'PMCT_SELF_TEST_RESULT=PASS\n'
