#!/usr/bin/env bash


declare -gA EOS_RECORD_REGISTRY=()
declare -g EOS_RECORD_REGISTRY_INITIALIZED=0

eos_workspace() {
    echo "${EOS_WORKSPACE:-/data/engineering}"
}

eos_repositories_root() {
    echo "$(eos_workspace)/repositories"
}

eos_project_root() {
    local project="${1:-}"
    local repositories candidate resolved

    if [[ -z "$project" ]]; then
        echo "ERROR: project name required" >&2
        return 1
    fi

    if [[ ! "$project" =~ ^[A-Za-z0-9._-]+$ ]]; then
        echo "ERROR: invalid project name: $project" >&2
        return 1
    fi

    repositories="$(eos_repositories_root)"
    candidate="$repositories/$project"
    if [[ -d "$candidate" ]]; then
        echo "$candidate"
        return 0
    fi

    resolved="$(find "$repositories" -mindepth 1 -maxdepth 1 -type d -iname "$project" -print 2>/dev/null | sort | head -2)"
    if [[ "$(wc -l <<<"$resolved")" -eq 1 && -n "$resolved" ]]; then
        echo "$resolved"
        return 0
    fi

    echo "ERROR: unknown project: $project" >&2
    return 1
}

eos_registry_initialize() {
    local project="${1:-homelab}"
    local root file id existing

    root="$(eos_project_root "$project")"

    EOS_RECORD_REGISTRY=()

    while IFS= read -r file; do
        id="$(grep -m1 '^document_id:' "$file" 2>/dev/null | sed 's/^document_id:[[:space:]]*//')"

        [[ -z "$id" ]] && continue

        existing="${EOS_RECORD_REGISTRY[$id]:-}"

        if [[ -n "$existing" ]]; then
            echo "ERROR: duplicate document_id: $id" >&2
            echo "  $existing" >&2
            echo "  $file" >&2
            return 1
        fi

        EOS_RECORD_REGISTRY["$id"]="$file"
    done < <(find "$root/docs" -type f -name "*.md" 2>/dev/null | sort)

    EOS_RECORD_REGISTRY_INITIALIZED=1
}

eos_registry_require_initialized() {
    if [[ "$EOS_RECORD_REGISTRY_INITIALIZED" -ne 1 ]]; then
        eos_registry_initialize homelab
    fi
}

eos_record_path() {
    local document_id="${1:-}"

    if [[ -z "$document_id" ]]; then
        echo "ERROR: document_id required" >&2
        return 1
    fi

    eos_registry_require_initialized

    if [[ -n "${EOS_RECORD_REGISTRY[$document_id]:-}" ]]; then
        echo "${EOS_RECORD_REGISTRY[$document_id]}"
        return 0
    fi

    echo "ERROR: unknown document_id: $document_id" >&2
    return 1
}

eos_record_exists() {
    local document_id="${1:-}"

    [[ -z "$document_id" ]] && return 1

    eos_registry_require_initialized

    [[ -n "${EOS_RECORD_REGISTRY[$document_id]:-}" ]]
}

eos_record_list() {
    eos_registry_require_initialized

    printf '%s\n' "${!EOS_RECORD_REGISTRY[@]}" | sort
}
