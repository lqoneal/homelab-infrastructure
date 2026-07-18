# Engineering Notification Event Catalog

## Canonical Baseline

The implementation shall consume the canonical SPEC-0009 envelope unchanged:
schema version, stable event ID, canonical event type, occurrence and recording
times, authenticated producer, subject, Handoff identity, sequence,
correlation/causation, independent classifications, and allowlisted attributes.

## Required Handoff Events

| Event type | Required payload additions | Owner and purpose |
| --- | --- | --- |
| `engineering.handoff.started.v1` | Handoff ID, attempt, execution `RUNNING`, accepted reason | EMLS target owner; qualified bridge transitional producer |
| `engineering.handoff.progress.v1` | milestone code, bounded elapsed seconds | Same lifecycle owner; explicit milestones only |
| `engineering.handoff.report-qualified.v1` | qualifier ID/version, result `PASS` | Report Qualification component |
| `engineering.handoff.report-qualification-failed.v1` | qualifier ID/version, safe reason code | Report Qualification component |
| `engineering.handoff.completed.v1` | execution `PASS`, report `PASS` or legitimate `NOT_APPLICABLE`, overall `PASS` | Single authoritative successful terminal event |
| `engineering.handoff.completion-rejected.v1` | execution `PASS`, report `FAIL`, overall `FAIL` | Report failure without falsifying execution |
| `engineering.handoff.blocked.v1` | blocker class, report result, overall `BLOCKED` | Declared blocker terminal event |
| `engineering.handoff.failed.v1` | safe failure class, exit category, report result | Failed execution terminal event |
| `engineering.handoff.timed-out.v1` | timeout policy ID, elapsed seconds | Timeout terminal event |
| `engineering.handoff.interrupted.v1` | safe signal category | Handled interruption terminal event |
| `engineering.handoff.cancelled.v1` | authorization reference class, safe reason | Authorized cancellation terminal event |

Exactly one terminal Handoff event is authoritative per execution attempt.
Delivery retries never create another lifecycle event.

## Notification-Service Events

- `engineering.notification.delivery-deferred.v1`
- `engineering.notification.delivery-exhausted.v1`
- `engineering.notification.delivery-recovered.v1`
- `engineering.notification.subscription-rejected.v1`

These use a notification-service subject and cannot recursively notify through
the same failed route.

## Candidate Future Event Families

The mission suggestions below are useful integration needs, but SPEC-0009 does
not currently define their canonical types. They remain planning candidates
until ownership, payload, lifecycle purpose, and permissions are separately
specified and qualified.

| Requested concept | Proposed future family | Required authoritative owner | Minimum value-blind payload |
| --- | --- | --- | --- |
| Work Started / Completed | `engineering.work.*` | Authoritative EWO lifecycle owner | work ID, revision, lifecycle transition, project, timestamp |
| Handoff Created | `engineering.handoff.accepted.v1` candidate | EMLS/Handoff Identity Authority | Handoff ID, attempt, authority reference class |
| Qualification Completed | `engineering.qualification.completed.v1` candidate | PROC-0006 execution component/qualified result owner | subject ID, result, finding counts, evidence locator class |
| Publication Completed | `engineering.publication.completed.v1` candidate | PROC-0005 publication executor | transaction ID, document IDs, outcome, immutable locator class |
| Milestone Recorded | `engineering.milestone.recorded.v1` candidate | Controlled milestone record owner | milestone ID, version, status, repository locator class |
| Process Started / Completed / Failed | `engineering.runtime.process.*` diagnostic candidate | Runtime/process supervisor | opaque process ID, component ID, result class, duration |
| Engineering Alert | `engineering.alert.raised.v1` candidate | Domain-specific alert owner | alert ID, domain, severity, safe reason, correlation ID |

Runtime process events are diagnostic only and shall never substitute for
Handoff, Work, qualification, publication, or milestone lifecycle events.

## Payload Policy

Never include prompts, Completion Reports, diffs, command output, repository
content, private endpoints/topics, credentials, tokens, or free-form secrets.
Use bounded identifiers, enumerations, counters, durations, and safe reason
codes. Unknown major schema versions fail closed.
