#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/lib/common.sh"

OUT_DIR="$(cd "$SCRIPT_DIR/../inventory" && pwd)"
JSON_OUT="$OUT_DIR/inventory.json"

mkdir -p "$OUT_DIR"

header "Homelab Inventory Generator"

########################################
# Hardware
########################################
generate_hardware() {
    info "Collecting hardware info..."

    {
        echo "# Hardware Inventory"
        echo
        echo "## CPU"
        lscpu | sed 's/^/ /'
        echo
        echo "## Memory"
        free -h
        echo
        echo "## Block Devices"
        lsblk -f
    } > "$OUT_DIR/hardware.md"
}

########################################
# Storage
########################################
generate_storage() {
    info "Collecting storage info..."

    {
        echo "# Storage Inventory"
        echo
        df -h
        echo
        echo "## Mounts"
        mount | column -t
    } > "$OUT_DIR/storage.md"
}

########################################
# Software
########################################
generate_software() {
    info "Collecting software info..."

    {
        echo "# Software Inventory"
        echo
        echo "## Kernel"
        uname -a
        echo
        echo "## Installed Tooling"
        for cmd in git python3 pip3 gcc make docker; do
            if command -v "$cmd" >/dev/null 2>&1; then
                echo "[OK] $cmd"
            else
                echo "[MISSING] $cmd"
            fi
        done
    } > "$OUT_DIR/software.md"
}

########################################
# Network
########################################
generate_network() {
    info "Collecting network info..."

    {
        echo "# Network Inventory"
        echo
        ip addr
        echo
        echo "## Routes"
        ip route
    } > "$OUT_DIR/network.md"
}

########################################
# Users
########################################
generate_users() {
    info "Collecting user info..."

    {
        echo "# User Inventory"
        echo
        whoami
        echo
        id
        echo
        echo "## System Users"
        cut -d: -f1 /etc/passwd
    } > "$OUT_DIR/users.md"
}

########################################
# JSON (lightweight structured snapshot)
########################################
generate_json() {
    info "Generating JSON snapshot..."

    cat <<EOF > "$JSON_OUT"
{
  "hostname": "$(hostname)",
  "user": "$(whoami)",
  "kernel": "$(uname -r)",
  "os": "$(grep PRETTY_NAME /etc/os-release | cut -d= -f2- | tr -d '\"')",
  "cpu_cores": "$(nproc)",
  "memory": "$(free -h | awk '/Mem:/ {print $2}')",
  "data_mounted": "$(mount | grep -q '/data' && echo true || echo false)"
}
EOF
}

########################################
# Main
########################################
main() {
    generate_hardware
    generate_storage
    generate_software
    generate_network
    generate_users
    generate_json

    success "Inventory generated in: $OUT_DIR"
}

main
