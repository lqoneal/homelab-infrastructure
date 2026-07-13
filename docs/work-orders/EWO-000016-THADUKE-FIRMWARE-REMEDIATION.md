---
document_id: EWO-000016
title: thaDuke Firmware Remediation
version: 1.0
revision: 1
status: Active
owner: Engineering Governance
created: 2026-07-11
last_updated: 2026-07-11
classification: Engineering Work Order
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: CODEX HANDOFF — Create and Activate Engineering Work Order for thaDuke Firmware Remediation
approval_date: 2026-07-11
persistence_status: Pending
phase: Bounded Engineering Side Mission
domain: Homelab Infrastructure
source_of_truth: true
related_documents:
  - CHAR-0001
  - POL-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - STD-0003
  - SPEC-0001
  - PROC-0001
  - TPL-0001
  - TPL-0002
  - TPL-0003
  - DOC-0001
  - PROJ-0001
  - INF-0001
  - AST-000001
tags:
  - engineering-work-order
  - bounded-side-mission
  - firmware-remediation
  - bios
  - charging
  - thaduke
---

# Engineering Work Order

## Engineering Governance Header

Engineering Operating System: Engineering Operating System (EOS)

Engineering Governance: Engineering Governance

Implementation Agent: Authorized Implementation Agent

Mission: thaDuke Firmware Remediation

Phase: Bounded Engineering Side Mission

Engineering Work Order: EWO-000016

Revision: 1

Title: thaDuke Firmware Remediation

Classification: Engineering Work Order

Status: Active

Execution Mode: Sequential Gated Firmware Remediation

## Governing References

This Engineering Work Order shall comply with:

* CHAR-0001 — Engineering Charter;
* POL-0001 — Engineering Governance Policy;
* STD-0000 — Engineering Governance Documentation Architecture;
* STD-0001 — Engineering Document Lifecycle Standard;
* STD-0002 — Engineering Document Persistence Standard;
* STD-0003 — Engineering Work Order Standard;
* SPEC-0001 — Controlled Document Model;
* PROC-0001 — Engineering Work Order Execution Procedure;
* TPL-0001 — Engineering Work Order Template;
* TPL-0002 — Engineering Completion Report Template;
* TPL-0003 — Engineering Evidence Package Template;
* DOC-0001 — Repository Document Index; and
* PROJ-0001 — Project State.

Repository-controlled records are the engineering authority for execution. Conversation, derived views, filenames, and implementation-agent inference shall not expand this Work Order.

## Engineering Governance Intent

### Purpose

Authorize controlled remediation of the charging failure on the Engineering Workstation `thaDuke`.

The workstation charges while powered off but does not charge while powered on. While the charger is physically connected, the operating system reports:

```text
ADP1/type = Mains
ADP1/online = 0
BAT0/status = Discharging
```

### Mission Classification and Relationship

This is a bounded engineering side mission.

The current primary repository mission, phase, and task remain unchanged. This side mission is temporarily authorized because it concerns the health and continued operability of the Engineering Workstation. It shall not replace, supersede, or displace the primary mission; disturb unrelated governance, controller, staged, unstaged, or untracked work; or combine its execution record with unrelated work. Completion or termination of this side mission returns control to the pre-existing primary mission.

### Target System

| Item | Required Identity |
| --- | --- |
| Hostname | `thaDuke` |
| Platform | HP Spectre x360 Convertible 15-eb0xxx |
| SKU | `9GB30UA#ABA` |
| Board | `86E8` |
| Board revision | `01.77` |
| Current BIOS | `F.16` |
| BIOS date | `2022-11-02` |
| Operating system | Ubuntu 22.04.5 LTS |

An identity discrepancy is a stop condition until resolved.

### Engineering Basis

Mission 0 — Read-Only Charging Diagnostics is complete. It identified a persistent UCSI / USB-C Power Delivery initialization failure.

Mission 1 — Firmware Investigation is complete. It established:

* current BIOS F.16;
* latest identified firmware candidate F.21;
* persistent UCSI timeout;
* firmware / Embedded Controller interaction as the leading cause; and
* a firmware update as warranted.

