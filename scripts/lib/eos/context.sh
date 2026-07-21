#!/usr/bin/env bash

set -Eeuo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/repository.sh"

eos_project_state() {
    local project="${1:-homelab}"
    echo "$(eos_project_root "$project")/docs/project/PROJ-0001-PROJECT_STATE.md"
}

eos_latest_checkpoint() {
    local workspace
    workspace="$(eos_workspace)"

    find "$workspace/eos/checkpoints" -maxdepth 1 -type f -name "*.md" 2>/dev/null | sort | tail -1
}

eos_git_summary() {
    local project="${1:-homelab}"
    local root
    root="$(eos_project_root "$project")"

    echo "Repository Root:"
    echo "$root"
    echo

    echo "Branch:"
    git -C "$root" branch --show-current 2>/dev/null || echo "unknown"
    echo

    echo "Current Commit:"
    git -C "$root" log -1 --oneline 2>/dev/null || echo "No commits yet"
    echo

    echo "Working Tree:"
    git -C "$root" status --short 2>/dev/null || true
}

eos_service_state() {
    local service="$1"

    if ! command -v systemctl >/dev/null 2>&1; then
        echo "unknown (systemctl unavailable)"
        return 0
    fi

    local state
    state="$(systemctl is-active "$service" 2>/dev/null || true)"

    if [[ -n "$state" ]]; then
        echo "$state"
    else
        echo "unknown (system status unavailable)"
    fi
}

eos_command_state() {
    local command_name="$1"

    if command -v "$command_name" >/dev/null 2>&1; then
        echo "present"
    else
        echo "missing"
    fi
}

eos_ssh_agent_socket() {
    printf '%s/openssh_agent\n' "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
}

eos_ssh_agent_state() {
    local socket identities
    socket="$(eos_ssh_agent_socket)"

    if [[ ! -S "$socket" ]]; then
        echo "unavailable (systemd user agent socket missing; run: systemctl --user start ssh-agent.service)"
        return 0
    fi

    identities="$(SSH_AUTH_SOCK="$socket" ssh-add -l 2>&1 || true)"
    if grep -Fq "The agent has no identities." <<<"$identities"; then
        echo "running; no identities loaded (run: engctl ssh load)"
    elif grep -Fq "Could not open a connection" <<<"$identities"; then
        echo "unavailable (agent connection failed)"
    else
        echo "running; identities loaded"
    fi
}

eos_ssh_agent_environment() {
    export SSH_AUTH_SOCK="$(eos_ssh_agent_socket)"
    printf 'export SSH_AUTH_SOCK=%q\n' "$SSH_AUTH_SOCK"
}

eos_ssh_agent_load() {
    local socket key loaded=0
    local keys=("$@")
    socket="$(eos_ssh_agent_socket)"

    if [[ "${#keys[@]}" -eq 0 ]]; then
        keys=("$HOME/.ssh/id_ed25519")
    fi

    if [[ ! -S "$socket" ]]; then
        echo "ERROR: Engineering Platform SSH agent is unavailable." >&2
        echo "Start it with: systemctl --user start ssh-agent.service" >&2
        return 1
    fi

    for key in "${keys[@]}"; do
        if [[ ! -f "$key" ]]; then
            echo "ERROR: configured engineering key not found: $key" >&2
            return 1
        fi
        SSH_AUTH_SOCK="$socket" ssh-add "$key"
        loaded=1
    done

    if [[ "$loaded" -eq 0 ]]; then
        echo "ERROR: no configured engineering private keys were found." >&2
        return 1
    fi
}

eos_pdf_printing_state() {
    if ! command -v lpstat >/dev/null 2>&1; then
        echo "unknown (lpstat unavailable)"
        return 0
    fi

    local queues
    queues="$(lpstat -v 2>/dev/null || true)"

    if grep -Eq '(^device for |:)PDF|CUPS-PDF|cups-pdf' <<<"$queues"; then
        echo "configured"
    elif dpkg -s printer-driver-cups-pdf >/dev/null 2>&1 || dpkg -s cups-pdf >/dev/null 2>&1; then
        echo "driver installed; queue not detected"
    else
        echo "not configured"
    fi
}

eos_scanner_workflow_state() {
    local workspace base
    workspace="$(eos_workspace)"
    base="$workspace/shared/documents/intake/scans"

    local required=(
        "$base/engineering-documents"
        "$base/receipts"
        "$base/drawings"
        "$base/photographs"
        "$base/reference-documents"
    )

    local dir
    for dir in "${required[@]}"; do
        if [[ ! -d "$dir" ]]; then
            echo "incomplete"
            return 0
        fi
    done

    echo "established"
}

eos_production_printer_queue() {
    echo "${EOS_PRODUCTION_PRINTER_QUEUE:-Engineering_HP_OfficeJet_Pro_8020}"
}

