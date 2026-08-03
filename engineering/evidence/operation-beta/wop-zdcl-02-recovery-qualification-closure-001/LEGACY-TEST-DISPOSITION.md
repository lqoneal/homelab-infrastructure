# Legacy Test Disposition

| Area | Disposition | Reason |
|---|---|---|
| Beta controller temporary fixtures | Reconciled | Removed hard-coded user directory; use platform temporary directory. |
| Controlled-document temporary fixtures | Reconciled | Removed hard-coded user directory. |
| CLI location portability | Reconciled | Uses resolver-selected isolated runtime and repository-derived locations. |
| OA-02 controlled-authority matrix | Out of scope | Separate Progressive OA authority contract; requires configured upstream publication and is not a `zeus resume` dependency. |

No recovery-focused test remains unresolved.
