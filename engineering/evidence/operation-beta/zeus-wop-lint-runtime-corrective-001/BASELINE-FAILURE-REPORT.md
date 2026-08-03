# Baseline Failure Report

**Work Order:** WOP-ZEUS-WOP-LINT-RUNTIME-CORRECTIVE-001  
**Classification:** Controlled evidence  
**Authority:** Published Operational Alpha authority chain; no session WOP provenance marker  
**Repository:** homelab

Before correction, `scripts/zeus wop lint <source>` terminated with
`UnboundLocalError` because source validation did not assign its parsed metadata
to the lint branch. The staged ZDCL-02 v2.1 source was unchanged (SHA-256
`6567d9eaac47bea91b0346731cc3bac91566ccfa52cb4e2e6d86f3da61ef5334`).
