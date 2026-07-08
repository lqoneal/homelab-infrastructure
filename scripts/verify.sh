#!/usr/bin/env bash
# Add Flag parsing

FIX_MODE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=1
            shift
            ;;
        *)
            shift
            ;;
    esac
done


set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

HEADER="Homelab Verification"
PASS=0
WARN=0
FAIL=0

########################################
# Helpers
########################################

pass() {
    success "$1"
    ((PASS++)) || true
}

fail() {
    error "$1"
    ((FAIL++)) || true
}

warn_item() {
    warn "$1"
    ((WARN++)) || true
}

########################################
# Checks
########################################

check_git() {
    header "Git"

    if command_exists git; then
        pass "git installed"
    else
        fail "git missing"
    fi

    if git config --global user.name >/dev/null 2>&1; then
        pass "git user.name set"
    else
        warn_item "git user.name not set"
    fi

    if git config --global user.email >/dev/null 2>&1; then
        pass "git user.email set"
    else
        warn_item "git user.email not set"
    fi
}

check_ssh() {
    header "SSH"

    if [[ -f "$HOME/.ssh/id_ed25519" || -f "$HOME/.ssh/id_rsa" ]]; then
        pass "SSH key exists"
    else
        warn_item "No SSH key found"
    fi
}

check_workspace() {
    header "Workspace"

    local CONFIG_FILE="$SCRIPT_DIR/../configs/directories.txt"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        error "Missing config: directories.txt"
        return 1
    fi

    while read -r dir; do
        [[ -z "$dir" || "$dir" =~ ^# ]] && continue

        local full_path
        if [[ "$dir" = /* ]]; then
            full_path="$dir"
        else
            full_path="$HOME/$dir"
        fi

        if [[ -d "$full_path" ]]; then
            success "exists: $dir"
        else
            if [[ "$FIX_MODE" -eq 1 ]]; then
                warn "creating: $full_path"
                mkdir -p "$full_path"
                success "created: $dir"
            else
                warn "missing: $full_path"
            fi
        fi
    done < "$CONFIG_FILE"
}

check_storage() {
    header "Storage"

    if mountpoint -q /data; then
        pass "/data mounted"
    else
        fail "/data NOT mounted"
    fi

    df -h / | awk 'NR==2 {print "root usage: " $5}'
    df -h /home | awk 'NR==2 {print "home usage: " $5}'
    df -h /data | awk 'NR==2 {print "data usage: " $5}'
}

check_tools() {
    header "Core Tools"

    local tools=(
        git
        curl
        wget
        vim
        python3
        pip3
        gcc
        make
        jq
    )

    for t in "${tools[@]}"; do
        if command_exists "$t"; then
            pass "$t installed"
        else
            fail "$t missing"
        fi
    done
}

########################################
# Summary
########################################

summary() {
    header "Summary"

    if [[ "$FIX_MODE" -eq 1 ]]; then
    echo
    warn "FIX MODE WAS ENABLED - SYSTEM MODIFIED"
    fi

    echo "Passed: $PASS"
    echo "Warnings: $WARN"
    echo "Failures: $FAIL"

    echo

    if [[ $FAIL -gt 0 ]]; then
        error "System NOT compliant"
        return 1
    elif [[ $WARN -gt 0 ]]; then
        warn "System partially compliant"
        return 0
    else
        success "System fully compliant"
        return 0
    fi
}

########################################
# Main
########################################

main() {
    header "$HEADER"

    check_git
    check_ssh
    check_workspace
    check_storage
    check_tools

    summary
}

main
