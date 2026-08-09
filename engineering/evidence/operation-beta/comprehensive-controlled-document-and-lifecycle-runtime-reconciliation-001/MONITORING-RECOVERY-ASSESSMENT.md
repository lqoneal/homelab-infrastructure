# Monitoring and Recovery Assessment

Monitoring is a read-only observation layer over provider/session/runtime state. Recovery modules and reconciliation receipts exist, but no complete proof covers process death, SSH loss, provider death, workstation restart, partial gate completion, repository mutation versus receipt ordering, EOS lag, or interrupted publication/closeout.

Recommended model: one immutable execution identity, explicit checkpoint and supersession receipts, and a single recovery boundary that refuses resume when binding, repository, evidence, or EOS state is ambiguous. This is `RECOMMENDED_ONLY`; no process or mission state was mutated.

