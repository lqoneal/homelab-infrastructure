# Predecessor Alias Resolution

The predecessor admission is a supported alias. It resolves deterministically
through `superseded_by` to
`EMM-DEV-ADMISSION-120e6eb0b34c6cadf46fd857d5e43bc4`, the sole terminal
successor. Supplying the successor directly returns the same result.

The resolver does not rewrite either admission or the execution projection.
