#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/lib/common.sh"

header "Homelab Doctor"

########################################
# System
########################################

header "System"

info "Hostname: $(hostname)"
info "User: $USER"
info "Kernel: $(uname -r)"

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    info "OS: $PRETTY_NAME"
fi

########################################
# Storage
########################################

header "Storage"

check_mount "/data"

df -h / /home /data

########################################
# Development Tools
########################################

header "Development Tools"

check_command git
check_command python3
check_command pip3
check_command gcc
check_command make

########################################
# Git Configuration
########################################

header "Git"

NAME=$(git config --global user.name || true)
EMAIL=$(git config --global user.email || true)

if [[ -n "$NAME" ]]; then
    success "Git Name: $NAME"
else
    warn "Git user.name not configured"
fi

if [[ -n "$EMAIL" ]]; then
    success "Git Email: $EMAIL"
else
    warn "Git user.email not configured"
fi

########################################
# SSH
########################################

header "SSH"

if [[ -f "$HOME/.ssh/id_ed25519" ]]; then
    success "SSH ed25519 key found"
elif [[ -f "$HOME/.ssh/id_rsa" ]]; then
    success "SSH RSA key found"
else
    warn "No SSH key found"
fi

########################################
# EOS Workspace
########################################

header "EOS Workspace"

EOS_WORKSPACE="${EOS_WORKSPACE:-/data/engineering}"

check_directory "$EOS_WORKSPACE"
check_directory "$EOS_WORKSPACE/eos"
check_directory "$EOS_WORKSPACE/eos/state"
check_directory "$EOS_WORKSPACE/repositories"
check_directory "$EOS_WORKSPACE/repositories/homelab"
check_directory "$EOS_WORKSPACE/repositories/shared-libraries"
check_directory "$EOS_WORKSPACE/shared"
check_directory "$EOS_WORKSPACE/backups"
check_directory "$EOS_WORKSPACE/staging"

check_directory "$EOS_WORKSPACE/repositories/shared-libraries/shell/projectctl"

########################################
# Future Platform
########################################

header "Future Platform"

check_command docker
check_command ollama

echo
success "Doctor completed."
