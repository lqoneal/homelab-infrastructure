---

document_id: INF-0001
title: Engineering Infrastructure Baseline
version: 2.6
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-19
phase: Controlled Documentation Reconciliation and Engineering Standards Update
domain: Infrastructure
classification: Global Infrastructure Baseline
predecessor_revision: INF-0001@2.5
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff - Mission 0 Controlled Documentation Reconciliation and Engineering Standards Update
approval_date: 2026-07-19
persistence_status: Pending
source_of_truth: true
declared_deferrals: []
relationships:
  - type: indexed_by
    target: DOC-0001
  - type: related_to
    target: PROJ-0001
  - type: related_to
    target: HW-0001
  - type: governed_by
    target: PROC-0003
  - type: conforms_to
    target: STD-0005
tags:
  - infrastructure
  - engineering
  - workstation
  - storage
  - network
  - software
  - baseline

---

# Engineering Infrastructure Baseline

## Purpose

This document defines the authoritative baseline for the global engineering infrastructure supporting the entire engineering portfolio.

It serves as the single source of truth for the engineering environment upon which all portfolio projects are developed.

Project repositories shall reference this document instead of duplicating global infrastructure information.

---

# Authority

This document owns the engineering baseline for:

* Engineering workstations
* Shared storage
* Shared networking
* Engineering software
* Development environment
* Shared engineering services
* Repository locations

Project-specific infrastructure shall be documented within the respective project repository.

---

# Work Initiation

This document shall be reviewed during the Work Initiation Ritual whenever engineering work depends on the development environment or shared infrastructure.

Before interpreting an access, mount, repository, device, or tool failure as an
infrastructure fault, verify the execution environment under PROC-0003. Record
whether execution occurs on the Engineering host or within a sandbox,
container, remote context, chroot, or other constrained namespace; verify the
canonical repository path and required write capability; and identify policy,
privilege, mount, device, and network limitations.

---

# Engineering Terminal Privilege Model

Standard non-elevated user terminals are the default execution environment for normal engineering workflows.

Normal engineering workflows include:

* SSH
* Codex
* Git
* Editing
* Documentation
* Repository operations

Elevated or administrative terminals shall be used only for tasks that explicitly require administrative privileges.

Administrative tasks include:

* System service changes
* Driver configuration
* Firewall administration
* Operating system maintenance

This principle preserves least privilege, reduces accidental system-level changes, improves reproducibility, and avoids clipboard or session isolation issues observed when running administrator terminal sessions.

## Engineering Host and Sandbox Model

The Engineering host is authoritative for infrastructure state. Sandboxes and
other constrained execution environments may intentionally expose read-only
bind mounts, filtered device nodes, restricted logs, reduced privileges, or
different mount namespaces. Those characteristics are execution constraints,
not evidence that the host filesystem, repository, or storage asset has failed.

Infrastructure conclusions shall be corroborated in the host context using
effective mount and filesystem options, configured mount sources, device and
logical-volume state, repository ownership and permissions, host logs, and a
minimal capability check appropriate to the authorized mission. If host
verification is unavailable, record the uncertainty and do not perform a
remount, repair, or configuration change based solely on the sandbox view.

---

# Current Engineering Workstation

| Item             | Current Baseline                      |
| ---------------- | ------------------------------------- |
| Hostname         | thaDuke                               |
| Manufacturer     | HP                                    |
| Model            | HP Spectre x360 Convertible 15-eb0xxx |
| Operating System | Ubuntu 22.04.5 LTS (Jammy Jellyfish)  |
| Kernel           | Linux 6.8.0-124-generic               |
| Architecture     | x86_64                                |
| CPU              | Intel Core i7-10750H                  |
| Cores / Threads  | 6 / 12                                |
| Installed Memory | 16 GB                                 |
| Swap             | None                                  |

---

# Target Engineering Workstation

This section represents the approved engineering target rather than the current implementation.

| Item                            | Target                             |
| ------------------------------- | ---------------------------------- |
| Operating System                | Ubuntu LTS                         |
| Engineering Memory              | 64 GB                              |
| Primary Storage                 | Dedicated engineering NVMe         |
| Shared Data                     | Centralized under `/data`          |
| Backup Strategy                 | Verified recoverable backups       |
| Engineering Controllers         | Standardized portfolio controllers |
| Engineering Management Platform | Operational                        |

