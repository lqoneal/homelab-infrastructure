# Invalid Dispatch Evidence Preservation

The invalid dispatch is copied into append-only transaction evidence with its canonical digest, failure reason, and recovery receipt. It is not repaired or treated as authoritative. Repeated reconciliation detects the same digest and does not append a duplicate.
