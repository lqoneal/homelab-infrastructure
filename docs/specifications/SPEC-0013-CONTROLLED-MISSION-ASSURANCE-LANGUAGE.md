---
document_id: SPEC-0013
title: Controlled Mission Assurance Language
version: 1.0
status: Draft
owner: EOS Program
created: 2026-07-28
last_updated: 2026-07-28
classification: Engineering Specification
predecessor_revision: null
successor_revision: null
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: GH-ZEUS-ASSURANCE-003
approval_date: null
persistence_status: Pending
source_of_truth: true
declared_deferrals:
  - Controlled publication and activation require a separate operator decision.
relationships:
  - type: governed_by
    target: EOS-0001
  - type: depends_on
    target: SPEC-0004
  - type: depends_on
    target: SPEC-0005
  - type: related_to
    target: PROC-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - assurance
  - language
  - deterministic
  - read-only
assurance_language:
  language_id: CONTROLLED-MISSION-ASSURANCE-LANGUAGE
  language_version: '1.0'
  phases:
    - preflight
    - execution
    - synchronization
    - closeout
  declaration:
    required_fields:
      - id
      - language_version
      - phase
      - description
      - assertion
    optional_fields:
      - applicability
    id_pattern: '^MA-[A-Z0-9]+(?:-[A-Z0-9]+)*$'
  expression:
    compound_operators:
      all:
        implementation: all
        minimum_children: 1
      any:
        implementation: any
        minimum_children: 1
    assertion_fields:
      - selector
      - operator
      - value
      - value_selector
      - exclude
  selector:
    separator: '.'
    segment_pattern: '^[a-z_][a-z0-9_]*$'
    allowed_roots:
      - discovery
      - mission_id
      - root
      - state
    traversal: mapping_keys_only
    unresolved: error
  operators:
    equals:
      implementation: strict_equals
      required_fields:
        - value
      optional_fields: []
    equals_selector:
      implementation: strict_equals_selector
      required_fields:
        - value_selector
      optional_fields: []
    not_equals:
      implementation: strict_not_equals
      required_fields:
        - value
      optional_fields: []
    empty:
      implementation: empty
      required_fields: []
      optional_fields: []
    not_empty:
      implementation: not_empty
      required_fields: []
      optional_fields: []
    one_of:
      implementation: one_of
      required_fields:
        - value
      optional_fields: []
      value_type: list
    not_contains:
      implementation: not_contains
      required_fields:
        - value
      optional_fields: []
    path_exists:
      implementation: repository_file_exists
      required_fields: []
      optional_fields: []
    all_paths_exist:
      implementation: all_repository_files_exist
      required_fields: []
      optional_fields: []
    required_map_values_equal:
      implementation: required_map_values_equal
      required_fields:
        - value
      optional_fields:
        - exclude
      exclude_type: list_of_strings
  applicability:
    absent: applicable
    'true': applicable
    'false': not_applicable
    not_applicable_assertion_status: SATISFIED
  phase_evaluation:
    empty_applicable_requirement_set: FAIL
    unsatisfied_requirement: FAIL
    otherwise: PASS
  compatibility:
    declaration_version_must_equal_language_version: true
    unknown_fields: error
    unknown_operators: error
    unknown_selector_roots: error
---

# Controlled Mission Assurance Language

## Purpose

This specification is the single semantic authority for mission-assurance
declarations. Controlled requirement owners declare obligations in this
language. Zeus is a read-only interpreter and does not own the language,
engineering lifecycle, or source state.

This revision is a controlled-document candidate. Its approval, activation,
and publication remain separate decisions.

## Declaration structure

Each declaration is a mapping containing exactly the required fields and any
listed optional fields in `assurance_language.declaration`. `language_version`
binds the declaration to this specification revision. Identifiers are globally
unique across the controlled owners resolved by the Engineering Execution
Interface. Descriptions are non-empty strings and phases are members of the
controlled phase list.

`assertion` is required. `applicability` is optional. Both use the same
expression grammar. Unknown fields, missing fields, incompatible versions, and
duplicate identities are errors.

## Expression semantics

An expression is exactly one of:

1. a compound expression containing only `all` or only `any` and a non-empty
   list of child expressions; or
2. an assertion containing `selector`, `operator`, and exactly the fields
   permitted for that operator.

`all` evaluates every child and succeeds only when every child succeeds.
`any` evaluates every child and succeeds when at least one child succeeds.
Evaluation order is declaration order and no expression has side effects.
Mixing compound and assertion fields, using both compounds, or adding unknown
fields is invalid.

## Selector semantics

Selectors are non-empty dot-separated paths. Every segment matches the
controlled segment pattern, the first segment is an allowed root, and traversal
uses mapping keys only. Array indexing, attributes, wildcards, recursive
descent, implicit coercion, and missing-key defaults are unsupported. An
unresolved or malformed selector is an evaluation error and fails closed.

The selector context is derived exclusively from the canonical Engineering
Execution Interface:

- `root`: repository identity;
- `mission_id`: requested mission identity;
- `discovery`: Mission Contract discovery evidence;
- `state`: canonical resolved engineering execution state.

## Operator semantics

The `operators` mapping in controlled front matter is normative and selects a
named interpreter primitive:

- `equals` and `not_equals` use type-preserving equality without coercion.
- `equals_selector` compares two resolved selector values.
- `empty` and `not_empty` apply deterministic truth-value testing.
- `one_of` requires a list operand and performs type-preserving membership.
- `not_contains` uses native containment and treats an incompatible operand as
  a language error rather than a false result.
- `path_exists` requires one non-empty repository-relative file path.
- `all_paths_exist` requires a non-empty list of repository-relative file
  paths and requires every path to be a file.
- `required_map_values_equal` requires a mapping containing at least one
  non-excluded item marked `required`; each such item must have a `state`
  matching the expected value case-insensitively. `exclude`, when present, is
  a list of strings.

Repository-file operators reject absolute paths, parent traversal, and paths
that escape the repository.

## Applicability and phase evaluation

An absent applicability expression means applicable. A true applicability
expression means applicable; false means not applicable. A non-applicable
assertion is not evaluated and is reported as satisfied, but it is excluded
from its phase's applicable requirement count.

A phase passes only when at least one applicable declaration exists and all
applicable assertions are satisfied. Any validation or evaluation error fails
closed and produces no partial assurance result.

## Compatibility and revision

Language revisions are independent of Zeus releases. The execution-interface
manifest binds exactly one controlled language owner and revision. Every
declaration must name the same language version. An unavailable owner,
ambiguous owner, missing language definition, version mismatch, unsupported
interpreter primitive, or malformed definition is incompatible and fails
closed.

A compatible controlled revision may add or remove allowed phases, operators,
selector roots, or field constraints without a Zeus logic change when it uses
existing interpreter primitives. A revision requiring a new primitive requires
an interpreter implementation and compatibility review; it must never be
silently approximated.

## Ownership boundary

The Engineering Execution Interface remains the canonical operational
resolver. Requirement owners retain their controlled engineering-process
requirements. This specification defines only the declaration language. Zeus
reads resolved state, validates declarations, evaluates them deterministically,
and returns evidence; it does not mutate lifecycle state, approve gates,
synchronize records, publish documents, or acquire engineering-process
ownership.
