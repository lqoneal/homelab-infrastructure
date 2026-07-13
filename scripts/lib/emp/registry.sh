#!/usr/bin/env bash

emp_registry_script() {
    local library_dir
    library_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "${EMP_REGISTRY_SCRIPT:-$library_dir/registry.py}"
}

emp_registry_path() {
    python3 "$(emp_registry_script)" path
}

emp_registry_validate() {
    python3 "$(emp_registry_script)" validate
}

emp_registry_context() {
    python3 "$(emp_registry_script)" context "${1:-homelab}"
}

emp_render_registry() {
    local action="${1:-list}"
    shift || true

    case "$action" in
        path|validate|show|list|get|context|create|update|archive|transition)
            python3 "$(emp_registry_script)" "$action" "$@"
            ;;
        *)
            echo "ERROR: unknown registry action: $action" >&2
            return 1
            ;;
    esac
}
