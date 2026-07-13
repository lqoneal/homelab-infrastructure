#!/usr/bin/env bash

emp_management_script() {
    local library_dir
    library_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "${EMP_MANAGEMENT_SCRIPT:-$library_dir/management.py}"
}

emp_render_management() {
    local command="${1:-portfolio}"
    shift || true
    python3 "$(emp_management_script)" "$command" "$@"
}

emp_portfolio_status_context() {
    local project_id="${1:-}"
    if [[ -n "$project_id" ]]; then
        emp_render_management status "$project_id"
    else
        emp_render_management status
    fi
}
