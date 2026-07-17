#!/usr/bin/env bash

# Reusable ntfy transport for Engineering Operations. This file is sourced by
# controllers; it intentionally does not enable or alter the caller's shell
# options.

notify_ntfy_config_file() {
    local repository_root="${1:-}"

    if [[ -n "${NTFY_CONFIG_FILE:-}" ]]; then
        printf '%s\n' "$NTFY_CONFIG_FILE"
    elif [[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/engineering/notifications.env" ]]; then
        printf '%s\n' "${XDG_CONFIG_HOME:-$HOME/.config}/engineering/notifications.env"
    elif [[ -n "$repository_root" && -f "$repository_root/configs/notifications.env" ]]; then
        printf '%s\n' "$repository_root/configs/notifications.env"
    fi
}

notify_ntfy_load_config() {
    local repository_root="${1:-}"
    local config_file config_mode

    config_file="$(notify_ntfy_config_file "$repository_root")"
    if [[ -z "$config_file" ]]; then
        printf 'ntfy notification unavailable: local configuration not found.\n' >&2
        return 2
    fi
    if [[ ! -r "$config_file" ]]; then
        printf 'ntfy notification unavailable: local configuration is not readable.\n' >&2
        return 2
    fi

    config_mode="$(stat -c '%a' "$config_file" 2>/dev/null || true)"
    if [[ "$config_mode" != "600" ]]; then
        printf 'ntfy notification unavailable: local configuration must have mode 600.\n' >&2
        return 2
    fi

    # The file is trusted per-user configuration and must contain shell-style
    # assignments only. Its path is never printed because it may reveal local
    # configuration details.
    # shellcheck disable=SC1090
    source "$config_file"

    : "${NTFY_BASE_URL:=https://ntfy.sh}"
    : "${NTFY_PRIORITY:=default}"
    if [[ -z "${NTFY_TOPIC:-}" ]]; then
        printf 'ntfy notification unavailable: a private topic is not configured.\n' >&2
        return 2
    fi
    case "${NTFY_TOPIC,,}" in
        "replace-with-private-topic"|"<private-topic>"|"private-topic"|"topic"|"your-topic"|"your_topic"|"changeme"|"change-me"|"replace-me"|"placeholder")
        printf 'ntfy notification rejected: configuration contains an example or placeholder topic.\n' >&2
        return 2
        ;;
    esac
    if [[ "$NTFY_BASE_URL" != https://* ]]; then
        printf 'ntfy notification rejected: NTFY_BASE_URL must use HTTPS.\n' >&2
        return 2
    fi
    if [[ "$NTFY_BASE_URL" == *$'\n'* || "$NTFY_BASE_URL" == *$'\r'* ||
          "$NTFY_TOPIC" == *$'\n'* || "$NTFY_TOPIC" == *$'\r'* ||
          "${NTFY_TOKEN:-}" == *$'\n'* || "${NTFY_TOKEN:-}" == *$'\r'* ]]; then
        printf 'ntfy notification rejected: configuration contains invalid characters.\n' >&2
        return 2
    fi
}

notify_ntfy_curl_quote() {
    local value="${1:-}"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    printf '%s' "$value"
}

notify_ntfy() {
    local title="${1:-}"
    local message="${2:-}"
    local priority="${3:-}"
    local tags="${4:-}"
    local repository_root="${NOTIFY_REPOSITORY_ROOT:-}"
    local curl_bin="${CURL_BIN:-curl}"
    local base_url topic_url curl_config token

    notify_ntfy_load_config "$repository_root" || return $?
    priority="${priority:-$NTFY_PRIORITY}"

    if [[ "$title" == *$'\n'* || "$title" == *$'\r'* ||
          "$priority" == *$'\n'* || "$priority" == *$'\r'* ||
          "$tags" == *$'\n'* || "$tags" == *$'\r'* ]]; then
        printf 'ntfy notification rejected: metadata contains invalid characters.\n' >&2
        return 2
    fi

    base_url="${NTFY_BASE_URL%/}"
    topic_url="$base_url/$NTFY_TOPIC"
    token="${NTFY_TOKEN:-}"

    if ! command -v "$curl_bin" >/dev/null 2>&1; then
        printf 'ntfy notification failed: curl is unavailable.\n' >&2
        return 127
    fi

    curl_config="url = \"$(notify_ntfy_curl_quote "$topic_url")\"\n"
    curl_config+="header = \"Title: $(notify_ntfy_curl_quote "$title")\"\n"
    curl_config+="header = \"Priority: $(notify_ntfy_curl_quote "$priority")\"\n"
    if [[ -n "$tags" ]]; then
        curl_config+="header = \"Tags: $(notify_ntfy_curl_quote "$tags")\"\n"
    fi
    if [[ -n "$token" ]]; then
        curl_config+="header = \"Authorization: Bearer $(notify_ntfy_curl_quote "$token")\"\n"
    fi

    if ! printf '%b' "$curl_config" | "$curl_bin" \
        --config - \
        --silent \
        --show-error \
        --fail-with-body \
        --connect-timeout 5 \
        --max-time 15 \
        --request POST \
        --data-raw "$message" \
        >/dev/null; then
        printf 'ntfy notification delivery failed; verify endpoint, network, and local credentials.\n' >&2
        return 1
    fi
}
