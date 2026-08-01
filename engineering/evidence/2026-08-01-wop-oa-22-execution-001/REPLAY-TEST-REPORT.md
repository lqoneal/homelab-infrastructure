# Replay Test Report

Result: **PASS**.

Identical durable receipt replay is idempotent. A request or receipt whose
content no longer matches its canonical digest is rejected as divergent replay.
