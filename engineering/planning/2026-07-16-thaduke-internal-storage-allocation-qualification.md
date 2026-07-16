# thaDuke Internal Storage Allocation Qualification

Date: 2026-07-16
Status: Qualified, planning only
Authority: thaDuke Internal Storage Allocation Verification and Capacity Reconciliation
Boundary: Read-only storage interrogation; no allocation, resize, migration, repair, deletion, role assignment, tag, or push

## Work Initiation

Host `thaDuke`, Engineering Platform PASS, Engineering State CURRENT, EOS
aligned, and active checkpoint
`20260716T173431Z-temporary-backup-consolidation-gate-qualified.md` were
verified. Homelab was clean at `807a6f22a6d9e3127764699da7df807d33030141`;
SprinterOS was clean at `eddc76a9ce2d5dee9fbb7cf544732e086f3f5b04`
and seven commits ahead of `origin/main`. No Git operation was active.
Administrator qualification passed with `sudo -v` and `sudo -n true`.

## Device and Health Inventory

| Namespace | Stable identity | Exact capacity | Firmware | Role | Health |
| --- | --- | ---: | --- | --- | --- |
| `/dev/nvme0n1` | Intel `HBRPEKNX0203AH`, `BTTE013307PJ1P0C-1`, EUI `eui.0000000001000000e4d25cb463ff5101` | 1,024,209,543,168 B (1.024 TB; 953.87 GiB) | HPS2 | H10 1 TB NAND portion; system and Engineering LVM | PASS; warning 0, spare 100%, used 7%, 30 C, 32,205 h, 143 unsafe shutdowns, zero media errors and log entries |
| `/dev/nvme1n1` | Intel `HBRPEKNX0203AHO`, `BTTE013307PJ1P0C-2`, EUI `eui.5cd2e4b463ff0100` | 29,260,513,280 B (29.26 GB; 27.25 GiB) | HPS3 | H10 32 GB Optane portion; Intel `isw_raid_member` 1.4.01 metadata; unavailable for allocation | PASS; warning 0, spare 100%, used 24%, 41 C, 35,882 h, 156 unsafe shutdowns, zero media errors and log entries |

Intel documents the H10 as one M.2 module combining 32 GB Optane memory and
1 TB QLC NAND. The two Linux namespaces are therefore components of one
physical module, not two freely assignable drives. Current boot logs show no
internal NVMe I/O, media, ext4, reset, or read-only errors. A reported SMBus
transaction timeout is not NVMe evidence. External `/dev/sd*` evidence is
excluded.

## Partition and LVM Allocation

The NAND namespace uses GPT with 512-byte sectors. Partitions begin at sector
2048 and are MiB aligned. The 1,065,472 bytes outside named partitions consist
of normal leading/trailing GPT and alignment space, not useful allocatable
capacity. `parted` was unavailable; `fdisk`, `sfdisk`, `lsblk`, `blkid`, and
`wipefs -n` supplied the required read-only evidence.

| Layer | Component | Provisioned | Used/allocated | Free/unallocated | Purpose |
| --- | --- | ---: | ---: | ---: | --- |
| Namespace | H10 NAND `/dev/nvme0n1` | 1,024,209,543,168 B | 1,024,208,477,696 B in partitions | 1,065,472 B GPT/alignment space | Primary storage |
| GPT | EFI p1, sectors 2,048-2,099,199 | 1,073,741,824 B | 8,675,328 B filesystem-used | 1,062,952,960 B filesystem-available | EFI |
| GPT | Boot p2, sectors 2,099,200-6,293,503 | 2,147,483,648 B | 106,401,792 B filesystem-used | 1,809,821,696 B filesystem-available | `/boot` |
| GPT | LVM p3, sectors 6,293,504-2,000,409,230 | 1,020,987,252,224 B | 1,020,985,868,288 B PV | 1,383,936 B LVM metadata/tail | Engineering LVM |
| LVM | `vg_engineering` | 1,020,985,868,288 B | 504,658,657,280 B (120,320 extents) | 516,327,211,008 B (123,102 extents; 480.87 GiB) | Allocation pool |
| LV | `lv_root` | 128,849,018,880 B | linear, extents 0-30,719 | none at LV layer | `/` |
| LV | `lv_home` | 107,374,182,400 B | linear, extents 30,720-56,319 | none at LV layer | `/home` |
| LV | `lv_data` | 268,435,456,000 B | linear, extents 56,320-120,319 | none at LV layer | `/data` |
| Namespace | H10 Optane `/dev/nvme1n1` | 29,260,513,280 B | Intel metadata/platform use | 0 B qualified free | Optane/RST component |

No thin pool, snapshot, hidden LV, RAID mapping, or LVM metadata LV exists.

## Filesystems and Utilization

All three LVM ext4 filesystems reported `clean` and are mounted `rw,relatime`.
EFI is vfat with restrictive masks and `errors=remount-ro`; boot is ext4.

