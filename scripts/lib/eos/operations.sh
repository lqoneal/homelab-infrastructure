#!/usr/bin/env bash

eos_runtime_dir() {
    echo "$(eos_workspace)/eos/runtime"
}

eos_operational_state_path() {
    echo "$(eos_runtime_dir)/operational-state.json"
}

eos_repository_inventory_path() {
    echo "$(eos_runtime_dir)/repositories.tsv"
}

eos_repository_discover() {
    local repositories entry name type branch commit state upstream divergence ahead behind remote
    repositories="$(eos_workspace)/repositories"

    printf 'name\tpath\ttype\tbranch\tcommit\tstate\tupstream\tahead\tbehind\tremote\n'
    [[ -d "$repositories" ]] || return 0

    while IFS= read -r entry; do
        name="$(basename "$entry")"
        if git -C "$entry" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            type="git"
            branch="$(git -C "$entry" branch --show-current 2>/dev/null || true)"
            commit="$(git -C "$entry" rev-parse HEAD 2>/dev/null || true)"
            state="$(git -C "$entry" status --porcelain 2>/dev/null | awk 'END { if (NR == 0) print "clean"; else print "modified" }')"
            upstream="$(git -C "$entry" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)"
            ahead=""
            behind=""
            if [[ -n "$upstream" ]]; then
                divergence="$(git -C "$entry" rev-list --left-right --count "HEAD...$upstream" 2>/dev/null || true)"
                ahead="${divergence%%[[:space:]]*}"
                behind="${divergence##*[[:space:]]}"
            fi
            remote="$(git -C "$entry" remote get-url origin 2>/dev/null || true)"
        else
            type="directory"
            branch=""
            commit=""
            state="present"
            upstream=""
            ahead=""
            behind=""
            remote=""
        fi
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$name" "$entry" "$type" "$branch" "$commit" "$state" "$upstream" "$ahead" "$behind" "$remote"
    done < <(find "$repositories" -mindepth 1 -maxdepth 1 -type d -print | sort)
}

eos_repository_inventory_refresh() {
    local destination temporary
    destination="$(eos_repository_inventory_path)"
    mkdir -p "$(dirname "$destination")"
    temporary="$(mktemp "$(dirname "$destination")/.repositories.XXXXXX")"
    eos_repository_discover > "$temporary"
    chmod 0644 "$temporary"
    mv "$temporary" "$destination"
    echo "$destination"
}

eos_repository_sync_status() {
    local project="${1:-homelab}"
    local root upstream divergence ahead behind
    root="$(eos_project_root "$project")"
    upstream="$(git -C "$root" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)"

    if [[ -z "$upstream" ]]; then
        echo "unavailable (no upstream configured)"
        return 0
    fi

    divergence="$(git -C "$root" rev-list --left-right --count "HEAD...$upstream")"
    ahead="${divergence%%[[:space:]]*}"
    behind="${divergence##*[[:space:]]}"

    if [[ "$ahead" -eq 0 && "$behind" -eq 0 ]]; then
        echo "aligned ($upstream)"
    else
        echo "diverged ($upstream: ahead=$ahead behind=$behind)"
    fi
}

eos_repository_health() {
    local project="${1:-homelab}"
    local root failures=0
    root="$(eos_project_root "$project")"

    if git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "PASS: repository discovery"
    else
        echo "FAIL: repository discovery"
        return 1
    fi

    if git -C "$root" fsck --no-dangling --no-reflogs >/dev/null 2>&1; then
        echo "PASS: repository integrity"
    else
        echo "FAIL: repository integrity"
        ((failures++)) || true
    fi

    if [[ -n "$(eos_repository_branch "$project")" ]]; then
        echo "PASS: active branch $(eos_repository_branch "$project")"
    else
        echo "FAIL: detached or missing branch"
        ((failures++)) || true
    fi

    echo "Repository State: $(eos_repository_state "$project")"
    echo "Upstream State: $(eos_repository_sync_status "$project")"

    [[ "$failures" -eq 0 ]] || return 1
    echo "Repository health passed."
}

eos_git_operation_active() {
    local project="${1:-homelab}"
    local root marker path
    root="$(eos_project_root "$project")"
    for marker in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD REBASE_HEAD rebase-merge rebase-apply sequencer; do
        path="$(git -C "$root" rev-parse --git-path "$marker")"
        [[ ! -e "$path" ]] || return 0
    done
    return 1
}

