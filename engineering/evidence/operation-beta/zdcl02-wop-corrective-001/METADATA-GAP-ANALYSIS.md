# Metadata Gap Analysis

| Gap | Resolution in v2.1 | Residual admission check |
|---|---|---|
| Revision disagreement | One 2.1 identity | Verify source digest and exact submitted revision |
| Unpinned baseline | Current baseline plus protected tag digests declared | Reverify clean tree and baseline at admission |
| Pending authority result | Producer/state/persistence named | Resolve policy attestation and EMM identity |
| Pending ETP | Producer and frozen manifest named | Resolve one compatible active profile |
| Provider registry ambiguity | Existing resource/qualification record required | Reject duplicate/foreign/conflicting providers |
| Receipt ownership | Producer-specific ownership stated | Verify digest, ordering, replay, and provenance |
| Domain overlap | Boundary table added | Reject scope that crosses owners without authority |

No gap is silently filled by the corrected WOP.
