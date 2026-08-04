# Root Cause

The Stage 1 transaction projection exposed the absence of authority snapshot,
provider selection, and dispatch receipts as if they were pre-resume
requirements. Those artifacts are produced by canonical resume for an
authorized transaction in `AWAITING_EXECUTION_DISPATCH`.

The existing recovery verifier already distinguished pending dispatch work
from invalid authority, receipt, repository, and baseline state. Readiness did
not reuse that distinction, creating a circular prerequisite.

No live runtime or receipt was changed.
