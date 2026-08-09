# Session Requirement Ledger

This bounded ledger records the active requirements of the submitted Git
automation corrective and the standing lifecycle constraints carried into it.

| ID | Requirement | Status | Verification |
|---|---|---|---|
| GIT-01 | Persist the Git Automation Contract in current controlled docs | SATISFIED | Architecture/procedure documents; controlled validation |
| GIT-02 | Implement one canonical live repository projection | SATISFIED | `repository_projection.py`; focused tests |
| GIT-03 | Provide machine-readable Zeus CLI projection | SATISFIED | `zeus repository projection --json` |
| GIT-04 | Use plumbing/porcelain, explicit refs, exit codes, NUL paths | SATISFIED | Implementation inspection and 9 focused tests |
| GIT-05 | Use noninteractive Git prompt behavior for unattended projection | SATISFIED | `GIT_TERMINAL_PROMPT=0` in projection runner |
| GIT-06 | Consume projection in directly affected current Zeus verification | SATISFIED | platform/doctor/mission verification wiring |
| GIT-07 | Preserve unrelated dirty/Class-C work | SATISFIED | index and worktree inventory; no cleanup/staging |
| GIT-08 | Preserve Live Projection First and hardcoding-last-resort rules | SATISFIED | controlled docs and projection operands |
| GIT-09 | Do not advance provider/session/execution lifecycle | SATISFIED | native verification and artifact-count inspection |
| GIT-10 | Do not publish, push, or synchronize EOS | SATISFIED | index empty; publication boundary evidence |
| GIT-11 | Run repository, EOS, controlled-doc, semantic, registry, assurance, schema, integrated, and whitespace validation | SATISFIED | final validation report |
| GIT-12 | Persist bounded evidence and omission audit | SATISFIED | this package and final audit |

Earlier lifecycle requirements remain historical input and are not silently
deleted; this corrective does not reopen their completed gates. Downstream
mission-work and closeout requirements remain outside this stop boundary.

