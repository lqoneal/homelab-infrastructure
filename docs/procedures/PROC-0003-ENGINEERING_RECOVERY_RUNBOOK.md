---
document_id: PROC-0003
title: Engineering Recovery Runbook
version: 1.2
status: Active
owner: Engineering Governance
created: 2026-07-15
last_updated: 2026-07-19
phase: Controlled Documentation Reconciliation and Engineering Standards Update
domain: Engineering Recovery
classification: Engineering Procedure
predecessor_revision: PROC-0003@1.1
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff - Mission 0 Controlled Documentation Reconciliation and Engineering Standards Update
approval_date: 2026-07-19
persistence_status: Pending
source_of_truth: true
declared_deferrals:
  - engineering-recovery-automation-design
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: related_to
    target: PROC-0001
  - type: conforms_to
    target: STD-0005
  - type: related_to
    target: INF-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - recovery
  - backup
  - restoration
  - evidence
  - storage
  - raspberry-pi
---

# Engineering Recovery Runbook

## Purpose

This runbook is the authoritative Homelab procedure for acquiring, verifying,
preserving, cleaning up, and qualifying restoration of block-device recovery
images. It converts the workflow qualified during SprinterOS Sprint 1.1 into a
reusable engineering control and preserves the lessons established by that
qualification.

## Scope

This procedure applies to whole-device recovery images acquired for Homelab or
portfolio systems using shared Homelab storage. It governs acquisition,
verification, artifact finalization, Windows NTFS reconciliation, controlled
cleanup, restore qualification, and evidence. A project record may define its
source identity, destination hierarchy, naming suffix, retention period, and
acceptance constraints, but shall reference this procedure instead of
duplicating it.

This runbook does not itself authorize acquisition, repair, cleanup,
restoration, platform modification, or automation. It does not make an image
restoration-qualified merely because the image is checksum-verified.

## Authority

Engineering Governance owns this procedure. An Active Engineering Work Order
or other explicit bounded mission authority shall identify the source,
destination, permitted actions, evidence location, acceptance criteria, and
stop conditions for each execution. Infrastructure and asset records remain
the information authorities for device identity and storage ownership.
Project-controlled records remain the information authorities for the system
baseline being protected.

Recovery qualification and restoration qualification are separate decisions.
Corrective action, including filesystem repair, media replacement, and
platform update, requires authority distinct from diagnostic qualification
unless the mission explicitly combines them.

## Preconditions

Before any recovery action, execute Engineering Work Initiation under
PROC-0001 and record:

1. mission authority, operator, execution host, UTC start time, and applicable
   controlled-document revisions;
2. repository identity, branch, HEAD, remotes, validation state, and all
   pre-existing working-tree changes;
3. source and destination assets using stable identity, model, exact capacity,
   expected partition layout, and applicable asset records;
4. mount state, filesystem type and health, required tools and versions,
   available destination bytes, and evidence destination;
5. the recovery point required before any major platform modification;
6. rollback criteria and confirmation that no destructive or corrective action
   is implied by qualification authority; and
7. the execution environment, including whether commands run on the
   Engineering host or in a sandbox, container, remote session, chroot, or
   other constrained context; effective repository and device access; write
   capability required by the mission; namespace and privilege boundaries;
   and any policy-imposed mount, network, tool, or filesystem constraints.

Device paths are observations, not identities. Re-discover identities after
every reconnect, reboot, remount, or session resumption. The destination shall
have more free bytes than the worst-case completed artifact and evidence set,
including an engineering margin specified by the mission. Source partitions
shall be unmounted for normal acquisition. Live acquisition is prohibited
unless explicitly accepted as a documented exception with consistency limits.

### Evidence Identity Verification

Before technical investigation, positively identify every source, target,
destination, evidence artifact, and applicable repository. Correlate stable
hardware identifiers, exact capacity, partition and filesystem identifiers,
physical attachment, controlled asset records, artifact names and hashes, and
expected topology as applicable. Preserve this correlation before
qualification, recovery, repair, restoration, or forensic analysis.

