# Generator Compatibility Model

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

A generator consumes an explicit input manifest: entity revisions, EMM schema versions, generator version, template/projection contract, and compatibility range. It produces an output digest, provenance block, qualification status, and synchronization state.

| Condition | Generator behavior |
|---|---|
| Supported source version | deterministically generate and attest inputs/output |
| Supported older version | use qualified adapter and label source version |
| Unsupported version | refuse generation; emit compatibility discrepancy |
| Mixed inputs | permit only when the projection contract declares a compatible version set |
| Rebuild | regenerate only from recorded input manifest, not mutable “current” state |

Generated artifacts cannot become authoritative through generation. Generator upgrade qualification compares stable test manifests and requires intentional approval of any changed output; a changed output is evidence of changed inputs, contract, or generator behavior.
