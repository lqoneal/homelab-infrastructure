# ZEUS OA-16 Execution-Start Architecture

OA-16 establishes the execution-start boundary used by the supervised Zeus
runtime. `MissionExecutionRuntime.start` derives one execution identity from
the admission and WOP digest, writes the execution state and chained evidence
atomically, and only then permits continuation. A repeated start resolves the
same durable record and cannot create a second start effect.

The existing EENS EventStore is the lifecycle notification authority. The
`EXECUTION_CREATED` evidence payload binds execution, mission, WOP,
repository, operator, and timestamp. EENS persistence uses a unique
idempotency key and an append-only SQLite journal. Restart recovery records a
recovery action and resumes from the durable execution state; it does not
re-emit the execution-start notification.

Zeus controllers remain projections. Recommendation data is resolved by the
Mission Knowledge Model and bound through the Capability Registry, roadmap,
EMM, and controlled objective documentation. No controller creates authority,
advances lifecycle, or implements OA-17.
