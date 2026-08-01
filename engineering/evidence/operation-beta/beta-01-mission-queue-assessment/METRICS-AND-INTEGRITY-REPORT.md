# BETA-01 Metrics and Integrity Report

The projection derives mission-inventory, staged, eligible, blocked, active,
and completed counts from the Mission Knowledge Model on every request. EMP
submission-specific metrics remain owned by the orchestration store and are not
duplicated into the MKM projection. It also reports the readiness next mission
and source authority.

Integrity checks remain delegated to existing authoritative services:

- MKM validates mission order, roadmap provenance, dependencies, readiness, and
  capability prerequisites;
- EMP validates submission, priority, approvals, resources, and policy;
- Zeus admission validates repository, baseline, authority, and agent context;
- WOP lifecycle validates ordered transitions and hash-chain history;
- EOS validates synchronized platform state.

No metric is persisted as independent authority. Unknown views and malformed
authority fail closed.
