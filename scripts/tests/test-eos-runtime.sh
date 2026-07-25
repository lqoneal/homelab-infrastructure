#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

export EOS_WORKSPACE="$TEST_ROOT/engineering"
PROJECT_ROOT="$EOS_WORKSPACE/repositories/homelab"
SPRINTER_ROOT="$EOS_WORKSPACE/repositories/SprinterOS"
mkdir -p "$PROJECT_ROOT/docs/project" "$EOS_WORKSPACE/eos/state" "$EOS_WORKSPACE/eos/checkpoints" \
    "$EOS_WORKSPACE/repositories/shared-libraries" "$SPRINTER_ROOT/docs/project"

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

git -C "$SPRINTER_ROOT" init -q
git -C "$SPRINTER_ROOT" config user.name "EOS Runtime Test"
git -C "$SPRINTER_ROOT" config user.email "eos-runtime@example.invalid"
cp "$PROJECT_ROOT/docs/project/PROJ-0001-PROJECT_STATE.md" "$SPRINTER_ROOT/docs/project/PROJ-0001-PROJECT_STATE.md"
printf '%s\n' "Current objective: SprinterOS Platform Recovery Assessment — Persistent MMC Storage I/O Investigation" \
    >> "$SPRINTER_ROOT/docs/project/PROJ-0001-PROJECT_STATE.md"
git -C "$SPRINTER_ROOT" add docs/project/PROJ-0001-PROJECT_STATE.md
git -C "$SPRINTER_ROOT" commit -q -m "test SprinterOS baseline"

source "$REPOSITORY_ROOT/scripts/lib/eos/context.sh"
source "$REPOSITORY_ROOT/scripts/lib/emp/registry.sh"
source "$REPOSITORY_ROOT/scripts/lib/eos/state.sh"
source "$REPOSITORY_ROOT/scripts/lib/eos/checkpoint.sh"
source "$REPOSITORY_ROOT/scripts/lib/eos/operations.sh"
source "$REPOSITORY_ROOT/scripts/lib/eos/platform.sh"

[[ "$(eos_repository_state homelab)" == "clean" ]]
[[ "$(eos_project_root sprinteros)" == "$SPRINTER_ROOT" ]]
[[ "$(eos_frontmatter_value "$(eos_state_path)" status)" == "Active" ]]

checkpoint="$(eos_checkpoint_create homelab "Runtime Test Checkpoint")"
[[ -s "$checkpoint" ]]
[[ "$(eos_checkpoint_latest)" == "$checkpoint" ]]
[[ "$(eos_checkpoint_recorded_commit "$checkpoint")" == "$(git -C "$PROJECT_ROOT" rev-parse HEAD)" ]]
[[ "$(eos_checkpoint_recorded_project "$checkpoint")" == "homelab" ]]
[[ "$(eos_checkpoint_recorded_root "$checkpoint")" == "$PROJECT_ROOT" ]]
[[ "$(eos_checkpoint_identity_status "$checkpoint" homelab)" == "applicable" ]]
[[ "$(eos_checkpoint_sync_status homelab)" == "aligned" ]]
[[ "$(eos_checkpoint_identity_status "$checkpoint" sprinteros)" == "not applicable" ]]
[[ "$(eos_checkpoint_sync_status sprinteros)" == "not applicable" ]]
[[ "$(eos_checkpoint_restore latest)" == "$checkpoint" ]]
[[ "$(eos_checkpoint_active)" == "$checkpoint" ]]

printf '%s\n' "homelab drift" >> "$PROJECT_ROOT/README.md"
git -C "$PROJECT_ROOT" add README.md
git -C "$PROJECT_ROOT" commit -q -m "advance homelab"
[[ "$(eos_checkpoint_sync_status homelab)" == drifted* ]]
homelab_checkpoint="$(eos_checkpoint_create homelab "Homelab Aligned Checkpoint")"
eos_checkpoint_restore "$homelab_checkpoint" >/dev/null
[[ "$(eos_checkpoint_sync_status homelab)" == "aligned" ]]

sprinter_checkpoint="$(eos_checkpoint_create sprinteros "SprinterOS Aligned Checkpoint")"
eos_checkpoint_restore "$sprinter_checkpoint" >/dev/null
[[ "$(eos_checkpoint_sync_status sprinteros)" == "aligned" ]]
[[ "$(eos_checkpoint_sync_status homelab)" == "not applicable" ]]

printf '%s\n' "sprinter drift" >> "$SPRINTER_ROOT/README.md"
git -C "$SPRINTER_ROOT" add README.md
git -C "$SPRINTER_ROOT" commit -q -m "advance SprinterOS"
[[ "$(eos_checkpoint_sync_status sprinteros)" == drifted* ]]
sprinter_checkpoint="$(eos_checkpoint_create sprinteros "SprinterOS Realigned Checkpoint")"
eos_checkpoint_restore "$sprinter_checkpoint" >/dev/null
[[ "$(eos_checkpoint_sync_status sprinteros)" == "aligned" ]]

