#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_UNIT="${REPOSITORY_ROOT}/systemd/eens-notify.service"
SOURCE_ENV="${REPOSITORY_ROOT}/config/eens.env.example"

USER_UNIT_DIRECTORY="${HOME}/.config/systemd/user"
CONFIG_DIRECTORY="${HOME}/.config/eens"

INSTALLED_UNIT="${USER_UNIT_DIRECTORY}/eens-notify.service"
INSTALLED_ENV="${CONFIG_DIRECTORY}/eens.env"

if [[ ! -f "${SOURCE_UNIT}" ]]; then
    printf 'Missing service unit: %s\n' "${SOURCE_UNIT}" >&2
    exit 1
fi

if [[ ! -f "${SOURCE_ENV}" ]]; then
    printf 'Missing environment template: %s\n' "${SOURCE_ENV}" >&2
    exit 1
fi

mkdir -p "${USER_UNIT_DIRECTORY}" "${CONFIG_DIRECTORY}"

install -m 0644 "${SOURCE_UNIT}" "${INSTALLED_UNIT}"

if [[ ! -e "${INSTALLED_ENV}" ]]; then
    install -m 0600 "${SOURCE_ENV}" "${INSTALLED_ENV}"
    printf 'Created configuration: %s\n' "${INSTALLED_ENV}"
    printf 'Edit the ntfy topic before starting the service.\n'
else
    printf 'Preserved existing configuration: %s\n' "${INSTALLED_ENV}"
fi

systemctl --user daemon-reload

printf 'Installed service unit: %s\n' "${INSTALLED_UNIT}"
printf '\n'
printf 'The service has not been enabled or started.\n'
printf 'After configuring %s, run:\n' "${INSTALLED_ENV}"
printf '  systemctl --user enable --now eens-notify.service\n'