---

# Repository Locations

| Repository | Location | Status |
| ---------- | -------- | ------ |
| Homelab | `/data/engineering/repositories/homelab` | Current Git repository; canonical Engineering Platform baseline |
| Shared Libraries | `/data/engineering/repositories/shared-libraries` | Present shared controller-library directory; not an independent Git repository |
| SprinterOS | `/data/engineering/repositories/SprinterOS` | Present Git repository; implementation remains deferred by the portfolio roadmap |

The EOS repository workspace is `/data/engineering/repositories`.

Legacy locations under `/home/loneal/Projects` are not authoritative.

Additional repositories shall be registered as they are promoted into the engineering portfolio.

---

# Filesystem Layout

| Mount     | Purpose                 |
| --------- | ----------------------- |
| /         | Operating System        |
| /home     | User data               |
| /boot     | Boot partition          |
| /boot/efi | EFI partition           |
| /var      | System services         |
| /tmp      | Temporary storage       |
| /data     | Shared engineering data |

---

# Storage Baseline

## Recovery Procedure Authority

PROC-0003 — Engineering Recovery Runbook is the authoritative procedure for
recovery-image acquisition, verification, preservation, NTFS reconciliation,
cleanup, restoration qualification, and evidence collection on shared Homelab
infrastructure. Project repositories own project-specific recovery facts and
constraints and shall reference PROC-0003 rather than duplicate its workflow.

Recovery shall be qualified before major platform modification, and a verified
rollback artifact is a prerequisite to system update. Recovery qualification
does not imply restoration qualification or authorize corrective action.

## Internal Storage

The Intel Optane Memory H10 module exposes a 1,024,209,543,168-byte NAND
namespace and a separate 29,260,513,280-byte Optane namespace. The Optane
namespace retains Intel `isw_raid_member` metadata and is not qualified as
free storage.

| Layer | Component | Provisioned bytes | Allocation or role |
| --- | --- | ---: | --- |
| GPT | EFI | 1,073,741,824 | `/boot/efi` |
| GPT | Boot | 2,147,483,648 | `/boot` |
| GPT | Engineering LVM partition | 1,020,987,252,224 | LVM PV |
| LVM | `vg_engineering` | 1,020,985,868,288 | 504,658,657,280 allocated; 516,327,211,008 free |
| LV | `lv_root` | 128,849,018,880 | `/` ext4 |
| LV | `lv_home` | 107,374,182,400 | `/home` ext4 |
| LV | `lv_data` | 268,435,456,000 | `/data` ext4 |
| LV | `lv_backup_temp` | 429,496,729,600 | `/data/engineering/backup-temp` ext4; temporary backup consolidation workspace |

`lv_backup_temp` uses filesystem label `ENG_BACKUP_TEMP`, UUID
`96331d76-8a8f-4839-bb53-134e09b8e689`, and persistent
`defaults,nosuid,nodev` mount policy. Its root and governed workspace
directories are owned by `loneal:loneal` with mode `0750`. It is temporary
infrastructure and has no permanent backup-storage role. Removal requires
verified migration completion, independent-copy and restore qualification,
retention/dependency closure, an empty-filesystem verification, and separately
authorized unmount, fstab removal, and LV destruction.

`/var` and `/tmp` are directories in the root filesystem, not separate
filesystems. Detailed point-in-time utilization and capacity arithmetic are
published in the 2026-07-16 thaDuke storage-allocation qualification record.

## External Storage

| Device                  | Capacity | Purpose                  |
| ----------------------- | -------- | ------------------------ |
| WD My Passport          | 4 TB     | Engineering backup       |
| Seagate BUP Ultra Touch | 2 TB     | Available ext4 engineering storage; no operational role assigned |
| Ubuntu Installation USB | 16 GB    | Recovery media           |
| Kali Live USB           | 16 GB    | Diagnostics and recovery |

AST-000005 uses ext4 label `AST-000005` and UUID
`9869447e-2c5c-4633-956f-e2dabb7699b4`. It intentionally has no persistent
mount while unassigned. Authorized work mounts it manually by UUID; a future
role assignment shall define any permanent mount point and boot-time policy.