F.21 is a candidate only. The exact official firmware package, supported update path, and compatibility with the exact product, SKU, board, board revision, and current BIOS require final verification from authoritative HP material before media creation or use.

### Completed Backup Gates

The prior engineering record reports:

* Step 7: `STEP 7 COMPLETE — HOME BACKUP VERIFIED`;
* Step 8: `STEP 8 COMPLETE — DATA BACKUP VERIFIED`;
* Step 9: `STEP 9 COMPLETE — SYSTEM RECOVERY BACKUP VERIFIED`; and
* Step 10: `STEP 10 COMPLETE — UBUNTU/KALI USB IMAGE VERIFIED`.

Verified USB image path:

```text
/mnt/backup/EngineeringBackups/2026-07-11-pre-BIOS-F16/usb-images/ubuntu-kali-multiboot-sandisk-14.6G.img
```

Expected SHA-256:

```text
699ff70a640476aa821c75b2d3d90009e9dbf9607aba02dbf62149f1a92e61e9
```

All backup gates must be reverified immediately before destructive media operations. Prior completion statements do not substitute for current verification.

### Engineering Governance Objectives

The implementation agent shall:

1. reverify all required backup artifacts and checksums;
2. re-identify the previously imaged SanDisk USB without stale device-path assumptions;
3. prepare official HP BIOS update or recovery media only after every preceding gate passes;
4. verify exact-model compatibility and package provenance before destructive media preparation;
5. conduct a controlled BIOS update from F.16 only to the firmware approved through the compatibility gate;
6. validate BIOS, charging, UCSI, USB-C Power Delivery, Thunderbolt, and kernel state after the update;
7. preserve evidence and perform only approved recovery handling if the update fails; and
8. produce separate evidence and completion records and identify required documentation updates.

### Mission Scope

This Work Order authorizes the sequential stages defined below: backup re-verification, verified SanDisk media repurposing, official HP firmware media preparation, pre-flash validation, controlled BIOS update, post-update validation, approved recovery or escalation, and completion documentation.

No destructive USB operation or firmware update may begin unless all prior required verification gates pass.

### Mission Constraints

Execution shall remain bounded to `thaDuke`, the verified backup volume, and the re-identified previously imaged SanDisk USB. Stages shall execute sequentially. A completed stage remains complete unless its inputs change or Engineering Governance authorizes repetition.

No simultaneous unrelated repository modification is permitted. Evidence and completion records for EWO-000016 shall remain separately identifiable.

## Authority Model

### Operational Authority

The implementation agent is authorized to:

* perform PROC-0001 initiation, inventory, preparation, baseline verification, and resume activities;
* mount the identified WD My Passport backup volume using its existing filesystem without changing its storage layout;
* read, hash, and validate required backup artifacts;
* inventory power, firmware, storage, USB, UCSI, USB-C, Thunderbolt, and kernel state;
* obtain official HP firmware packages and vendor documentation after verifying provenance;
* re-identify the target USB immediately before each destructive command;
* run non-destructive validation and collect evidence; and
* create EWO-000016 evidence and completion records and make the documentation updates expressly authorized below.

### Engineering Authority

After successful completion of every preceding gate, the implementation agent is authorized to:

* intentionally erase and repurpose only the verified previously imaged SanDisk USB;
* create the FAT32 or vendor-required update/recovery media using only official HP firmware tooling and packages;
* apply only the official HP firmware approved by exact-platform compatibility verification;
* perform an approved HP BIOS recovery procedure if required by a failed update; and
* update `PROJ-0001`, `INF-0001`, `AST-000001`, relevant EOS/project-state records, and EWO-000016 evidence and completion records to reflect observed remediation results.

This authority is gated and does not make any later stage executable before all earlier completion criteria pass.

### Prohibited Activities

The implementation agent is not authorized to:

