# Root Cause Analysis

`main()` initialized `metadata` only while handling a canonical package. For
Markdown and DOCX sources, `validate_source()` returned a `ValidationResult`
but the lint branch referenced the unbound local. The corrective assigns
`metadata` from that result and uses the same validation object for lint,
validation, inspection, and explanation. No duplicate parser or ruleset was
introduced.
