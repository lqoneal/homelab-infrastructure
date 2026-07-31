# Engineering Owner Directory Model

Status: `PROPOSED LOGICAL EXECUTION CONTRACT — NON-AUTHORITATIVE`

The Owner Directory is the canonical registry for resolvable owner references. It records roles/subsystems, not ownership of their facts. Each entry has immutable `owner_ref`, type, status, permitted stewardship/publication/verification/synchronization/lifecycle responsibilities, successor reference, and directory revision.

| Assignment | Rule |
|---|---|
| Authoritative owner | every authoritative entity and relationship references exactly one active `owner_ref` |
| Steward | maintains schema/lineage correctness for its assigned fact; may equal owner but is explicit |
| Synchronizer | executes delivery/rebuild for a target; never becomes source owner by doing so |
| Publisher | may publish on behalf of the owner only through an immutable delegated publication binding |
| Verifier/qualifier | evaluates evidence; never becomes owner of the assessed fact |
| Lifecycle owner | owns the entity’s transition record only where the entity contract names it |
| Delegation/transfer | an immutable, time/version-scoped binding names delegator, delegate, scope, and successor/revocation; no implicit transfer |

Resolution validates that the owner exists, is active for the requested revision, is permitted for its declared responsibility, and has no conflicting authoritative assignment. Unknown, inactive, duplicate, or ambiguous assignments fail validation and block publication/adoption.
