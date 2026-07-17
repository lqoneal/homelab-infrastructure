#!/usr/bin/env bash

eos_codex_duration() {
    local total="${1:-0}"
    printf '%02d:%02d:%02d' "$((total / 3600))" "$(((total % 3600) / 60))" "$((total % 60))"
}

eos_codex_repository_name() {
    local root
    root="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -n "$root" ]]; then
        basename "$root"
    else
        printf '%s' "$(basename "$PWD")"
    fi
}

eos_codex_notification() {
    local title="$1"
    local status="$2"
    local repository="$3"
    local work_order="$4"
    local host="$5"
    local duration="${6:-}"
    local signal="${7:-}"
    local message

    message="Status: $status
Repository: $repository
Work Order: $work_order"
    [[ -z "$duration" ]] || message+=$'\n'"Duration: $duration"
    [[ -z "$signal" ]] || message+=$'\n'"Signal: $signal"
    message+=$'\n'"Host: $host"

    notify_ntfy "$title" "$message" "" "codex,engineering" || {
        printf 'Warning: Codex lifecycle notification failed.\n' >&2
        return 1
    }
}

eos_codex_usage() {
    cat <<'EOF'
Usage: engctl codex [--ewo EWO-XXXXXX] [--timeout SECONDS] [--] [codex arguments ...]

Environment:
  CODEX_EWO       Default Work Order when --ewo is omitted.
  CODEX_BIN       Underlying Codex executable; intended for controlled tests.
  CODEX_TIMEOUT   Optional positive mission timeout in seconds; zero disables.
  NTFY_CONFIG_FILE  Explicit local notification configuration.
EOF
}

eos_codex_wrapper_gate() {
    local operation="${1:-repository-governed engineering initiation}"

    # Non-Codex operators and automation are outside the Codex launch contract.
    [[ -n "${CODEX_THREAD_ID:-}" ]] || return 0
    if [[ "${ENGINEERING_CODEX_WRAPPER:-}" == "engctl-codex-v1" ]]; then
        return 0
    fi
    if [[ "${ENGINEERING_CODEX_WRAPPER_EXCEPTION:-}" == "EWO-000019-bootstrap" ]]; then
        printf 'WARNING: documented EWO-000019 wrapper-enforcement bootstrap exception active.\n' >&2
        return 0
    fi

    printf 'ERROR: Codex wrapper bypass detected during %s; repository-governed Codex missions SHALL launch through engctl codex.\n' "$operation" >&2
    eos_codex_notification \
        "Codex Wrapper Bypass" "Wrapper bypass detected" \
        "$(eos_codex_repository_name)" "${CODEX_EWO:-Not specified}" "$(hostname)" || true
    return 78
}

eos_codex_run() {
    local work_order="${CODEX_EWO:-Not specified}"
    local codex_bin="${CODEX_BIN:-codex}"
    local mission_timeout="${CODEX_TIMEOUT:-0}"
    local repository host start_epoch end_epoch elapsed duration
    local child_pid="" final_sent=0 codex_exit=0
    local -a codex_args=()

    while (($#)); do
        case "$1" in
            --ewo)
                if (($# < 2)) || [[ -z "$2" ]]; then
                    printf 'ERROR: --ewo requires an identifier.\n' >&2
                    return 64
                fi
                work_order="$2"
                shift 2
                ;;
            --timeout)
                if (($# < 2)) || [[ ! "$2" =~ ^[1-9][0-9]*$ ]]; then
                    printf 'ERROR: --timeout requires a positive number of seconds.\n' >&2
                    return 64
                fi
                mission_timeout="$2"
                shift 2
                ;;
            --help|-h)
                eos_codex_usage
                return 0
                ;;
            --)
                shift
                codex_args+=("$@")
                break
                ;;
            *)
                codex_args+=("$1")
                shift
                ;;
        esac
    done

    if [[ "$work_order" != "Not specified" && ! "$work_order" =~ ^EWO-[0-9]{6}$ ]]; then
        printf 'ERROR: Work Order must match EWO-XXXXXX.\n' >&2
        return 64
    fi
    if [[ ! "$mission_timeout" =~ ^[0-9]+$ ]]; then
        printf 'ERROR: CODEX_TIMEOUT must be zero or a positive number of seconds.\n' >&2
        return 64
    fi
    if ! command -v "$codex_bin" >/dev/null 2>&1; then
        printf 'ERROR: Codex executable is unavailable.\n' >&2
        return 127
    fi

    repository="$(eos_codex_repository_name)"
    host="$(hostname)"
    start_epoch="$(date +%s)"

    eos_codex_notification "Codex Started" "Running" "$repository" "$work_order" "$host" || true

    eos_codex_interrupted() {
        local signal_name="$1"
        local signal_number="$2"
        trap - INT TERM HUP
        if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
            kill -s "$signal_name" "$child_pid" 2>/dev/null || true
            wait "$child_pid" 2>/dev/null || true
        fi
        end_epoch="$(date +%s)"
        elapsed=$((end_epoch - start_epoch))
        duration="$(eos_codex_duration "$elapsed")"
        eos_codex_notification "Codex Interrupted" "Interrupted" "$repository" "$work_order" "$host" "$duration" "$signal_name" || true
        final_sent=1
        return "$((128 + signal_number))"
    }

    trap 'eos_codex_interrupted INT 2; return $?' INT
    trap 'eos_codex_interrupted TERM 15; return $?' TERM
    trap 'eos_codex_interrupted HUP 1; return $?' HUP

    export ENGINEERING_CODEX_WRAPPER="engctl-codex-v1"
    export ENGINEERING_CODEX_EWO="$work_order"
    if ((mission_timeout > 0)); then
        timeout --preserve-status --signal=TERM --kill-after=5 \
            "$mission_timeout" "$codex_bin" "${codex_args[@]}" <&0 &
    else
        "$codex_bin" "${codex_args[@]}" <&0 &
    fi
    child_pid=$!
    wait "$child_pid" || codex_exit=$?
    child_pid=""
    trap - INT TERM HUP

    if ((final_sent)); then
        return "$codex_exit"
    fi

    end_epoch="$(date +%s)"
    elapsed=$((end_epoch - start_epoch))
    duration="$(eos_codex_duration "$elapsed")"
    if ((mission_timeout > 0 && codex_exit == 143)); then
        eos_codex_notification "Codex Timed Out" "Timed out after ${mission_timeout}s" "$repository" "$work_order" "$host" "$duration" || true
    elif ((codex_exit == 0)); then
        eos_codex_notification "Codex Complete" "Success" "$repository" "$work_order" "$host" "$duration" || true
    else
        eos_codex_notification "Codex Failed" "Exit code $codex_exit" "$repository" "$work_order" "$host" "$duration" || true
    fi

    return "$codex_exit"
}
