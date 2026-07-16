# Engineering Storage Role Assignment and Roadmap

Date: 2026-07-16
Status: Planning and evidence record
Authority: Engineering Storage Role Assignment and Initialization mission
Governing authorities: PROC-0001, PROC-0003, STD-0004, STD-0005

## Supported Storage Architecture

| Asset | Supported role | Decision |
| --- | --- | --- |
| AST-000005 | None | Remains excluded under Engineering Qualification Hold; no modification |
| AST-000010 | Engineering preservation storage | Preserve the historical Ubuntu and home-directory backup; operational workspace role deferred |
| AST-000004 | Primary engineering backup and preservation storage | Private AI Assistant platform role not assigned; qualification and preservation gates remain open |

No asset is newly approved as Engineering operational workspace or Private AI
Assistant platform storage. Role decisions are limited by observed content,
filesystem state, media-health evidence, and existing recovery dependencies.

## WD 500 GB Preservation Recommendation

Treat `homedir.backup.tar.xz` as potentially unique and retain the entire
device unchanged. During a separately authorized consolidation mission,
establish a governed destination, record source identity and hashes, validate
the archive through non-destructive read and test extraction to separate
media, preserve provenance, and retain the original for an approved overlap
period. Only after verified migration, retention approval, and filesystem
disposition may AST-000010 be reconsidered for temporary workspace, shared
engineering storage, or another governed operational role.

## Future Mission 1 — Engineering Backup Consolidation

Objectives: preserve the historical Ubuntu backup; inventory and hash legacy
backup sets; identify uniqueness and duplication; consolidate verified copies
into a governed engineering backup repository; define retention, access,
redundancy, and restore-test requirements; eliminate duplicate locations only
under explicit disposition authority. No migration or deletion is authorized
by this plan.

## Future Mission 2 — Engineering Media Library Migration

Objectives: inventory the movie library; preserve ownership and DRM-related
metadata; establish a long-term archive target; verify copied media before any
source disposition; and separate media storage from engineering backups. No
media migration or deletion is authorized by this plan.

## Future Mission 3 — Private AI Storage Expansion

Objectives: define an AI storage hierarchy; dataset ownership, provenance,
classification, and retention governance; model repository and versioning;
vector-database durability; inference workspace and cache policy; capacity and
performance tiers; encryption and access control; and backup, restore, and
disaster-recovery strategy. Select or acquire qualified storage only after the
architecture and preservation dependencies are approved. No AI deployment or
storage initialization is authorized by this plan.
