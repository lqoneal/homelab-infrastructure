# Platform Self-Audit Specification

The self-audit is read-only and shall verify:

- canonical resolver usage by Beta controllers;
- unique runtime ownership;
- separation of current and historical lifecycle records;
- human/JSON projection parity;
- production/development baseline isolation;
- explicit recommendation dispositions;
- Future Knowledge Audit coverage;
- clean repository and synchronized platform state.

Failure shall identify the invariant and reconciliation boundary and shall not mutate canonical state.