* erase any USB until Stage A passes and Stage B positively identifies the intended SanDisk device;
* select firmware by filename alone or use unofficial, modified, repackaged, or uncertain firmware;
* affect any internal disk, its partition table, filesystems, boot configuration, or operating system;
* interrupt firmware writing except when required by an authoritative vendor safety procedure;
* attempt hardware repair or replacement;
* proceed to hardware replacement without a separate authorization decision;
* modify unrelated repository content or disturb existing staged, unstaged, or untracked work;
* stage, commit, push, tag, or publish changes without separate authorization; or
* continue beyond a stop condition.

### Escalation Requirements

Engineering Governance authorization is required when a necessary action exceeds scope, platform or package compatibility cannot be proven, vendor recovery guidance is ambiguous, recovery would require an unapproved method, hardware repair or replacement is proposed, a dependent controlled-document change exceeds the authorized documentation scope, or deterministic execution cannot be maintained.

## Execution Overview

### Stage A — Backup Re-Verification

Mount and verify the WD My Passport backup volume, required archives, system-recovery backup, USB image, and required checksums. Stop on any failure.

### Stage B — BIOS Media Preparation

Re-identify the SanDisk USB, prove it matches the previously imaged device, verify official HP firmware provenance and exact-platform compatibility, then intentionally erase only that verified USB and create the required BIOS update/recovery media.

### Stage C — Pre-Flash Validation

Confirm all backups, stable AC, safe battery charge, current F.16 identity, exact package identity, platform compatibility, media integrity, and absence of stop conditions.

### Stage D — Controlled BIOS Update

Apply only the approved official HP firmware without interruption and record all observed stages and outcomes.

### Stage E — Post-Update Validation

Verify firmware identity, AC detection, battery charging, UCSI initialization, USB-C Power Delivery visibility, Thunderbolt state, kernel logs, and sustained charging behavior.

### Stage F — Recovery, Escalation, and Closeout

If required, preserve evidence and use only the approved BIOS recovery procedure. Determine the next controlled diagnostic or repair mission if charging remains unresolved. Produce evidence, completion reporting, and authorized documentation updates.

## Phase Execution

### Stage A — Backup Re-Verification

Purpose: Prove recoverability inputs before destructive activity.

Inputs:

* identified WD My Passport backup volume;
* Step 7 through Step 10 artifact locations and recorded hashes; and
* current storage inventory.

Activities:

* mount the verified backup filesystem;
* verify the home archive, data archive, system-recovery backup, and USB image;
* reverify every required recorded SHA-256 checksum, including the USB image hash; and
* verify adequate media and backup availability.

Expected Outputs and Evidence:

* mount source, filesystem, and options;
* artifact identities, sizes, timestamps, and checksum results; and
* an explicit PASS or STOP determination.

Completion Criteria: Every required artifact exists and every required checksum matches.

Stop Conditions: Backup drive unavailable, artifact missing, checksum mismatch, ambiguous backup identity, read error, or insufficient evidence.

### Stage B — BIOS Media Preparation

Purpose: Safely repurpose only the intended USB and create official compatible BIOS media.

Inputs: Passing Stage A evidence, current device inventory, official HP source material, and candidate firmware.

Activities:

* re-identify the SanDisk USB by vendor, model, size, serial, and current content;
* compare it with Step 10 evidence;
* verify firmware provenance, package integrity, supported update path, and exact compatibility with the product, SKU, board, board revision, and current BIOS;
* record package identity and hash where available;
* immediately re-identify the device path before every destructive operation;
* erase and repurpose only the verified USB; and
* create and validate FAT32 or vendor-required BIOS media using official HP tooling and packages.

Expected Outputs and Evidence: USB identity, package provenance and compatibility evidence, package hash where available, commands, media layout, written files, and media validation result.

Completion Criteria: The uniquely identified SanDisk contains validated official compatible BIOS update/recovery media.

Stop Conditions: USB identity uncertainty, stale or wrong device path, any target resolving to an internal disk, firmware provenance uncertainty, package mismatch, compatibility uncertainty, unsupported tool behavior, or failed media validation.

### Stage C — Pre-Flash Validation

Purpose: Establish safe flash readiness.

Activities:

