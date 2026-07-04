#!/usr/bin/env bash

set -Eeuo pipefail

########################################
# Colors
########################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

########################################
# Output Helpers
########################################

header() {
    echo
    echo -e "${BLUE}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[ OK ]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

########################################
# Utility Functions
########################################

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_command() {
    if command_exists "$1"; then
        success "$1 installed"
        return 0
    else
        error "$1 not installed"
        return 1
    fi
}

check_directory() {
    if [[ -d "$1" ]]; then
        success "$1 exists"
    else
        warn "$1 missing"
    fi
}

check_mount() {
    if mountpoint -q "$1"; then
        success "$1 mounted"
    else
        error "$1 not mounted"
    fi
}
