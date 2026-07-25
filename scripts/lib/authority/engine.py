#!/usr/bin/env python3
"""Validate and resolve an offline, single-parent authority DAG."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from yaml.constructor import ConstructorError


class AuthorityValidationError(ValueError):
    """Raised when an authority graph is structurally or semantically invalid."""

    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(sorted(set(errors)))
        super().__init__("; ".join(self.errors))


class AuthorityDomain(str, Enum):
    AUTHORITY = "authority"
    INFORMATION = "information"
    LIFECYCLE = "lifecycle"
    PUBLICATION = "publication"
    EVIDENCE = "evidence"
    QUALIFICATION = "qualification"
    REGISTRY = "registry"
    RUNTIME = "runtime"
    RESUME = "resume"
    REPOSITORY = "repository"


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True, order=True)
class AuthorityEdge:
    """One child-to-parent authority edge."""

    child: str
    parent: str


@dataclass(frozen=True)
class AuthorityNode:
    """Typed authority node with an explicit finite capability set."""

    node_id: str
    kind: str
    domain: AuthorityDomain
    rank: int
    authority_parents: tuple[str, ...]
    capabilities: frozenset[str]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AuthorityNode":
        required = {
            "id",
            "kind",
            "domain",
            "rank",
            "authority_parents",
            "capabilities",
        }
        missing = sorted(required - set(value))
        if missing:
            raise AuthorityValidationError(
                [f"node is missing required field: {field}" for field in missing]
            )
        node_id = value["id"]
        kind = value["kind"]
        rank = value["rank"]
        parents = value["authority_parents"]
        capabilities = value["capabilities"]
        errors: list[str] = []
        if not isinstance(node_id, str) or not node_id:
            errors.append("node id must be a non-empty string")
        if not isinstance(kind, str) or not kind:
            errors.append(f"{node_id}: kind must be a non-empty string")
        try:
            domain = AuthorityDomain(value["domain"])
        except (TypeError, ValueError):
            errors.append(f"{node_id}: authority domain is not recognized")
            domain = AuthorityDomain.AUTHORITY
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 0:
            errors.append(f"{node_id}: rank must be a non-negative integer")
        if not isinstance(parents, list) or any(
            not isinstance(parent, str) or not parent for parent in parents
        ):
            errors.append(f"{node_id}: authority_parents must be a list of identifiers")
        if not isinstance(capabilities, list) or any(
            not isinstance(capability, str) or not capability
            for capability in capabilities
        ):
            errors.append(f"{node_id}: capabilities must be a list of identifiers")
        if isinstance(parents, list) and len(parents) != len(set(parents)):
            errors.append(f"{node_id}: duplicate authority parent")
        if isinstance(capabilities, list) and len(capabilities) != len(set(capabilities)):
            errors.append(f"{node_id}: duplicate capability")
        if errors:
            raise AuthorityValidationError(errors)
        return cls(
            node_id=node_id,
            kind=kind,
            domain=domain,
            rank=rank,
            authority_parents=tuple(parents),
            capabilities=frozenset(capabilities),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "kind": self.kind,
            "domain": self.domain.value,
            "rank": self.rank,
            "authority_parents": list(self.authority_parents),
            "capabilities": sorted(self.capabilities),
        }


@dataclass(frozen=True)
class AuthorityResolution:
    """Deterministic authority resolution for one node."""

    node_id: str
    root_id: str
    path: tuple[str, ...]
    effective_capabilities: frozenset[str]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "root_id": self.root_id,
            "path": list(self.path),
            "effective_capabilities": sorted(self.effective_capabilities),
        }


class AuthorityGraph:
    """Immutable offline authority graph with fail-closed resolution."""

    def __init__(
        self,
        graph_id: str,
        root_id: str,
        nodes: Iterable[AuthorityNode],
        schema_version: int = 1,
    ) -> None:
        self.schema_version = schema_version
        self.graph_id = graph_id
        self.root_id = root_id
        node_list = tuple(nodes)
        self.nodes = {node.node_id: node for node in node_list}
        self._duplicate_ids = sorted(
            {
                node.node_id
                for node in node_list
                if sum(item.node_id == node.node_id for item in node_list) > 1
            }
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AuthorityGraph":
        if not isinstance(value, Mapping):
            raise AuthorityValidationError(["authority graph root must be a mapping"])
        errors: list[str] = []
        if value.get("schema_version") != 1:
            errors.append("schema_version must be 1")
        graph_id = value.get("graph_id")
        root_id = value.get("root")
        raw_nodes = value.get("nodes")
        if not isinstance(graph_id, str) or not graph_id:
            errors.append("graph_id must be a non-empty string")
        if not isinstance(root_id, str) or not root_id:
            errors.append("root must be a non-empty node identifier")
        if not isinstance(raw_nodes, list):
            errors.append("nodes must be a list")
        if errors:
            raise AuthorityValidationError(errors)
        nodes: list[AuthorityNode] = []
        node_errors: list[str] = []
        for position, raw_node in enumerate(raw_nodes, start=1):
            if not isinstance(raw_node, Mapping):
                node_errors.append(f"node {position} must be a mapping")
                continue
            try:
                nodes.append(AuthorityNode.from_mapping(raw_node))
            except AuthorityValidationError as error:
                node_errors.extend(f"node {position}: {item}" for item in error.errors)
        if node_errors:
            raise AuthorityValidationError(node_errors)
        return cls(graph_id, root_id, nodes)

    @classmethod
    def load(cls, path: Path | str) -> "AuthorityGraph":
        graph_path = Path(path)
        if not graph_path.is_file():
            raise AuthorityValidationError([f"authority graph not found: {graph_path}"])
        try:
            value = yaml.load(
                graph_path.read_text(encoding="utf-8"),
                Loader=UniqueKeyLoader,
            )
        except (OSError, yaml.YAMLError) as error:
            raise AuthorityValidationError([f"invalid authority graph: {error}"]) from error
        return cls.from_mapping(value)

    @property
    def edges(self) -> tuple[AuthorityEdge, ...]:
        return tuple(
            sorted(
                AuthorityEdge(node.node_id, parent)
                for node in self.nodes.values()
                for parent in node.authority_parents
            )
        )

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.schema_version != 1:
            errors.append("schema_version must be 1")
        if not self.graph_id:
            errors.append("graph_id must be a non-empty string")
        if self._duplicate_ids:
            errors.extend(
                f"duplicate node id: {node_id}" for node_id in self._duplicate_ids
            )
        if self.root_id not in self.nodes:
            errors.append(f"root does not resolve: {self.root_id}")

        roots = sorted(
            node.node_id
            for node in self.nodes.values()
            if not node.authority_parents
        )
        if roots != [self.root_id]:
            errors.append(
                "exactly one root authority is required: "
                + (",".join(roots) if roots else "none")
            )

        for node in sorted(self.nodes.values(), key=lambda item: item.node_id):
            if node.domain is not AuthorityDomain.AUTHORITY:
                errors.append(
                    f"{node.node_id}: cross-domain authority transfer is prohibited "
                    f"for domain {node.domain.value}"
                )
            expected_parent_count = 0 if node.node_id == self.root_id else 1
            if len(node.authority_parents) != expected_parent_count:
                errors.append(
                    f"{node.node_id}: expected {expected_parent_count} authority "
                    f"parent(s), found {len(node.authority_parents)}"
                )
            for parent_id in node.authority_parents:
                parent = self.nodes.get(parent_id)
                if parent is None:
                    errors.append(
                        f"{node.node_id}: orphan authority parent does not resolve: "
                        f"{parent_id}"
                    )
                    continue
                if parent.domain is not node.domain:
                    errors.append(
                        f"{node.node_id}: cross-domain authority edge to {parent_id}"
                    )
                if parent.rank >= node.rank:
                    errors.append(
                        f"{node.node_id}: authority rank must decrease toward parent "
                        f"{parent_id}"
                    )
                expansion = sorted(node.capabilities - parent.capabilities)
                if expansion:
                    errors.append(
                        f"{node.node_id}: effective authority expands parent "
                        f"{parent_id}: {','.join(expansion)}"
                    )

        errors.extend(self._cycle_errors())
        return tuple(sorted(set(errors)))

    def _cycle_errors(self) -> list[str]:
        errors: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str, path: tuple[str, ...]) -> None:
            if node_id in visiting:
                start = path.index(node_id)
                cycle = path[start:] + (node_id,)
                errors.append("authority cycle detected: " + " -> ".join(cycle))
                return
            if node_id in visited or node_id not in self.nodes:
                return
            visiting.add(node_id)
            node = self.nodes[node_id]
            for parent in sorted(node.authority_parents):
                visit(parent, path + (node_id,))
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in sorted(self.nodes):
            visit(node_id, ())
        return errors

    def validate(self) -> None:
        errors = self.validation_errors()
        if errors:
            raise AuthorityValidationError(errors)

    def resolve(self, node_id: str) -> AuthorityResolution:
        self.validate()
        if node_id not in self.nodes:
            raise AuthorityValidationError([f"authority node not found: {node_id}"])
        path: list[str] = []
        seen: set[str] = set()
        current = node_id
        while True:
            if current in seen:
                raise AuthorityValidationError(
                    ["authority traversal repeated a node: " + current]
                )
            seen.add(current)
            path.append(current)
            node = self.nodes[current]
            if current == self.root_id:
                break
            current = node.authority_parents[0]
        return AuthorityResolution(
            node_id=node_id,
            root_id=self.root_id,
            path=tuple(path),
            effective_capabilities=self.nodes[node_id].capabilities,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "graph_id": self.graph_id,
            "root": self.root_id,
            "nodes": [
                self.nodes[node_id].to_mapping() for node_id in sorted(self.nodes)
            ],
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_mapping(),
            indent=2,
            sort_keys=True,
            separators=(",", ": "),
        ) + "\n"

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            self.to_mapping(),
            sort_keys=True,
            allow_unicode=True,
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "serialize"):
        child = subparsers.add_parser(command)
        child.add_argument("graph", type=Path)
        if command == "serialize":
            child.add_argument("--format", choices=("json", "yaml"), default="json")
    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("graph", type=Path)
    resolve.add_argument("node_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        graph = AuthorityGraph.load(args.graph)
        graph.validate()
        if args.command == "validate":
            print(
                f"PASS: authority graph {graph.graph_id} "
                f"({len(graph.nodes)} nodes, {len(graph.edges)} edges)"
            )
        elif args.command == "resolve":
            print(json.dumps(graph.resolve(args.node_id).to_mapping(), sort_keys=True))
        elif args.command == "serialize":
            output = graph.to_json() if args.format == "json" else graph.to_yaml()
            sys.stdout.write(output)
    except AuthorityValidationError as error:
        for item in error.errors:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
