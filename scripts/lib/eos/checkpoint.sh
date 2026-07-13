#!/usr/bin/env bash

eos_checkpoints_dir() {
    echo "$(eos_workspace)/eos/checkpoints"
}

eos_checkpoint_list() {
    local dir
    dir="$(eos_checkpoints_dir)"

    [[ -d "$dir" ]] || return 0
    find "$dir" -maxdepth 1 -type f -name '*.md' -print | sort
}

eos_checkpoint_latest() {
    eos_checkpoint_list | tail -1
}

eos_checkpoint_slug() {
    local title="${1:-}"
    printf '%s' "$title" \
        | tr '[:upper:]' '[:lower:]' \
        | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' \
        | cut -c1-80
}

eos_checkpoint_create() {
    local project="${1:-homelab}"
    shift || true
    local title="${*:-}"
    local dir slug timestamp path temporary root branch commit tree_state status

    title="${title//$'\n'/ }"
    if [[ -z "$title" ]]; then
        echo "ERROR: checkpoint title required" >&2
        return 1
    fi

    root="$(eos_project_root "$project")"
    if ! git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "ERROR: project repository unavailable: $root" >&2
        return 1
    fi

    dir="$(eos_checkpoints_dir)"
    mkdir -p "$dir"
    slug="$(eos_checkpoint_slug "$title")"
    [[ -n "$slug" ]] || slug="checkpoint"
    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    path="$dir/${timestamp}-${slug}.md"

    if [[ -e "$path" ]]; then
        echo "ERROR: checkpoint already exists: $path" >&2
        return 1
    fi

    branch="$(eos_repository_branch "$project")"
    commit="$(eos_repository_commit "$project")"
    tree_state="$(eos_repository_state "$project")"
    status="$(git -C "$root" status --short)"
    [[ -n "$status" ]] || status="clean"

    temporary="$(mktemp "$dir/.checkpoint.XXXXXX")"
    {
        echo "# EOS Checkpoint — $title"
        echo
        echo "Date: $(date -u +%Y-%m-%d)"
        echo
        echo "## Status"
        echo
        echo "Captured"
        echo
        echo "## Project"
        echo
        echo "$project"
        echo
        echo "## Repository"
        echo
        echo "Root: \`$root\`"
        echo
        echo "Branch: \`$branch\`"
        echo
        echo "Commit: \`$commit\`"
        echo
        echo "Working tree: $tree_state"
        echo
        echo '```text'
        echo "$status"
        echo '```'
        echo
        echo "## Project State"
        echo
        echo "\`$(eos_project_state "$project")\`"
    } > "$temporary"
    chmod 0644 "$temporary"
    mv "$temporary" "$path"

    echo "$path"
}

eos_checkpoint_recorded_commit() {
    local checkpoint="${1:-}"
    [[ -f "$checkpoint" ]] || return 1

    sed -n 's/^Commit: `\([^`]*\)`.*/\1/p' "$checkpoint" | head -1
}

eos_checkpoint_sync_status() {
    local project="${1:-homelab}"
    local checkpoint recorded current resolved

    checkpoint="$(eos_checkpoint_latest)"
    if [[ -z "$checkpoint" ]]; then
        echo "unavailable (no checkpoint)"
        return 1
    fi

    recorded="$(eos_checkpoint_recorded_commit "$checkpoint" || true)"
    current="$(eos_repository_commit "$project")"
    if [[ -z "$recorded" ]]; then
        echo "unavailable (checkpoint has no repository commit)"
        return 1
    fi

    resolved="$(git -C "$(eos_project_root "$project")" rev-parse "$recorded^{commit}" 2>/dev/null || true)"
    if [[ -z "$resolved" ]]; then
        echo "invalid (checkpoint commit does not resolve)"
        return 1
    fi

    if [[ "$resolved" == "$current" ]]; then
        echo "aligned"
    else
        echo "drifted (checkpoint ${recorded:0:12}, repository ${current:0:12})"
    fi
}

eos_render_checkpoint() {
    local action="${1:-latest}"
    shift || true
    local project="${EOS_PROJECT:-homelab}"
    local checkpoint

    case "$action" in
        latest)
            checkpoint="$(eos_checkpoint_latest)"
            if [[ -z "$checkpoint" ]]; then
                echo "No EOS checkpoint found."
                return 1
            fi
            echo "$checkpoint"
            echo
            cat "$checkpoint"
            ;;
        list)
            eos_checkpoint_list
            ;;
        create)
            eos_checkpoint_create "$project" "$@"
            ;;
        *)
            echo "ERROR: unknown checkpoint action: $action" >&2
            return 1
            ;;
    esac
}
