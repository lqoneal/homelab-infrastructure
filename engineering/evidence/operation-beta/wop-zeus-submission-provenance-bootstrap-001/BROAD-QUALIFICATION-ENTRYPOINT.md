# Broad Qualification Entrypoint

Original entrypoint: `for test in scripts/tests/test-*.py; do python3 "$test"; done`.
It is non-deterministic because stateful tests share runtime state and some can
stall without a completion status. Reproduction used one isolated subprocess
per test with a bounded timeout. Candidate: `80c8e1c`. Baseline:
`64394a57015fbab2f6f7b928dfbdc20fba027bc5`.
