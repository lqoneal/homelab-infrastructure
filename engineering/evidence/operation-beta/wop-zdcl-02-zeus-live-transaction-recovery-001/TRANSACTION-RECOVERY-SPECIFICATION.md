# Transaction Recovery Specification

Recovery preserves `instance_id`, WOP identity, registration identity, package digest, source digest, and all historical receipts. It never calls submission, creates a replacement transaction, or advances a phase without its receipt. A verified dispatch is replayed as an idempotent read; an invalid dispatch is demoted to `AWAITING_EXECUTION_DISPATCH`.