eos_printer_uri() {
    local queue="$1"

    if ! command -v lpstat >/dev/null 2>&1; then
        echo "unknown"
        return 0
    fi

    local uri
    uri="$(lpstat -v "$queue" 2>/dev/null | sed -n "s/^device for ${queue}: //p" | head -1)"

    if [[ -n "$uri" ]]; then
        echo "$uri"
    else
        echo "unknown"
    fi
}

eos_printer_pending_jobs() {
    local queue="$1"

    if ! command -v lpstat >/dev/null 2>&1; then
        echo "unknown"
        return 0
    fi

    lpstat -W not-completed 2>/dev/null | awk -v queue="$queue" '
        index($1, queue "-") == 1 { count++ }
        END { print count + 0 }
    '
}

eos_printer_accepting_state() {
    local queue="$1"

    if ! command -v lpstat >/dev/null 2>&1; then
        echo "unknown"
        return 0
    fi

    local status
    status="$(lpstat -t 2>/dev/null || true)"

    if grep -Fq "$queue accepting requests" <<<"$status"; then
        echo "accepting"
    elif grep -Fq "$queue not accepting" <<<"$status"; then
        echo "not accepting"
    else
        echo "unknown"
    fi
}

eos_printer_enabled_state() {
    local queue="$1"

    if ! command -v lpstat >/dev/null 2>&1; then
        echo "unknown"
        return 0
    fi

    local status
    status="$(lpstat -p "$queue" -l 2>/dev/null || true)"

    if grep -Eq '\. +enabled' <<<"$status"; then
        echo "enabled"
    elif grep -Eq '\. +disabled' <<<"$status"; then
        echo "disabled"
    else
        echo "unknown"
    fi
}

eos_printer_queue_activity_state() {
    local queue="$1"

    if ! command -v lpstat >/dev/null 2>&1; then
        echo "unknown"
        return 0
    fi

    local status
    status="$(lpstat -p "$queue" -l 2>/dev/null || true)"

    if grep -Fq " is idle." <<<"$status"; then
        echo "idle"
    elif grep -Fq " now printing " <<<"$status"; then
        echo "printing"
    elif grep -Fq " is " <<<"$status"; then
        sed -n "s/^printer ${queue} is \([^ .]*\).*$/\1/p" <<<"$status" | head -1
    else
        echo "unknown"
    fi
}

eos_printer_ipp_attributes() {
    local uri="$1"

    if [[ "$uri" == "unknown" ]] || ! command -v ipptool >/dev/null 2>&1; then
        return 0
    fi

    local ipp_test
    ipp_test="/usr/share/cups/ipptool/get-printer-attributes.test"
    if [[ ! -r "$ipp_test" ]]; then
        ipp_test="get-printer-attributes.test"
    fi

    if command -v timeout >/dev/null 2>&1; then
        timeout 10 ipptool -tv "$uri" "$ipp_test" 2>/dev/null || true
    else
        ipptool -tv "$uri" "$ipp_test" 2>/dev/null || true
    fi
}

eos_ipp_attr() {
    local attributes="$1"
    local name="$2"

    awk -v name="$name" '
        $0 ~ "^[[:space:]]*" name " \\(" {
            sub(/^.* = /, "")
            print
            exit
        }
    ' <<<"$attributes"
}

eos_printer_warning_state() {
    local attributes="$1"
    local reasons

    reasons="$(eos_ipp_attr "$attributes" "printer-state-reasons")"

    if [[ -z "$attributes" ]]; then
        echo "unavailable"
    elif [[ -z "$reasons" ]]; then
        echo "unknown"
    elif [[ "$reasons" == "none" ]]; then
        echo "none"
    else
        echo "$reasons"
    fi
}

eos_printer_supply_levels() {
    local attributes="$1"
    local names levels

    names="$(eos_ipp_attr "$attributes" "marker-names")"
    levels="$(eos_ipp_attr "$attributes" "marker-levels")"

    if [[ -z "$names" || -z "$levels" ]]; then
        echo "unavailable"
        return 0
    fi

    local IFS=,
    read -r -a name_parts <<<"$names"
    read -r -a level_parts <<<"$levels"

    local index output level
    output=""
    for index in "${!name_parts[@]}"; do
        level="${level_parts[$index]:-unknown}"
        if [[ "$level" =~ ^[0-9]+$ ]]; then
            level="${level}%"
        fi

        if [[ -n "$output" ]]; then
            output+=", "
        fi
        output+="${name_parts[$index]}=${level}"
    done

    echo "$output"
}

