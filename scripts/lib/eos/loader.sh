#!/usr/bin/env bash


source "$(dirname "${BASH_SOURCE[0]}")/repository.sh"

eos_record_metadata_value() {
    local document_id="${1:-}"
    local key="${2:-}"
    local record_path line metadata_opened value

    if [[ -z "$document_id" ]]; then
        echo "ERROR: document_id required" >&2
        return 1
    fi

    if [[ -z "$key" ]]; then
        echo "ERROR: metadata key required" >&2
        return 1
    fi

    record_path="$(eos_record_path "$document_id")" || return 1
    metadata_opened=0

    while IFS= read -r line; do
        if [[ "$metadata_opened" -eq 0 ]]; then
            if [[ "$line" == "---" ]]; then
                metadata_opened=1
                continue
            fi

            return 1
        fi

        if [[ "$line" == "---" ]]; then
            return 1
        fi

        if [[ "$line" == "$key:"* ]]; then
            value="${line#"$key:"}"
            value="${value#"${value%%[![:space:]]*}"}"
            printf '%s\n' "$value"
            return 0
        fi
    done < "$record_path"

    return 1
}