synthetic_checkpoint() {
    local path="$1" project="$2" root="$3" commit="$4"
    cat > "$path" <<EOF
# EOS Checkpoint — Synthetic Applicability Test

Date: 2026-07-15

## Project

$project

## Repository

Root: \`$root\`

Commit: \`$commit\`
EOF
}

invalid_checkpoint="$EOS_WORKSPACE/eos/checkpoints/invalid-applicable-commit.md"
synthetic_checkpoint "$invalid_checkpoint" homelab "$PROJECT_ROOT" 0000000000000000000000000000000000000000
eos_checkpoint_restore "$invalid_checkpoint" >/dev/null
[[ "$(eos_checkpoint_sync_status homelab)" == "invalid (checkpoint commit does not resolve)" ]]

malformed_checkpoint="$EOS_WORKSPACE/eos/checkpoints/malformed-applicable-commit.md"
synthetic_checkpoint "$malformed_checkpoint" homelab "$PROJECT_ROOT" not-a-commit
eos_checkpoint_restore "$malformed_checkpoint" >/dev/null
[[ "$(eos_checkpoint_sync_status homelab)" == "invalid (checkpoint commit does not resolve)" ]]

root_mismatch_checkpoint="$EOS_WORKSPACE/eos/checkpoints/root-mismatch.md"
synthetic_checkpoint "$root_mismatch_checkpoint" homelab "$SPRINTER_ROOT" "$(git -C "$PROJECT_ROOT" rev-parse HEAD)"
eos_checkpoint_restore "$root_mismatch_checkpoint" >/dev/null
[[ "$(eos_checkpoint_sync_status homelab)" == "invalid (checkpoint project and repository root disagree)" ]]

project_mismatch_checkpoint="$EOS_WORKSPACE/eos/checkpoints/project-mismatch.md"
synthetic_checkpoint "$project_mismatch_checkpoint" sprinteros "$PROJECT_ROOT" "$(git -C "$PROJECT_ROOT" rev-parse HEAD)"
eos_checkpoint_restore "$project_mismatch_checkpoint" >/dev/null
[[ "$(eos_checkpoint_sync_status homelab)" == "invalid (checkpoint project and repository root disagree)" ]]

rm -f "$invalid_checkpoint" "$malformed_checkpoint" "$root_mismatch_checkpoint" "$project_mismatch_checkpoint"
eos_checkpoint_restore "$homelab_checkpoint" >/dev/null
sprinter_resume="$("$REPOSITORY_ROOT/scripts/engctl" resume sprinteros)"
grep -Fq "Checkpoint Project:    homelab" <<<"$sprinter_resume"
grep -Fq "Checkpoint Applicability: not applicable to sprinteros" <<<"$sprinter_resume"
grep -Fq "Checkpoint Sync:       not applicable" <<<"$sprinter_resume"
grep -Fq "Persistent MMC Storage I/O Investigation" <<<"$sprinter_resume"

homelab_resume="$("$REPOSITORY_ROOT/scripts/engctl" resume homelab)"
grep -Fq "ENGINEERING WORK INITIATION — ACTION REQUIRED" <<<"$homelab_resume"
grep -Fq "Mission:                  Zeus Operational Alpha" <<<"$homelab_resume"
grep -Fq "Phase:                    Zeus Operational Alpha" <<<"$homelab_resume"
! grep -Fq "Issue the bounded, read-only HNS Phase 1" <<<"$homelab_resume"
grep -Fq "EXECUTIVE SUMMARY" <<<"$homelab_resume"
grep -Fq "ENGINEERING SESSION CONTRACT" <<<"$homelab_resume"
grep -Fq "Next Recommended Action:" <<<"$homelab_resume"
grep -Fq "Platform Health:" <<<"$homelab_resume"
[[ "$(grep -n -m1 "EXECUTIVE SUMMARY" <<<"$homelab_resume" | cut -d: -f1)" -lt \
    "$(grep -n -m1 "OPERATIONAL STATUS" <<<"$homelab_resume" | cut -d: -f1)" ]]
[[ "$(grep -n -m1 "OPERATIONAL STATUS" <<<"$homelab_resume" | cut -d: -f1)" -lt \
    "$(grep -n -m1 "ENGINEERING CONTEXT" <<<"$homelab_resume" | cut -d: -f1)" ]]
homelab_wrapper_resume="$(ENGCTL_PATH="$REPOSITORY_ROOT/scripts/engctl" "$REPOSITORY_ROOT/scripts/homelabctl" resume)"
[[ "$homelab_resume" == "$homelab_wrapper_resume" ]]

conflict_state="$EOS_WORKSPACE/eos/state/conflicting-project-state.md"
cp "$PROJECT_ROOT/docs/project/PROJ-0001-PROJECT_STATE.md" "$conflict_state"
sed -i '2i mission: Conflicting Mission' "$conflict_state"
registry_context="$(emp_registry_context homelab)"
conflict_resume="$(eos_render_resume_summary homelab "$conflict_state" "$registry_context")"
grep -Fq "ENGINEERING WORK INITIATION — RECONCILIATION REQUIRED" <<<"$conflict_resume"
grep -Fq "AUTHORITY DISAGREEMENT" <<<"$conflict_resume"
rm -f "$conflict_state"

sprinter_wrapper_resume="$(ENGCTL="$REPOSITORY_ROOT/scripts/engctl" \
    "$REPOSITORY_ROOT/../SprinterOS/scripts/sprinterctl" resume)"
grep -Fq "sprinteros" <<<"$sprinter_wrapper_resume"
grep -Fq "Checkpoint Sync:       not applicable" <<<"$sprinter_wrapper_resume"

retention_output="$(eos_checkpoint_retention_report 3)"
grep -Fq "Deletion: prohibited" <<<"$retention_output"
[[ "$(eos_checkpoint_retention_count)" == "3" ]]
[[ "$(eos_checkpoint_list | awk 'END { print NR + 0 }')" == "4" ]]
eos_checkpoint_validate homelab >/dev/null

operational_state="$(eos_operational_refresh homelab)"
[[ -s "$operational_state" ]]
[[ -s "$(eos_repository_inventory_path)" ]]
eos_operational_validate homelab >/dev/null
eos_persistence_validate homelab >/dev/null
printf '%s\n' "invalid" > "$(eos_checkpoint_retention_path)"
if eos_persistence_validate homelab >/dev/null; then
    echo "malformed persisted retention setting was accepted" >&2
    exit 1
fi
eos_checkpoint_retention_set 3
discovery_output="$(eos_repository_discover)"
grep -Fq $'shared-libraries\t' <<<"$discovery_output"
eos_repository_health homelab >/dev/null
context_output="$(eos_engineering_context homelab)"
grep -Fq "checkpoint_sync=aligned" <<<"$context_output"
grep -Fq "management_project_id=EMP-PROJECT-HOMELAB" <<<"$context_output"

printf '%s\n' "drift" >> "$PROJECT_ROOT/README.md"
[[ "$(eos_repository_state homelab)" == "modified (1 path(s))" ]]
eos_operational_refresh homelab >/dev/null
eos_operational_validate homelab >/dev/null
git -C "$PROJECT_ROOT" add README.md
eos_publication_readiness homelab >/dev/null

eos_validate_state homelab >/dev/null
platform_output="$(eos_render_platform homelab)"
grep -Fq "ENGINEERING PLATFORM" <<<"$platform_output"
inventory_output="$(eos_platform_repository_inventory)"
grep -Fq "homelab" <<<"$inventory_output"
qualification_output="$(eos_platform_qualify homelab)"
grep -Fq "Active Git Operation: none" <<<"$qualification_output"
grep -Fq "SSH Agent:" <<<"$qualification_output"

agent_output="$(eos_ssh_agent_state)"
[[ -n "$agent_output" ]]

[[ "$("$REPOSITORY_ROOT/scripts/engctl" version)" == "engctl version 0.8.0" ]]
"$REPOSITORY_ROOT/scripts/engctl" eos validate >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" eos refresh >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" eos persistence >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" ssh status >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" ssh environment >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" checkpoint create "CLI Test Checkpoint" >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" checkpoint restore latest >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" checkpoint validate >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" checkpoint retention 4 >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" repository discover >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" repository health >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" repository sync-status >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" repository refresh >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" registry path >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" registry validate >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" registry list projects >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" registry get EMP-PROJECT-HOMELAB >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" registry context homelab >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" portfolio summary >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" project list >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" queue validate >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" dependency check >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" milestone qualify EMP-MILESTONE-ROADMAP-COMPLETE >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" defer history EMP-WORK-SPRINTEROS-PRODUCT >/dev/null
"$REPOSITORY_ROOT/scripts/engctl" context >/dev/null
wrapper_output="$(ENGCTL_PATH="$REPOSITORY_ROOT/scripts/engctl" \
    "$REPOSITORY_ROOT/scripts/homelabctl" status)"
grep -Fq "ENGINEERING PLATFORM" <<<"$wrapper_output"

echo "EOS runtime tests passed."