Do not infer identity from a device path, mount point, readable content,
successful command, backup label, or operator expectation alone. Stop when
identity is ambiguous, inconsistent, duplicated, or changes unexpectedly.

### Execution Environment Verification

Determine infrastructure state from the Engineering host. A sandbox may
present a read-only bind mount, hidden device nodes, filtered logs, restricted
privileges, or a different namespace while the host remains healthy. Compare
VFS and filesystem options, host configuration, device mapping, repository
ownership, and effective write capability in the host context before
classifying an infrastructure failure.

Execution-environment constraints are limitations of the investigation unless
independently corroborated by host evidence. If host verification is not
authorized or available, report the limitation and leave infrastructure state
undetermined; do not remount, repair, or reconfigure based solely on sandbox
observations.

### Investigation Sequence

Apply the following order and preserve evidence at each boundary:

1. verify authority, scope, repository state, and execution environment;
2. positively identify evidence and assets;
3. inventory configuration, topology, mounts, dependencies, and symptoms;
4. acquire original non-mutating evidence;
5. qualify the evidence and isolate the failing layer or variable;
6. preserve required artifacts and establish rollback;
7. request or confirm separate corrective authority;
8. perform recovery or repair only when supported; and
9. validate restoration and operational deployment as separate decisions.

Evidence acquisition, qualification, recovery, restoration, and operational
deployment are not interchangeable. Preservation precedes repair, and
qualification precedes recovery whenever practical.

## Recovery Acquisition

### Block-Device Imaging

1. Shut down the protected system cleanly, remove its media when applicable,
   attach it to a separate qualified execution context, identify it again, and
   keep all source partitions unmounted.
2. Qualify and mount the destination by stable identifier with
   `nosuid,nodev,noexec`; assess it read-only before any authorized read-write
   remount.
3. Record the source exact byte count before reading it.
4. Read the entire block device, including partition table and boot regions.
   Use a tool and options that preserve input alignment, make short reads
   explicit, and produce an auditable byte count. When `dd` is authorized,
   `iflag=fullblock` and `conv=noerror,sync` provide the qualified semantics.
5. Write to a uniquely named `.partial` artifact. If a pipeline compresses or
   transports the stream, enable pipeline-failure propagation and capture the
   status of every stage, not only the last process.
6. Do not mount, repair, resize, update, or otherwise modify the source during
   acquisition.

### Synchronization and Logging

Capture stdout, stderr, command lines, stage exit status, UTC timestamps, and
transfer counters in the original acquisition log. Preserve that log
unchanged. On stream completion, require all stages to exit successfully,
synchronize buffered writes to stable storage, and record synchronization
completion before verification begins.

### Acquisition Monitoring

Monitor progress without interrupting the data path. Record periodic UTC time,
bytes completed, elapsed time, calculated throughput, source and destination
health observations, and available destination space. Monitoring shall not
substitute for final counters or verification.

### Acquisition Evidence

Evidence shall include sanitized stable identities, exact source size,
partition observations, mount state, commands and versions, the original
transfer log, stage exit statuses, byte counters, timing, throughput,
synchronization result, operator observations, and every warning or error.

## Recovery Verification

### Exact Byte-Count Validation

For an uncompressed image, the completed image size shall equal the recorded
source byte count. For a compressed or transported image, verify that the
decoded stream contains exactly the recorded source byte count. Transfer
counters shall agree with that value. Any short, excess, ambiguous, or
unaccounted byte count fails qualification.

### Dual Independent SHA-256 Verification

Perform two complete SHA-256 reads of the finalized artifact in separate
passes. The passes shall be independently invoked after synchronization and
shall both read the destination artifact from storage. Record each command,
start and end time, exit status, and digest. Both digests must match exactly.
Publish the accepted digest in an adjacent checksum manifest and verify that
manifest from its final directory. A manifest shall not hash itself.