## Engineering Storage Qualification Capability

`thaDuke` provides the administrator-authenticated, non-destructive storage
qualification environment for the engineering portfolio. The qualified tool
baseline is:

| Capability | Tool | Qualified version |
| ---------- | ---- | ----------------- |
| SMART discovery and inspection | `smartctl` (`smartmontools`) | 7.2-1ubuntu0.1 |
| exFAT read-only inspection | `fsck.exfat -n` (`exfatprogs`) | 1.1.3-1ubuntu0.1 |
| Block and partition discovery | `lsblk`, `blkid`, `blockdev` (`util-linux`) | 2.37.2-4ubuntu3.5 |
| Mount-state inspection and control | `mount`, `umount`, `findmnt` (`util-linux`) | 2.37.2-4ubuntu3.5 |
| Stable device-property discovery | `udevadm` | systemd 249 |

PROC-0003 governs use of this capability. Qualification begins with stable
identity, exact capacity, transport, read-only state, partition, filesystem,
and mount-state discovery. Media assessment uses SMART data when the device
and bridge expose it, filesystem checks use non-repair modes, and assessment
mounts use `ro,nosuid,nodev,noexec`. A capability installation or validation
does not qualify, register, assign, repair, or authorize writes to any storage
asset.

### Infrastructure Qualification Philosophy

Mission 0 qualifies infrastructure assets independently of project
assignment. Following qualification, an asset may be retained as a reusable
Homelab engineering resource until a separate Operational Assignment
(Appropriation) decision integrates it into a project or service.

The controlled lifecycle is Asset Discovery, Asset Identification, Inventory,
Evidence Acquisition, Qualification, Operational Assignment, Monitoring, and
Retirement. Evidence acquisition, recovery, restoration, and operational
deployment remain separate decisions. Incidental Homelab assets discovered
during an investigation should be preserved and independently qualified under
their own identity and evidence boundary when authorized.

Backups, successful reads, successful mounts, and tool health summaries do not
alone qualify storage. Qualification is an evidence-based fitness decision
under STD-0005 and PROC-0003. Temporary disqualification, quarantine, or
pending qualification is acceptable when identity, health, interface, power,
filesystem, or preservation evidence is incomplete or conflicting.

Before permanent hardware disqualification, isolate one variable at a time
where safe: media, reader, controller, interface, host, power delivery,
adapter, cable, firmware, or software layer. Preserve evidence before repair;
qualify before recovery whenever practical.

---

## Codex Lifecycle Notification Capability

EWO-000017 establishes Codex lifecycle notifications as shared Engineering
Operations infrastructure owned by Homelab. The global entry point is:

```bash
engctl codex [--ewo EWO-XXXXXX] [--timeout SECONDS] [--] [codex arguments ...]
```

The controller records start time, repository, host, optional Work Order, and
elapsed runtime. It preserves the interactive terminal, forwards arguments
after `--` unchanged, returns the underlying Codex exit status, and sends:

- `Codex Started` when the child begins;
- `Codex Complete` when Codex exits zero;
- `Codex Failed` when Codex exits nonzero; and
- `Codex Interrupted` for `SIGINT`, `SIGTERM`, or `SIGHUP`.

Notification delivery failure prints a warning but never replaces the Codex
result. Signal handling forwards the signal, waits for the child, and prevents
an orphaned Codex process.

Repository-governed Codex missions are required to use this entry point. The
wrapper exports an inherited marker and Work Order identity. Resume and
Engineering Work Initiation qualification reject a detected Codex session that
lacks the marker with exit status 78, emit a value-free engineering condition,
and attempt a non-fatal bypass notification. This detects procedural bypass at
the first governed initiation gate; it is not cryptographic process attestation
and cannot force an already-running external Codex host to relaunch itself.

`--timeout` or `CODEX_TIMEOUT` applies an optional mission runtime bound. A
timed-out child receives `SIGTERM`, retains the resulting status, and produces
`Codex Timed Out`. The existing `Codex Started`, `Codex Complete`, `Codex
Failed`, and `Codex Interrupted` events remain unchanged.

### Secure local configuration

