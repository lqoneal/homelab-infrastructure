#!/usr/bin/env bash

set -Eeuo pipefail

PROJECTS_DIR="$HOME/Projects"
LOCAL_BIN="$HOME/.local/bin"

echo "===================================="
echo "HOMELAB BOOTSTRAP"
echo "===================================="

mkdir -p "$LOCAL_BIN"

install_ctl() {
    local name="$1"
    local source_path="$2"
    local target_path="$LOCAL_BIN/$name"

    if [[ ! -f "$source_path" ]]; then
        echo "ERROR: missing $source_path"
        return 1
    fi

    chmod +x "$source_path"
    ln -sf "$source_path" "$target_path"
    echo "OK: installed $name -> $target_path"
}

install_ctl "homelabctl" "$PROJECTS_DIR/homelab/scripts/homelabctl"
install_ctl "sprinterctl" "$PROJECTS_DIR/SprinterOS/scripts/sprinterctl"

echo
echo "Verifying..."
command -v homelabctl
command -v sprinterctl

echo
echo "Bootstrap complete."
