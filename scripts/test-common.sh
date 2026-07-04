#!/usr/bin/env bash

source "$(dirname "$0")/lib/common.sh"

header "Testing Common Library"

info "Information"
success "Everything works"
warn "Example warning"
error "Example failure"

check_command git
check_command python3

check_directory "$HOME"

check_mount "/data"
