#!/usr/bin/env bash

set -Eeuo pipefail

eos_workspace() {
    echo "${EOS_WORKSPACE:-/data/engineering}"
}

eos_project_root() {
    local project="${1:-homelab}"
    case "$project" in
        homelab)
            echo "$(eos_workspace)/repositories/homelab"
            ;;
        *)
            echo "ERROR: unknown project: $project" >&2
            return 1
            ;;
    esac
}

eos_project_state() {
    local project="${1:-homelab}"
    echo "$(eos_project_root "$project")/docs/project/PROJ-0001-PROJECT_STATE.md"
}

eos_latest_checkpoint() {
    local workspace
    workspace="$(eos_workspace)"

    find "$workspace/eos/checkpoints" -type f -name "*.md" 2>/dev/null | sort | tail -1
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

eos_render_operational_status() {
    echo "------------------------------------"
    echo "OPERATIONAL STATUS"
    echo "------------------------------------"
    printf "%-18s %s\n" "SSH:" "$(eos_service_state ssh)"
    printf "%-18s %s\n" "Host Firewall:" "$(eos_service_state ufw)"
    printf "%-18s %s\n" "Print Services:" "$(eos_service_state cups)"
    printf "%-18s %s\n" "PDF Printing:" "$(eos_pdf_printing_state)"
    printf "%-18s %s\n" "Scanner Workflow:" "$(eos_scanner_workflow_state)"
    printf "%-18s %s\n" "Avahi:" "$(eos_service_state avahi-daemon)"
    printf "%-18s %s\n" "Scanner Tools:" "$(eos_command_state scanimage)"
}

eos_render_resume() {
    local project="${1:-homelab}"
    local root state checkpoint

    root="$(eos_project_root "$project")"
    state="$(eos_project_state "$project")"
    checkpoint="$(eos_latest_checkpoint || true)"

    echo "===================================="
    echo "EOS ENGINEERING RESUME"
    echo "===================================="
    echo
    echo "Project:"
    echo "$project"
    echo

    eos_git_summary "$project"

    echo
    eos_render_operational_status

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
