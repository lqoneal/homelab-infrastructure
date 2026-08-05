# Test Harness Defect Report

The serial shell loop has no per-test timeout, shares mutable runtime state,
and can stall without a definitive status. Some fixtures assume write access
under the repository, which this session does not provide. Isolated bounded
subprocesses were used for reproduction without weakening assertions.
