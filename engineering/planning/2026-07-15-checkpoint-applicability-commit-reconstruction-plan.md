# Checkpoint Applicability Commit Reconstruction Plan

Date: 2026-07-15
Status: Approved by mission authority
Authority: Codex Handoff Procedure — Multi-Repository Checkpoint Applicability and Resume Drift Correction
Classification report: `engineering/planning/2026-07-15-checkpoint-applicability-commit-classification-report.md`
Governing procedure: PROC-0001 Version 1.5

## Common Gates

Before each commit, verify the classified path set, repository identity, clean
index, absence of active Git operations, `git diff --check`, Bash syntax, and
the applicable validation suite. After each commit, inspect its exact paths and
message, run Git integrity checks, and confirm remaining changes match the next
approved boundary. Stop on any unexpected path or failed validation.

## C01 — Implementation and Tests

- Paths: `scripts/lib/eos/checkpoint.sh`, `scripts/lib/eos/operations.sh`, and
  `scripts/tests/test-eos-runtime.sh`.
- Method: whole-file staging because every hunk serves the single correction.
- Validation: Bash syntax; EOS runtime tests; checkpoint validation; EOS
  persistence; corrected Homelab and SprinterOS resume output; aggregate
  Engineering Platform and SprinterOS validation.
- Title: `fix(eos): scope checkpoint synchronization by repository`.
- Expected result: Homelab remains aligned; a Homelab checkpoint is not
  applicable to SprinterOS; strict verification prevents nonexistent objects
  from entering aligned/drifted comparison.

## C02 — Documentation

- Paths: EOS-0003, SPEC-0004, this plan, and the paired classification report.
- Method: whole-file staging after C01 validates.
- Validation: controlled-document checks; relationship validation; aggregate
  Engineering Platform validation; Git whitespace and integrity.
- Title: `docs(eos): define multi-repository checkpoint applicability`.
- Expected result: the implemented checkpoint identity and precedence model is
  explicit without changing Project State, Sprint State, or the global pointer
  architecture.

## Post-Commit Reconciliation

After both commits validate, refresh repository inventory and operational
state, create and select one Homelab post-correction checkpoint, and validate
checkpoint persistence. Homelab shall report aligned; SprinterOS shall report
the active Homelab checkpoint as not applicable while retaining the persistent
MMC investigation as its current objective. No tag or push is authorized.