The preferred per-user file is
`~/.config/engineering/notifications.env`. An ignored repository-local
`configs/notifications.env` is supported as a fallback. Copy
`configs/notifications.env.example`, set mode `0600`, and configure:

```bash
NTFY_BASE_URL="https://ntfy.sh"
NTFY_TOPIC="<private-topic>"
NTFY_TOKEN=""
NTFY_PRIORITY="default"
```

`NTFY_TOPIC` and `NTFY_TOKEN` are local secrets and shall never be committed.
The helper requires HTTPS, enforces bounded five-second connect and 15-second
total timeouts, does not disable TLS verification, and supplies the topic and
optional authorization header through curl configuration input so they do not
appear in curl command-line arguments. Messages contain operational metadata
only; prompts, output, diffs, repository content, and credentials are excluded.
The loader rejects published example topics and known placeholder topics before
invoking curl and reports only a value-free engineering diagnostic.

### Operation and troubleshooting

Use `--ewo` or `CODEX_EWO`; absent either, notifications report `Work Order:
Not specified`. Use `CODEX_BIN` only for controlled validation. Missing config,
mode other than `0600`, non-HTTPS base URL, missing `curl`, timeout, HTTP
failure, or rejected credentials produce bounded diagnostics without exposing
the topic.

To migrate to a self-hosted ntfy service, change only `NTFY_BASE_URL` in the
local configuration to its HTTPS endpoint and add `NTFY_TOKEN` if required.
No wrapper or repository change is necessary.

Stage 1 has no heartbeat, progress estimation, output parsing, dashboard,
background daemon, remote control, or alternate transport. Stage 2 heartbeat
notifications and Stage 3 structured progress/lifecycle-event integration are
authoritatively deferred in the Engineering Work Registry.

Stage 1 notification delivery, lifecycle titles and bodies, default priority,
authentication behavior, bounded latency, exit preservation, signal handling,
timeout behavior, and graceful notification-failure degradation were accepted
under EWO-000017 on 2026-07-17. A possible standalone `engctl notify` diagnostic
interface remains future engineering work and is not part of this baseline.

# Network Baseline

| Item              | Value                     |
| ----------------- | ------------------------- |
| Primary Interface | wlo1                      |
| IPv4              | 10.0.0.35/24              |
| Gateway           | 10.0.0.1                  |
| IPv6              | Enabled                   |
| Docker Bridge     | Available                 |
| DNS               | 75.75.75.75 / 75.75.76.76 |

---

# Engineering Software Baseline

| Software | Version |
| -------- | ------- |
| Git      | 2.34.1  |
| Python   | 3.10.12 |
| pip      | 22.0.2  |
| GCC      | 11.4.0  |
| Docker   | 29.1.3  |
| GNU Make | 4.3     |
| Vim      | 8.2     |
| jq       | 1.6     |
| CUPS     | 2.4.1   |
| Avahi    | 0.8     |
| bwrap    | 0.6.1   |
| UFW      | 0.36.1  |
| smartmontools | 7.2-1ubuntu0.1 |
| exfatprogs | 1.1.3-1ubuntu0.1 |
| util-linux | 2.37.2-4ubuntu3.5 |

---

# Shared Engineering Services

The following services form part of the global engineering environment.

* Docker
* Containerd
* SSH
* SMART Monitoring
* Non-destructive storage qualification
* NetworkManager
* systemd-resolved
* CUPS
* CUPS-PDF
* Avahi
* UFW

## Firewall Baseline

| Item            | Current Baseline                                                       |
| --------------- | ---------------------------------------------------------------------- |
| Firewall Tool   | UFW                                                                    |
| Status          | Active and enabled at startup                                          |
| Incoming Policy | Deny                                                                   |
| Outgoing Policy | Allow                                                                  |
| Routed Policy   | Disabled                                                               |
| SSH Access      | TCP/22 allowed from `10.0.0.0/24` only                                 |
| CUPS Access     | TCP/631 allowed from `10.0.0.0/24` only                                |
| mDNS Access     | UDP/5353 allowed from `10.0.0.0/24` only                               |
| IPv6 Policy     | UFW IPv6 handling disabled; exposed services configured IPv4-only.     |

