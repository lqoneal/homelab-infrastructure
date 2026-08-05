# Session Lifecycle Contract

Native sessions are derived from the canonical execution identity and provider launch acknowledgment. Session creation is idempotent and identity-bound. A session failure rolls back or records a resumable checkpoint; no session may substitute for Stage 1 authority.
