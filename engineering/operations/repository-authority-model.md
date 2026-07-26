# Repository Authority Model

Date: 2026-07-26
Status: Operational model for Zeus Operational Alpha

The repository distinguishes authority domains by record type, not by assuming
different people. Lawrence O'Neal, authenticated as `loneal`, owns every
production authority domain defined by the Authority Ownership Specification.

| Repository record | Authority domain | Production signer |
| --- | --- | --- |
| mission, phase, work item | Mission and Work Authority | `loneal` |
| repository identity and baseline | Repository Authority | `loneal` |
| authority node | Governance Authority | `loneal` |
| approval and authorization decision | Approval Authority | `loneal` |
| identity record | Identity Authority | `loneal` |
| governing baseline | Governance and Qualification Authority | `loneal` |
| operational configuration and revocation | Publication and Execution Authority | `loneal` |
| qualification, completion, reconciliation records | Qualification, Completion, and Reconciliation Authority | `loneal` |

The owner field in operational authority records is `Lawrence O'Neal`.
The signer-principal field is `loneal`. A single enrollment can therefore
satisfy the human ownership relationship for all record types; each record
still requires its own valid content, signature, dependencies, and provenance.

Zeus may persist and enforce an authenticated operator decision, but it cannot
create the decision merely because a command was invoked. Commands represent
the operator's authority; repository policy determines whether that authority
is sufficient and whether the requested transition is valid.

This model is extended by changing data, not control flow. Later domain
delegation uses different owner assignments, enrollment records, trust-policy
principals, and signed envelopes while retaining the same runtime interfaces.