Checksum agreement proves artifact stability, not source equivalence. Where
the source remains available, also compare a complete decoded artifact stream
with the unmounted source or use an equivalently strong full-read comparison.
Test compressed-container integrity separately and inspect partition and
filesystem signatures read-only.

### Acceptance Criteria

An artifact is recovery-qualified only when all of the following pass:

- source identity and exact byte count are unambiguous;
- acquisition and every pipeline stage completed successfully;
- destination synchronization completed;
- decoded byte count equals the source byte count;
- two independent SHA-256 passes match and the published manifest verifies;
- format integrity and required full-stream/source comparison pass;
- read-only structural inspection finds the expected layout;
- required logs, metadata, summaries, and observations are preserved; and
- no stop condition remains unresolved.

Failure of any criterion leaves the artifact partial, failed, or quarantined;
it shall not become the recovery prerequisite for a platform change.

## Artifact Finalization

Use the project-approved hierarchy and UTC-based canonical name. The minimum
artifact set is the finalized image, `.sha256` manifest, metadata record,
acquisition log, and verification summary. Only after all acquisition gates,
synchronization, and format checks pass may an image be atomically renamed
from `.partial` to its final image name. The verification summary shall clearly
state `RECOVERY-QUALIFIED` or `NOT RECOVERY-QUALIFIED` and separately state
`RESTORATION-QUALIFIED` or `NOT RESTORATION-QUALIFIED`.

Metadata shall record authority, operator, UTC timing, sanitized asset
identities, exact source and artifact sizes, format, commands and tool
versions, transfer counters, synchronization, both SHA-256 results, structural
checks, limitations, evidence paths, and final disposition. Preserve the first
verified pre-change baseline, every artifact referenced by an active incident
or controlled record, and the project-required number of newer verified
images. Never replace the sole verified rollback image.

Evidence and accepted artifacts shall be protected from routine mutation.
Apply storage controls available to the evidence system—restricted write
access, read-only snapshots, immutable flags, or write-once retention—and
record which control was used. Never alter an original log or artifact to make
the evidence appear cleaner.

## Windows NTFS Reconciliation

### Dirty-State Qualification and Online Assessment

If the destination is NTFS, first inventory it without repair. Record the
stable device identity, filesystem implementation, mount state, dirty flag,
Windows fast-startup or hibernation indicators, and kernel or driver errors.
Prefer a read-only mount for assessment. A read-write mount shall not be forced
when NTFS is dirty, hibernated, inconsistent, or already mounted elsewhere.

When Windows is available, use native Windows health assessment and a clean
shutdown to clear state. Disable fast startup for media shared with Linux when
the platform baseline permits. Record native tool output and reboot results.

### Offline Repair Authority

Offline repair is corrective action and requires explicit authority. Before
repair, preserve diagnostic evidence and, when feasible, protect the most
recent verified artifacts elsewhere. Use the filesystem owner's native repair
tool for full repair. Linux `ntfsfix` is a limited reconciliation aid, not a
substitute for Windows `chkdsk`, and shall not be represented as full repair.
Stop on media I/O errors, identity ambiguity, unsupported features, or evidence
that repair could endanger the only verified recovery image.

### Safe Remount and Ejection

After a clean assessment or authorized repair, unmount fully, reconnect or
rescan as required, re-identify the volume, and mount by stable identifier with
the approved options. Confirm the expected source and read-write status before
writing. At closeout, synchronize, wait for writes to finish, unmount every
partition, verify no process or mount remains, power off/eject the device with
the operating-system mechanism, and only then disconnect it.

## Recovery Cleanup

Cleanup is allowed only under explicit authority after at least one replacement
artifact is fully recovery-qualified and all preservation and retention gates
pass. Inventory candidate artifacts by stable path, size, checksum state,
creation mission, references, and disposition before removal.

Remove only named obsolete partials, failed attempts, or superseded artifacts
within the authorized set. Preserve original acquisition and verification
logs, metadata, checksum manifests, evidence referenced by controlled records
or incidents, the first verified pre-change baseline, the sole verified image,
and the project retention minimum. Do not delete an artifact merely to satisfy
free-space pressure. Record each removed path, reason, authority, UTC time,
bytes reclaimed, remaining free space, and retained recovery set. Revalidate
the retained manifests after cleanup.

