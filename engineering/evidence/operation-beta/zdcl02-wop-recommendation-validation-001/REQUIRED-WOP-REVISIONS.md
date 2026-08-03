# Required WOP Revisions

The following revisions are required before any admission review can return
`Approved`:

1. Correct the revision identity. Make filename, frontmatter `version`, body
   `Revision`, revision history, and any digest agree. Do not call a 1.2 body
   v2.0.
2. Declare the governing domain and authority model explicitly. If this is
   Beta/Development, reference its current authority; if Operational Alpha,
   bind SPEC-0014 exactly. Do not generalize SPEC-0014 by implication.
3. Pin repository identity and qualified baseline to immutable locators and
   record the source digest.
4. Resolve and record the ETP identity/revision, selection authority,
   components, compatibility result, and frozen manifest locator. A pending
   placeholder is not an admission value.
5. Identify the exact EMM entity and resolution-receipt producer. Keep the
   receipt derived and do not make the WOP an authority source.
6. Add a field-level mapping for mission, WOP, authority, ETP, execution
   interface, provider, receipt, EOS, EENS, and runtime metadata. For every
   proposed extension state owner, producer, consumer, and compatibility
   strategy.
7. Convert “provider registration” into a bounded qualification/resource
   record unless an existing authoritative registry is identified. State
   cardinality and collision behavior.
8. Define non-live plan and receipt schemas by reference to existing owners;
   include stale, replay, forged, missing-provider, and ambiguous-selection
   failure behavior.
9. State exact test fixtures and acceptance evidence for provider neutrality,
   deterministic selection, read-only behavior, and no lifecycle advancement.
10. Re-run controlled-document validation and Zeus admission dry-run against
    the corrected source, then attach the outputs and exact digests.

Until all ten revisions are complete, disposition remains `Requires Revision`
and no implementation WOP admission is recommended.
