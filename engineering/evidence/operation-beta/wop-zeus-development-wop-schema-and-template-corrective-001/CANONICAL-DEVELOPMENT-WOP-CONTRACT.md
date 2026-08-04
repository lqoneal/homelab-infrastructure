# Canonical Development WOP Contract

Development WOPs require the legacy bounded metadata plus:

- `approval.authorized_lifecycle_state: Active`;
- `PROC-0001@1.11`, `TPL-0001@1.7`, and `STD-0000` through `STD-0004`;
- `execution_package_references.authority_node_id` and `authorization_decision_record`;
- all thirteen execution sections, including completion, deliverables, dependencies, sequence, authority, references, classification, prohibited activities, publication, scope, stop/resume, acceptance, and validation.

The source representation is flat for Markdown/DOCX authoring and is projected to the canonical nested submission/package representation. No authority is created by the projection.