## Restore Qualification

Restoration requires separate authority naming the accepted image and the
specific target media. A recovery-qualified image is not automatically
restoration-qualified. Restore only to positively identified whole-device
media that is at least as large in exact bytes and suitable for the workload;
it shall be neither internal host storage, the backup device, nor the preserved
original source.

Before writing, verify the published SHA-256. Write the complete decoded image,
capture every pipeline status, synchronize, and read back the written range for
a full comparison with the decoded artifact. Inspect partitions and
filesystems read-only. Boot the intended platform and verify identity, firmware
and OS expectations, partition layout, services, network and administrative
access, time synchronization, application checks required by the project, and
absence of storage, power, thermal, or throttling faults.

The first image and the first image after a material boot, firmware, OS, or
storage-layout change require a rehearsal on equal-or-larger spare media. Keep
the original source unchanged until read-back, boot qualification, evidence,
and closeout pass. Roll back to the preserved original or stop for governance
decision on checksum mismatch, incomplete write, read-back mismatch,
unexpected layout, boot failure, required-service failure, or new hardware or
storage error. Restore testing shall never overwrite the only rollback path.

## Raspberry Pi Update Qualification

Verified rollback is a prerequisite to a Raspberry Pi update. After a
separately authorized update, allow the mandatory stabilization period defined
by the project or vendor before declaring failure or cycling power; when no
stronger value exists, observe at least 15 minutes after apparent first boot.
Use an extended first-boot qualification window of at least 30 minutes because
package configuration, firmware work, filesystem expansion, and service
settling can materially exceed ordinary boot time.

During and after that window, record console and journal behavior, boot count,
service convergence, temperature, throttling, undervoltage, kernel errors, and
storage health. Validate the boot device with full kernel-log review, block and
filesystem state, capacity, read behavior, and available device health data.
Do not accept an update while new MMC or filesystem errors remain unexplained.

## Storage Diagnostics

### Non-Destructive Removable-Media Qualification

The qualified Engineering Platform toolchain is `lsblk`, `blkid`, `blockdev`,
`findmnt`, `udevadm`, `smartctl`, and the applicable filesystem checker in an
explicit non-repair mode. Apply this sequence to a separately authorized
storage-qualification mission:

1. capture UTC time, authority, host, operator, package versions, repository
   state, and the complete pre-attachment block-device inventory;
2. attach one candidate device, compare inventories, and establish identity
   from transport, model, serial, WWN when available, exact byte size,
   partition UUID, filesystem UUID, and udev properties rather than a device
   path alone;
3. confirm every candidate partition is unmounted and record the kernel
   read-only flag with `blockdev --getro` before inspection;
4. inspect the partition table and filesystem signatures read-only with
   `lsblk`, `blkid`, and non-modifying filesystem-specific tooling; for exFAT,
   use `fsck.exfat -n`, never a repair option;
5. inspect SMART identity, capability, attributes, health, and error logs with
   `smartctl`; if a USB bridge requires an explicit device type, record the
   detected or selected bridge mode and treat unavailable pass-through as a
   qualification limitation rather than a healthy result;
6. when the mission authorizes content inspection, mount the identified
   partition at a dedicated empty mount point using
   `ro,nosuid,nodev,noexec`, verify those effective options with `findmnt`,
   and perform only the authorized read operations;
7. unmount with `umount`, verify with `findmnt` that no mount remains, check
   for open users when needed, and use the operating-system power-off/eject
   mechanism before disconnection; and
8. preserve commands, stdout, stderr, exit statuses, stable identities,
   versions, SMART limitations, filesystem observations, mount options,
   qualification decisions, and hashes or inventories produced by the
   authorized evidence workflow.

