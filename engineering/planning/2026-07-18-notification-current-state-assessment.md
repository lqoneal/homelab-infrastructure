# Engineering Notification Current-State Assessment

## Baseline

- Repository: `/data/engineering/repositories/homelab`
- Planning baseline: `65d0132c394c8fa5043f9903972e5de7031a020b`
- Governing architecture: Active SPEC-0009 Version 1.0
- Runtime modification: Prohibited and not performed

## Existing Flow

```text
engctl codex
  -> scripts/lib/eos/codex.sh
  -> eos_codex_notification(title, status, repository, EWO, host, duration, signal)
  -> notify_ntfy(...)
  -> synchronous curl POST
  -> configured ntfy topic
```

The wrapper emits `Codex Started`, `Codex Complete`, `Codex Failed`, `Codex
Interrupted`, `Codex Timed Out`, wrapper-bypass, and—within current uncommitted
runtime work—report-qualification-failed observations.

## Components and Configuration

| Asset | Current responsibility | Assessment |
| --- | --- | --- |
| `scripts/engctl` | Sources notification and Codex wrapper libraries | Coupled entry point; no notification command or service client |
| `scripts/lib/eos/codex.sh` | Detects process outcomes and formats messages | Process/session-oriented transitional observation source |
| `scripts/lib/notifications/ntfy.sh` | Loads secrets and performs HTTPS delivery | Reusable transport mechanics, but provider-specific public surface |
| `configs/notifications.env.example` | Documents one ntfy endpoint/topic/token | Secure local pattern; not a multi-provider configuration model |
| `scripts/tests/test-codex-notifications.sh` | Tests lifecycle wrapper and ntfy behavior | Valuable compatibility and failure-isolation suite |
| `.gitignore` | Excludes local notification configuration | Correct secret boundary to preserve |

Configuration is resolved from `NTFY_CONFIG_FILE`, per-user XDG configuration,
or the ignored repository-local file. Mode `0600`, HTTPS, placeholder rejection,
newline rejection, optional bearer token, bounded curl timeouts, and nonfatal
delivery failure are already implemented.

## Coupling and Limitations

- Lifecycle observation, message rendering, routing, and transport invocation
  occur in one wrapper path.
- Wrapper process/session identity substitutes for the not-yet-implemented
  stable Handoff Identity Authority.
- Delivery is synchronous and has no durable outbox, retry schedule,
  obligation identity, acknowledgement, or recovery.
- One ntfy destination and priority apply globally.
- There is no provider-neutral adapter contract or subscription model.
- Delivery evidence is limited to process output and mock-curl test capture.
- Adding a provider would require wrapper or shared-shell changes.
- Current titles use `Codex` process language rather than canonical Handoff
  event types.
- Notification failure is correctly isolated from engineering execution.
- Payloads are bounded and value-blind, but no shared schema validator exists.

## Reusable Assets

Preserve and migrate:

1. ntfy HTTPS request construction and authentication behavior;
2. secure configuration precedence and permission checks;
3. placeholder and control-character rejection;
4. bounded transport timeouts;
5. nonfatal adapter failure behavior;
6. signal, timeout, exit-code, and report-qualification observations; and
7. mock transport and lifecycle regression cases.

## Replacement Opportunity

Replace direct `eos_codex_notification -> notify_ntfy` calls with a qualified
lifecycle bridge that publishes canonical SPEC-0009 envelopes. The Notification
Service, not the wrapper, shall own persistence, routing, retry, adapter
selection, and delivery evidence. The ntfy helper becomes adapter internals or
a compatibility shim until equivalence is proven.

Existing dirty runtime files are user-owned work and were inspected read-only.
This assessment does not classify, accept, or modify them.
