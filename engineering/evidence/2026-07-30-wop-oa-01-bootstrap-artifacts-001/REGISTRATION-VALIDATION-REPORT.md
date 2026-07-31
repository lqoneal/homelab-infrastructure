# OA-01 Bootstrap Artifact Registration Validation Report

## Result

PASS. `WOP-OA-01-ROOT-ADMISSION-001@1` and
`OA-01-BOOTSTRAP-GATE-ACTIONS@1` are each represented by one authoritative
EMM entity with an exact SHA-256 source digest.

| Artifact | EMM entity | Source digest |
| --- | --- | --- |
| Root WOP | `ImplementationWOP/WOP-OA-01-ROOT-ADMISSION-001@1` | `860be1c4c098502c9eb633bde7b8c839b10d310fcac041585bf008033cc52920` |
| Bootstrap actions | `BootstrapGateActionSpecification/OA-01-BOOTSTRAP-GATE-ACTIONS@1` | `af94ccb15296cd84c9a7dcdb208ec116e8776f0faa4582148ff5a5d87554e5c6` |

The root WOP declares the active
`MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY@1.0`, a complete submission
attestation, and an explicit allowlist. It is `READY`; no WOP lifecycle
transition was performed.

## Validation evidence

`scripts/zeus execution bootstrap-actions WOP-OA-01-ROOT-ADMISSION-001 --revision 1 --correlation-id WOP-OA-01-BOOTSTRAP-ARTIFACTS-001`
returned `outcome: RESOLVED`, `authority_mode: MANUAL_GOVERNANCE_WOP`, and
`lifecycle_effect: NONE`.
