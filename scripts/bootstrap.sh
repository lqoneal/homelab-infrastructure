#!/usr/bin/env bash

set -Eeuo pipefail

EOS_WORKSPACE="${EOS_WORKSPACE:-/data/engineering}"
REPOSITORIES_DIR="$EOS_WORKSPACE/repositories"
LOCAL_BIN="$HOME/.local/bin"

echo "===================================="
echo "HOMELAB EOS BOOTSTRAP"
echo "===================================="

mkdir -p "$LOCAL_BIN"

install_ctl() {
    local name="$1"
    local source_path="$2"
    local target_path="$LOCAL_BIN/$name"

    if [[ ! -f "$source_path" ]]; then
        echo "WARN: missing $source_path"
        return 0
    fi

    chmod +x "$source_path"
    ln -sf "$source_path" "$target_path"
    echo "OK: installed $name -> $target_path"
}

install_ctl "engctl" "$REPOSITORIES_DIR/homelab/scripts/engctl"
install_ctl "homelabctl" "$REPOSITORIES_DIR/homelab/scripts/homelabctl"
install_ctl "sprinterctl" "$REPOSITORIES_DIR/SprinterOS/scripts/sprinterctl"

echo
echo "Verifying..."
command -v engctl || true
command -v homelabctl || true
command -v sprinterctl || true

echo
echo "EOS Workspace:"
echo "$EOS_WORKSPACE"

echo
echo "Bootstrap complete."
