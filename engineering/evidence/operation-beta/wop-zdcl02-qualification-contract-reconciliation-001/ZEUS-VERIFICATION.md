# Zeus Verification

The following commands resolve from the same contract:

```text
zeus qualification show --json
zeus publication show --json
zeus blockers --json
zeus readiness --json
zeus next-action --json
zeus snapshot --json
zeus verify qualification
```

For the current candidate all return the same decision digest and `NOT_QUALIFIED` / `PUBLICATION_BLOCKED` result.

