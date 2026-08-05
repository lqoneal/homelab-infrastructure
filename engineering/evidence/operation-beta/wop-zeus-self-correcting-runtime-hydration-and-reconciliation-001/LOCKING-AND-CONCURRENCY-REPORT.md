# Locking and Concurrency Report

An exclusive `reconciliation-locks/<transaction>.lock` serializes reconciliation attempts. The lock is always released and no operator-visible workflow step was introduced.
