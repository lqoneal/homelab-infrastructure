# Submission Lifecycle State Machine

Development lifecycle projection is receipt-derived:

```text
SOURCE_ACCEPTED -> VALIDATED -> PACKAGED -> REGISTERED -> AUTHORIZED
-> ADMITTED -> DISPATCHED -> EXECUTING -> QUALIFYING -> QUALIFIED
-> PUBLICATION_READY -> PUBLISHED -> SYNCHRONIZING -> SYNCHRONIZED
-> CLOSING -> CLOSED
```

The implementation records only the first five receipt-backed phases during
ordinary submission. With no configured qualified executor it stops at:

```text
State       : AWAITING_EXECUTION_DISPATCH
Completed   : VALIDATED, PACKAGED, REGISTERED, AUTHORIZED, ADMITTED
Pending     : DISPATCHED
Next action : Dispatch to a qualified Development execution agent
```

No phase is appended merely because a loop reached its name. Terminal phases
require their receipt contracts and predecessor receipts. Historical records
using the former projection are immutable and are not reinterpreted in place.
