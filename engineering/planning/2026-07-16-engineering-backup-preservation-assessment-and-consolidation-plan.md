# Engineering Backup Preservation Assessment and Consolidation Plan

Date: 2026-07-16
Status: Qualified preservation assessment and future planning
Authority: Engineering Backup Preservation Qualification mission
Governing authorities: PROC-0001, PROC-0003, STD-0004, STD-0005

## Preservation Boundary

AST-000004 remains primary engineering backup and preservation storage with
qualification limitations. AST-000010 remains Engineering preservation
storage under preservation hold. AST-000005 remains excluded under Engineering
Qualification Hold. No role, filesystem, partition, archive, or data state was
changed.

## Preservation Classification

| Category | Classification | Retention recommendation |
| --- | --- | --- |
| Governance records, manifests, checksums, identity material, repository history, recovery evidence | Critical engineering evidence | Indefinite; two verified governed copies minimum |
| Current Homelab and SprinterOS backup sets | Engineering backups | Retain until superseded by a verified restore-qualified generation, then at least 12 months; keep two generations minimum |
| AST-000010 home archive and older user/repository sets | Historical backups | Presume unique; retain until two verified migrated copies exist, then retain the source at least 12 additional months |
| Pre-BIOS system recovery, USB images, home/data archives | Operating-system and recovery backups | Retain through dependent firmware/recovery mission closure plus at least 12 months; preserve checksum sidecars |
| Movie and iTunes Extras content | Media library | Preserve until inventoried, ownership/DRM requirements reviewed, and a separately governed media archive is verified |
| Vendor installers, empty archive placeholders, recycle-bin metadata, and confirmed checksum-identical redundant copies | Disposable candidates only | No item is presently qualified disposable; disposition requires reproducibility or checksum identity, dependency review, and explicit deletion authority |

## Future Consolidated Architecture

| Repository role | Purpose | Assignment requirement |
| --- | --- | --- |
| Primary backup repository | Current versioned Engineering, Homelab, SprinterOS, and workstation backups | Qualified writable storage with snapshots, access control, monitoring, and restore testing |
| Archive repository | Immutable historical and superseded backup generations | Separate failure domain, checksum catalog, retention lock, restricted writes |
| Recovery repository | Boot images, system recovery, firmware prerequisites, manifests, and recovery evidence | Read-mostly, independently recoverable, lifecycle-linked to platforms |
| Media repository | Movies and DRM/ownership metadata | Separated from engineering backup capacity and retention policy |
| AI repository | Models, datasets, vector databases, and governed inference artifacts | Deferred until AI data governance, capacity tiers, security, and backup design are approved |
| Engineering repository | Source repositories, controlled publications, evidence packages, and configuration exports | Version-controlled where appropriate and backed up into primary and archive tiers |

Physical assets shall be selected only after qualification, capacity,
redundancy, security, recovery, and performance review. This logical design
does not assign a new role to any current asset.

## Future Migration Order

1. Preserve and catalog critical manifests, checksum sidecars, governance,
   identity, repository, and recovery evidence.
2. Hash and consolidate current Homelab and SprinterOS backups while retaining
   every source.
3. Verify and consolidate AST-000010's historical home archive and other
   historical generations.
4. Establish the independent recovery repository and complete restore tests.
5. Migrate the media library to its separate governed repository.
6. Establish the AI repository only after its architecture and backup controls
   are approved.
7. Consider duplicate deletion or asset reuse only after retention overlap,
   restore qualification, dependency closure, and explicit authority.

## Verification and Checksum Policy

- Record SHA-256 for every archive, image, manifest, and other immutable large
  object before migration and again from the destination after stable sync.
- For directory trees, generate a deterministic relative-path, size, mtime,
  type, and SHA-256 manifest; protect the manifest with its own SHA-256.
- Require exact source/destination byte counts, matching checksums, readable
  archive traversal, and representative restore tests to separate media.
- Preserve command, tool-version, device-identity, timestamp, and error logs.
- A matching checksum proves byte identity, not semantic completeness or
  restore fitness; retain sources until restore qualification and overlap
  requirements pass.

## Retention and Governance Policy

Use grandfather-father-son generations for active backups: current plus two
prior successful generations, monthly recovery points for 12 months, and
annual or milestone archives indefinitely where engineering or recovery value
persists. Critical evidence and provenance are never expired automatically.
Media follows a separate ownership and archive policy. No item may be called
disposable solely because names or sizes match; checksum identity, canonical
copy selection, dependency closure, retention expiry, and explicit disposition
approval are required.
