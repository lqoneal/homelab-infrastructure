# Publication Decision Integration

Publication readiness consumes only `active_blockers` whose lifecycle is `VERIFIED` or `ACTIVE` and whose `publication_blocking` flag is true. The current result is `NOT_QUALIFIED` / `PUBLICATION_BLOCKED`. Resolved and retired objects remain visible but cannot block publication.
