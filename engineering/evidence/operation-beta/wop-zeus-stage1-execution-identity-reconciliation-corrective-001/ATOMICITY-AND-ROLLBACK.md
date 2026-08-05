# Atomicity and Rollback

Admission, execution, and reconciliation receipt writes use a transaction-scoped advisory lock, fsynced temporary files, backup replacement, and rollback on any installation error. Disposable failure injection after an intermediate replacement restored both original files byte-for-byte.
