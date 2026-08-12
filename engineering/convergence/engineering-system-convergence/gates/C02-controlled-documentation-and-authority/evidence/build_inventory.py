#!/usr/bin/env python3
"""Build the frozen C02 controlled-document inventory deterministically.

This script is evidence tooling only.  It reads repository publications and
writes the requested output path; it does not modify controlled sources.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import Counter
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
INDEX_PATH = REPOSITORY_ROOT / "docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md"
AUTHORITY_PATTERN = re.compile(
    r"\b(authoritative|authority|canonical|source of truth|normative|controlled|"
    r"current mission|current phase|current gate|active mission|active phase)\b",
    re.IGNORECASE,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frontmatter(path: Path) -> tuple[dict, dict[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, {}
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}, {}
    raw = "\n".join(lines[1:end])
    try:
        value = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        value = {}
    line_map: dict[str, int] = {}
    for number, line in enumerate(lines[1:end], start=2):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if match and match.group(1) not in line_map:
            line_map[match.group(1)] = number
    return value if isinstance(value, dict) else {}, line_map


def first_heading(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def authority_signals(path: Path) -> list[dict]:
    signals = []
    for number, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        if AUTHORITY_PATTERN.search(line):
            signals.append({"line": number, "text": line.strip()[:240]})
        if len(signals) == 5:
            break
    return signals


def index_rows() -> list[dict]:
    rows = []
    inside = False
    section = None
    for number, line in enumerate(INDEX_PATH.read_text().splitlines(), start=1):
        if line.startswith("| Document ID |") or line.startswith("| Asset ID |"):
            inside = True
            section = (
                "CONTROLLED_DOCUMENTS_TABLE"
                if line.startswith("| Document ID |")
                else "CONTROLLED_ASSET_RECORDS_TABLE"
            )
            continue
        if not inside:
            continue
        if not line.startswith("|"):
            inside = False
            section = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0].startswith("---"):
            continue
        if len(cells) != 5:
            continue
        identifier, title, status, owner, path = cells
        rows.append(
            {
                "identifier": identifier,
                "title": title,
                "status": status,
                "owner": owner,
                "path": path.strip("`"),
                "index_line": number,
                "index_section": section,
            }
        )
    return rows


def scalar(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = index_rows()
    row_by_id = {row["identifier"]: row for row in rows}
    records = []
    family_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    persistence_counts: Counter[str] = Counter()
    metadata_mismatches = []

    docs_files = sorted((REPOSITORY_ROOT / "docs").rglob("*.md"))
    for path in docs_files:
        metadata, line_map = frontmatter(path)
        identifier = metadata.get("document_id") or metadata.get("asset_id")
        if not identifier:
            continue
        identifier = str(identifier)
        family = identifier.split("-")[0]
        family_counts[family] += 1
        status = scalar(metadata.get("status")) or "MISSING"
        persistence = scalar(metadata.get("persistence_status")) or "MISSING"
        title_field = "asset_name" if metadata.get("asset_id") else "title"
        status_counts[str(status)] += 1
        persistence_counts[str(persistence)] += 1
        rel = path.relative_to(REPOSITORY_ROOT).as_posix()
        record = {
            "identifier": identifier,
            "family": family,
            "path": rel,
            "sha256": sha256(path),
            "title": scalar(metadata.get(title_field)) or first_heading(path),
            "version": scalar(metadata.get("version")),
            "status": status,
            "approval_status": scalar(metadata.get("approval_status")),
            "persistence_status": persistence,
            "indexed": identifier in row_by_id,
            "metadata_lines": {
                key: line_map[key]
                for key in (
                    "document_id",
                    "asset_id",
                    "asset_name",
                    "title",
                    "version",
                    "status",
                    "approval_status",
                    "persistence_status",
                )
                if key in line_map
            },
            "relationship_count": len(metadata.get("relationships") or []),
        }
        records.append(record)
        row = row_by_id.get(identifier)
        if row:
            for field in ("title", "status", "owner"):
                source_field = title_field if field == "title" else field
                source_value = scalar(metadata.get(source_field))
                index_value = row[field]
                if source_value is not None and str(source_value).casefold() != index_value.casefold():
                    metadata_mismatches.append(
                        {
                            "identifier": identifier,
                            "field": field,
                            "index_value": index_value,
                            "source_value": source_value,
                            "index_line": row["index_line"],
                            "source_line": line_map.get(source_field),
                            "path": rel,
                        }
                    )
            if rel != row["path"]:
                metadata_mismatches.append(
                    {
                        "identifier": identifier,
                        "field": "path",
                        "index_value": row["path"],
                        "source_value": rel,
                        "index_line": row["index_line"],
                        "source_line": None,
                        "path": rel,
                    }
                )

    engineering_files = sorted(
        path for path in (REPOSITORY_ROOT / "engineering/docs").rglob("*") if path.is_file()
    )
    candidates = []
    for path in engineering_files:
        metadata, _ = frontmatter(path)
        candidates.append(
            {
                "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                "sha256": sha256(path),
                "document_id": scalar(metadata.get("document_id")),
                "heading": first_heading(path),
                "authority_signals": authority_signals(path),
                "classification": "NONCONTROLLED_IMPLEMENTATION_DOCUMENT_AUTHORITY_CANDIDATE",
            }
        )

    indexed_ids = set(row_by_id)
    record_ids = {record["identifier"] for record in records}
    controlled_missing_index = [record for record in records if not record["indexed"]]
    index_missing_source = [row for row in rows if row["identifier"] not in record_ids]
    legacy_paths = ["docs/architecture.md", "docs/roadmap.md"]

    output = {
        "schema_version": 1,
        "gate_id": "C02",
        "baseline": "f2e85d857dc73210c428d42ef9530ce9ffc4933b",
        "method": {
            "script": "engineering/convergence/engineering-system-convergence/gates/C02-controlled-documentation-and-authority/evidence/build_inventory.py",
            "scope": ["docs/**/*.md", "engineering/docs/**/*"],
            "index": INDEX_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
            "classification_rule": (
                "document_id or asset_id metadata denotes a controlled record; "
                "engineering/docs records without such identity remain non-controlled authority candidates"
            ),
        },
        "summary": {
            "docs_markdown_files": len(docs_files),
            "controlled_records": len(records),
            "document_id_records": sum(1 for record in records if record["family"] != "AST"),
            "legacy_asset_records": family_counts["AST"],
            "families": len(family_counts),
            "doc_0001_indexed_record_rows": len(rows),
            "controlled_records_missing_from_index": len(controlled_missing_index),
            "index_rows_without_source": len(index_missing_source),
            "registered_legacy_publications": len(legacy_paths),
            "engineering_docs_files": len(engineering_files),
            "engineering_docs_with_document_id": sum(
                1 for candidate in candidates if candidate["document_id"]
            ),
            "index_source_metadata_mismatches": len(metadata_mismatches),
        },
        "family_counts": dict(sorted(family_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "persistence_status_counts": dict(sorted(persistence_counts.items())),
        "controlled_records_missing_from_index": controlled_missing_index,
        "index_rows_without_source": index_missing_source,
        "index_source_metadata_mismatches": metadata_mismatches,
        "registered_legacy_publications": [
            {"path": rel, "sha256": sha256(REPOSITORY_ROOT / rel)} for rel in legacy_paths
        ],
        "controlled_records": records,
        "engineering_docs_authority_candidates": candidates,
        "disposition": {
            "controlled_records": "ASSESSED",
            "missing_index_records": "FINDING_C02_F001_NO_CORRECTION",
            "metadata_mismatches": "FINDING_C02_F002_NO_CORRECTION",
            "legacy_publications": "ASSESSED_AS_REGISTERED_LEGACY",
            "engineering_docs": "ASSESSED_AS_NONCONTROLLED_AUTHORITY_CANDIDATES",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(output, sort_keys=False, width=120), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
