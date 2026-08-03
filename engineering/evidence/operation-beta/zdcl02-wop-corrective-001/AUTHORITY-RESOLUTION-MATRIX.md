# Authority Resolution Matrix

| Input | State before admission | Admission resolver | Required outcome |
|---|---|---|---|
| Development policy | Published active policy `MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY@1.0` | Zeus/EMM policy verifier | active, exact policy id |
| WOP identity | Source declares `...@2.1` | WOP intake/EMM | exact identity and digest |
| Governance submission | Not asserted by source alone | authorized Engineering Governance submission | complete attestation |
| EMM registration | Not created by this corrective | EMM registration service | one exact entity |
| Authority Record | Not required for valid allowlisted Development root action | EMM/authority resolver | policy path or normal Authority Record path |
| ETP | Not resolved in source | Authorization Kernel/PROC-0004 | one compatible active profile |
| Baseline | source binds current baseline and protected tags | EOS/repository qualification | exact digest match |
| Execution agent | not selected | Zeus capability qualification | one qualified agent |
| Lifecycle | `Draft` | Governance/Zeus lifecycle owner | no transition in this corrective |

Any missing, duplicate, stale, incompatible, or digest-mismatched input fails
closed. This matrix is not an authority record.
