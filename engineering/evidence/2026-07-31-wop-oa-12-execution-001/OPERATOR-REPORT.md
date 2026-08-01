# OA-12 Operator Report

The Mission Brief is a read-only projection of the Mission Knowledge Model,
roadmap provenance, and Capability Registry. It exposes the complete engineering
narrative, previous/current/next mission context, Mission 12 of 30 progress, and
the dynamic Zeus capability delta.

The `mission explain`, `mission readiness`, and `mission blockers` controllers
remain distinct projections over the same authoritative model and report
consistent OA-11 COMPLETED and OA-12 CURRENT/eligible state.

Verification commands:

```text
zeus mission brief OA-12
zeus mission brief OA-12 --verify
zeus mission brief OA-12 --json
zeus mission explain OA-12
zeus mission readiness OA-12
zeus mission blockers OA-12
```
