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
MARKER_BIN="$TEST_ROOT/marker-bin"

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
exec /bin/sleep "$@"
EOF
chmod 700 "$LONG_BIN"

cat > "$MARKER_BIN" <<'EOF'
#!/usr/bin/env bash
[[ "${ENGINEERING_CODEX_WRAPPER:-}" == "engctl-codex-v1" ]]
[[ "${ENGINEERING_CODEX_EWO:-}" == "EWO-000019" ]]
EOF
chmod 700 "$MARKER_BIN"

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

CODEX_BIN=/bin/true "$ENGCTL" codex --ewo EWO-000017 --
[[ $? -eq 0 ]]

set +e
CODEX_BIN=/bin/false "$ENGCTL" codex --ewo EWO-000017 --
false_status=$?
set -e
[[ $false_status -eq 1 ]]

CODEX_BIN="$MARKER_BIN" "$ENGCTL" codex --ewo EWO-000019 --

# A Codex-context initiation outside the wrapper is rejected and reports a
# value-free bypass condition. The accepted marker permits the same operation.
set +e
CODEX_THREAD_ID=controlled-bypass-test ENGINEERING_CODEX_WRAPPER= \
    "$ENGCTL" resume >/dev/null 2>"$TEST_ROOT/bypass.error"
bypass_status=$?
set -e
[[ $bypass_status -eq 78 ]]
rg -q 'Codex wrapper bypass detected' "$TEST_ROOT/bypass.error"
CODEX_THREAD_ID=controlled-wrapper-test ENGINEERING_CODEX_WRAPPER=engctl-codex-v1 \
    "$ENGCTL" resume >/dev/null

export CODEX_TEST_ARGS="$TEST_ROOT/codex.args"
CODEX_BIN="$ARGS_BIN" "$ENGCTL" codex --ewo EWO-000017 -- \
    --flag value "argument with spaces" "quoted value"
python3 - "$CODEX_TEST_ARGS" <<'PY'
import pathlib
import sys

actual = pathlib.Path(sys.argv[1]).read_bytes().split(b"\0")[:-1]
expected = [b"--flag", b"value", b"argument with spaces", b"quoted value"]
if actual != expected:
    raise SystemExit(f"argument mismatch: {actual!r}")
PY

set +e
CODEX_BIN="$LONG_BIN" "$ENGCTL" codex --ewo EWO-000017 -- 300 &
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
MOCK_CURL_EXIT=28 CODEX_BIN=/bin/true "$ENGCTL" codex --ewo EWO-000017 --
notification_failure_status=$?
set -e
[[ $notification_failure_status -eq 0 ]]

set +e
CODEX_BIN="$LONG_BIN" "$ENGCTL" codex --ewo EWO-000019 --timeout 1 -- 300
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
rg -q 'Title: Codex Failed' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Interrupted' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Timed Out' "$MOCK_CURL_CONFIG"
rg -q 'Title: Codex Wrapper Bypass' "$MOCK_CURL_CONFIG"

printf 'PASS: Codex lifecycle notification controlled tests\n'
