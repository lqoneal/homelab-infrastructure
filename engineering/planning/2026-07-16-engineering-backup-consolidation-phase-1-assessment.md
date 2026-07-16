# Engineering Backup Consolidation Phase 1 Assessment

Date: 2026-07-16
Status: Migration blocked at destination qualification
Authority: Engineering Backup Consolidation — Phase 1 Temporary Consolidation
Governing authorities: PROC-0001, PROC-0003, STD-0004, STD-0005

## Work Initiation and Preservation Boundary

Work Initiation confirmed `thaDuke`, Homelab commit
`011f3f15a689468094f931cf79e02467c9aace97`, SprinterOS commit
`eddc76a9ce2d5dee9fbb7cf544732e086f3f5b04`, aligned EOS, active checkpoint
`20260716T164614Z-engineering-storage-consolidation-prepared.md`, current
Engineering State and resume, clean repositories, no active Git operation, and
Engineering Platform PASS.

AST-000004 and AST-000010 remained unmounted and unchanged. AST-000005 remained
excluded under Engineering Qualification Hold. No source mount, read,
checksum, manifest, directory creation, copy, repair, deletion, or role change
was performed during this phase.

## Temporary Destination Qualification

### Engineering Workstation — `thaDuke`

| Field | Observation |
| --- | --- |
| Storage device | Intel HBRPEKNX0203AH NVMe, serial `BTTE013307PJ1P0C-1` |
| Engineering data LV | `/dev/mapper/vg_engineering-lv_data`, 268,435,456,000 bytes |
| Filesystem | ext4, label `DATA`, UUID `a018c0dd-d636-46d3-a272-f3360886ae1d` |
| Mount | `/data`, mounted read-write as the active Engineering Platform data volume |
| Capacity | 263,086,084,096 bytes total; 249,638,838,272 bytes available at qualification |
| Ownership boundary | `/data/engineering/backups` owned by `loneal:loneal`, mode `0750`; currently empty |
| Intended temporary purpose | Governed temporary preservation repository under a future phase-specific subdirectory |
| Platform/filesystem state | Active ext4 filesystem and Engineering Platform validation PASS; fresh privileged NVMe SMART and ext4 superblock interrogation unavailable after non-interactive administrator authorization expired |

`thaDuke` is operational but is not qualified as the complete Phase 1
destination. Available capacity is less than the approximately 585 GB observed
source footprint and less than the SprinterOS or media category individually.
Consuming most of the data LV would also threaten Engineering Platform growth
margin. No capacity reservation or destination directory was created.

### Playhouse

| Field | Observation |
| --- | --- |
| Name resolution | `playhouse.local` resolved to `10.0.0.222` |
| Network observation | Neighbor entry present at MAC `64:49:7d:83:32:13` |
| Service access | SSH port 22 timed out; ports 139, 445, 3389, 5985, and 5986 also timed out |
| Stable device identity | Not observable |
| Filesystem and mount | Not observable |
| Capacity and health | Not observable |
| Ownership and governed path | Not established |
| Intended temporary purpose | Proposed redundant temporary preservation repository; not qualified |

Playhouse cannot be accepted as a preservation destination until authenticated
read-only access proves host and storage identity, ownership, filesystem,
health, capacity, mount state, available space, governed destination path, and
safe write/rollback behavior.

## Capacity Decision

The two systems do not presently provide proven sufficient capacity for
redundant preservation. `thaDuke` alone is undersized, and Playhouse capacity
is unknown and inaccessible. Destination qualification, redundancy, growth
margin, and rollback prerequisites fail. Under the mission's explicit gate,
no migration may begin.

## Governed Migration Matrix — Prepared, Not Executed

