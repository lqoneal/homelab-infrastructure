# Engineering Storage Consolidation Preparation Plan

Date: 2026-07-16
Status: Qualified design and migration preparation
Authority: Engineering Storage Consolidation Preparation mission
Governing authorities: PROC-0001, PROC-0003, STD-0004, STD-0005

## Preservation and Execution Boundary

AST-000004 remains primary Engineering backup and preservation storage with
qualification limitations. AST-000010 remains Engineering preservation
storage under hold. AST-000005 remains excluded under Engineering
Qualification Hold. Both in-scope volumes were verified unmounted. This plan
authorizes no repair, mount, migration, deletion, directory creation, or role
change.

## Governed Logical Hierarchy

```text
/engineering-storage/
├── engineering/
│   ├── repositories/
│   ├── operational-workspace/
│   ├── backups/
│   │   ├── current/
│   │   ├── generations/
│   │   └── manifests/
│   ├── recovery/
│   │   ├── system-images/
│   │   ├── boot-media/
│   │   ├── firmware-prerequisites/
│   │   └── evidence/
│   ├── archive/
│   │   ├── historical-backups/
│   │   ├── milestones/
│   │   └── manifests/
│   └── validation-workspace/
├── media/
│   ├── library/
│   ├── metadata/
│   └── manifests/
├── ai/
│   ├── datasets/{incoming,curated,restricted}/
│   ├── models/{source,quantized,approved}/
│   ├── vector-databases/{active,snapshots}/
│   ├── operational-workspace/
│   ├── cache/
│   └── manifests/
└── staging/
    ├── incoming/
    ├── checksum-verification/
    └── rejected/
```

The hierarchy is logical. Physical mount points, filesystems, and assets shall
be selected only after capacity, performance, redundancy, security, recovery,
and qualification review.

## Ownership and Lifecycle Responsibilities

| Area | Information owner | Lifecycle responsibility |
| --- | --- | --- |
| Engineering repositories | Owning engineering project | Version integrity, access, release and archival boundaries |
| Operational and validation workspaces | Engineering Platform | Quotas, isolation, cleanup, reproducibility; never sole-copy storage |
| Engineering backups | Homelab Infrastructure | Scheduling, generation retention, manifests, monitoring, restore tests |
| Recovery artifacts | Platform/recovery owner | Bootability, dependency tracking, evidence, periodic recovery qualification |
| Long-term archive | Engineering Governance with Homelab custody | Immutability, provenance, retention holds, controlled disposition |
| Media library | Media owner with Homelab custody | Ownership/DRM metadata, integrity, separation from backup policy |
| AI datasets | Private AI Assistant data owner | Provenance, classification, licensing, privacy, lineage, retention |
| AI models | Private AI Assistant model owner | Source, license, version, checksum, approval and deprecation |
| Vector databases | Private AI Assistant service owner | Source linkage, snapshot consistency, rebuild and restore procedure |
| AI workspace/cache | Private AI Assistant operations | Capacity, eviction, reproducibility, security; cache is non-authoritative |
| Temporary staging | Engineering Platform | Time-limited intake, malware/content review, checksum gate, automatic expiry only after authority |

## Migration Matrix

| Category | Current source | Future destination | Verification and manifest | Restore validation | Overlap and retirement gate |
| --- | --- | --- | --- | --- | --- |
| Controlled repositories and engineering evidence | AST-000004 `Engineering-Backup`, `homelab-backups`, repository trees | `engineering/repositories` and `engineering/archive/milestones` | Git integrity plus deterministic path/type/size/mtime/SHA-256 manifest | Clone/open repository, validate controlled documents and referenced evidence | Indefinite critical evidence; source retirement only after two copies and project-owner acceptance |
| Current Homelab backups | AST-000004 `homelab-backups/2026-07-06` | `engineering/backups/{current,generations}` | SHA-256 per immutable archive and every regular file; signed/controlled manifest | Restore representative repository, configuration and user-data sample to validation workspace | Minimum 12 months and two newer successful generations |
| SprinterOS backups | AST-000004 `EngineeringBackups/SprinterOS/atreides` | Engineering backup generations and archive as classified | Full deterministic manifest and source/destination byte totals | Project-defined recovery rehearsal on separate target | Retain source through SprinterOS owner acceptance and 12-month overlap |
| Pre-BIOS and system recovery | AST-000004 `2026-07-11-pre-BIOS-F16` | `engineering/recovery` | Verify existing sidecars, compute missing SHA-256, manifest device and provenance | Non-destructive archive traversal and future boot/restore rehearsal | Firmware/recovery dependency closure plus 12 months; critical evidence indefinite |
| Historical home archive | AST-000010 `homedir.backup.tar.xz` | `engineering/archive/historical-backups` plus independent backup copy | Require recorded checksum `ef9af4d901d2737b7e958a9265728ceddba1d3902ecda87e3a7fd23916531f47` at source and each destination | Complete non-extracting traversal, then authorized representative restore to validation media | Two verified copies, successful restore validation, minimum 12-month source overlap, owner approval |
| Movie library and metadata | AST-000004 `Movies` and related media metadata | `media/{library,metadata,manifests}` | Per-file SHA-256, size, mtime, title/path and DRM/ownership metadata | Open representative media from destination without modifying source | Preserve source until 100% manifest match, playback sampling, ownership review and separate disposition authority |
| Reproducible vendor utilities | AST-000004 WD utility trees | Archive only if dependency requires; otherwise future disposition candidate | Hash, version, provenance and reproducibility record | Installer readability only in isolated validation environment if retained | Never delete until reproducibility and dependency closure are approved |

## Global Migration Gates

No migration may begin until the destination asset and filesystem are
qualified; ownership and access controls are approved; capacity includes
retention overlap and growth margin; source and destination identities are
recorded; both are healthy and safely mounted; manifests and evidence paths are
prepared; rollback and stop conditions are documented; and a separate
migration authority is active.

For every batch, compute SHA-256 at the source, copy without deleting or
renaming the source, synchronize the destination, compute SHA-256 again from
destination storage, compare exact byte counts and manifests, perform the
category restore test, record exceptions, and retain the source. A matching
checksum establishes byte identity only. Retirement additionally requires
restore qualification, retention expiry, dependency closure, canonical-copy
selection, and explicit disposition authority.

## Filesystem Remediation Sequence

1. Consolidate and verify protected data while both legacy sources remain
   read-only.
2. Establish two governed copies and complete category restore validation.
3. Capture fresh SMART, filesystem, identity, and connection baselines.
4. Repair AST-000004 with Windows-native NTFS tooling under separate authority;
   do not begin with a surface scan.
5. Repair AST-000010 exFAT and disposition its label under separate authority.
6. Reconnect read-only, repeat health checks, and compare protected-object
   checksums.
7. Requalify each asset independently before considering a role transition.

## Readiness Decision

Neither asset is ready for a new operational role. AST-000004 remains a
conditional preservation source, not an AI platform, governed archive, or sole
long-term copy. AST-000010 remains a qualified preserved source, not
operational workspace. Successful consolidation does not itself assign a role;
post-repair health qualification, integration design, and separate assignment
authority remain mandatory.
