# Submission Deadlock Root Cause

Before this change, direct submission entered the Stage-1 package path, but the authoritative execution chain was represented only by a later runtime record. Controllers therefore treated provenance, admission, or execution identity as inputs even though each was derived from the submitted source. The bootstrap envelope makes `zeus submit` the root transaction and retains fail-closed validation.
