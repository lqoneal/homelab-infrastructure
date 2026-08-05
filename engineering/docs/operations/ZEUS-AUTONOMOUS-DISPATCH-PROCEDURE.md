# Zeus Autonomous Dispatch Procedure

The operator workflow ends at `zeus submit <authorized-wop>` unless governance explicitly requires approval. Runtime reconciliation invokes the autonomous dispatch controller after a valid dispatch receipt. The controller validates provider, authority, package, source, transaction, and dispatch bindings; persists launch intent; invokes the qualified adapter; verifies acknowledgment and session identity; and continues execution.

No operator may manually create launch acknowledgments, session records, or provider processes. Missing adapters and ambiguous or conflicting state remain blocked with a diagnostic and next action. Prepublication qualification uses disposable adapters only; no live provider is launched from the candidate branch.
