#!/usr/bin/env bash
pmct_result_valid() {
  case "$1" in
    PASS|FAIL|BLOCKED|NOT_READY|EXPECTED_NOT_YET_IMPLEMENTED|NOT_APPLICABLE) return 0 ;;
    *) return 1 ;;
  esac
}
