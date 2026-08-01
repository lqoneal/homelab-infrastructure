# Authorization Validation Report

CAP-021 validates mission, WOP, repository, baseline, authority, operator,
scope, authority lease, decision, and expiry bindings before an authorization
receipt can be accepted.

Result: **PASS**. An authorized receipt is valid only while its explicit lease
is current and its protected-effect flag is true; no corrective-work effect is
created by the boundary.
