# Idempotency and Replay Report

Valid predecessor and successor resolution return the same terminal successor
on replay. The admission and execution stores are byte-identical before and
after read-only digest qualification. No duplicate lifecycle object or receipt
is created.