System-wide IPv6 remains enabled. Public service exposure over IPv6 is intentionally disabled at the service configuration layer for SSH, CUPS, and Avahi.

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.9 | 2026-07-16 | Established the qualified `thaDuke` storage-discovery, SMART, read-only filesystem inspection, stable-identification, and safe mount-control tool baseline. |
| 2.0 | 2026-07-16 | Reconciled the rebuilt thaDuke GPT, LVM, filesystem, H10 NAND/Optane namespace, and available-capacity baseline. |
| 2.1 | 2026-07-16 | Established the dedicated 400 GiB temporary Engineering backup LV and governed empty workspace while retaining 80.87 GiB VG expansion capacity. |

## Print Service Baseline

| Item              | Current Baseline                        |
| ----------------- | --------------------------------------- |
| Print Scheduler   | CUPS                                    |
| Discovery Service | Avahi / DNS-SD                          |
| Web Interface     | Enabled                                 |
| Listen Address    | IPv4 TCP/631                            |
| Local Access      | `http://localhost:631`                  |
| Network Access    | `http://10.0.0.35:631`                  |
| Printer Queue     | Engineering_HP_OfficeJet_Pro_8020       |
| Printer Device    | HP OfficeJet Pro 8020 series [9D4237]   |
| Printer Address   | `10.0.0.239`                            |
| Driver Model      | Driverless IPPS                         |
| Firewall Status   | LAN-only via UFW                        |
| Test Print        | Job `Engineering_HP_OfficeJet_Pro_8020-1` accepted and cleared from the CUPS queue. |

## PDF Printing Service Baseline

| Item              | Current Baseline                                   |
| ----------------- | -------------------------------------------------- |
| Service Type      | Managed virtual PDF printing                       |
| Driver            | CUPS-PDF / `printer-driver-cups-pdf`               |
| Queue             | `PDF`                                              |
| Output Hierarchy  | `/data/engineering/shared/documents/generated/pdf` |
| Current Status    | Operational                                        |
| Validation Status | PASS; job `PDF-2` produced `EWO-0002-PDF-VALIDATION-job_2.pdf`. |

## Engineering Scanner Workflow Baseline

The scanner workflow establishes intake locations only. OCR, AI classification, and automated indexing remain out of scope.

| Intake Class | Directory |
| ------------ | --------- |
| Engineering document intake | `/data/engineering/shared/documents/intake/scans/engineering-documents` |
| Receipt intake | `/data/engineering/shared/documents/intake/scans/receipts` |
| Drawing intake | `/data/engineering/shared/documents/intake/scans/drawings` |
| Photograph intake | `/data/engineering/shared/documents/intake/scans/photographs` |
| Reference document intake | `/data/engineering/shared/documents/intake/scans/reference-documents` |

| Item              | Current Baseline                    |
| ----------------- | ----------------------------------- |
| Scanner Utilities | SANE command-line utilities present |
| Workflow Status   | Directory workflow established      |
| OCR               | Out of scope                        |
| AI Classification | Out of scope                        |
| Automated Indexes | Out of scope                        |

## Engineering Workstation Shared Services Inventory

| Service | Implementation | Operational Record |
| ------- | -------------- | ------------------ |
| SSH Service | OpenSSH service | Active baseline; LAN-scoped access via UFW |
| SSH Agent | Ubuntu OpenSSH systemd user service | Active per-login agent; shared protected-key cache and Engineering Platform diagnostics |
| Host Firewall | UFW | Active baseline; deny incoming / allow outgoing |
| Print Service | CUPS | Active baseline; HP OfficeJet queue configured |
| PDF Printing Service | CUPS-PDF | Operational baseline; managed PDF output validated |
| Scanner Workflow | EOS document hierarchy + SANE tools | Workflow directories established |
| Avahi Discovery | Avahi / DNS-SD | Active baseline; LAN-scoped mDNS |

No failed systemd services were present when the secure SSH, firewall, network printing, and Avahi baseline was established.

## Engineering SSH Agent Architecture

The Engineering Platform uses Ubuntu's native `ssh-agent.service` in the
operator's systemd user manager. `default.target` starts exactly one agent at
login, and all terminals reuse the stable owner-only socket at
`$XDG_RUNTIME_DIR/openssh_agent`. The unused GnuPG SSH-emulation socket is
masked so that the platform has one authentication mechanism and one identity
cache.

