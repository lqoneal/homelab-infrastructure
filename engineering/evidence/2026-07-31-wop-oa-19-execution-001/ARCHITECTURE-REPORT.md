# OA-19 Architecture Report

CAP-018 uses the existing EENS `EventStore` as its append-only persistence
boundary. Records are immutable `EngineeringEvent` values with deterministic
event identity, unique idempotency keys, UTC timestamps, canonical payload
checksums, and SQLite WAL durability. Replays return the original sequence;
conflicting reuse fails closed. No alternate authority or OA-20 runtime was
introduced.
