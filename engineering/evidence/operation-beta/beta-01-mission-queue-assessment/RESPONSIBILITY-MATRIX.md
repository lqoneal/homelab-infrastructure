# BETA-01 Responsibility and Ownership Matrix

| Concern | EMP | Zeus | ZDCL | CAGF | EOS | EENS |
| --- | --- | --- | --- | --- | --- | --- |
| submit/stage | owner | validates projection | consumes context | derives views | records synchronized state | emits events |
| prioritize/schedule policy | owner | enforces input | bounded execution | derives metrics | state source | emits events |
| eligibility/selection | supplies policy | owner | session control | derives projections | state source | emits events |
| admission/execution | requests | enforcement/orchestration | bounded session control | no authority | baseline/state | events |
| lifecycle/history | portfolio record | qualification/closeout | recovery/session record | projection only | synchronized state | notification |

No component may create a competing mission identity, lifecycle, queue, or
admission authority. Ambiguous or conflicting state fails closed.
