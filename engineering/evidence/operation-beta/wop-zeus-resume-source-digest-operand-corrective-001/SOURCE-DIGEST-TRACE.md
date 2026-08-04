# Source Digest Trace

`status`, `session`, and `resume` enter the shared Stage 1 execution resolver.
The resolver loads the receipt-backed transaction, resolves admission lineage,
validates any execution projection, and then hands the current successor to the
runtime.

The prior failure occurred while validating a lineage admission whose generic
`source_digest` field was absent. The corrected path resolves source identity
from Stage 1 first and treats the absent generic field as non-authoritative.
