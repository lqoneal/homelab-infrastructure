# Synchronization Architecture Model

Status: `PROPOSED — NON-AUTHORITATIVE`

| Relationship | Authoritative owner | Direction / trigger | Verification | Reconciliation owner |
|---|---|---|---|---|
| Governance → Authority Record | Governance | decision → record; issue/revoke | signature, scope, lineage | Governance |
| Authority/Contract → EMP and Zeus | Governance / EMP | source → evaluation; revision/freshness | digest, applicability | source owner |
| Work Registry/Project State → EMP | respective fact owner | source → planning; owner revision | schema/revision/identity | respective owner |
| EMP → Zeus | EMP | snapshot → selection; sealed snapshot | snapshot digest/policy | EMP for planning fact |
| WOP → Zeus admission | WOP publisher | package → receipt; publish/qualify | immutable digest/type | WOP publisher |
| Zeus → EENS | Zeus for decision facts; EENS for event storage | event → durable stream; append | sequence/digest/checkpoint | EENS for event store |
| Zeus/EENS → EOS | source owners | source → projection; separately authorized checkpoint | source revision/directional audit | source owner; EOS replays projection |
| source systems → Controlled Documentation | declared owners | metadata → generated docs; source revision | manifest/schema/graph validation | source owner then generator |
| qualification records → Gate Catalog/dashboards | qualifier | historical record → derived status | receipt digest/applicability | qualifier for record; generator rebuilds view |
| Gate Catalog metadata → Capability Matrix | roadmap/capability owner | metadata → generated matrix | IDs, coverage, source manifest | metadata owner |
| EOS/EENS → Zeus health view | EOS/EENS | runtime state → read-only health projection | freshness/drift/reason code | EOS/EENS respectively |

EENS records synchronization failures as events; EOS records projection state;
Zeus exposes blockers through the public interface; independent qualification
evaluates the applicable evidence. These are complementary responsibilities,
not competing owners of the synchronized fact.
