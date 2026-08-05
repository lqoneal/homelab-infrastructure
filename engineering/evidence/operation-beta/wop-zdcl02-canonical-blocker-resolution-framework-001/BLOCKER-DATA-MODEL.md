# Blocker Data Model

`scripts.lib.emp.blocker_framework` is the sole blocker projection service. Every object contains identity, lifecycle state, type, severity, originating controller, authoritative source and evidence locator, component/transaction/mission/execution/authority ownership, detection and verification fields, resolution policy, publication impact, retirement condition, reevaluation trigger, and next authorized action.

Objects are derived from authoritative qualification evidence and digest-bound. No text-only or controller-local blocker is accepted.