Do not run SMART self-tests, destructive read tests, repair modes, writable
mounts, label or UUID changes, registration, or asset assignment unless a
separate mission explicitly authorizes that action. A successful read-only
mount validates access for that media; tool availability alone validates the
platform capability but makes no claim about a storage asset.

Backups and successful reads are evidence, not qualification decisions.
Qualification requires identity-linked evidence sufficient for the stated
use, including material limitations and contradictory observations. Record a
temporary disqualification or pending-qualification disposition when the
evidence is incomplete, unsafe to extend, or dependent on an unisolated
component.

### Hardware Failure Isolation

Before permanently disqualifying an asset, vary one factor at a time when safe
and within authority. For storage investigations this commonly means comparing
media, reader or enclosure, controller, interface, host, power delivery,
adapter, and cable independently. For compute, network, and peripheral assets,
apply the same method to their equivalent replaceable layers.

Capture the baseline symptom before substitution, preserve stable identity,
change only the selected variable, repeat the relevant non-destructive test,
and record whether the fault follows the asset or remains with the path. An
unavailable SMART bridge, failed mount, or single-host error does not by itself
permanently disqualify the media.

### MMC I/O Classification

Classify each storage symptom by layer and preserve its exact timestamp and
kernel message:

- transport/controller: command timeouts, CRC errors, resets, tuning failures,
  or repeated retries;
- media: uncorrectable reads, bad blocks, capacity instability, or failures at
  repeatable sectors;
- block layer: request failures and read/write error ranges;
- filesystem: journal replay, metadata inconsistency, remount-read-only, or
  allocation errors; and
- application: missing or corrupt files without lower-layer evidence.

A filesystem error does not by itself prove failed media, and clean filesystem
metadata does not clear repeated controller or media I/O errors. Correlate
kernel evidence, repeatability, alternate-reader tests, power and thermal
state, and read-only filesystem checks before assigning cause.

### Emergency Mode and Local-Console Sequence

Emergency mode is a controlled diagnostic state, not proof of catastrophic
failure. Do not repeatedly power-cycle it. At the local console:

1. photograph or transcribe the first failure and timestamp;
2. record power, undervoltage, and thermal indicators;
3. identify the failed unit or mount with `systemctl --failed`, the boot
   journal, and kernel log;
4. inventory block devices, stable identifiers, partition layout, filesystem
   types, and mount state;
5. compare `/etc/fstab`, cryptographic mappings, and device identity with the
   controlled baseline;
6. preserve logs to separate media when safe;
7. perform read-only filesystem and media assessment; and
8. decide whether the evidence indicates configuration, filesystem, transport,
   power, or media failure before requesting corrective authority.

Do not run a modifying filesystem check, rewrite configuration, remount a
questionable filesystem read-write, or conceal the original symptom during
diagnosis.

## Engineering Evidence

Each execution shall preserve:

- mission authority, controlled-document revisions, operator, host, and UTC
  start/end times;
- source, target, and destination identity evidence without publishing secrets
  or unnecessary serials;
- exact sizes, partition and mount observations, filesystem health, capacity,
  commands, tool versions, and exit statuses;
- original acquisition, monitoring, synchronization, diagnostic, and restore
  logs;
- metadata, checksum manifests, both independent SHA-256 results, format and
  read-back results, and verification summaries;
- elapsed time, throughput, progress samples, boot/stabilization timing, and
  storage-health observations;
- operator observations, warnings, exceptions, limitations, stop decisions,
  and final artifact disposition; and
- every instrumentation defect and the independent evidence used to qualify or
  reject the affected conclusion.

Instrumentation defects shall be recorded, not hidden or silently repaired in
the original evidence. Preserve the original evidence immutably and create a
separate annotated qualification record. Qualification determines what the
evidence supports; corrective action changes a system or artifact. Keep those
activities and their authorities distinct.

## Stop Conditions

Stop immediately and preserve evidence when any of the following occurs:

- authority, controlled-document identity, numbering, ownership, retention, or
  governing relationship is ambiguous or conflicting;
