# Provider Launch Contract

Provider selection and dispatch receipts are immutable bindings, not authority sources. Launch acknowledgment must be receipt-backed before `EXECUTING`; an absent or malformed acknowledgment leaves the transaction resumable and does not create a duplicate dispatch.
