# Operator Capability Summary

The Zeus controller interface now has one operator workflow:

```text
zeus mission roadmap
zeus mission roadmap --verify
zeus mission roadmap --json
zeus mission readiness OA-11
zeus mission readiness OA-11 --verify
zeus mission blockers OA-11
zeus capability list
zeus capability list --json
zeus capability verify
zeus dispatch status
zeus dispatch verify
zeus orchestrate status
zeus orchestrate verify
```

Default output is for operators. Verification and structured output are
explicit automation interfaces. All views consume the existing authoritative
state and remain read-only.
