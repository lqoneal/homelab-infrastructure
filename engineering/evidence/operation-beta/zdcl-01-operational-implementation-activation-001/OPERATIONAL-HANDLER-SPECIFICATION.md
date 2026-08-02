# Operational Handler Specification

Handler `zeus.operational.zdcl01-native-session` version `0.1.0` accepts only operational `EXECUTE_WORK` and `VERIFY_COMPLETION` gates carrying profile `ZDCL-01`. It verifies mission, session, repository context, idempotency, cancellation, and declared effects. It refuses unrelated missions and undeclared effects. Qualification remains independently available through `zeus.qualification.reference`.
