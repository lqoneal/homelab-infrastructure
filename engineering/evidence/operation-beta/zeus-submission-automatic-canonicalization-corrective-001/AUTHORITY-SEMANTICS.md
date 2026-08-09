# Authority Semantics

The live receipt reports:

```text
governance_authority=operator-submitted WOP
wop_authority=operator-submitted WOP
generic_second_approval_required=NO
approval_state=NOT_REQUIRED_UNLESS_DECLARED_IN_WOP
explicit_wop_approvals=[]
```

No legacy `required_approvals` record was created. The existing WOP admission validator and authority-convergence tests remain in place, so an approval gate declared inside a WOP remains enforceable.

