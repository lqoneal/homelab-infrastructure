# Generation Suitability Matrix

| Artifact family | Future method | Suitability | Boundary |
| --- | --- | --- | --- |
| PMCT/gate projections | Deterministic projection | High | Source semantics remain PMCT/gate authority |
| Roadmap/readiness/blockers/prerequisites | Deterministic projection | High | MKM and Capability Registry remain sources |
| Controller machine views | Deterministic projection | High | Presentation cannot add authority |
| Operational metadata/manifests | Deterministic projection | High | Bind source digests and generator version |
| Capability identity/state | Manual canonical source | None | Registry remains authoritative |
| Mission objective/lifecycle | Manual canonical source | None | MKM remains authoritative |
| EMM bindings | Manual/canonical source | Low | CAGF may validate, not repair |
| EOS runtime state | Runtime projection | None | EOS remains derived from repository authority |
| Governance approvals/publication | Signed controlled record | None | Never generated as authorization |
| Standards/procedures | Controlled manual source | Medium | Generate indexes/consistency reports only |
| Historical evidence | Immutable manual record | None | Generate indexes only |
| Recommendations | Structured future object | Medium/high | Requires owner, disposition, and verification |
