# Engineering Projection Model

Status: `PROPOSED — NON-AUTHORITATIVE`

| Kind | Meaning | Write rule | Regeneration / retention |
|---|---|---|---|
| Authoritative facts | owned engineering truth | declared owner creates successor only | retain by owner; consumers re-read revision |
| Derived views | deterministic representation | generator only; never source writer | rebuild from complete source manifest |
| Runtime views | current operational checkpoint/state | runtime owner updates attributed ledger | replay checkpoint; expire by policy |
| Historical views | sealed past fact/result/archive | sealer/archive owner only | immutable retention/lineage |

A projection stores input manifest, EMM version, generator version, generated-at time, output digest, synchronization status, and qualification status. Drift is mismatch with current eligible sources. Reconciliation is source-owner correction, source validation, rebuild, verification, then publication. No catalog, report, dashboard, or EOS projection overwrites an authoritative fact.
