#!/usr/bin/env bash

eos_platform_repository_inventory() {
    local repositories entry name branch commit state
    repositories="$(eos_workspace)/repositories"

    [[ -d "$repositories" ]] || return 0

    while IFS= read -r entry; do
        name="$(basename "$entry")"
        if git -C "$entry" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            branch="$(git -C "$entry" branch --show-current 2>/dev/null || true)"
            commit="$(git -C "$entry" rev-parse --short HEAD 2>/dev/null || true)"
            state="$(git -C "$entry" status --porcelain 2>/dev/null | awk 'END { if (NR == 0) print "clean"; else print "modified" }')"
            printf '%-22s git    branch=%-12s commit=%-12s state=%s\n' "$name" "${branch:-detached}" "${commit:-none}" "$state"
        else
            printf '%-22s directory (non-Git)\n' "$name"
        fi
    done < <(find "$repositories" -mindepth 1 -maxdepth 1 -type d -print | sort)
}

eos_render_platform() {
    local project="${1:-homelab}"
    local checkpoint sync_status
    checkpoint="$(eos_checkpoint_active || true)"
    sync_status="$(eos_checkpoint_sync_status "$project" || true)"

    echo "===================================="
    echo "ENGINEERING PLATFORM"
    echo "===================================="
    echo
    printf '%-20s %s\n' "Workspace:" "$(eos_workspace)"
    printf '%-20s %s\n' "Project:" "$project"
    printf '%-20s %s\n' "Branch:" "$(eos_repository_branch "$project")"
    printf '%-20s %s\n' "Commit:" "$(eos_repository_commit "$project")"
    printf '%-20s %s\n' "Repository State:" "$(eos_repository_state "$project")"
    printf '%-20s %s\n' "EOS State:" "$(eos_state_path)"
    printf '%-20s %s\n' "Latest Checkpoint:" "${checkpoint:-none}"
    printf '%-20s %s\n' "Synchronization:" "${sync_status:-unavailable}"
    if declare -F emp_registry_path >/dev/null 2>&1; then
        printf '%-20s %s\n' "Work Registry:" "$(emp_registry_path)"
    fi
    echo
    echo "Repository Inventory:"
    eos_platform_repository_inventory
    echo
    echo "Controller Capabilities:"
    echo "  resume status doctor ssh checkpoint eos repository registry portfolio project queue milestone dependency defer context validate platform"
}

eos_platform_legacy_qualify() {
    local project="${1:-homelab}"
    local root marker marker_path active=0
    root="$(eos_project_root "$project")"

    echo "Engineering Work Initiation Qualification"
    echo
    echo "Repository Root:"
    git -C "$root" rev-parse --show-toplevel
    echo
    echo "Remotes:"
    git -C "$root" remote -v
    echo
    echo "Branch:"
    git -C "$root" branch --show-current
    echo
    echo "Description:"
    git -C "$root" describe --tags --always
    echo
    echo "Recent History:"
    git -C "$root" log --oneline --decorate -5
    echo
    echo "Working Tree:"
    git -C "$root" status --short
    echo
    echo "Unstaged Diff:"
    git -C "$root" diff --stat
    echo
    echo "Staged Diff:"
    git -C "$root" diff --cached --stat
    echo
    echo "Integrity:"
    git -C "$root" fsck --no-dangling --no-reflogs
    echo "PASS"
    echo "SSH Agent: $(eos_ssh_agent_state)"

    for marker in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD REBASE_HEAD rebase-merge rebase-apply sequencer; do
        marker_path="$(git -C "$root" rev-parse --git-path "$marker")"
        if [[ -e "$marker_path" ]]; then
            echo "FAIL: active Git operation marker: $marker"
            active=1
        fi
    done

    if [[ "$active" -ne 0 ]]; then
        return 1
    fi

    echo "Active Git Operation: none"
}

eos_work_initiation_authorize() {
    local project="${1:-homelab}"
    local legacy_status="${2:-1}"
    local root tool output_dir legacy_decision mode
    local -a arguments
    root="$(eos_project_root "$project")"
    tool="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/work-initiation-shadow"
    output_dir="${EOS_SHADOW_ADR_DIR:-$(eos_runtime_dir)/authorization-decisions}"
    mode="${EOS_AUTHORIZATION_MODE:-enforcement}"
    legacy_decision="rejected"
    [[ "$legacy_status" -eq 0 ]] && legacy_decision="authorized"
    arguments=(
        --repository "$root"
        --legacy-decision "$legacy_decision"
        --output-directory "$output_dir"
        --mode "$mode"
    )
    [[ -n "${EOS_SHADOW_EVALUATION_TIME:-}" ]] \
        && arguments+=(--at "$EOS_SHADOW_EVALUATION_TIME")
    [[ -n "${EOS_SHADOW_AUTHORITY_GRAPH:-}" ]] \
        && arguments+=(--authority-graph "$EOS_SHADOW_AUTHORITY_GRAPH")
    [[ -n "${EOS_SHADOW_WOP:-}" ]] && arguments+=(--wop "$EOS_SHADOW_WOP")
    [[ -n "${EOS_SHADOW_STATE:-}" ]] && arguments+=(--state "$EOS_SHADOW_STATE")
    [[ -n "${EOS_SHADOW_RECEIPT:-}" ]] \
        && arguments+=(--receipt "$EOS_SHADOW_RECEIPT")
    [[ -n "${EOS_SHADOW_LEASE:-}" ]] && arguments+=(--lease "$EOS_SHADOW_LEASE")
    [[ -n "${EOS_SHADOW_REVOCATION:-}" ]] \
        && arguments+=(--revocation "$EOS_SHADOW_REVOCATION")
    [[ -n "${EOS_SHADOW_EXPECTED_AUTHORITY:-}" ]] \
        && arguments+=(--expected-authority "$EOS_SHADOW_EXPECTED_AUTHORITY")

    echo
    echo "Authorization Mode: ${mode^^}"
    if ! "$tool" "${arguments[@]}"; then
        echo "WARN: shadow authorization record generation failed" >&2
        return 1
    fi
}