Interactive Bash startup exports the stable socket. When the shared agent has
no identities, the first interactive terminal requests the passphrase for the
protected `~/.ssh/id_ed25519` engineering key. Subsequent interactive and
noninteractive sessions reuse the loaded identity without prompting. Additional
protected identities may be loaded with `engctl ssh load <key>...`.

The agent persists across terminal closure for the lifetime of the systemd user
session. It intentionally does not retain decrypted identities across a full
logout or reboot because user lingering is disabled. The first interactive
login after either event must unlock the engineering key once. No passphrase,
decrypted key, private-key copy, or agent environment file is persisted.

Operational commands are:

```text
engctl ssh status
engctl ssh environment
engctl ssh load [key ...]
```

`engctl resume` and Engineering Work Initiation report whether the agent socket
is available and whether identities are loaded. If authentication is
unavailable, run `systemctl --user start ssh-agent.service`, then `engctl ssh
load`. Host authorization remains governed by `~/.ssh/config`, each remote
host's `authorized_keys`, and normal known-host verification. Agent forwarding
is not enabled by this architecture.

---

# Infrastructure Ownership

## Homelab Owns

* Engineering workstation
* Shared storage
* Shared networking
* Backup infrastructure
* Engineering software baseline
* Bootstrap tooling
* Controller installation
* Development environment

## Product Repositories Own

Examples include:

* SprinterOS vehicle infrastructure
* AI Assistant compute infrastructure
* Future project-specific deployment environments

---

# Referencing Policy

Projects shall reference this document for global infrastructure information.

Infrastructure owned by Homelab shall not be duplicated in project repositories.

Project repositories shall document only infrastructure unique to that project.

---

# Future Engineering Direction

The engineering environment is expected to evolve toward:

* Dedicated AI compute resources
* Centralized storage
* Expanded memory capacity
* Automated engineering validation
* Engineering Management Platform integration

These targets describe the intended engineering direction and shall be updated as milestones are achieved.

---

# Revision History

| Version | Date       | Description                                                     |
| ------- | ---------- | --------------------------------------------------------------- |
| 1.0     | 2026-07-06 | Initial global engineering infrastructure baseline established. |
| 1.1     | 2026-07-08 | Added engineering print service and LAN-only firewall baseline. |
| 1.2     | 2026-07-08 | Added engineering terminal privilege model.                     |
| 1.3     | 2026-07-08 | Reconciled repository locations with EOS workspace authority.   |
| 1.4     | 2026-07-09 | Added PDF printing service baseline, scanner workflow hierarchy, and shared services inventory. |
| 1.5     | 2026-07-09 | Recorded CUPS-PDF installation, queue validation, and managed PDF output validation. |
| 1.6     | 2026-07-13 | Corrected repository inventory for the present SprinterOS repository and the non-Git shared-libraries directory during Mission 0.1 reconciliation. |
| 1.7     | 2026-07-15 | Established the native systemd user SSH-agent lifecycle, shared socket, protected identity-loading behavior, diagnostics, and security boundary. |
| 1.8     | 2026-07-15 | Registered PROC-0003 as the shared recovery procedure authority while preserving project-specific recovery ownership. |
| 2.2     | 2026-07-17 | Replaced the obsolete secure-drive baseline with the qualified AST-000005 ext4 configuration and intentional manual-mount strategy. |
| 2.3     | 2026-07-17 | Established shared Codex lifecycle notifications, secure ntfy configuration, controller usage, failure behavior, troubleshooting, and future self-hosted migration. |
| 2.4     | 2026-07-17 | Recorded value-free example rejection and completed controlled live acceptance of the Stage 1 notification workflow. |
| 2.5     | 2026-07-17 | Required wrapper use for repository-governed Codex missions, added initiation-time bypass detection, and added bounded mission-timeout notification behavior. |
| 2.6     | 2026-07-19 | Distinguished authoritative host state from sandbox constraints; required execution-environment and write-capability verification; codified asset-oriented infrastructure qualification, evidence-based storage decisions, incidental-asset handling, preservation sequencing, and one-variable hardware isolation. |
