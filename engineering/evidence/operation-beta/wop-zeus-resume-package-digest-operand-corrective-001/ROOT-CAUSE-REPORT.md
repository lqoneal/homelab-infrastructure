# Root Cause Report

The root cause was operand conflation in the admission supersession start
path. A generic admission projection field was selected before the immutable
Stage 1 package identity was derived and receipt-checked. This made a migrated,
projected, absent, or otherwise non-equivalent value produce the generic
`package digest differs from Stage 1` failure.

The corrective establishes the Stage 1 transaction and its receipt lineage as
the sole package-identity authority and validates all admission bindings
against it.
