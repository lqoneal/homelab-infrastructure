#!/usr/bin/env bash
# Gate identity: OA-01
# Capability statement: Assessment recognition and controlled mission transition
# Current applicability: discovered at runtime; unavailable future interfaces produce NOT_READY.
# Required authority: controlled PMCT observation authority; state changes require --authorized-transition.
# Required commands: zeus status, zeus next-action
# Required artifacts: run manifest, repository, discovery, assertions, result, report, hashes, COMPLETE.
# Preconditions: exact repository identity and prior gate PASS where required.
# Positive path: Through the authoritative CLI, demonstrate assessment recognition and controlled mission transition and capture the resulting production-observable state.
# Negative path: Present a malformed, unauthorized, stale, mismatched, or incomplete OA-01 request and verify Zeus rejects it without advancing state.
# Idempotency: Repeat the OA-01 observation or authorized request with the same identity and verify no duplicate state, event, evidence, or action.
# Interruption/recovery: Authoritative-state observation: verify repeatable discovery without authoritative engineering, repository, or operational decision-state mutation; only documented bounded presentation telemetry is permitted.
# Regression scope: none
# Evidence requirements: repository identity and exact HEAD; command stdout, stderr, and return code; OA-01 positive and negative assertions; evidence integrity manifest and completion marker
# PASS: all mandatory observable assertions pass and evidence is complete.
# FAIL: an available required capability behaves incorrectly or unsafely.
# BLOCKED: repository identity, authority, or prerequisite prevents evaluation.
# NOT READY: a mandatory acceptance interface or demonstration is unavailable.
# Manual review: inspect terminal result, report, assertions, and artifacts.sha256.
set -u
set -o pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec "${SCRIPT_DIR}/../bin/pmct" run "OA-01" "$@"
