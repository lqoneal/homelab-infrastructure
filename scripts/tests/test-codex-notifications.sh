#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENGCTL="$ROOT/scripts/engctl"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

CONFIG="$TEST_ROOT/notifications.env"
MOCK_CURL="$TEST_ROOT/mock-curl"
ARGS_BIN="$TEST_ROOT/args-bin"
LONG_BIN="$TEST_ROOT/long-bin"
QUALIFY_BIN="$TEST_ROOT/qualify-bin"

PRIVATE_TEST_TOPIC="qualification-$PPID-$$-$RANDOM"
cat > "$CONFIG" <<EOF
NTFY_BASE_URL="https://ntfy.invalid"
NTFY_TOPIC="$PRIVATE_TEST_TOPIC"
NTFY_TOKEN="test-token"
NTFY_PRIORITY="default"
EOF
chmod 600 "$CONFIG"

cat > "$MOCK_CURL" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s\n' "$*" >> "$MOCK_CURL_ARGS"
cat >> "$MOCK_CURL_CONFIG"
printf '%s\n' '---' >> "$MOCK_CURL_CONFIG"
exit "${MOCK_CURL_EXIT:-0}"
EOF
chmod 700 "$MOCK_CURL"

cat > "$ARGS_BIN" <<'EOF'
#!/usr/bin/env bash
printf '%s\0' "$@" > "$CODEX_TEST_ARGS"
EOF
chmod 700 "$ARGS_BIN"

cat > "$LONG_BIN" <<'EOF'
#!/usr/bin/env bash
while [[ "${1:-}" == "-c" ]]; do shift 2; done
exec /bin/sleep "$@"
EOF
chmod 700 "$LONG_BIN"

cat > "$QUALIFY_BIN" <<'EOF'
#!/usr/bin/env bash
if [[ "${CODEX_TEST_EXPECT_MARKER:-0}" == "1" ]]; then
    [[ "${ENGINEERING_CODEX_WRAPPER:-}" == "engctl-codex-v1" ]]
    [[ "${ENGINEERING_CODEX_WOP:-}" == "WOP-TEST-001" ]]
fi
notify_json=""
while [[ "${1:-}" == "-c" ]]; do
    [[ "$2" != notify=* ]] || notify_json="${2#notify=}"
    shift 2
done
printf '%s\n' "$CODEX_TEST_REPORT"
if [[ -n "$notify_json" ]]; then
    mapfile -t notify_command < <(jq -r '.[]' <<<"$notify_json")
    "${notify_command[@]}" "$(jq -cn \
        --arg turn "${CODEX_TEST_TURN:-test-turn}" \
        --arg report "$CODEX_TEST_REPORT" \
        '{type:"agent-turn-complete","turn-id":$turn,"last-assistant-message":$report}')"
fi
exit "${CODEX_TEST_EXIT:-0}"
EOF
chmod 700 "$QUALIFY_BIN"

QUALIFIED_REPORT='# Completion Report

## Transaction Identification
test
## Execution Summary
test
## Repository State
test
## Commands Executed
test
## Artifacts Reviewed
test
## Repository Changes
test
## Validation Activities
test
## Deliverables Produced
test
## Findings
test
## Analysis
test
## Recommendations
test
## Final Certification
test
## Follow-on Work
test
## Governance Conformance Review
test'

export NTFY_CONFIG_FILE="$CONFIG"
export CURL_BIN="$MOCK_CURL"
export MOCK_CURL_ARGS="$TEST_ROOT/curl.args"
export MOCK_CURL_CONFIG="$TEST_ROOT/curl.config"

# Published examples and common placeholders must fail in the loader before
# curl is invoked. Error text must not echo the rejected value.
source "$ROOT/scripts/lib/notifications/ntfy.sh"
for rejected_topic in \
    'replace-with-private-topic' '<private-topic>' 'private-topic' \
    'topic' 'your-topic' 'your_topic' 'changeme' 'change-me' \
    'replace-me' 'placeholder'; do
    : > "$MOCK_CURL_CONFIG"
    printf 'NTFY_BASE_URL="https://ntfy.invalid"\nNTFY_TOPIC="%s"\n' \
        "$rejected_topic" > "$CONFIG"
    set +e
    rejection_error="$(notify_ntfy 'Qualification' 'Rejected placeholder' 2>&1)"
    rejection_status=$?
    set -e
    [[ $rejection_status -eq 2 ]]
    [[ ! -s "$MOCK_CURL_CONFIG" ]]
    [[ "$rejection_error" == 'ntfy notification rejected: configuration contains an example or placeholder topic.' ]]
done

# A non-example private configuration remains acceptable to the loader.
cat > "$CONFIG" <<EOF
NTFY_BASE_URL="https://ntfy.invalid"
NTFY_TOPIC="$PRIVATE_TEST_TOPIC"
NTFY_TOKEN="test-token"
NTFY_PRIORITY="default"
EOF
notify_ntfy_load_config "$ROOT"
: > "$MOCK_CURL_CONFIG"

CODEX_TEST_REPORT="$QUALIFIED_REPORT" CODEX_BIN="$QUALIFY_BIN" "$ENGCTL" codex --wop WOP-TEST-001 --
[[ $? -eq 0 ]]

set +e
CODEX_TEST_REPORT="$QUALIFIED_REPORT" CODEX_TEST_EXIT=1 CODEX_BIN="$QUALIFY_BIN" "$ENGCTL" codex --wop WOP-TEST-001 --
false_status=$?
set -e
[[ $false_status -eq 1 ]]

