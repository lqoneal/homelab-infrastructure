#!/usr/bin/env bash
# Gate identity: OA-20
# Capability statement: Evidence Integrity and Provenance
# Current applicability: discovered at runtime; unavailable future interfaces produce NOT_READY.
# Required authority: controlled PMCT observation authority; state changes require --authorized-transition.
# Required commands: zeus evidence self-test, zeus capability verify ZEUS-OA-CAP-019
# Required artifacts: run manifest, repository, discovery, assertions, result, report, hashes, COMPLETE.
# Preconditions: exact repository identity and prior gate PASS where required.
# Positive path: Through the authoritative CLI, demonstrate evidence binding to repository commit, authority, mission, WOP, execution, gate, and agent.
# Negative path: Present a malformed, unauthorized, stale, mismatched, or incomplete OA-20 request and verify Zeus rejects it without advancing state.
# Idempotency: Repeat the OA-20 observation or authorized request with the same identity and verify no duplicate state, event, evidence, or action.
# Interruption/recovery: With explicit transition authority and a controlled object, interrupt after preflight and verify checkpointed resume without duplicate effects.
# Regression scope: OA-01, OA-02, OA-03, OA-04, OA-05, OA-06, OA-07, OA-08, OA-09, OA-10, OA-11, OA-12, OA-13, OA-14, OA-15, OA-16, OA-17, OA-18, OA-19
# Evidence requirements: repository identity and exact HEAD; command stdout, stderr, and return code; OA-20 positive and negative assertions; evidence integrity manifest and completion marker
# PASS: all mandatory observable assertions pass and evidence is complete.
# FAIL: an available required capability behaves incorrectly or unsafely.
# BLOCKED: repository identity, authority, or prerequisite prevents evaluation.
# NOT READY: a mandatory acceptance interface or demonstration is unavailable.
# Manual review: inspect terminal result, report, assertions, and artifacts.sha256.
set -u
set -o pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec "${SCRIPT_DIR}/../bin/pmct" run "OA-20" "$@"
