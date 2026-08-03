# Legacy Alias Compatibility Plan

Short name `homelab` is accepted only because it equals the canonical
repository directory name and resolves against the verified repository root.
Unknown names, path-only matches to another repository, foreign fingerprints,
and conflicting runtime records fail closed with a controlled mismatch.
Equivalent GitHub SSH/HTTPS forms normalize for comparison; the historical
runtime fingerprint remains unchanged.
