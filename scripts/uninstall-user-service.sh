#!/usr/bin/env bash

set -euo pipefail

USER_UNIT="${HOME}/.config/systemd/user/eens-notify.service"

if systemctl --user list-unit-files eens-notify.service \
    --no-legend 2>/dev/null |
    grep -q '^eens-notify\.service'; then
    systemctl --user disable --now eens-notify.service || true
fi

if [[ -e "${USER_UNIT}" ]]; then
    rm -- "${USER_UNIT}"
    printf 'Removed service unit: %s\n' "${USER_UNIT}"
else
    printf 'Service unit is not installed: %s\n' "${USER_UNIT}"
fi

systemctl --user daemon-reload
systemctl --user reset-failed

printf 'Configuration was preserved at:\n'
printf '  %s\n' "${HOME}/.config/eens/eens.env"