* confirm backups remain verified;
* confirm charger connection and stable AC power;
* verify battery charge meets the official HP requirement and is otherwise sufficient for safe execution;
* confirm BIOS is still F.16;
* reconfirm package identity, provenance, integrity, and exact compatibility;
* confirm media integrity; and
* confirm no unresolved stop condition exists.

Evidence Required: Timestamped firmware, battery, AC, platform, package, media, and gate results.

Completion Criteria: Every pre-flash check passes immediately before update initiation.

Stop Conditions: Battery below the vendor-required safe threshold, unstable or unrecognized AC, unexpected BIOS version, package or platform mismatch, firmware utility incompatibility, unexpected hardware state, or any failed prior gate.

### Stage D — Controlled BIOS Update

Purpose: Apply the approved official firmware under controlled conditions.

Activities:

* initiate only the compatible official HP update through the approved method;
* do not interrupt firmware writing; and
* record all observable stages, messages, restarts, versions, errors, and outcome.

Expected Outputs and Evidence: Update method, start and end observations, utility results, reported versions, and outcome.

Completion Criteria: The firmware utility reports successful completion and the system reaches a stable boot state, or execution transitions to Stage F after a recorded failure.

Stop Conditions: Utility incompatibility, pre-write validation failure, unexpected target, or vendor-directed stop. Once firmware writing begins, follow authoritative HP safety behavior and do not interrupt it.

### Stage E — Post-Update Validation

Purpose: Determine whether firmware remediation succeeded and the charging fault is resolved.

Activities:

* verify BIOS version and date;
* verify AC detection and battery charging state;
* verify UCSI initialization and USB-C Power Delivery visibility;
* verify Thunderbolt state and relevant kernel logs; and
* observe sustained charging behavior.

Expected Outputs and Evidence: Post-update identity, power-supply readings, battery percentage trend, UCSI/USB-C/Thunderbolt evidence, kernel logs, and sustained behavior assessment.

Completion Criteria: All required observations are captured and compared with the pre-update baseline.

Stop Conditions: Unexpected firmware identity, unstable system state, unsafe power behavior, or evidence that continued operation risks data or hardware.

### Stage F — Recovery, Escalation, and Closeout

Purpose: Recover safely when authorized, preserve the outcome, and close the bounded mission.

Activities:

* preserve failure evidence;
* use the approved HP BIOS recovery procedure only when required and supported;
* do not proceed to hardware replacement;
* determine the recommended next controlled diagnostic or repair mission;
* create an Engineering Evidence Package and Engineering Completion Report; and
* update only the authorized dependent records with observed results.

Evidence Required: Recovery decision, procedure provenance, actions, outcome, remaining fault state, documentation changes, and recommendation.

Completion Criteria: The system is in a documented stable or escalated state, required records are complete, and control returns to the primary mission.

Stop Conditions: Recovery method uncertainty, unsupported recovery path, hardware intervention requirement, or authority boundary conflict.

## Safety Controls

* Identify destructive targets by stable physical identity and current topology, never by a stale `/dev/sdX` assumption.
* Re-identify the USB immediately before every destructive command.
* Stop if any proposed target is or contains an internal disk.
* Verify backup checksums before USB erasure.
* Use only official HP firmware and tooling from verified vendor sources.
* Never select or approve firmware by filename alone.
* Verify product, SKU, board, revision, current BIOS, supported path, package integrity, and vendor compatibility.
* Verify battery charge and stable AC immediately before flashing.
* Do not interrupt firmware writing.
* Do not perform simultaneous unrelated repository modifications.

## Evidence Requirements

The execution record shall preserve:

* pre-update BIOS identity;
* charging fault evidence;
* backup mount and verification results;
* home, data, system-recovery, and USB-image verification results;
* USB physical identity, topology, prior content, and current device path;
* USB image SHA-256;
* firmware package identity and hash where available;
* vendor/source provenance;
* exact-platform compatibility evidence;
* media-creation method and validation result;
* update stages and result;
* post-update BIOS identity;
* post-update AC and charging state;
* UCSI, USB-C Power Delivery, Thunderbolt, and kernel-log evidence;
* sustained charging behavior; and
* recovery decision and outcome when applicable.