eos_render_printer_health() {
    local queue uri pending accepting enabled queue_activity queue_state
    local attributes ipp_state ipp_accepting device_state warnings media_ready supply_levels supplies

    queue="$(eos_production_printer_queue)"
    uri="$(eos_printer_uri "$queue")"
    pending="$(eos_printer_pending_jobs "$queue")"
    accepting="$(eos_printer_accepting_state "$queue")"
    enabled="$(eos_printer_enabled_state "$queue")"
    queue_activity="$(eos_printer_queue_activity_state "$queue")"
    queue_state="${queue_activity}/${enabled}/${accepting}"

    attributes="$(eos_printer_ipp_attributes "$uri")"
    ipp_state="$(eos_ipp_attr "$attributes" "printer-state")"
    ipp_accepting="$(eos_ipp_attr "$attributes" "printer-is-accepting-jobs")"
    warnings="$(eos_printer_warning_state "$attributes")"
    media_ready="$(eos_ipp_attr "$attributes" "media-ready")"
    supply_levels="$(eos_printer_supply_levels "$attributes")"

    if [[ -n "$ipp_state" ]]; then
        device_state="$ipp_state"
    else
        device_state="unknown"
    fi

    if [[ "$ipp_accepting" == "false" && "$device_state" != *"not accepting"* ]]; then
        device_state="$device_state/not accepting"
    fi

    if [[ "$supply_levels" == "unavailable" ]]; then
        supplies="unavailable"
    else
        supplies="available"
    fi

    echo
    echo "Printer Health:"
    printf "  %-14s %s\n" "Queue:" "$queue"
    printf "  %-14s %s\n" "Queue State:" "$queue_state"
    printf "  %-14s %s\n" "Device State:" "$device_state"
    printf "  %-14s %s\n" "Pending Jobs:" "$pending"
    printf "  %-14s %s\n" "Printer URI:" "$uri"
    printf "  %-14s %s\n" "Warnings:" "$warnings"
    printf "  %-14s %s\n" "Supplies:" "$supplies"
    printf "  %-14s %s\n" "Supply Levels:" "$supply_levels"
    printf "  %-14s %s\n" "Media Ready:" "${media_ready:-unavailable}"
}

eos_render_operational_status() {
    echo "------------------------------------"
    echo "OPERATIONAL STATUS"
    echo "------------------------------------"
    printf "%-18s %s\n" "SSH:" "$(eos_service_state ssh)"
    printf "%-18s %s\n" "SSH Agent:" "$(eos_ssh_agent_state)"
    printf "%-18s %s\n" "Host Firewall:" "$(eos_service_state ufw)"
    printf "%-18s %s\n" "Print Services:" "$(eos_service_state cups)"
    printf "%-18s %s\n" "PDF Printing:" "$(eos_pdf_printing_state)"
    printf "%-18s %s\n" "Scanner Workflow:" "$(eos_scanner_workflow_state)"
    printf "%-18s %s\n" "Avahi:" "$(eos_service_state avahi-daemon)"
    printf "%-18s %s\n" "Scanner Tools:" "$(eos_command_state scanimage)"
    # Resume is a context-reconstruction surface. Optional device telemetry may
    # be unavailable, but that must not turn a successfully rendered context
    # into a failed command or abort the runtime regression suite.
    eos_render_printer_health || true
}

eos_markdown_field() {
    local path="$1" label="$2"
    awk -v label="$label" '
        $0 == "**" label ":**" { capture=1; next }
        capture && /^[[:space:]]*$/ { if (value != "") { print value; printed=1; exit } }
        capture {
            line=$0
            sub(/^[[:space:]]+/, "", line)
            value=(value == "" ? line : value " " line)
        }
        END { if (capture && value != "" && !printed) print value }
    ' "$path" 2>/dev/null
}

eos_context_value() {
    local context="$1" key="$2"
    sed -n "s/^${key}=//p" <<<"$context" | head -1
}

