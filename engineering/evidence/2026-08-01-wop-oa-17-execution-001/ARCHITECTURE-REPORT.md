# OA-17 Architecture Report

Authorization is a distinct durable phase after execution start. A request is
bound to execution, mission, WOP, repository, authority, operator, and expiry.
Only a validated, non-expired authorization receipt permits continuation.
State and receipt digests make replay and interrupted recovery deterministic;
invalid, expired, revoked, or ambiguous inputs fail closed.

