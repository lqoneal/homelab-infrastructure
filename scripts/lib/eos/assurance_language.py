#!/usr/bin/env python3
"""Deterministic interpreter for a controlled mission-assurance language."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


class AssuranceLanguageError(ValueError):
    """A language definition, declaration, or expression is not safe to use."""


class AssuranceLanguage:
    """Validate and evaluate declarations using one resolved controlled definition."""

    IMPLEMENTATIONS = {
        "strict_equals",
        "strict_equals_selector",
        "strict_not_equals",
        "empty",
        "not_empty",
        "one_of",
        "not_contains",
        "repository_file_exists",
        "all_repository_files_exist",
        "required_map_values_equal",
    }

    def __init__(self, root: Path | str, definition: Mapping[str, Any]):
        self.root = Path(root).resolve()
        self.definition = definition
        self._validate_definition()

    @property
    def language_id(self) -> str:
        return str(self.definition["language_id"])

    @property
    def version(self) -> str:
        return str(self.definition["language_version"])

    @property
    def phases(self) -> tuple[str, ...]:
        return tuple(self.definition["phases"])

    def _mapping(self, value: Any, label: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise AssuranceLanguageError(f"{label} must be a mapping")
        return value

    def _string_list(self, value: Any, label: str, *, nonempty: bool = False) -> list[str]:
        if not isinstance(value, list) or (nonempty and not value) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise AssuranceLanguageError(f"{label} must be a list of strings")
        if len(value) != len(set(value)):
            raise AssuranceLanguageError(f"{label} contains duplicates")
        return value

    def _validate_definition(self) -> None:
        definition = self._mapping(self.definition, "assurance language definition")
        required = {
            "language_id", "language_version", "phases", "declaration", "expression",
            "selector", "operators", "applicability", "phase_evaluation",
            "compatibility", "authoritative_source",
        }
        if set(definition) != required:
            raise AssuranceLanguageError(
                "assurance language definition fields are incompatible"
            )
        if not all(
            isinstance(definition[key], str) and definition[key]
            for key in ("language_id", "language_version")
        ):
            raise AssuranceLanguageError("assurance language identity is invalid")
        self._string_list(definition["phases"], "assurance phases", nonempty=True)
        declaration = self._mapping(definition["declaration"], "declaration schema")
        if set(declaration) != {"required_fields", "optional_fields", "id_pattern"}:
            raise AssuranceLanguageError("declaration schema fields are incompatible")
        required_fields = self._string_list(
            declaration["required_fields"], "declaration required_fields", nonempty=True
        )
        optional_fields = self._string_list(
            declaration["optional_fields"], "declaration optional_fields"
        )
        if set(required_fields) & set(optional_fields):
            raise AssuranceLanguageError("declaration fields overlap")
        try:
            re.compile(str(declaration["id_pattern"]))
        except re.error as error:
            raise AssuranceLanguageError("declaration id_pattern is invalid") from error

        expression = self._mapping(definition["expression"], "expression schema")
        if set(expression) != {"compound_operators", "assertion_fields"}:
            raise AssuranceLanguageError("expression schema fields are incompatible")
        compounds = self._mapping(
            expression["compound_operators"], "compound operator definitions"
        )
        if not compounds:
            raise AssuranceLanguageError("compound operator definitions are empty")
        for name, raw in compounds.items():
            item = self._mapping(raw, f"compound operator {name}")
            if set(item) != {"implementation", "minimum_children"}:
                raise AssuranceLanguageError(f"compound operator {name} is malformed")
            if item["implementation"] not in {"all", "any"}:
                raise AssuranceLanguageError(
                    f"unsupported compound implementation: {item['implementation']}"
                )
            if not isinstance(item["minimum_children"], int) or item["minimum_children"] < 1:
                raise AssuranceLanguageError(
                    f"compound operator {name} minimum_children is invalid"
                )
        assertion_fields = self._string_list(
            expression["assertion_fields"], "assertion_fields", nonempty=True
        )
        if not {"selector", "operator"} <= set(assertion_fields):
            raise AssuranceLanguageError("assertion_fields lacks selector or operator")

        selector = self._mapping(definition["selector"], "selector definition")
        if set(selector) != {
            "separator", "segment_pattern", "allowed_roots", "traversal", "unresolved"
        }:
            raise AssuranceLanguageError("selector definition fields are incompatible")
        if selector["separator"] != "." or selector["traversal"] != "mapping_keys_only":
            raise AssuranceLanguageError("unsupported selector semantics")
        if selector["unresolved"] != "error":
            raise AssuranceLanguageError("selector resolution must fail closed")
        self._string_list(selector["allowed_roots"], "selector roots", nonempty=True)
        try:
            re.compile(str(selector["segment_pattern"]))
        except re.error as error:
            raise AssuranceLanguageError("selector segment_pattern is invalid") from error

        operators = self._mapping(definition["operators"], "operator definitions")
        if not operators:
            raise AssuranceLanguageError("operator definitions are empty")
        for name, raw in operators.items():
            item = self._mapping(raw, f"operator {name}")
            permitted = {
                "implementation", "required_fields", "optional_fields",
                "value_type", "exclude_type",
            }
            if not {"implementation", "required_fields", "optional_fields"} <= set(item):
                raise AssuranceLanguageError(f"operator {name} schema is incomplete")
            if not set(item) <= permitted:
                raise AssuranceLanguageError(f"operator {name} schema has unknown fields")
            if item["implementation"] not in self.IMPLEMENTATIONS:
                raise AssuranceLanguageError(
                    f"unsupported interpreter primitive: {item['implementation']}"
                )
            required_operator_fields = self._string_list(
                item["required_fields"], f"operator {name} required_fields"
            )
            optional_operator_fields = self._string_list(
                item["optional_fields"], f"operator {name} optional_fields"
            )
            if set(required_operator_fields) & set(optional_operator_fields):
                raise AssuranceLanguageError(f"operator {name} fields overlap")
            if not set(required_operator_fields + optional_operator_fields) <= set(
                assertion_fields
            ):
                raise AssuranceLanguageError(
                    f"operator {name} uses undeclared assertion fields"
                )
            if item.get("value_type") not in {None, "list"}:
                raise AssuranceLanguageError(f"operator {name} value_type is unsupported")
            if item.get("exclude_type") not in {None, "list_of_strings"}:
                raise AssuranceLanguageError(
                    f"operator {name} exclude_type is unsupported"
                )

        applicability = self._mapping(
            definition["applicability"], "applicability semantics"
        )
        if applicability != {
            "absent": "applicable",
            "true": "applicable",
            "false": "not_applicable",
            "not_applicable_assertion_status": "SATISFIED",
        }:
            raise AssuranceLanguageError("unsupported applicability semantics")
        phase = self._mapping(definition["phase_evaluation"], "phase semantics")
        if phase != {
            "empty_applicable_requirement_set": "FAIL",
            "unsatisfied_requirement": "FAIL",
            "otherwise": "PASS",
        }:
            raise AssuranceLanguageError("unsupported phase evaluation semantics")
        compatibility = self._mapping(
            definition["compatibility"], "compatibility rules"
        )
        if compatibility != {
            "declaration_version_must_equal_language_version": True,
            "unknown_fields": "error",
            "unknown_operators": "error",
            "unknown_selector_roots": "error",
        }:
            raise AssuranceLanguageError("compatibility rules must fail closed")

    def validate_declaration(self, declaration: Any) -> None:
        item = self._mapping(declaration, "assurance declaration")
        schema = self.definition["declaration"]
        required, optional = set(schema["required_fields"]), set(schema["optional_fields"])
        missing, unknown = sorted(required - set(item)), sorted(set(item) - required - optional)
        if missing:
            raise AssuranceLanguageError(f"assurance declaration is missing {missing}")
        if unknown:
            raise AssuranceLanguageError(f"assurance declaration has unknown fields {unknown}")
        if str(item["language_version"]) != self.version:
            raise AssuranceLanguageError(
                f"assurance language version incompatible: declaration "
                f"{item['language_version']}, interpreter {self.version}"
            )
        if not isinstance(item["id"], str) or not re.fullmatch(
            str(schema["id_pattern"]), item["id"]
        ):
            raise AssuranceLanguageError("assurance declaration id is invalid")
        if item["phase"] not in self.phases:
            raise AssuranceLanguageError(
                f"assurance declaration {item['id']} has invalid phase"
            )
        if not isinstance(item["description"], str) or not item["description"].strip():
            raise AssuranceLanguageError(
                f"assurance declaration {item['id']} has invalid description"
            )
        self.validate_expression(item["assertion"])
        if "applicability" in item:
            self.validate_expression(item["applicability"])

    def validate_expression(self, expression: Any) -> None:
        clause = self._mapping(expression, "assurance expression")
        compounds = self.definition["expression"]["compound_operators"]
        present = [name for name in compounds if name in clause]
        if present:
            if len(present) != 1 or set(clause) != {present[0]}:
                raise AssuranceLanguageError("ambiguous compound assurance expression")
            name = present[0]
            children = clause[name]
            minimum = compounds[name]["minimum_children"]
            if not isinstance(children, list) or len(children) < minimum:
                raise AssuranceLanguageError(
                    f"assurance {name} expression requires {minimum} children"
                )
            for child in children:
                self.validate_expression(child)
            return
        if "selector" not in clause or "operator" not in clause:
            raise AssuranceLanguageError("assurance assertion lacks selector or operator")
        operator = clause["operator"]
        operators = self.definition["operators"]
        if not isinstance(operator, str) or operator not in operators:
            raise AssuranceLanguageError(f"unsupported assurance operator: {operator}")
        operator_schema = operators[operator]
        permitted = {
            "selector", "operator", *operator_schema["required_fields"],
            *operator_schema["optional_fields"],
        }
        missing = sorted(set(operator_schema["required_fields"]) - set(clause))
        unknown = sorted(set(clause) - permitted)
        if missing:
            raise AssuranceLanguageError(
                f"assurance operator {operator} is missing {missing}"
            )
        if unknown:
            raise AssuranceLanguageError(
                f"assurance operator {operator} has unknown fields {unknown}"
            )
        self._validate_selector(clause["selector"])
        if "value_selector" in clause:
            self._validate_selector(clause["value_selector"])
        if operator_schema.get("value_type") == "list" and not isinstance(
            clause.get("value"), list
        ):
            raise AssuranceLanguageError(f"assurance operator {operator} requires list value")
        if operator_schema.get("exclude_type") == "list_of_strings":
            self._string_list(clause.get("exclude", []), f"operator {operator} exclude")

    def _validate_selector(self, selector: Any) -> None:
        spec = self.definition["selector"]
        if not isinstance(selector, str) or not selector:
            raise AssuranceLanguageError("assurance selector is invalid")
        segments = selector.split(spec["separator"])
        pattern = re.compile(spec["segment_pattern"])
        if (
            any(not pattern.fullmatch(segment) for segment in segments)
            or segments[0] not in spec["allowed_roots"]
        ):
            raise AssuranceLanguageError(f"unsupported assurance selector: {selector}")

    def select(self, context: Mapping[str, Any], selector: str) -> Any:
        self._validate_selector(selector)
        value: Any = context
        for segment in selector.split(self.definition["selector"]["separator"]):
            if not isinstance(value, Mapping) or segment not in value:
                raise AssuranceLanguageError(f"assurance selector unresolved: {selector}")
            value = value[segment]
        return value

    def _repository_file(self, value: Any) -> bool:
        if not isinstance(value, str) or not value:
            raise AssuranceLanguageError("repository path operand must be a string")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            raise AssuranceLanguageError("repository path operand escapes repository")
        resolved = (self.root / path).resolve()
        if self.root not in resolved.parents:
            raise AssuranceLanguageError("repository path operand escapes repository")
        return resolved.is_file()

    def evaluate(
        self, expression: Mapping[str, Any], context: Mapping[str, Any]
    ) -> tuple[bool, Any]:
        self.validate_expression(expression)
        compounds = self.definition["expression"]["compound_operators"]
        for name, schema in compounds.items():
            if name in expression:
                results = [self.evaluate(child, context) for child in expression[name]]
                implementation = schema["implementation"]
                result = (
                    all(item[0] for item in results)
                    if implementation == "all"
                    else any(item[0] for item in results)
                )
                return result, [item[1] for item in results]

        selector, operator = expression["selector"], expression["operator"]
        value = self.select(context, selector)
        expected = expression.get("value")
        implementation = self.definition["operators"][operator]["implementation"]
        try:
            if implementation == "strict_equals":
                result = type(value) is type(expected) and value == expected
            elif implementation == "strict_equals_selector":
                expected = self.select(context, expression["value_selector"])
                result = type(value) is type(expected) and value == expected
            elif implementation == "strict_not_equals":
                result = type(value) is not type(expected) or value != expected
            elif implementation == "empty":
                result = not value
            elif implementation == "not_empty":
                result = bool(value)
            elif implementation == "one_of":
                result = any(type(value) is type(item) and value == item for item in expected)
            elif implementation == "not_contains":
                result = expected not in value
            elif implementation == "repository_file_exists":
                result = self._repository_file(value)
            elif implementation == "all_repository_files_exist":
                if not isinstance(value, list) or not value:
                    raise AssuranceLanguageError(
                        "all_repository_files_exist requires a non-empty list"
                    )
                result = all(self._repository_file(path) for path in value)
            elif implementation == "required_map_values_equal":
                if not isinstance(value, Mapping):
                    raise AssuranceLanguageError(
                        "required_map_values_equal requires a mapping"
                    )
                exclude = set(expression.get("exclude", []))
                required = [
                    (name, item) for name, item in value.items()
                    if name not in exclude
                    and isinstance(item, Mapping)
                    and item.get("required") is True
                ]
                result = bool(required) and all(
                    isinstance(item.get("state"), str)
                    and isinstance(expected, str)
                    and item["state"].casefold() == expected.casefold()
                    for _, item in required
                )
            else:  # Definition validation makes this unreachable.
                raise AssuranceLanguageError(
                    f"unsupported interpreter primitive: {implementation}"
                )
        except AssuranceLanguageError:
            raise
        except (TypeError, ValueError) as error:
            raise AssuranceLanguageError(
                f"invalid operand for assurance operator {operator}"
            ) from error
        return result, {"selector": selector, "value": value}
