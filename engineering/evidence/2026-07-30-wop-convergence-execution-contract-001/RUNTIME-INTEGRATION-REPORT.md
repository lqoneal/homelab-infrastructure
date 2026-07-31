# Runtime Integration Report

## Changes

- Added the authoritative Operational Alpha execution-contract artifact and EMM identity with source digest.
- Revised SPEC-0014 to state the controlled plan source, lifecycle, and fail-closed rules.
- Updated the execution interface to expose the contract to runtime consumers.
- Added `ConvergenceRuntime.execution_contract`, `operational_gate_plan`, and `operational_execution_context`.
- Updated Zeus operational dispatch to request the derived handler context rather than pass an incomplete convergence envelope.

## Runtime behavior

When a resolved authority flow reaches dispatch, Zeus asks the Metadata Engine facade for the exact plan bound to the resolved Implementation WOP. The facade verifies contract identity, EMM entity uniqueness, source digest, baseline, WOP identity/revision, lifecycle, and handler payload. Only then can it construct the immutable handler context.

The current OA-01 records do not meet this last prerequisite because no plan entity exists. The runtime returns a pre-dispatch error; it does not translate a legacy authority object, synthesize a plan, or invoke a handler.
