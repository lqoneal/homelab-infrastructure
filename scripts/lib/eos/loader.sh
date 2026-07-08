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

eos_record_section() {
    local document_id="${1:-}"
    local section_title="${2:-}"
    local record_path

    if [[ -z "$document_id" ]]; then
        echo "ERROR: document_id required" >&2
        return 1
    fi

    if [[ -z "$section_title" ]]; then
        echo "ERROR: section_title required" >&2
        return 1
    fi

    record_path="$(eos_record_path "$document_id")" || return 1

    awk -v target="$section_title" '
        function trim(value) {
            sub(/^[[:space:]]+/, "", value)
            sub(/[[:space:]]+$/, "", value)
            return value
        }

        function heading_level(line, hashes) {
            if (line !~ /^#+/) {
                return 0
            }

            hashes = line
            sub(/[^#].*$/, "", hashes)
            return length(hashes)
        }

        function heading_title(line, title) {
            title = line
            sub(/^#+/, "", title)
            return trim(title)
        }

        function comparable_title(title, value) {
            value = title
            sub(/^[0-9]+([.][0-9]+)*[.][[:space:]]+/, "", value)
            return value
        }

        {
            level = heading_level($0)

            if (level > 0) {
                title = heading_title($0)

                if (in_section && level <= section_level) {
                    exit 0
                }

                if (!in_section && (title == target || comparable_title(title) == target)) {
                    in_section = 1
                    section_level = level
                    found = 1
                    next
                }
            }

            if (in_section) {
                print
            }
        }

        END {
            if (!found) {
                exit 1
            }
        }
    ' "$record_path"
}