eos_publication_readiness() {
    local project="${1:-homelab}"
    local root validator staged failures=0
    root="$(eos_project_root "$project")"
    validator="$root/scripts/validate_controlled_documents.py"

    if eos_git_operation_active "$project"; then
        echo "FAIL: active Git operation"
        ((failures++)) || true
    else
        echo "PASS: no active Git operation"
    fi

    if git -C "$root" fsck --no-dangling --no-reflogs >/dev/null 2>&1; then
        echo "PASS: repository integrity"
    else
        echo "FAIL: repository integrity"
        ((failures++)) || true
    fi

    if [[ -f "$validator" ]] && ! PYTHONDONTWRITEBYTECODE=1 python3 "$validator" >/dev/null; then
        echo "FAIL: controlled-document validation"
        ((failures++)) || true
    else
        echo "PASS: controlled-document validation"
    fi

    if git -C "$root" diff --cached --check; then
        echo "PASS: staged whitespace"
    else
        echo "FAIL: staged whitespace"
        ((failures++)) || true
    fi

    staged="$(git -C "$root" diff --cached --name-only | awk 'END { print NR + 0 }')"
    if [[ "$staged" -gt 0 ]]; then
        echo "PASS: staged publication set ($staged path(s))"
    else
        echo "FAIL: no staged publication set"
        ((failures++)) || true
    fi

    echo "Unstaged Paths: $(git -C "$root" status --porcelain | awk 'substr($0, 1, 2) == "??" || substr($0, 2, 1) != " " { count++ } END { print count + 0 }')"

    if [[ "$failures" -ne 0 ]]; then
        echo "Publication readiness failed: $failures"
        return 1
    fi

    echo "Publication readiness passed."
}

eos_engineering_context() {
    local project="${1:-homelab}"
    local project_state eos_state checkpoint
    project_state="$(eos_project_state "$project")"
    eos_state="$(eos_state_path)"
    checkpoint="$(eos_checkpoint_active || true)"

    echo "Engineering Context"
    echo "project=$project"
    echo "project_state=$project_state"
    echo "project_status=$(eos_frontmatter_value "$project_state" status 2>/dev/null || echo unknown)"
    echo "project_phase=$(eos_frontmatter_value "$project_state" phase 2>/dev/null || echo unknown)"
    echo "repository_root=$(eos_project_root "$project")"
    echo "repository_branch=$(eos_repository_branch "$project")"
    echo "repository_commit=$(eos_repository_commit "$project")"
    echo "repository_state=$(eos_repository_state "$project")"
    echo "repository_upstream=$(eos_repository_sync_status "$project")"
    echo "eos_state=$eos_state"
    echo "eos_version=$(eos_frontmatter_value "$eos_state" version 2>/dev/null || echo unknown)"
    echo "eos_status=$(eos_frontmatter_value "$eos_state" status 2>/dev/null || echo unknown)"
    echo "active_checkpoint=${checkpoint:-none}"
    echo "checkpoint_sync=$(eos_checkpoint_sync_status "$project" || true)"
}

eos_operational_refresh() {
    local project="${1:-homelab}"
    local destination temporary checkpoint checkpoint_commit checkpoint_sync publication_state
    destination="$(eos_operational_state_path)"
    mkdir -p "$(dirname "$destination")"
    eos_repository_inventory_refresh >/dev/null

    checkpoint="$(eos_checkpoint_active || true)"
    checkpoint_commit="$(eos_checkpoint_recorded_commit "$checkpoint" 2>/dev/null || true)"
    checkpoint_sync="$(eos_checkpoint_sync_status "$project" || true)"
    if git -C "$(eos_project_root "$project")" diff --cached --quiet; then
        publication_state="no-staged-publication"
    else
        publication_state="staged"
    fi

    temporary="$(mktemp "$(dirname "$destination")/.operational-state.XXXXXX")"
    jq -n \
        --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg project "$project" \
        --arg root "$(eos_project_root "$project")" \
        --arg branch "$(eos_repository_branch "$project")" \
        --arg commit "$(eos_repository_commit "$project")" \
        --arg repository_state "$(eos_repository_state "$project")" \
        --arg upstream_state "$(eos_repository_sync_status "$project")" \
        --arg eos_state "$(eos_state_path)" \
        --arg checkpoint "$checkpoint" \
        --arg checkpoint_commit "$checkpoint_commit" \
        --arg checkpoint_sync "$checkpoint_sync" \
        --arg publication_state "$publication_state" \
        --arg inventory "$(eos_repository_inventory_path)" \
        '{schema_version: 1, generated_at: $generated_at, project: $project,
          repository: {root: $root, branch: $branch, commit: $commit, state: $repository_state, upstream: $upstream_state},
          eos: {state_record: $eos_state, active_checkpoint: $checkpoint, checkpoint_commit: $checkpoint_commit, synchronization: $checkpoint_sync},
          publication: {state: $publication_state}, inventory: $inventory}' > "$temporary"
    chmod 0644 "$temporary"
    mv "$temporary" "$destination"
    echo "$destination"
}

