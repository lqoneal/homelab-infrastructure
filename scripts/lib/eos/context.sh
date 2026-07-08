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
