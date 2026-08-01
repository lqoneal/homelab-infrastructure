# Runtime Ownership Matrix

| Runtime concern | Owner | Projection consumers | Mutation rule |
| --- | --- | --- | --- |
| Submission | EMP/Zeus submission authority | queue, admission | append-only/idempotent |
| Admission | Zeus admission authority | execution, controllers | immutable decision; supersession |
| Execution | Zeus / qualified agent | status, qualification | lifecycle-controlled |
| Evidence/history | evidence authority | history/archive/audit | immutable |
| EOS state | EOS | platform validation | synchronized authoritative state |
| Presentation | canonical resolver | human/JSON controllers | read-only |
