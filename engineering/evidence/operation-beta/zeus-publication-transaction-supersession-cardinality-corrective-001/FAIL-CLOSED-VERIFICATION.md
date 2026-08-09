# Fail-Closed Verification

Focused regression tests prove failure for duplicate publication identity,
missing superseded target, wrong Mission, wrong WOP, wrong repository, cycle,
two unrelated open tips, two incompatible open sibling successors, malformed
transaction JSON, and receipt/state integrity mismatch. No failure path selects
a winner by timestamp.

Failed/aborted successors do not retire a predecessor. A terminal-qualified
historical sibling does not create false cardinality when exactly one open
authorized reprepare exists. Read-only resolution leaves input records, Git
index, repository candidate files, transaction files, and historical receipts
unchanged.
