# OA-22 Authority Management Recommendations

1. Require every mission capability prerequisite and outcome to resolve to a
   Capability Registry entity before publication.
2. Make PMCT and executable gates consume the same objective and capability
   bindings as the MKM; reject stale titles during validation.
3. Require EMM to validate entity existence and digest bindings, not only
   source-file presence.
4. Add a cross-source qualification that fails when a capability ID appears in
   MKM but not in the Capability Registry.
5. Keep controllers read-only and report the exact unresolved authority field.

These are documentation and validation recommendations only. No engineering
platform implementation is introduced.