| Mount | Filesystem provisioned | `df` used | `df` available | ext4 reserved |
| --- | ---: | ---: | ---: | ---: |
| `/` | 126,227,120,128 B | 5,344,071,680 B | 114,423,820,288 B | 6,442,450,944 B |
| `/home` | 105,089,261,568 B | 2,071,093,248 B | 97,632,681,984 B | 5,368,709,120 B |
| `/data` | 263,086,084,096 B | 8,753,152 B | 249,638,780,928 B | 13,421,772,800 B |
| `/boot` | 2,040,373,248 B | 106,401,792 B | 1,809,821,696 B | not separately interrogated |
| `/boot/efi` | 1,071,628,288 B | 8,675,328 B | 1,062,952,960 B | not applicable |

Existing filesystems expose 464,568,057,856 bytes available in total. The
ext4 reserved-block totals are policy-reserved capacity and must not be counted
as ordinary destination headroom.

## Directory Utilization

`du -x` preserved one-filesystem boundaries. Root occupies 5,343,952,896 B,
led by `/usr` (4,470,452,224 B) and `/var` (866,820,096 B). `/var/lib` is
428,326,912 B, `/var/log` 133,763,072 B, and `/var/cache` 303,251,456 B.
Home occupies 2,071,089,152 B; `/home/loneal/.codex` accounts for
2,070,560,768 B. Data occupies 8,744,960 B; Engineering repositories account
for 8,085,504 B, EOS 159,744 B, shared 73,728 B, checkpoints 368,640 B,
reconstruction 20,480 B, staging 8,192 B, and backups 4,096 B. No deletion or
cleanup classification was made; caches, logs, and reconstruction/staging
content are merely identified as potentially reconstructable.

## Capacity Finding and Prior 250 GB Review

The previous finding is **correct but narrowly scoped**: 268,435,456,000 bytes
(250 GiB) is the provisioned size of `lv_data`; its ext4 filesystem exposed
about 249.64 GB (232.5 GiB) available. It is not total workstation capacity.
The primary reason is 516,327,211,008 bytes of unallocated VG extents that the
previous destination qualification did not interrogate.

Potentially allocatable capacity without replacing hardware is precisely the
VG-free 516,327,211,008 bytes. The 29,260,513,280-byte Optane namespace and
1,065,472-byte GPT/alignment remainder are excluded.

## Expansion Feasibility (No Selection)

| Option | Capacity and prerequisites | Risk, validation, rollback, downtime |
| --- | --- | --- |
| A — extend `/data` | Up to 516,327,211,008 B from VG free extents; choose retained VG margin, take verified backup, extend LV, then grow ext4 | ext4 supports online growth; validate LVM/filesystem health, capacity, mounts, and application access. LV reduction is not a simple rollback; restore/rebuild from backup is the conservative rollback. No expected downtime, but a maintenance window is prudent. |
| B — temporary-backup LV | Up to 516,327,211,008 B less required VG reserve; create LV, filesystem, mount, permissions, encryption and retention policy | New independent allocation boundary, but still same failure domain. Validate UUID, mount policy, capacity, manifests and restores. Rollback is unmount/remove only after copied data is independently preserved. Brief setup window required; routine use need not require downtime. |
| C — staging LV | Same pool, sized for verification workspace plus growth margin | Separates transient verification work but consumes capacity needed for copies. Validate workload sizing and cleanup authority. Rollback as for B. |
| D — no change | Retain current filesystems and use qualified Playhouse/external NVMe | Avoids local allocation change; depends on authenticated destination identity, health, capacity, network, security and restore qualification. |

## Backup Capacity Reassessment

The supplied estimates total 599,036,243,804 bytes when GB values are treated
as decimal: historical archive 14,466,243,804 B, Homelab 6.88 GB, Engineering
9.16 GB, pre-BIOS 16.26 GB, SprinterOS 258.50 GB, and Movies 293.77 GB. This
explains why the earlier rounded working estimate of about 585 GB must remain
an estimate until a deterministic source manifest supplies exact byte totals.

Currently `/data` can hold the archive, Homelab, Engineering, and pre-BIOS
sets together (46,766,243,804 B), or the SprinterOS set alone, but not Movies
alone and not SprinterOS plus the smaller non-movie sets. After allocating VG
free extents, local usable capacity is sufficient in principle for the whole
estimated 599.04 GB set, but only with a deliberately sized destination and
verification workspace. A minimum 15% safety margin plus at least the largest
batch's temporary verification workspace is recommended; if full duplicate
workspace is required, thaDuke alone is insufficient. Even when one temporary
copy fits, a second independent destination remains mandatory because new LVs
on the same H10 module do not create an independent failure domain.

## Reconciliation Decision

INF-0001 and AST-000002/AST-000003 required correction because their current
storage layout and device roles were incomplete or obsolete. Project State,
EOS operational state, and checkpoint selection did not change: the mission
qualified an existing allocation and performed no storage operation or role
assignment. Therefore EOS refresh or checkpoint creation is unnecessary.
