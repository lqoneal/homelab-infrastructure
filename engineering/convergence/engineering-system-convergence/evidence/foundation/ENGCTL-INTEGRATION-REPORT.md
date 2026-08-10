# engctl Integration Report

engctl advances from 0.8.0 to 0.9.0 and adds read-only `roadmap status`,
`show`, `gate`, `results`, and `validate` surfaces. The resolver validates all
canonical inputs before projection and prints `FAIL CLOSED` with a nonzero
status on disagreement.

For Homelab, `engctl resume` renders the convergence program, roadmap, current
and completed gates, blockers, next action, gate definition/result/evidence,
and last result/evidence before the broader legacy context. Resume validation
no longer synchronizes or refreshes EOS. Existing runtime drift is reported
without preventing discovery of the repository-authoritative assessment gate.

The projection remains non-authoritative and requires neither conversation nor
provider/session identifiers.
