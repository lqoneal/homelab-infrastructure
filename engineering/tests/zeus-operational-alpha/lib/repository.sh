#!/usr/bin/env bash
pmct_repository_head() {
  git -C "${PMCT_REPOSITORY_ROOT}" rev-parse HEAD
}
