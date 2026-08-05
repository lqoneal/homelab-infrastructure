# engctl Provider Service Contract

`engctl codex --wop ID --context-file PATH --timeout N -- ARGS` is the internal
service contract. PATH must contain schema-versioned JSON with a context digest.
The service exports the exact envelope to the child and retains legacy prose
only when called without a Zeus context file.