CODEX_TEST_REPORT="$QUALIFIED_REPORT" CODEX_TEST_EXPECT_MARKER=1 \
    CODEX_BIN="$QUALIFY_BIN" "$ENGCTL" codex --wop WOP-TEST-001 --

CODEX_TEST_REPORT="$QUALIFIED_REPORT" CODEX_TEST_TURN=resumed \
    CODEX_BIN="$QUALIFY_BIN" "$ENGCTL" codex --wop WOP-TEST-001 -- resume test-session

# Direct Codex-context initiation remains usable when authority is resolved by
# the published WOP chain; the wrapper is optional orchestration, not a gate.
CODEX_THREAD_ID=controlled-bypass-test ENGINEERING_CODEX_WRAPPER= \
    "$ENGCTL" resume >/dev/null
CODEX_THREAD_ID=controlled-wrapper-test ENGINEERING_CODEX_WRAPPER=engctl-codex-v1 \
    "$ENGCTL" resume >/dev/null

export CODEX_TEST_ARGS="$TEST_ROOT/codex.args"
CODEX_BIN="$ARGS_BIN" "$ENGCTL" codex -- \
    --flag value "argument with spaces" "quoted value"
python3 - "$CODEX_TEST_ARGS" <<'PY'
import pathlib
import sys

actual = pathlib.Path(sys.argv[1]).read_bytes().split(b"\0")[:-1]
expected = [b"--flag", b"value", b"argument with spaces", b"quoted value"]
if actual[-4:] != expected or actual[:1] != [b"-c"]:
    raise SystemExit(f"argument mismatch: {actual!r}")
if b"no WOP provenance marker" not in actual[1]:
    raise SystemExit(f"session classification missing: {actual[1]!r}")
PY

source "$ROOT/scripts/lib/eos/codex.sh"
governed_contract="$(eos_codex_completion_contract WOP-TEST-001)"
grep -Fq 'candidate revisions through engineering/execution/execution-interface.yaml' <<<"$governed_contract"
grep -Fq 'mission-delta Completion Report' <<<"$governed_contract"

# Three handoffs in one governed session, including concise, FAIL, and BLOCKED
# outcomes, consume the same durable contract and qualify independently.
MULTI_STATE="$TEST_ROOT/multi-handoff.tsv"
: > "$MULTI_STATE"
for turn in first second third concise failed blocked resumed; do
    report="$QUALIFIED_REPORT"
    report="${report/## Execution Summary/## Execution Summary\nMission Status: ${turn^^}}"
    bash "$ROOT/scripts/lib/eos/codex-report-qualify.sh" "$MULTI_STATE" governed \
        "$(jq -cn --arg turn "$turn" --arg report "$report" \
            '{type:"agent-turn-complete","turn-id":$turn,"last-assistant-message":$report}')"
done
[[ "$(awk -F '\t' '$2 == "PASS" { count++ } END { print count + 0 }' "$MULTI_STATE")" -eq 7 ]]

NONCONFORMING_STATE="$TEST_ROOT/nonconforming.tsv"
: > "$NONCONFORMING_STATE"
bash "$ROOT/scripts/lib/eos/codex-report-qualify.sh" "$NONCONFORMING_STATE" governed \
    "$(jq -cn '{type:"agent-turn-complete","turn-id":"bad","last-assistant-message":"Implementation complete."}')"
grep -Fq $'bad\tFAIL\texact-heading' "$NONCONFORMING_STATE"

set +e
CODEX_TEST_REPORT='Implementation complete.' CODEX_BIN="$QUALIFY_BIN" \
    "$ENGCTL" codex --wop WOP-TEST-001 --
qualification_failure_status=$?
set -e
[[ $qualification_failure_status -eq 65 ]]

set +e
CODEX_BIN="$LONG_BIN" "$ENGCTL" codex --wop WOP-TEST-001 -- 300 &
wrapper_pid=$!
sleep 1
child_pid="$(pgrep -P "$wrapper_pid" -f "$LONG_BIN|sleep 300" | head -1)"
kill -TERM "$wrapper_pid"
wait "$wrapper_pid"
interrupt_status=$?
set -e
[[ $interrupt_status -eq 143 ]]
if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    printf 'orphaned controlled child: %s\n' "$child_pid" >&2
    exit 1
fi

set +e
MOCK_CURL_EXIT=28 CODEX_TEST_REPORT="$QUALIFIED_REPORT" CODEX_BIN="$QUALIFY_BIN" \
    "$ENGCTL" codex --wop WOP-TEST-001 --
notification_failure_status=$?
set -e
[[ $notification_failure_status -eq 0 ]]

set +e
CODEX_BIN="$LONG_BIN" "$ENGCTL" codex --wop WOP-TEST-001 --timeout 1 -- 300
timeout_status=$?
set -e
[[ $timeout_status -eq 143 ]]

if rg -n "$PRIVATE_TEST_TOPIC|test-token" "$MOCK_CURL_ARGS" >/dev/null; then
    printf 'secret material appeared in curl arguments\n' >&2
    exit 1
fi

notification_count="$(rg -c '^---$' "$MOCK_CURL_CONFIG")"
[[ $notification_count -ge 9 ]]
rg -q 'Title: Codex Started' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Complete' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Report Qualification Failed' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Failed' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Interrupted' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Timed Out' "$MOCK_CURL_CONFIG"

printf 'PASS: Codex lifecycle notification controlled tests\n'