eos_operational_validate() {
    local project="${1:-homelab}"
    local state expected_commit observed_commit checkpoint
    state="$(eos_operational_state_path)"
    [[ -s "$state" ]] || { echo "FAIL: operational state missing"; return 1; }
    jq -e '.schema_version == 1 and .project and .repository.commit and .eos.active_checkpoint' "$state" >/dev/null \
        || { echo "FAIL: operational state schema"; return 1; }

    expected_commit="$(eos_repository_commit "$project")"
    observed_commit="$(jq -r '.repository.commit' "$state")"
    [[ "$expected_commit" == "$observed_commit" ]] \
        || { echo "FAIL: operational state repository commit is stale"; return 1; }

    checkpoint="$(jq -r '.eos.active_checkpoint' "$state")"
    [[ "$checkpoint" == "$(eos_checkpoint_active)" ]] \
        || { echo "FAIL: operational state checkpoint is stale"; return 1; }

    [[ -s "$(eos_repository_inventory_path)" ]] \
        || { echo "FAIL: repository inventory missing"; return 1; }

    echo "Operational state validation passed."
}

eos_persistence_validate() {
    local project="${1:-homelab}"
    local inventory pointer retention failures=0
    inventory="$(eos_repository_inventory_path)"
    pointer="$(eos_checkpoint_active_path)"
    retention="$(eos_checkpoint_retention_path)"

    if eos_operational_validate "$project" >/dev/null; then
        echo "PASS: regenerable operational state"
    else
        echo "FAIL: regenerable operational state"
        ((failures++)) || true
    fi

    if [[ -s "$inventory" ]] \
        && [[ "$(sed -n '1p' "$inventory")" == $'name\tpath\ttype\tbranch\tcommit\tstate\tupstream\tahead\tbehind\tremote' ]]; then
        echo "PASS: regenerable repository inventory"
    else
        echo "FAIL: repository inventory schema"
        ((failures++)) || true
    fi

    if [[ -s "$pointer" ]] && [[ "$(awk 'END { print NR + 0 }' "$pointer")" -eq 1 ]] \
        && eos_checkpoint_resolve "$(sed -n '1p' "$pointer")" >/dev/null 2>&1; then
        echo "PASS: authoritative active-checkpoint pointer"
    else
        echo "FAIL: active-checkpoint pointer persistence"
        ((failures++)) || true
    fi

    if [[ -s "$retention" ]] \
        && [[ "$(awk 'END { print NR + 0 }' "$retention")" -eq 1 ]] \
        && [[ "$(sed -n '1p' "$retention")" =~ ^[1-9][0-9]*$ ]] \
        && [[ "$(sed -n '1p' "$retention")" -le 1000 ]]; then
        echo "PASS: authoritative checkpoint-retention setting"
    else
        echo "FAIL: checkpoint-retention setting persistence"
        ((failures++)) || true
    fi

    if eos_checkpoint_validate "$project" >/dev/null; then
        echo "PASS: append-only checkpoint metadata"
    else
        echo "FAIL: append-only checkpoint metadata"
        ((failures++)) || true
    fi

    if [[ "$failures" -ne 0 ]]; then
        echo "EOS persistence validation failed: $failures"
        return 1
    fi

    echo "EOS persistence validation passed."
}

eos_render_operational_summary() {
    local project="${1:-homelab}"
    printf '%-22s %s\n' "Active Checkpoint:" "$(eos_checkpoint_active || echo none)"
    printf '%-22s %s\n' "Checkpoint Sync:" "$(eos_checkpoint_sync_status "$project" || true)"
    printf '%-22s %s\n' "Repository Upstream:" "$(eos_repository_sync_status "$project")"
    printf '%-22s %s\n' "Operational State:" "$(eos_operational_state_path)"
    printf '%-22s %s\n' "Repository Inventory:" "$(eos_repository_inventory_path)"
}

eos_render_repository_operation() {
    local action="${1:-health}"
    local project="${2:-${EOS_PROJECT:-homelab}}"
    case "$action" in
        discover) eos_repository_discover ;;
        health) eos_repository_health "$project" ;;
        sync-status) eos_repository_sync_status "$project" ;;
        readiness) eos_publication_readiness "$project" ;;
        refresh) eos_repository_inventory_refresh ;;
        *) echo "ERROR: unknown repository action: $action" >&2; return 1 ;;
    esac
}
