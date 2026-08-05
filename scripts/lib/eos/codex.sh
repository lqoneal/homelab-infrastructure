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
Usage: engctl codex [--wop WOP-ID] [--context-file JSON] [--timeout SECONDS] [--] [codex arguments ...]

Environment:
  CODEX_WOP       Optional controlled WOP provenance when --wop is omitted.
  CODEX_BIN       Underlying Codex executable; intended for controlled tests.
  CODEX_TIMEOUT   Optional positive mission timeout in seconds; zero disables.
  ZEUS_CODEX_CONTEXT_FILE  Zeus-owned machine-readable context envelope.
  NTFY_CONFIG_FILE  Explicit local notification configuration.
EOF
}

eos_codex_completion_contract() {
    local wop="$1"
    if [[ "$wop" == "Not specified" ]]; then
        printf '%s' 'This repository session has no WOP provenance marker. Resolve authority from the published Operational Alpha authority chain; do not imply authorization from the session itself.'
        return 0
    fi

    printf '%s' "This repository session references $wop. Reconstruct every mission from the repository Engineering Execution Interface and Mission Snapshot; resolve authority through the published Operational Alpha WOP chain and EMM; do not rely on conversational recall or duplicate repository procedures in a handoff. Resolve exact controlled-owner identities and candidate revisions through engineering/execution/execution-interface.yaml. Produce a mission-delta Completion Report using the resolved Completion Report owner; candidate documents are not activated by consumption."
}

eos_codex_report_qualification_summary() {
    local state="$1" governance="$2"
    local total passed failed
    if [[ "$governance" != "governed" ]]; then
        printf 'Report Qualification: NOT APPLICABLE (unbound WOP session)\n'
        return 0
    fi

    total="$(awk 'END { print NR + 0 }' "$state" 2>/dev/null)"
    passed="$(awk -F '\t' '$2 == "PASS" { count++ } END { print count + 0 }' "$state" 2>/dev/null)"
    failed=$((total - passed))
    printf 'Report Qualification: %s (passed=%s failed=%s total=%s)\n' \
        "$([[ "$total" -gt 0 && "$failed" -eq 0 ]] && echo PASS || echo FAIL)" \
        "$passed" "$failed" "$total"
    [[ "$total" -gt 0 && "$failed" -eq 0 ]]
}

eos_codex_run() {
    local work_order="${CODEX_WOP:-Not specified}"
    local context_file="${ZEUS_CODEX_CONTEXT_FILE:-}"
    local codex_bin="${CODEX_BIN:-codex}"
    local mission_timeout="${CODEX_TIMEOUT:-0}"
    local repository host start_epoch end_epoch elapsed duration governance
    local contract contract_config notify_config qualification_root qualification_state qualifier
    local child_pid="" final_sent=0 codex_exit=0
    local -a codex_args=()

    while (($#)); do
        case "$1" in
            --wop)
                if (($# < 2)) || [[ -z "$2" ]]; then
                    printf 'ERROR: --wop requires an identifier.\n' >&2
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
            --context-file)
                if (($# < 2)) || [[ -z "$2" ]] || [[ ! -f "$2" ]]; then
                    printf 'ERROR: --context-file requires a readable JSON file.\n' >&2
                    return 64
                fi
                context_file="$2"
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
    qualifier="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/codex-report-qualify.sh"
    qualification_root="$(mktemp -d "${TMPDIR:-/tmp}/engctl-codex-qualification.XXXXXX")"
    qualification_state="$qualification_root/report-qualification.tsv"
    : > "$qualification_state"
    trap 'rm -rf "$qualification_root"' RETURN

    if [[ "$work_order" == "Not specified" ]]; then
        governance="wop-unbound"
    else
        governance="governed"
    fi
    if [[ -n "$context_file" ]]; then
        if ! jq -e 'type == "object" and .schema_version == 1 and .context_digest' "$context_file" >/dev/null 2>&1; then
            printf 'ERROR: Zeus Codex context envelope is invalid.\n' >&2
            return 65
        fi
        local context_digest expected_context_digest
        context_digest="$(jq -r '.context_digest' "$context_file")"
        expected_context_digest="$(jq -c 'del(.context_digest)' "$context_file" | sha256sum | awk '{print $1}')"
        if [[ "$context_digest" != "$expected_context_digest" ]]; then
            printf 'ERROR: Zeus Codex context digest mismatch.\n' >&2
            return 65
        fi
        export ZEUS_CODEX_CONTEXT_FILE="$context_file"
        export ZEUS_CODEX_CONTEXT_JSON="$(jq -c . "$context_file")"
        contract="$ZEUS_CODEX_CONTEXT_JSON"
    else
        contract="$(eos_codex_completion_contract "$work_order")"
    fi
    contract_config="developer_instructions=$(jq -Rn --arg value "$contract" '$value')"
    notify_config="notify=$(jq -cn \
        --arg qualifier "$qualifier" \
        --arg state "$qualification_state" \
        --arg governance "$governance" \
        '["bash", $qualifier, $state, $governance]')"
    codex_args=( -c "$contract_config" -c "$notify_config" "${codex_args[@]}" )

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
        eos_codex_report_qualification_summary "$qualification_state" "$governance" || true
        eos_codex_notification "Codex Interrupted" "Interrupted" "$repository" "$work_order" "$host" "$duration" "$signal_name" || true
        final_sent=1
        return "$((128 + signal_number))"
    }

    trap 'eos_codex_interrupted INT 2; return $?' INT
    trap 'eos_codex_interrupted TERM 15; return $?' TERM
    trap 'eos_codex_interrupted HUP 1; return $?' HUP

    export ENGINEERING_CODEX_WRAPPER="engctl-codex-v1"
    export ENGINEERING_CODEX_WOP="$work_order"
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
    local qualification_output qualification_status=0
    qualification_output="$(eos_codex_report_qualification_summary "$qualification_state" "$governance")" \
        || qualification_status=$?
    printf '%s\n' "$qualification_output"

    if ((mission_timeout > 0 && codex_exit == 143)); then
        eos_codex_notification "Codex Timed Out" "Timed out after ${mission_timeout}s" "$repository" "$work_order" "$host" "$duration" || true
    elif ((codex_exit == 0 && qualification_status == 0)); then
        eos_codex_notification "Codex Complete" "Success" "$repository" "$work_order" "$host" "$duration" || true
    elif ((codex_exit == 0)); then
        eos_codex_notification "Codex Report Qualification Failed" "Execution succeeded; report qualification failed" "$repository" "$work_order" "$host" "$duration" || true
        codex_exit=65
    else
        eos_codex_notification "Codex Failed" "Exit code $codex_exit" "$repository" "$work_order" "$host" "$duration" || true
    fi

    return "$codex_exit"
}
