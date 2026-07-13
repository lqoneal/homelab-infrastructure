#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

export EOS_WORKSPACE="$TEST_ROOT/engineering"
PROJECT_ROOT="$EOS_WORKSPACE/repositories/homelab"
mkdir -p "$PROJECT_ROOT/docs/project" "$EOS_WORKSPACE/eos/state" "$EOS_WORKSPACE/eos/checkpoints"

git -C "$PROJECT_ROOT" init -q
git -C "$PROJECT_ROOT" config user.name "EOS Runtime Test"
git -C "$PROJECT_ROOT" config user.email "eos-runtime@example.invalid"
printf '%s\n' "runtime test" > "$PROJECT_ROOT/README.md"

for state_record in EOS-ID.md EOS-MANIFEST.md; do
    printf '%s\n' "# $state_record" > "$EOS_WORKSPACE/eos/state/$state_record"
done

cat > "$EOS_WORKSPACE/eos/state/EOS-STATE.md" <<'EOF'
---
document_id: EOS-STATE
version: 1.0
status: Active
---

# EOS State
EOF

cat > "$PROJECT_ROOT/docs/project/PROJ-0001-PROJECT_STATE.md" <<'EOF'
---
document_id: PROJ-0001
version: 1.0
status: Active
---

# Project State
EOF

git -C "$PROJECT_ROOT" add README.md docs/project/PROJ-0001-PROJECT_STATE.md
git -C "$PROJECT_ROOT" commit -q -m "test baseline"

source "$REPOSITORY_ROOT/scripts/lib/eos/context.sh"
source "$REPOSITORY_ROOT/scripts/lib/eos/state.sh"
source "$REPOSITORY_ROOT/scripts/lib/eos/checkpoint.sh"
source "$REPOSITORY_ROOT/scripts/lib/eos/platform.sh"

[[ "$(eos_repository_state homelab)" == "clean" ]]
[[ "$(eos_frontmatter_value "$(eos_state_path)" status)" == "Active" ]]

checkpoint="$(eos_checkpoint_create homelab "Runtime Test Checkpoint")"
[[ -s "$checkpoint" ]]
[[ "$(eos_checkpoint_latest)" == "$checkpoint" ]]
[[ "$(eos_checkpoint_recorded_commit "$checkpoint")" == "$(git -C "$PROJECT_ROOT" rev-parse HEAD)" ]]
[[ "$(eos_checkpoint_sync_status homelab)" == "aligned" ]]

printf '%s\n' "drift" >> "$PROJECT_ROOT/README.md"
[[ "$(eos_repository_state homelab)" == "modified (1 path(s))" ]]

eos_validate_state homelab >/dev/null
platform_output="$(eos_render_platform homelab)"
grep -Fq "ENGINEERING PLATFORM" <<<"$platform_output"
inventory_output="$(eos_platform_repository_inventory)"
grep -Fq "homelab" <<<"$inventory_output"
qualification_output="$(eos_platform_qualify homelab)"
grep -Fq "Active Git Operation: none" <<<"$qualification_output"

[[ "$("$REPOSITORY_ROOT/scripts/engctl" version)" == "engctl version 0.2.0" ]]
"$REPOSITORY_ROOT/scripts/engctl" eos validate >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" checkpoint create "CLI Test Checkpoint" >/dev/null
wrapper_output="$(ENGCTL_PATH="$REPOSITORY_ROOT/scripts/engctl" \
    "$REPOSITORY_ROOT/scripts/homelabctl" status)"
grep -Fq "ENGINEERING PLATFORM" <<<"$wrapper_output"

echo "EOS runtime tests passed."