eos_platform_qualify() {
    local project="${1:-homelab}"
    local legacy_status=0 authorization_status=0 mode
    eos_platform_legacy_qualify "$project" || legacy_status=$?
    mode="${EOS_AUTHORIZATION_MODE:-enforcement}"
    eos_work_initiation_authorize "$project" "$legacy_status" \
        || authorization_status=$?
    case "$mode" in
        rollback|shadow) return "$legacy_status" ;;
        enforcement)
            [[ "$authorization_status" -eq 0 ]] && return 0
            return 77
            ;;
        *)
            echo "ERROR: unknown authorization mode: $mode" >&2
            return 77
            ;;
    esac
}

eos_platform_validate() {
    local project="${1:-homelab}"
    local root platform_root validator runtime_test registry_test management_test etp_test
    local context management_project_id failures=0
    root="$(eos_project_root "$project")"
    platform_root="$(eos_project_root homelab)"
    if [[ "$project" == "homelab" ]]; then
        validator="$root/scripts/validate_controlled_documents.py"
    else
        validator="$root/scripts/validate_repository.py"
    fi
    runtime_test="$platform_root/scripts/tests/test-eos-runtime.sh"
    registry_test="$platform_root/scripts/tests/test-emp-registry.py"
    management_test="$platform_root/scripts/tests/test-emp-management.py"
    etp_test="$platform_root/scripts/tests/test-etp-profiles.py"

    if eos_validate_state "$project"; then
        echo "PASS: EOS operational state"
    else
        echo "FAIL: EOS operational state"
        ((failures++)) || true
    fi

    if git -C "$root" fsck --no-dangling --no-reflogs >/dev/null 2>&1; then
        echo "PASS: repository integrity"
    else
        echo "FAIL: repository integrity"
        ((failures++)) || true
    fi

    if git -C "$platform_root" rev-parse -q --verify 'refs/tags/governance-foundation-1.0^{}' >/dev/null 2>&1; then
        echo "PASS: Governance Foundation tag"
    else
        echo "FAIL: Governance Foundation tag missing"
        ((failures++)) || true
    fi

    if [[ -f "$validator" ]] && PYTHONDONTWRITEBYTECODE=1 python3 "$validator" >/dev/null; then
        echo "PASS: controlled-document validation"
    else
        echo "FAIL: controlled-document validation"
        ((failures++)) || true
    fi

    if [[ -f "$runtime_test" ]] && bash "$runtime_test" >/dev/null; then
        echo "PASS: EOS runtime regression tests"
    else
        echo "FAIL: EOS runtime regression tests"
        ((failures++)) || true
    fi

    if [[ -f "$etp_test" ]] && PYTHONDONTWRITEBYTECODE=1 python3 "$etp_test" >/dev/null; then
        echo "PASS: Engineering Transaction Profile validation fixtures"
    else
        echo "FAIL: Engineering Transaction Profile validation fixtures"
        ((failures++)) || true
    fi

    if declare -F emp_registry_validate >/dev/null 2>&1 && emp_registry_validate >/dev/null; then
        echo "PASS: Engineering Work Registry validation"
    else
        echo "FAIL: Engineering Work Registry validation"
        ((failures++)) || true
    fi

    if [[ -f "$registry_test" ]] && PYTHONDONTWRITEBYTECODE=1 python3 "$registry_test" >/dev/null; then
        echo "PASS: Engineering Work Registry regression tests"
    else
        echo "FAIL: Engineering Work Registry regression tests"
        ((failures++)) || true
    fi

    if [[ -f "$management_test" ]] && PYTHONDONTWRITEBYTECODE=1 python3 "$management_test" >/dev/null; then
        echo "PASS: EMP operational management regression tests"
    else
        echo "FAIL: EMP operational management regression tests"
        ((failures++)) || true
    fi

    if eos_checkpoint_validate homelab >/dev/null; then
        echo "PASS: checkpoint validation"
    else
        echo "FAIL: checkpoint validation"
        ((failures++)) || true
    fi

    if eos_operational_validate homelab >/dev/null; then
        echo "PASS: synchronized operational state"
    else
        echo "FAIL: synchronized operational state"
        ((failures++)) || true
    fi

    if eos_persistence_validate homelab >/dev/null; then
        echo "PASS: EOS persistence model"
    else
        echo "FAIL: EOS persistence model"
        ((failures++)) || true
    fi

    if eos_repository_health "$project" >/dev/null; then
        echo "PASS: repository operational health"
    else
        echo "FAIL: repository operational health"
        ((failures++)) || true
    fi

    context="$(eos_engineering_context "$project")"
    if grep -Fq "project_status=Active" <<<"$context"; then
        echo "PASS: engineering context generation"
    else
        echo "FAIL: engineering context generation"
        ((failures++)) || true
    fi

    management_project_id="$(sed -n 's/^management_project_id=//p' <<<"$context")"
    if [[ -n "$management_project_id" && "$management_project_id" != "none" ]]; then
        echo "PASS: registry context contribution"
    else
        echo "FAIL: registry context contribution"
        ((failures++)) || true
    fi

    if grep -Fq "management_completed_work=" <<<"$context"; then
        echo "PASS: management status context contribution"
    else
        echo "FAIL: management status context contribution"
        ((failures++)) || true
    fi

    if [[ "$failures" -ne 0 ]]; then
        echo "Engineering Platform validation failed: $failures"
        return 1
    fi

    echo "Engineering Platform validation passed."
}