eos_render_resume_summary() {
    local project="$1" state="$2" registry_context="$3"
    local project_title mission phase active_work authority next_action repository_state
    local checkpoint_sync upstream platform_health banner

    project_title="$(eos_context_value "$registry_context" management_project_title)"
    mission="$(eos_context_value "$registry_context" management_current_missions)"
    phase="$(eos_context_value "$registry_context" management_current_phases)"
    active_work="$(eos_context_value "$registry_context" management_active_work)"
    [[ -n "$project_title" ]] || project_title="$project"
    [[ -n "$mission" && "$mission" != "none" ]] || mission="No active mission"
    if [[ -z "$phase" || "$phase" == "none" ]]; then
        phase="$(eos_frontmatter_value "$state" phase 2>/dev/null || true)"
    fi
    [[ -n "$phase" ]] || phase="unknown"
    [[ -n "$active_work" ]] || active_work="unknown"

    if [[ "$active_work" == "none" ]]; then
        authority="No active work authority; separate authorization required"
        next_action="$(eos_markdown_field "$state" "Next Immediate Step")"
        [[ -n "$next_action" ]] || next_action="Obtain separate authorization before beginning engineering work"
    else
        authority="Consult the controlled authority associated with $active_work"
        next_action="Continue authorized active work: $active_work"
    fi

    repository_state="$(eos_repository_state "$project")"
    upstream="$(eos_repository_sync_status "$project")"
    checkpoint_sync="$(eos_checkpoint_sync_status "$project" 2>/dev/null || true)"
    platform_health="PASS"
    if [[ "$repository_state" == unknown* || "$checkpoint_sync" == invalid* ]]; then
        platform_health="FAIL"
    elif [[ "$repository_state" != "clean" || "$checkpoint_sync" != "aligned" || "$upstream" == unavailable* ]]; then
        platform_health="WARNING"
    fi
    if [[ "$active_work" == "none" || "$active_work" == "unknown" || "$platform_health" == "FAIL" ]]; then
        banner="ACTION REQUIRED"
    else
        banner="READY"
    fi

    echo "===================================="
    echo "ENGINEERING WORK INITIATION — $banner"
    echo "===================================="
    echo
    echo "EXECUTIVE SUMMARY"
    echo "------------------------------------"
    printf '%-25s %s\n' "Project:" "$project_title ($project)"
    printf '%-25s %s\n' "Mission:" "$mission"
    printf '%-25s %s\n' "Phase:" "$phase"
    printf '%-25s %s\n' "Active Work:" "$active_work"
    printf '%-25s %s\n' "Current Authority:" "$authority"
    printf '%-25s %s\n' "Next Recommended Action:" "$next_action"
    printf '%-25s %s\n' "Repository Status:" "$repository_state; $upstream"
    printf '%-25s %s\n' "Platform Health:" "$platform_health"
    echo
    echo "ENGINEERING SESSION CONTRACT"
    echo "------------------------------------"
    if [[ "$active_work" == "none" ]]; then
        printf '%-25s %s\n' "Objective:" "Obtain and confirm separate engineering work authorization"
        printf '%-25s %s\n' "Authorized Work:" "None"
        printf '%-25s %s\n' "Success Criteria:" "Authorized work and its bounded success criteria are recorded"
        printf '%-25s %s\n' "Expected Closeout:" "No engineering closeout until work is separately authorized"
    else
        printf '%-25s %s\n' "Objective:" "Execute the active work within its recorded scope"
        printf '%-25s %s\n' "Authorized Work:" "$active_work"
        printf '%-25s %s\n' "Success Criteria:" "Satisfy the criteria recorded for the authorized work"
        printf '%-25s %s\n' "Expected Closeout:" "Complete the closeout required by the recorded authority"
    fi
}

eos_render_resume() {
    local project="${1:-homelab}"
    local root state checkpoint registry_context=""

    root="$(eos_project_root "$project")"
    state="$(eos_project_state "$project")"
    if declare -F eos_checkpoint_active >/dev/null 2>&1; then
        checkpoint="$(eos_checkpoint_active || true)"
    else
        checkpoint="$(eos_latest_checkpoint || true)"
    fi

    if declare -F emp_registry_context >/dev/null 2>&1; then
        registry_context="$(emp_registry_context "$project")"
    fi

    eos_render_resume_summary "$project" "$state" "$registry_context"

    echo
    eos_render_operational_status

    if declare -F eos_render_operational_summary >/dev/null 2>&1; then
        echo
        echo "------------------------------------"
        echo "ENGINEERING CONTEXT"
        echo "------------------------------------"
        eos_render_operational_summary "$project"
    fi

    echo
    echo "------------------------------------"
    echo "EOS ENGINEERING RESUME — DETAILED"
    echo "------------------------------------"
    echo
    echo "Project:"
    echo "$project"
    echo
    eos_git_summary "$project"

    if [[ -n "$registry_context" ]]; then
        echo
        echo "------------------------------------"
        echo "ENGINEERING WORK REGISTRY"
        echo "------------------------------------"
        printf '%s\n' "$registry_context"
    fi

    echo
    echo "------------------------------------"
    echo "PROJECT STATE"
    echo "------------------------------------"
    echo "$state"
    echo

    if [[ -f "$state" ]]; then
        cat "$state"
    else
        echo "Missing project state document:"
        echo "$state"
    fi

    echo
    echo "------------------------------------"
    echo "LATEST EOS CHECKPOINT"
    echo "------------------------------------"

    if [[ -n "$checkpoint" && -f "$checkpoint" ]]; then
        echo "$checkpoint"
        echo
        cat "$checkpoint"
    else
        echo "No EOS checkpoint found."
    fi

    echo
    echo "------------------------------------"
    echo "WORKING TREE"
    echo "------------------------------------"
    git -C "$root" status --short 2>/dev/null || true
}
