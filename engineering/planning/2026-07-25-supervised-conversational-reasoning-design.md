# Supervised Conversational Reasoning Design

Mission O implements a closed deterministic intent router, schema-derived WOP
guidance and generation, record-bound explanations, and non-authoritative
session context.

The single source for WOP structure is
`engineering/admission/wop-submission.schema.yaml`. Its Zeus contract extension
owns required sections, execution references, controlled references, example
values, and the operator-review rule. Admission, generated templates, examples,
requirements, CLI guidance, and conversational guidance import that contract.

Generated packages are complete Active candidates with deterministic UUIDv5
identity and canonical digest. Generation returns `review_required: true` and
`automatically_submitted: false`; no admission call is made. Operators review
then explicitly validate or submit through Mission N0.

Conversation supports bounded WOP help, validation and rejection explanation,
status, planning questions, mission preparation, repository inquiries, and
guidance. Unknown intents fail closed. Explanations read facts from existing
selection, eligibility, approval, qualification, reconciliation, or validation
records. Context contains conversation references and recent actions only and
is marked non-authoritative.

No subprocess, repository mutation, policy generation, approval,
authorization, dispatch, or execution interface exists in the reasoning layer.