Evidence shall be objective, reproducible where safe, attributable, timestamped where material, and traceable to EWO-000016.

## Documentation Impact

Following remediation, execution shall review and update as supported by observed evidence and within this Work Order's authority:

* PROJ-0001 — Project State;
* INF-0001 — Infrastructure Baseline;
* AST-000001 — Engineering Workstation asset record;
* EWO-000016 Engineering Evidence Package and Engineering Completion Report; and
* relevant EOS/project-state records.

The Engineering Workstation Power & Charging Diagnostics Runbook remains an approved, required documentation follow-up. The completed remediation should be incorporated as a case study. Creation of that controlled runbook requires a separate controlled-document Work Order unless Engineering Governance explicitly expands current authority. This Work Order does not authorize runbook creation.

## Success Criteria

### Mission Success

The mission succeeds when all gates are honored, compatible official firmware is safely applied or an approved recovery/escalation endpoint is reached, required post-update validation is complete, evidence is preserved, and control returns to the primary mission.

### Definition of Done

* Each stage has an explicit PASS, FAIL, BLOCKED, or NOT REQUIRED result.
* No unauthorized device, internal disk, repository work, operating-system state, or hardware is affected.
* Required evidence and completion reporting are complete.
* Authorized dependent records accurately reflect observed results.
* The primary mission resume point is preserved.

### Acceptance Criteria

* Backup gates pass before destructive media work.
* USB identity and firmware compatibility are proven.
* Firmware activity uses only approved official HP materials.
* Post-update validation addresses every required subsystem.
* Recovery and escalation remain within authority.
* Engineering Governance can reconstruct and assess the mission from its controlled record.

Engineering Governance determines mission acceptance.

## Resume Policy

Upon interruption, the implementation agent shall:

1. verify EWO-000016 Revision 1 remains the unique Active authority for this side mission;
2. repeat Operational Inventory, Operational Preparation, and Baseline Verification;
3. verify repository and unrelated-working-tree preservation boundaries;
4. identify the first incomplete stage;
5. revalidate any safety-critical input that may have changed; and
6. resume only at the first incomplete authorized stage.

Completed stages remain complete unless their inputs changed or Engineering Governance authorizes repetition. Device paths, mounts, power state, firmware identity, package availability, and checksums shall never be assumed across sessions.

## Communication Contract

The implementation agent shall report observations, supporting evidence, mission impact, scope compliance, uncertainty, stop conditions, and recommendations. It shall not infer Engineering Governance intent, conceal uncertainty, exceed authority, or continue beyond a stop condition.

## Stop Conditions

Execution shall stop immediately if:

* the backup drive is unavailable;
* a backup artifact is missing;
* any required checksum mismatches;
* USB identity is uncertain;
* the USB device path is stale, wrong, or ambiguous;
* firmware package provenance is uncertain;
* exact platform compatibility is unverified;
* the BIOS package mismatches the target;
* battery charge is below the official safe threshold;
* AC power is unstable or not recognized as required by the vendor procedure;
* the firmware utility reports incompatibility;
* the BIOS version changed unexpectedly;
* an unexpected hardware state exists;
* any operation would affect an internal disk;
* the working-tree preservation boundary would be violated;
* repository integrity or deterministic execution fails;
* a required action exceeds granted authority; or
* another Work Order conflicts within this side mission's execution scope.

The implementation agent shall preserve evidence and report the observation, mission impact, and required resolution. No later gated stage may begin.

## Completion Report Requirements

The EWO-000016 Completion Report shall include:

* Work Order Summary;
* Mission Status;
* stage-by-stage Execution Status;
* Scope Compliance;
* Definition of Done;
* Acceptance Criteria;
* Files Modified;
* Runtime and firmware Changes;
* Repository Integrity and working-tree preservation;
* Engineering Findings;
* Operational Observations;
* evidence inventory;
* recovery outcome when applicable;
* Recommended Next Engineering Work Order;
* primary-mission return state; and
* blank Engineering Governance Notes for governance disposition.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-11 | Created and activated the bounded thaDuke firmware-remediation side mission. |
