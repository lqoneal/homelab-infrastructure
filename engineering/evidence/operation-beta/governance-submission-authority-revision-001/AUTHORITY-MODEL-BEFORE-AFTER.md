# Governance Submission Authority Revision — Before/After

## Before

Stage 1 Development submission required `governance_authority: Engineering
Governance` after the operator had already invoked the authoritative Zeus
submission interface. Runtime records also described submission as execution
authority, and controlled procedure text placed execution authorization before
submission.

## After

`zeus submit <WOP>` is the single canonical submission protocol. The operation
itself establishes submission authority and creates validation, registration,
and provenance. Mission/WOP authority resolution, admission, execution
authorization, effect authorization, approval, acceptance, publication,
synchronization, and closeout remain separate downstream controls.

```text
AUTHORITATIVE_SUBMISSION_IS_SUBMISSION_ACT=YES
SECOND_GOVERNANCE_SUBMISSION_DECLARATION_REQUIRED=NO
DEVELOPMENT_PRODUCTION_SUBMISSION_PROTOCOL_DISTINCTION=NONE
SUBMISSION_IMPLIES_EXECUTION_AUTHORITY=NO
SUBMISSION_IMPLIES_PUBLICATION_AUTHORITY=NO
```
