# Publication Orchestration

The lifecycle records `PUBLICATION_PREPARATION` and
`PUBLICATION_APPROVAL` as authority-aware phases. This candidate does not
publish or merge. Publication uses the existing governed publication service;
when approval is required Zeus records the blocker and resumes from the same
transaction after approval.
