# Codex Session Lifecycle

One deterministic session ID is derived from execution, context digest, and
provider. Launch records `LAUNCH_REQUESTED`, process identity, then `RUNNING`.
Stop is bounded graceful termination followed by forced group termination;
recoverable stopped or interrupted state resumes the same execution lineage.
