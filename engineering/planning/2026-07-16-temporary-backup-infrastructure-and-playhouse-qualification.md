# Temporary Backup Infrastructure and Playhouse Qualification

Date: 2026-07-16
Status: thaDuke infrastructure established; Playhouse qualification blocked
Authority: Engineering Platform Expansion and Temporary Backup Infrastructure

## Initiation and Baseline

Work Initiation passed on `thaDuke`: Engineering Platform PASS, Engineering
State CURRENT, EOS aligned, checkpoint
`20260716T180130Z-thaduke-storage-baseline-reconciled.md`, Homelab
`77d291896da301de8a8db0c98e060bb523b6852f`, SprinterOS
`eddc76a9ce2d5dee9fbb7cf544732e086f3f5b04`, clean trees, no active Git
operation, and authenticated administrator access. The pre-change VG-free
value was exactly 516,327,211,008 bytes; no intervening storage change existed.

## Temporary LV Design and Implementation

The selected size was 400 GiB (429,496,729,600 bytes; 102,400 extents). The
supplied preservation estimates total approximately 599.04 GB, so this LV is
not represented as a complete-copy destination. It can accommodate either the
approximately 305.27 GB non-movie grouping with margin or the approximately
340.54 GB movies-plus-small-sets grouping. It preserves 20,702 VG extents,
86,830,481,408 bytes (80.87 GiB), for future Engineering expansion.

| Item | Qualified state |
| --- | --- |
| LV | `/dev/vg_engineering/lv_backup_temp`, linear, 429,496,729,600 bytes |
| Filesystem | ext4, label `ENG_BACKUP_TEMP`, UUID `96331d76-8a8f-4839-bb53-134e09b8e689`, clean |
| Mount | `/data/engineering/backup-temp`, persistent `defaults,nosuid,nodev`; observed `rw,nosuid,nodev,relatime` |
| Capacity | 421,606,629,376 filesystem bytes; 400,114,962,432 bytes available immediately after preparation |
| Ownership | `loneal:loneal`, mode `0750` |
| Workspace | Empty `incoming`, `verified`, `manifests`, `restore-tests`, `logs`, and `staging`, all `0750` |

No backup data was copied or populated. The only additional entry is ext4's
root-owned `lost+found`.

The LV is temporary Engineering Backup Consolidation infrastructure. Cleanup
or removal is prohibited until migration completes, two independent governed
copies and representative restores are verified, retention and dependency
gates close, the filesystem is proven empty, and a separate mission authorizes
unmount, fstab removal, and LV destruction.

## Playhouse Identity and Connectivity

| Evidence | Observation |
| --- | --- |
| Name | `playhouse.local` maps to `10.0.0.222` through local name lookup; system resolver qualification failed |
| IPv4 | `10.0.0.222`, directly routed over `wlo1` from `10.0.0.35` |
| MAC | `64:49:7d:83:32:13`, confirmed by neighbor discovery and Nmap |
| Power/link | Host responds to ARP discovery; ICMP echo receives no response |
| Services | TCP 22, 139, 445, 3389, 5985, and 5986 filtered; Nmap top 100 TCP ports all filtered/no-response |
| SSH identity | Existing loaded ED25519 identity confirmed; no new key created and no passphrase changed |
| SSH result | `loneal@10.0.0.222:22` timed out before authentication |

The prior failure is reproduced as network/service filtering, not an SSH-key
failure. No governed remote administration path is reachable. Enabling SSH,
changing a host firewall, waking/logging into the console, or discovering OS
and storage requires local console or another already authorized management
channel. None was available in this mission.

## Destination and Architecture Decision

Playhouse classification: **BLOCKED**. Identity is only partially qualified;
OS, hardware, storage devices, filesystems, SMART health, filesystem health,
capacity, existing data, ownership, permissions, and preservation constraints
remain unavailable. It is not a backup destination.

thaDuke now provides 400,114,962,432 bytes of available governed temporary
space. This is one copy in one H10 failure domain. Because Playhouse remains
unqualified, the architecture cannot provide two governed temporary copies,
the full approximately 599.04 GB corpus, or an independent verification and
restore workspace. Engineering Backup Consolidation Phase 1 remains BLOCKED.

Re-entry requires local-console or existing-management access to Playhouse;
confirmation of its hostname, OS, hardware, network policy, and SSH service;
authorization of the existing ED25519 public key; and read-only device,
filesystem, health, capacity, existing-data, ownership, and permission
qualification. No migration may begin before those results meet the planned
capacity, safety-margin, verification-workspace, and independent-failure-domain
requirements.
