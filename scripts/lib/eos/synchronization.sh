#!/usr/bin/env bash

eos_synchronization_tool() {
    local synchronization_dir
    synchronization_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "$synchronization_dir/state_sync.py"
}

eos_synchronize() {
    local project="${1:-homelab}"
    python3 "$(eos_synchronization_tool)" synchronize \
        --root "$(eos_project_root homelab)" \
        --workspace "$(eos_workspace)" \
        --project homelab
    mkdir -p "$(eos_checkpoints_dir)"
    if [[ ! -s "$(eos_checkpoint_retention_path)" ]]; then
        eos_checkpoint_retention_set 10
    fi
    if [[ -z "$(eos_checkpoint_latest)" ]]; then
        eos_checkpoint_create homelab "Repository EOS Integration Baseline" >/dev/null
    fi
    if [[ ! -s "$(eos_checkpoint_active_path)" ]]; then
        eos_checkpoint_restore latest >/dev/null
    fi
    eos_operational_refresh "$project" >/dev/null
}

eos_synchronization_validate() {
    local project="${1:-homelab}"
    python3 "$(eos_synchronization_tool)" validate \
        --root "$(eos_project_root homelab)" \
        --workspace "$(eos_workspace)" \
        --project homelab
}