- source, destination, target, or mount identity is ambiguous, changes, or
  resolves to internal storage or another protected asset;
- source partitions are mounted for an offline acquisition, the source cannot
  be cleanly stopped, or a live acquisition lacks explicit exception authority;
- destination filesystem health or mount state is unsafe, NTFS is dirty or
  hibernated, required repair lacks authority, or safe ejection cannot be
  confirmed;
- destination space is insufficient or falls below the mission margin;
- a source, destination, transport, MMC, filesystem, power, thermal, or media
  I/O error occurs or remains unexplained;
- acquisition, compression, transport, synchronization, hashing, comparison,
  or restoration returns a nonzero, missing, or ambiguous status;
- transfer counters or decoded bytes differ from the exact source byte count;
- either SHA-256 pass fails or the two digests, manifest, source comparison, or
  restore read-back do not match;
- an artifact, original log, checksum, metadata record, or required evidence is
  missing, altered, or cannot be protected;
- the only verified recovery image, preserved original source, active-incident
  evidence, or retention minimum would be endangered by cleanup or restore;
- target media is undersized, unsuitable, or not uniquely identified;
- unexpected partition layout, boot behavior, service failure, emergency mode,
  or new post-update storage-health fault appears;
- an instrumentation defect prevents the required conclusion and independent
  evidence is insufficient;
- repository integrity or required validation fails; or
- deterministic execution cannot be maintained or an action would exceed the
  mission authority.

The SprinterOS Sprint 1.1 missing pipeline-exit field is a historical qualified
exception, not permission to ignore a future missing status. It was accepted
only because the original transfer log, operator-observed process exit zero,
complete transfer counters, exact byte count, and two full matching SHA-256
passes independently supported the recovery conclusion. Its live-acquisition
limitation and deferred restoration qualification remain explicit.

## Engineering Incident Lessons Learned

The reusable conclusions established by qualification are:

1. qualify recovery before any major platform change;
2. require a verified rollback artifact before system updates;
3. keep recovery qualification separate from restore qualification;
4. treat emergency mode as diagnostic evidence rather than catastrophic
   failure by assumption;
5. isolate storage faults across power, controller, transport, media, block,
   filesystem, and application layers;
6. allow and observe extended Raspberry Pi stabilization and first-boot windows;
7. preserve original evidence and disclose instrumentation defects;
8. keep evidence qualification separate from corrective action; and
9. never trade the only verified rollback path for convenience or storage
   reclamation.

## Completion Report Requirements

The Engineering Recovery completion report shall contain:

1. authority, scope, operator, host, controlled references, and execution
   timing;
2. source, destination, target, and filesystem qualification;
3. acquisition method, exact bytes, stage results, timing, throughput, and
   synchronization;
4. both SHA-256 passes, manifest verification, format checks, full comparisons,
   and structural inspection;
5. final artifact names, locations, sizes, metadata, preservation controls,
   retention, and cleanup disposition;
6. NTFS assessment or repair/ejection outcome when applicable;
7. restoration authority, write/read-back, boot, stabilization, rollback, and
   qualification outcome when applicable;
8. logs and evidence inventory, operator observations, instrumentation defects,
   limitations, deviations, and stop conditions encountered;
9. repository, document, relationship, and index validation results;
10. explicit scope confirmation that unauthorized platform, recovery-artifact,
    and repository changes did not occur; and
11. exactly one terminal status: `ENGINEERING RECOVERY COMPLETE` or `BLOCKED`.

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-15 | Published the authoritative recovery workflow and lessons qualified during SprinterOS Sprint 1.1. |
| 1.1 | 2026-07-16 | Added the qualified non-destructive removable-media discovery, SMART, read-only filesystem and mount, safe-unmount, stable-identification, and evidence-preservation workflow. |
| 1.2 | 2026-07-19 | Required evidence identity and execution-environment verification, separated acquisition through deployment decisions, established preservation-before-repair sequencing, codified evidence-based storage qualification and temporary disqualification, and required one-variable hardware isolation before permanent disqualification. |
