# Roadmap Persistence Architecture Assessment

The baseline had many roadmap documents and WOP-local roadmaps, but no generic
repository-authoritative current-program state/result tree. `docs/roadmap.md`
was prose; Project State owned project resume facts; Work Registry owned EMP
coordination facts; EOS checkpoints were runtime evidence/projections. PROC-0001
already declared the controlled roadmap owner of identity, sequence, and
objectives, EMM the owner of source binding/digest/drift, PROC-0006 the owner of
qualification, and resume a derived non-authoritative view.

The preservation branch was inspected read-only. Its later draft PROC-0009 and
roadmap assessments reinforced planning/execution separation, stable identity,
anti-duplication, history preservation, and fail-closed behavior. They were not
copied, merged, cherry-picked, or activated.

The selected design therefore adds one program root under
`engineering/convergence/`, consistent with repository use of `engineering/`
for durable planning/evidence records. It extends the existing ownership model:

- roadmap and gate files own planning definitions;
- one `STATE.yaml` owns gate position;
- Project State binds the current project resume point;
- result/evidence files prove completed gates;
- an EMM digest manifest owns binding and drift detection; and
- engctl exposes only validated read-only projections.

The Work Registry was not repurposed into a roadmap registry and its existing
authority disagreement was not silently repaired. C05 remains responsible for
the full roadmap/Project-State/registry assessment.
