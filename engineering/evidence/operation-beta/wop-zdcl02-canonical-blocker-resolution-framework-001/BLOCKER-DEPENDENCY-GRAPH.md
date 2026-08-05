# Blocker Dependency Graph

```text
authoritative evidence -> blocker verification -> ACTIVE blocker set
ACTIVE blocker set -> qualification/publication decision -> next authorized action
evidence change -> automatic reevaluation -> RESOLVED/RETIRED or ACTIVE
```

The current graph has nodes `QUAL-001` and `QUAL-002` and no inter-blocker edges. Duplicate IDs with identical digests merge; conflicting duplicate IDs fail closed.
