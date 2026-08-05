# Platform Validation Report

Stage 1 direct-submission code and controlled-document validation passed. The
shared repository classifier reports the candidate as `EOS_STALE`: the active
EOS projection represents an earlier candidate rather than published
`64394a5`. No EOS synchronization is authorized by this WOP.

The focused lifecycle suites, Registry, controlled-document validation, and
diff checks pass. A final aggregate platform invocation was terminated by the
execution environment after its Stage 1 banner and returned no completion code;
therefore no aggregate platform PASS is claimed. A prior completed run of the
same validator implementation reported the expected three fail-closed
synchronization failures: Stage 2 stale EOS plus dependent Stage 4 operational
state and persistence checks.

No provider, live runtime, published mission, or EOS state was modified.
