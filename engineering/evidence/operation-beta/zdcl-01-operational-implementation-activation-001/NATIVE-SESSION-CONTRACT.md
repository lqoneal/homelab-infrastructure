# Native Session Contract

The normative contract is in `ZDCL-01-WOP-CONTRACT.md` and implemented by `scripts/lib/emp/native_session.py`. Session identity is UUIDv5 over execution identity. Required authority fields fail closed when absent. State is digest sealed; evidence is sequenced, hash chained, and create-only. Replay with the same binding returns the same session; a conflict is rejected. Completion is not qualification, acceptance, or publication.
