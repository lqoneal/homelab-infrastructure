# Direct Submission Root Cause

The canonical Stage 1 `zeus submit <WOP>` path already validates an unpublished Development WOP and establishes the receipt-backed transaction, authority, registration, and admission state. The remaining publication-before-submission dependency was semantic: the mission-oriented package resolver returned a publication action for an unavailable package, and controlled lifecycle descriptions called the package “published”.

The corrective makes submission explicitly the first lifecycle event and treats publication and EOS synchronization as later qualification/output gates.
