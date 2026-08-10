# Roadmap State Contract

`STATE.yaml` is the only current gate-position record. It explicitly records
roadmap identity/version, program state, current/completed/blocked/pending gate
sets, last completed gate/result/evidence, next authorized action, baseline,
time, and provenance.

The sets must be unique, non-overlapping, exhaustive, and reference known
gates. The current gate must be pending, must exist, and must have all required
dependencies complete. Definition status and state classification must agree.
Project State must carry the same program, roadmap, current gate, and next
action. Unknown, missing, malformed, overlapping, contradictory, or drifted
state fails closed. No newest-file or result-presence fallback is permitted.
