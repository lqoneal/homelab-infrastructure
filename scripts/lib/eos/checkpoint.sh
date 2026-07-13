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

eos_checkpoint_active_path() {
    echo "$(eos_state_dir)/ACTIVE-CHECKPOINT"
}

eos_checkpoint_retention_path() {
    echo "$(eos_state_dir)/CHECKPOINT-RETENTION"
}

eos_checkpoint_resolve() {
    local selector="${1:-latest}"
    local dir candidate resolved
    dir="$(eos_checkpoints_dir)"

    case "$selector" in
        latest)
            candidate="$(eos_checkpoint_latest)"
            ;;
        active)
            candidate="$(sed -n '1p' "$(eos_checkpoint_active_path)" 2>/dev/null || true)"
            [[ -n "$candidate" ]] || candidate="$(eos_checkpoint_latest)"
            ;;
        /*)
            candidate="$selector"
            ;;
        *)
            candidate="$dir/$selector"
            ;;
    esac

    [[ -n "$candidate" && -f "$candidate" ]] || return 1
    resolved="$(readlink -f "$candidate")"
    [[ "$resolved" == "$(readlink -f "$dir")/"*.md ]] || return 1
    echo "$resolved"
}

eos_checkpoint_active() {
    local pointer checkpoint
    pointer="$(eos_checkpoint_active_path)"

    if [[ -s "$pointer" ]]; then
        checkpoint="$(sed -n '1p' "$pointer")"
        if eos_checkpoint_resolve "$checkpoint" >/dev/null 2>&1; then
            eos_checkpoint_resolve "$checkpoint"
            return 0
        fi
    fi

    eos_checkpoint_latest
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

eos_checkpoint_restore() {
    local selector="${1:-latest}"
    local checkpoint pointer temporary
    checkpoint="$(eos_checkpoint_resolve "$selector")" || {
        echo "ERROR: checkpoint does not resolve: $selector" >&2
        return 1
    }

    pointer="$(eos_checkpoint_active_path)"
    mkdir -p "$(dirname "$pointer")"
    temporary="$(mktemp "$(dirname "$pointer")/.active-checkpoint.XXXXXX")"
    printf '%s\n' "$checkpoint" > "$temporary"
    chmod 0644 "$temporary"
    mv "$temporary" "$pointer"

    echo "$checkpoint"
}

eos_checkpoint_retention_count() {
    local policy value
    policy="$(eos_checkpoint_retention_path)"
    value="$(sed -n '1p' "$policy" 2>/dev/null || true)"

    if [[ "$value" =~ ^[1-9][0-9]*$ ]]; then
        echo "$value"
    else
        echo "10"
    fi
}

eos_checkpoint_retention_set() {
    local count="${1:-}"
    local policy temporary

    if [[ ! "$count" =~ ^[1-9][0-9]*$ || "$count" -gt 1000 ]]; then
        echo "ERROR: retention count must be an integer from 1 through 1000" >&2
        return 1
    fi

    policy="$(eos_checkpoint_retention_path)"
    mkdir -p "$(dirname "$policy")"
    temporary="$(mktemp "$(dirname "$policy")/.checkpoint-retention.XXXXXX")"
    printf '%s\n' "$count" > "$temporary"
    chmod 0644 "$temporary"
    mv "$temporary" "$policy"
}

eos_checkpoint_retention_report() {
    local count="${1:-}"
    local total recent historical

    if [[ -n "$count" ]]; then
        eos_checkpoint_retention_set "$count"
    fi
    count="$(eos_checkpoint_retention_count)"
    total="$(eos_checkpoint_list | awk 'END { print NR + 0 }')"
    recent="$total"
    [[ "$recent" -le "$count" ]] || recent="$count"
    historical=$((total - recent))

    echo "Retention Policy: preserve all checkpoints"
    echo "Recent Set: $count"
    echo "Checkpoint Count: $total"
    echo "Recent Checkpoints: $recent"
    echo "Historical Checkpoints: $historical"
    echo "Deletion: prohibited"
}

eos_checkpoint_recorded_commit() {
    local checkpoint="${1:-}"
    [[ -f "$checkpoint" ]] || return 1

    sed -n 's/^Commit: `\([^`]*\)`.*/\1/p' "$checkpoint" | head -1
}

eos_checkpoint_sync_status() {
    local project="${1:-homelab}"
    local checkpoint recorded current resolved

    checkpoint="$(eos_checkpoint_active)"
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

eos_checkpoint_validate() {
    local project="${1:-homelab}"
    local checkpoint active recorded root failures=0 count=0
    root="$(eos_project_root "$project")"
    active="$(eos_checkpoint_active || true)"

    while IFS= read -r checkpoint; do
        ((count++)) || true
        if [[ ! -s "$checkpoint" ]]; then
            echo "FAIL: empty checkpoint: $checkpoint"
            ((failures++)) || true
            continue
        fi
        if ! head -1 "$checkpoint" | grep -Eq '^# EOS Checkpoint'; then
            echo "FAIL: checkpoint heading: $checkpoint"
            ((failures++)) || true
        fi
        if ! grep -Eq '^Date: [0-9]{4}-[0-9]{2}-[0-9]{2}$' "$checkpoint"; then
            echo "FAIL: checkpoint date: $checkpoint"
            ((failures++)) || true
        fi

        recorded="$(eos_checkpoint_recorded_commit "$checkpoint" || true)"
        if [[ -n "$recorded" ]]; then
            if git -C "$root" rev-parse "$recorded^{commit}" >/dev/null 2>&1; then
                echo "PASS: $(basename "$checkpoint")"
            else
                echo "FAIL: checkpoint commit does not resolve: $checkpoint"
                ((failures++)) || true
            fi
        else
            echo "PASS: $(basename "$checkpoint") (legacy checkpoint without canonical Commit field)"
        fi
    done < <(eos_checkpoint_list)

    if [[ "$count" -eq 0 ]]; then
        echo "FAIL: no checkpoints found"
        ((failures++)) || true
    fi

    if [[ -n "$active" && -f "$active" ]]; then
        echo "PASS: active checkpoint resolves"
    else
        echo "FAIL: active checkpoint does not resolve"
        ((failures++)) || true
    fi

    if [[ "$failures" -ne 0 ]]; then
        echo "Checkpoint validation failed: $failures"
        return 1
    fi

    echo "Checkpoint validation passed: $count checkpoint(s)."
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
        active)
            checkpoint="$(eos_checkpoint_active)"
            [[ -n "$checkpoint" ]] || { echo "No active EOS checkpoint found."; return 1; }
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
        restore)
            eos_checkpoint_restore "${1:-latest}"
            ;;
        validate)
            eos_checkpoint_validate "$project"
            ;;
        retention)
            eos_checkpoint_retention_report "${1:-}"
            ;;
        *)
            echo "ERROR: unknown checkpoint action: $action" >&2
            return 1
            ;;
    esac
}