| Category | Source | Proposed temporary destination | Verification destination | SHA-256 and manifest policy | Restore validation | Rollback strategy |
| --- | --- | --- | --- | --- | --- | --- |
| Engineering repositories | AST-000004 `Engineering-Backup/repositories` and `homelab-backups/.../repositories` | `thaDuke:/data/engineering/backups/temporary-consolidation/phase-1/engineering/repositories` | Qualified Playhouse repository | Git integrity plus deterministic relative-path/type/size/mtime/SHA-256 manifest | Clone/open and controlled-document validation | Preserve sources; quarantine and remove only incomplete destination batch under explicit cleanup authority |
| Engineering backups | AST-000004 Engineering backup trees | `thaDuke:.../engineering/backups` where capacity permits | Playhouse engineering-backup mirror | SHA-256 every immutable object and every regular file; manifest checksum | Representative archive and file restore to isolated validation workspace | Never alter source; discard failed destination batch only after evidence capture |
| Homelab backups | AST-000004 `homelab-backups/2026-07-06` | `thaDuke:.../homelab` | Playhouse Homelab mirror | Exact bytes, counts, structure and deterministic SHA-256 manifest | Restore repository, system-config and user-data sample | Source retained through two verified copies and 12-month overlap |
| SprinterOS backups | AST-000004 `EngineeringBackups/SprinterOS/atreides` | Playhouse primary temporary destination because category exceeds `thaDuke` available capacity | A separately qualified destination with at least 259 GB plus margin; `thaDuke` is not currently sufficient | Full deterministic manifest, byte totals and SHA-256 | SprinterOS-defined recovery rehearsal on separate media | Source remains canonical; stop and quarantine incomplete destination |
| Recovery artifacts | AST-000004 pre-BIOS and system-recovery tree | `thaDuke:.../recovery` | Playhouse recovery mirror | Verify existing sidecars; calculate missing SHA-256 and controlled manifest | Non-extracting archive validation and later boot/restore rehearsal | Preserve source and both evidence sets until dependency closure |
| Historical Ubuntu archive | AST-000010 `homedir.backup.tar.xz` | `thaDuke:.../archive/historical-ubuntu` | Playhouse historical archive | Require source and destination SHA-256 `ef9af4d901d2737b7e958a9265728ceddba1d3902ecda87e3a7fd23916531f47` | Complete non-extracting traversal, later representative restore | Source retained at least 12 months after two copies and restore qualification |
| Media library | AST-000004 `Movies` | Playhouse media repository; observed category exceeds `thaDuke` capacity | Separately qualified media copy | Per-file SHA-256, count, bytes, path and DRM/ownership metadata | Representative playback from destination | Preserve source until 100% match, playback review and disposition authority |
| Vendor utilities | AST-000004 WD utilities | Playhouse archive or omit only after reproducibility approval | `thaDuke` manifest/evidence copy | SHA-256, version and provenance manifest | Readability in isolated validation environment if retained | Source unchanged; no omission means deletion authority |
| Identity and configuration | AST-000004 identity, documentation, configuration and system-config trees | Restricted `thaDuke:.../critical/identity-configuration` | Restricted Playhouse mirror | SHA-256 every file; permissions/ownership metadata; encrypt destinations under approved key custody | Controlled representative recovery without exposing secret content | Preserve source; revoke and securely disposition failed destination only under separate authority |

No row is authorized for execution until both its temporary and verification
destinations are qualified, capacity is reserved with growth margin, access and
encryption controls are approved, and a batch-specific evidence and rollback
path exists.

## Preservation Verification

No new redundant copy was created or claimed. Known status remains:

- AST-000010's historical archive is a verified readable source but remains a
  presumed single governed copy.
- AST-000004 contains backup and recovery sets whose cross-location redundancy
  was not established by this mission.
- SprinterOS backup and media categories exceed `thaDuke` available capacity.
- All categories remain preserved at their sources; zero migration or
  verification failures occurred because execution did not start.

Required additional work is to restore authenticated Playhouse management or
file-service access, qualify its storage and ownership, provide sufficient
capacity for the 258.50 GB SprinterOS and 293.77 GB media categories with
growth margin, refresh privileged `thaDuke` NVMe/ext4 health evidence, approve
restricted-data protection, and re-run the migration gate.

## Storage Readiness

AST-000004 is not ready for filesystem repair, AI storage, or governed archive
assignment because no new redundant verified copies exist. AST-000010 is not
ready for filesystem repair, Raspberry Pi investigation workspace, or
Engineering operational storage for the same reason. Existing preservation
roles and repair blockers remain unchanged.

## Follow-on Mission Sequence

1. **Phase 1 re-entry — Destination Qualification and Temporary
   Consolidation:** restore and authenticate Playhouse access; qualify capacity,
   filesystem, storage health, ownership and governed paths; refresh privileged
   `thaDuke` health; then execute category batches with two destinations.
2. **Filesystem Remediation:** after redundancy and restore gates pass, repair
   AST-000004 NTFS and AST-000010 exFAT under separate authority and complete
   post-repair qualification.
3. **Raspberry Pi Recovery Investigation:** only after AST-000010 preservation
   and repair gates pass, consider temporary assignment as Engineering Recovery
   Investigation Workspace for duplicate images, analysis, logs, experiments
   and comparison reports. This plan does not assign that role.
4. **Operational Storage Assignment:** only after preservation, redundancy,
   filesystem health, and investigation closure, separately approve permanent
   roles.
