# BETA-01 Qualification Report

The qualification suite covers:

- valid and unknown mission projections;
- staged, eligible, blocked, active, and completed queue views;
- deterministic next selection and dependency ordering;
- existing submission, admission, execution, and lifecycle interfaces;
- malformed authority and production/development isolation;
- idempotent read-only projection behavior;
- controller, roadmap, EOS, Registry, and controlled-document validation.

The queue projection is recalculated from authoritative records on each
request. It does not persist metrics or mutate lifecycle state.
