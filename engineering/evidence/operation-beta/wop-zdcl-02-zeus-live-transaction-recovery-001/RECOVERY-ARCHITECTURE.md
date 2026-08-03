# Recovery Architecture

`zeus resume <transaction-id|mission-id>` is the sole canonical transaction recovery entry point. It discovers one persisted Stage 1 record, verifies its immutable inputs, migrates the record in place, reconciles an invalid dispatch, and invokes the existing execution boundary only when dispatch is not receipt-backed.

Authority is resolved from the published Operational Alpha EOS projection and repository publications; the session itself is not an authority source.
