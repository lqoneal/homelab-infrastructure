# Replay Evidence

First exact live invocation returned:

```text
submission_id=SUBMISSION-a2c024ce-077a-5d70-bb1d-067e056e5a23
admission_request_id=ADMISSION-REQUEST-4b9473ec-4a03-5d09-93c6-557f86ff71ad
submission_digest=9f2b0408e0ee770207a5385769cd0fe69452b787e3f60cd4c47edd2e96b60350
submission_state=ADMISSION_REQUESTED
submission_result=PASS
duplicate_submission=NEW
```

The exact same command returned `duplicate_submission=IDEMPOTENT`, the same submission and admission-request identities, and the same receipt digest. The runtime contains one receipt and one request only.

