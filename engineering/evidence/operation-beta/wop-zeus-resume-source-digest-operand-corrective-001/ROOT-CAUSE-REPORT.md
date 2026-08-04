# Root Cause Report

The root cause was treating a generic admission `source_digest` field as
mandatory and authoritative. A migrated successor omitted that field, causing
the comparison to reject `observed=None` despite the immutable Stage 1 source
digest being receipt-backed.

The corrective separates canonical Stage 1 source identity from generic
projection metadata and preserves strict equality for every present generic or
Stage 1-specific binding.
