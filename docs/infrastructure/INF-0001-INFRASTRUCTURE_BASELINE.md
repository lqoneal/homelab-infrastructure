---

document_id: INF-0001
title: Engineering Infrastructure Baseline
version: 1.9
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-16
phase: Engineering Storage Qualification Capability
domain: Infrastructure
classification: Global Infrastructure Baseline
predecessor_revision: INF-0001@1.8
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering Storage Qualification Capability Implementation
approval_date: 2026-07-16
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

| Mount     | Size     | Current Usage |
| --------- | -------- | ------------- |
| /         | 55.9 GB  | 23%           |
| /home     | 232.8 GB | 35%           |
| /var      | 18.6 GB  | 62%           |
| /tmp      | 18.6 GB  | 1%            |
| /data     | 27.9 GB  | 1%            |
| /boot     | 429 MB   | 88%           |
| /boot/efi | 47 MB    | 14%           |

## External Storage

| Device                  | Capacity | Purpose                  |
| ----------------------- | -------- | ------------------------ |
| WD My Passport          | 4 TB     | Engineering backup       |
| Secure Drive            | 2 TB     | Encrypted storage        |
| Ubuntu Installation USB | 16 GB    | Recovery media           |
| Kali Live USB           | 16 GB    | Diagnostics and recovery |

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

---

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
