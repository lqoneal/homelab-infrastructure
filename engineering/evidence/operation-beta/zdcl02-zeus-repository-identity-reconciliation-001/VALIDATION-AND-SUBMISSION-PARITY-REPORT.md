# Validation and Submission Parity Report

`validate_source(..., repository_root=ROOT)`, packaging, package inspection,
and Stage 1 submission all call the same resolver. Focused tests prove alias,
remote, ID, fingerprint, canonical-path, unknown-alias, and foreign-path
behavior. No submission of the staged ZDCL-02 source was performed.
