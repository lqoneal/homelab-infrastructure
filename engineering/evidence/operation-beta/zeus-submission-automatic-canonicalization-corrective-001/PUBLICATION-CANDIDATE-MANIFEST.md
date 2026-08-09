# Publication Candidate Manifest

Corrective implementation files:

- `scripts/zeus`
- `scripts/lib/emp/wop_canonicalization.py`
- `scripts/lib/emp/submission_boundary.py`
- `engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md.traceability.json` (derived immutable provenance)

Corrective test:

- `scripts/tests/test-zeus-submission-automatic-canonicalization.py`

Controlled documents:

- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`
- `engineering/docs/operations/ZEUS-WOP-AUTHORING-GUIDE.md`
- `engineering/docs/architecture/ZEUS-WOP-SUBMISSION-PROCEDURE.md`
- `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md`
- `engineering/docs/architecture/WOP-SCHEMA-AND-EXECUTION-INTERFACE.md`

Evidence directory:

- `engineering/evidence/operation-beta/zeus-submission-automatic-canonicalization-corrective-001/`

The lifecycle source and all unrelated pre-existing dirty paths are preserved.
The existing unrelated `scripts/zeus` managed-handoff hunks must be isolated
from the corrective routing hunks at publication. No files were staged,
published, pushed, or synchronized to EOS.
