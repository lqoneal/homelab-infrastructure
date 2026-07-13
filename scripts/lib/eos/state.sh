#!/usr/bin/env bash

eos_state_dir() {
    echo "$(eos_workspace)/eos/state"
}

eos_state_path() {
    echo "$(eos_state_dir)/EOS-STATE.md"
}

eos_manifest_path() {
    echo "$(eos_state_dir)/EOS-MANIFEST.md"
}

eos_identity_path() {
    echo "$(eos_state_dir)/EOS-ID.md"
}

eos_frontmatter_value() {
    local path="${1:-}"
    local key="${2:-}"

    if [[ -z "$path" || -z "$key" || ! -f "$path" ]]; then
        return 1
    fi

    awk -v key="$key" '
        NR == 1 && $0 == "---" { metadata = 1; next }
        metadata && $0 == "---" { exit }
        metadata && index($0, key ":") == 1 {
            value = substr($0, length(key) + 2)
            sub(/^[[:space:]]+/, "", value)
            print value
            found = 1
            exit
        }
        END { if (!found) exit 1 }
    ' "$path"
}

eos_repository_branch() {
    local project="${1:-homelab}"
    git -C "$(eos_project_root "$project")" branch --show-current 2>/dev/null
}

eos_repository_commit() {
    local project="${1:-homelab}"
    git -C "$(eos_project_root "$project")" rev-parse HEAD 2>/dev/null
}

eos_repository_dirty_count() {
    local project="${1:-homelab}"
    git -C "$(eos_project_root "$project")" status --porcelain 2>/dev/null | awk 'END { print NR + 0 }'
}

eos_repository_state() {
    local project="${1:-homelab}"
    local count
    count="$(eos_repository_dirty_count "$project")"

    if [[ "$count" -eq 0 ]]; then
        echo "clean"
    else
        echo "modified ($count path(s))"
    fi
}

eos_render_state() {
    local state
    state="$(eos_state_path)"

    echo "EOS State:"
    echo "$state"
    echo

    if [[ ! -f "$state" ]]; then
        echo "ERROR: EOS state record is missing." >&2
        return 1
    fi

    cat "$state"
}

eos_validate_state() {
    local project="${1:-homelab}"
    local failures=0
    local required state project_state checkpoint_count

    for required in "$(eos_identity_path)" "$(eos_state_path)" "$(eos_manifest_path)"; do
        if [[ -s "$required" ]]; then
            echo "PASS: $required"
        else
            echo "FAIL: missing or empty EOS state record: $required"
            ((failures++)) || true
        fi
    done

    state="$(eos_state_path)"
    if [[ "$(eos_frontmatter_value "$state" document_id 2>/dev/null || true)" == "EOS-STATE" \
        && "$(eos_frontmatter_value "$state" status 2>/dev/null || true)" == "Active" ]]; then
        echo "PASS: EOS state identity and lifecycle"
    else
        echo "FAIL: EOS state identity or lifecycle"
        ((failures++)) || true
    fi

    if [[ -d "$(eos_workspace)/eos/checkpoints" ]]; then
        echo "PASS: EOS checkpoint directory"
        checkpoint_count="$(find "$(eos_workspace)/eos/checkpoints" -maxdepth 1 -type f -name '*.md' | awk 'END { print NR + 0 }')"
        if [[ "$checkpoint_count" -gt 0 ]]; then
            echo "PASS: EOS checkpoint inventory ($checkpoint_count)"
        else
            echo "FAIL: EOS checkpoint inventory is empty"
            ((failures++)) || true
        fi
    else
        echo "FAIL: EOS checkpoint directory missing"
        ((failures++)) || true
    fi

    if git -C "$(eos_project_root "$project")" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "PASS: $project repository"
    else
        echo "FAIL: $project repository unavailable"
        ((failures++)) || true
    fi

    project_state="$(eos_project_state "$project")"
    if [[ -s "$project_state" \
        && "$(eos_frontmatter_value "$project_state" status 2>/dev/null || true)" == "Active" ]]; then
        echo "PASS: $project project state"
    else
        echo "FAIL: $project project state missing"
        ((failures++)) || true
    fi

    if [[ "$failures" -ne 0 ]]; then
        echo "EOS state validation failed: $failures"
        return 1
    fi

    echo "EOS state validation passed."
}
