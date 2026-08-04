# Lint and Validation Report

`wop lint` and `wop validate` now consume `validate_source` and report all missing canonical fields before submission. Invalid approval state, missing references, missing execution-package authority fields, and missing sections fail closed without package or runtime mutation. Complete generated Markdown and DOCX sources passed both commands in disposable qualification.
