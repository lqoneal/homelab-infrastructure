---

document_id: INF-0001
title: Engineering Infrastructure Baseline
version: 1.0
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-06
phase: Mission 0 / Phase 0.1
domain: Infrastructure
classification: Global Infrastructure Baseline
source_of_truth: true
related_documents:

* DOC-0001
* PROJ-0001
* HW-0001
  tags:
* infrastructure
* engineering
* workstation
* storage
* network
* software
* baseline

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

| Repository | Location                           |
| ---------- | ---------------------------------- |
| Homelab    | `/home/loneal/Projects/homelab`    |
| SprinterOS | `/home/loneal/Projects/SprinterOS` |

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

---

# Shared Engineering Services

The following services form part of the global engineering environment.

* Docker
* Containerd
* SSH
* UFW
* SMART Monitoring
* NetworkManager
* systemd-resolved

No failed systemd services were present when this baseline was established.

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

