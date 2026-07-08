#!/usr/bin/env bash

set -Eeuo pipefail

eos_workspace() {
    echo "${EOS_WORKSPACE:-/data/engineering}"
}

eos_repositories_root() {
    echo "$(eos_workspace)/repositories"
}

eos_project_root() {
    local project="${1:-}"

    case "$project" in
        homelab)
            echo "$(eos_repositories_root)/homelab"
            ;;
        *)
            echo "ERROR: unknown project: $project" >&2
            return 1
            ;;
    esac
}
