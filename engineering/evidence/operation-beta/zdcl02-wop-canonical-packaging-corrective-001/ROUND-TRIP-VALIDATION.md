# Round-Trip Validation

An isolated run performed:

```text
source WOP → canonical package → reconstructed Markdown metadata
```

Observed:

- package identity: `ebeec97412e405e26b721c09`;
- source/package source digest: `6567d9eaac47bea91b0346731cc3bac91566ccfa52cb4e2e6d86f3da61ef5334`;
- source/package/reconstructed scope count: `30 / 30 / 30`;
- source/package/reconstructed completion count: `8 / 8 / 8`;
- reconstructed required metadata: exact equality;
- repeated packaging: same package identity and source digest;
- source preservation: exact byte/digest match.

The complete non-schema sections remain lossless through preserved
`source-wop.md`. Result: **PASS**.
