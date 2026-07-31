# End-to-End Information Flow Model

Status: `PROPOSED INTEGRATION — NON-AUTHORITATIVE`

```text
Decision → Authority → Mission/Contract → Snapshot → WOP → Admission → Initiation → Dispatch
  → Attempt → Event → Evidence → Qualification → Acceptance ─┐
                                                              ├→ Closeout → Archive
Source facts → versioned EMM → derived docs / state / health ─┘
                                  ↓
                         drift → reconciliation → rebuilt target
```

Every arrow is an immutable reference or a directional synchronization. Information is created by its named owner, validated/qualified before applicable publication, version-negotiated by consumers, and archived with lineage. Derived documents and runtime views are regenerated from manifests; they are not information sources for upstream decisions.
