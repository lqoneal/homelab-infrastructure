#!/usr/bin/env python3
"""Deterministic, fail-closed WOP submission admission control."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.wop_schema import is_wop_id, validate_optional_approval_date


SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "engineering/admission/wop-submission.schema.yaml"
)
AUTHORITATIVE_SCHEMA = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
CONTRACT = AUTHORITATIVE_SCHEMA["x-zeus-authoritative-contract"]
DECISIONS = {"ACCEPTED", "RESUBMISSION_REQUIRED"}
VALIDATOR_VERSION = "1"
PROCEDURE = CONTRACT["procedure"]
TEMPLATE = CONTRACT["template"]
STANDARDS = tuple(CONTRACT["standards"])
REQUIRED_SECTIONS = tuple(CONTRACT["required_sections"])
REQUIRED_EXECUTION_REFERENCES = tuple(CONTRACT["execution_package_references"])
REQUIRED_SUBMISSION_FORMAT = {
    "schema_version": 1,
    "document_type": "EngineeringWorkOrder",
    "wop_id": "WOP-<semantic-reference-or-UUID>",
    "mission_id": "<mission identifier>",
    "phase_id": "<phase identifier>",
    "revision": "<positive integer>",
    "status": "Active",
    "title": "<title>",
    "repository_identity": "<repository identity>",
    "submitter_identity": "<submitter identity>",
    "submission_authority": {
        "source": "operator-submitted WOP",
        "submission_id": "<submission identifier>",
    },
    "execution_package_references": {
        key: f"<{key}>" for key in REQUIRED_EXECUTION_REFERENCES
    },
    "authoritative_references": [
        PROCEDURE,
        TEMPLATE,
        *STANDARDS,
    ],
    "sections": {key: "<non-empty content>" for key in REQUIRED_SECTIONS},
    "submission_digest": "<sha256 of canonical submission without this field>",
}
OPTIONAL_CONVERGENCE_FIELDS = {
    "authority_lineage",
    "convergence_flow_digest",
    "approval_gate",
    "submission_authority",
    "approval",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def submission_digest(value: Mapping[str, Any]) -> str:
    return digest({key: item for key, item in value.items() if key != "submission_digest"})


def admission_identifier(value: Mapping[str, Any]) -> str:
    identity = {
        key: item for key, item in value.items()
        if key not in {
            "admission_id", "deterministic_checksum", "evaluation_timestamp",
            "execution_status", "required_submission_format", "validation_summary",
        }
    }
    return "ADMISSION-" + str(
        uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(identity))
    )


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ValidationFailure:
    reason_code: str
    field: str
    message: str
    required_correction: str

    def to_mapping(self) -> dict[str, str]:
        return {
            "field": self.field,
            "message": self.message,
            "reason_code": self.reason_code,
            "required_correction": self.required_correction,
        }


@dataclass(frozen=True)
class AdmissionDecision:
    canonical_data: str

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def to_json(self) -> str:
        return json.dumps(self.data, indent=2, sort_keys=True) + "\n"


class AdmissionController:
    """Validate, decide, and record without rewriting the submission."""

    def validate(
        self, submission: Mapping[str, Any], expected_repository: str
    ) -> tuple[ValidationFailure, ...]:
        failures: list[ValidationFailure] = []

        def require(field: str, value: Any, correction: str) -> None:
            if value is None or value == "" or value == [] or value == {}:
                failures.append(
                    ValidationFailure(
                        "REQUIRED_FIELD_MISSING", field,
                        f"{field} is required", correction
                    )
                )

        if submission.get("schema_version") != 1:
            failures.append(ValidationFailure(
                "UNSUPPORTED_SCHEMA_VERSION", "schema_version",
                "schema_version must equal 1", "Set schema_version to 1."
            ))
        if submission.get("document_type") != "EngineeringWorkOrder":
            failures.append(ValidationFailure(
                "INVALID_DOCUMENT_TYPE", "document_type",
                "document_type must be EngineeringWorkOrder",
                "Set document_type to EngineeringWorkOrder."
            ))
        for field in (
            "wop_id", "mission_id", "phase_id", "revision", "status", "title",
            "repository_identity", "submitter_identity", "submission_digest",
        ):
            require(field, submission.get(field), f"Provide a non-empty {field}.")
        wop_id = submission.get("wop_id")
        if wop_id and not is_wop_id(wop_id):
            failures.append(ValidationFailure(
                "INVALID_WOP_IDENTIFIER", "wop_id",
                "wop_id must be a canonical semantic WOP reference or legacy UUID",
                "Use the published semantic WOP ID or a lowercase RFC 4122 UUID."
            ))
        if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9.]+)+", str(submission.get("mission_id", ""))):
            failures.append(ValidationFailure(
                "INVALID_MISSION_IDENTIFIER", "mission_id",
                "mission_id is not a canonical uppercase mission identifier",
                "Provide an uppercase, hyphen-delimited mission identifier."
            ))
        if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9.]+)+", str(submission.get("phase_id", ""))):
            failures.append(ValidationFailure(
                "INVALID_PHASE_IDENTIFIER", "phase_id",
                "phase_id is not a canonical uppercase phase identifier",
                "Provide an uppercase, hyphen-delimited phase identifier."
            ))
        if not isinstance(submission.get("revision"), int) or submission.get("revision", 0) < 1:
            failures.append(ValidationFailure(
                "INVALID_REVISION", "revision", "revision must be a positive integer",
                "Provide a positive integer revision."
            ))
        if submission.get("status") != "Active":
            failures.append(ValidationFailure(
                "INACTIVE_SUBMISSION", "status", "only Active Work Orders are admissible",
                "Submit the Active revision; approval is required only for an approval gate declared by the WOP."
            ))
        if submission.get("repository_identity") != expected_repository:
            failures.append(ValidationFailure(
                "REPOSITORY_IDENTITY_MISMATCH", "repository_identity",
                "repository identity does not match the admission target",
                f"Set repository_identity to {expected_repository}."
            ))

        approval = submission.get("approval")
        sections = submission.get("sections")
        explicit_gate = submission.get("approval_gate") or (
            sections.get("approval_gates") if isinstance(sections, Mapping) else None
        )
        if approval is not None and not isinstance(approval, Mapping):
            failures.append(ValidationFailure(
                "INVALID_APPROVAL_BLOCK", "approval", "approval must be an object when supplied",
                "Provide the declared in-WOP approval gate as an object."
            ))
        elif isinstance(approval, Mapping):
            for field in ("authority", "reference", "authorized_lifecycle_state"):
                require(f"approval.{field}", approval.get(field), f"Provide approval.{field}.")
            if approval.get("authorized_lifecycle_state") != "Active":
                failures.append(ValidationFailure(
                    "APPROVAL_NOT_ACTIVE", "approval.authorized_lifecycle_state",
                    "approval must authorize the Active lifecycle state",
                    "Provide an approval authorizing Active lifecycle state."
                ))
            if not validate_optional_approval_date(approval.get("date")):
                failures.append(ValidationFailure(
                    "INVALID_APPROVAL_DATE", "approval.date",
                    "approval.date must use ISO-8601 format when supplied",
                    "Omit approval.date when no authoritative date exists, or provide an ISO-8601 date/time."
                ))
        elif explicit_gate not in (None, False, "", [], {}):
            failures.append(ValidationFailure(
                "APPROVAL_GATE_UNSATISFIED", "approval",
                "the submitted WOP declares an approval gate but supplies no approval",
                "Resolve the approval gate declared by the WOP before admission."
            ))

        package = submission.get("execution_package_references")
        if not isinstance(package, Mapping):
            failures.append(ValidationFailure(
                "EXECUTION_PACKAGE_REFERENCES_MISSING", "execution_package_references",
                "execution_package_references must be an object",
                "Provide all required execution package references."
            ))
        else:
            for field in REQUIRED_EXECUTION_REFERENCES:
                require(
                    f"execution_package_references.{field}", package.get(field),
                    f"Provide execution_package_references.{field}."
                )

        if not isinstance(sections, Mapping):
            failures.append(ValidationFailure(
                "SECTIONS_MISSING", "sections", "sections must be an object",
                "Use the TPL-0001 section structure."
            ))
        else:
            for field in REQUIRED_SECTIONS:
                require(f"sections.{field}", sections.get(field), f"Complete sections.{field}.")

        references = submission.get("authoritative_references")
        if not isinstance(references, list):
            failures.append(ValidationFailure(
                "AUTHORITATIVE_REFERENCES_MISSING", "authoritative_references",
                "authoritative_references must be an array",
                "Reference PROC-0001, TPL-0001, and STD-0000 through STD-0004."
            ))
        else:
            for reference in (PROCEDURE, TEMPLATE, *STANDARDS):
                if reference not in references:
                    failures.append(ValidationFailure(
                        "AUTHORITATIVE_REFERENCE_MISSING", "authoritative_references",
                        f"required reference {reference} is missing",
                        f"Add {reference} to authoritative_references."
                    ))

        actual_digest = submission.get("submission_digest")
        if actual_digest and actual_digest != submission_digest(submission):
            failures.append(ValidationFailure(
                "SUBMISSION_DIGEST_MISMATCH", "submission_digest",
                "submission digest does not match canonical content",
                "Recompute SHA-256 over canonical JSON excluding submission_digest."
            ))
        if "authority_lineage" in submission and not isinstance(submission.get("authority_lineage"), Mapping):
            failures.append(ValidationFailure(
                "INVALID_AUTHORITY_LINEAGE", "authority_lineage",
                "authority_lineage must be an object when supplied",
                "Provide the convergence authority lineage as an object."
            ))
        flow_digest = submission.get("convergence_flow_digest")
        if flow_digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(flow_digest)):
            failures.append(ValidationFailure(
                "INVALID_CONVERGENCE_FLOW_DIGEST", "convergence_flow_digest",
                "convergence_flow_digest must be a SHA-256 digest when supplied",
                "Provide the 64-character convergence flow digest."
            ))
        allowed = set(REQUIRED_SUBMISSION_FORMAT) | OPTIONAL_CONVERGENCE_FIELDS
        extras = sorted(set(submission) - allowed)
        for field in extras:
            failures.append(ValidationFailure(
                "UNRECOGNIZED_TOP_LEVEL_FIELD", field,
                f"unrecognized top-level field: {field}",
                f"Remove the unsupported field {field}."
            ))
        return tuple(sorted(failures, key=lambda item: (item.field, item.reason_code)))

    def decide(
        self,
        submission: Mapping[str, Any],
        *,
        expected_repository: str,
        evaluated_at: datetime,
    ) -> AdmissionDecision:
        failures = self.validate(submission, expected_repository)
        decision = "RESUBMISSION_REQUIRED" if failures else "ACCEPTED"
        core = {
            "admission_decision": decision,
            "authoritative_references": [PROCEDURE, TEMPLATE, *STANDARDS],
            "evaluation_timestamp": utc_text(evaluated_at),
            "mission_id": str(submission.get("mission_id", "")),
            "repository_identity": expected_repository,
            "schema_version": 1,
            "submission_digest": submission_digest(submission),
            "submitter_identity": str(submission.get("submitter_identity", "")),
            "validation_failures": [item.to_mapping() for item in failures],
            "validator_version": VALIDATOR_VERSION,
            "wop_id": str(submission.get("wop_id", "")),
        }
        core["admission_id"] = admission_identifier(core)
        core["validation_summary"] = {
            "failure_count": len(failures),
            "reason_codes": sorted({item.reason_code for item in failures}),
        }
        if failures:
            core["required_submission_format"] = REQUIRED_SUBMISSION_FORMAT
            core["execution_status"] = [
                "No engineering work has been accepted.",
                "No repository modifications have been performed.",
                "No planning has begun.",
                "No commands have been executed.",
                "Resubmit using the authoritative WOP format.",
            ]
        checksum_input = dict(core)
        core["deterministic_checksum"] = digest(checksum_input)
        return AdmissionDecision(canonical_json(core))


class AdmissionLedger:
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def record(self, decision: AdmissionDecision) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / f"{decision.data['admission_id']}.json"
        serialized = decision.to_json()
        try:
            with target.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            if target.read_text(encoding="utf-8") != serialized:
                raise ValueError("immutable Admission Ledger collision")
        return target


def load_submission(path: Path | str) -> Mapping[str, Any]:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("submission must be a YAML or JSON object")
    return value


def verify_accepted_record(
    path: Path | str, *, expected_repository: str, expected_wop: str | None = None
) -> bool:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    checksum = value.pop("deterministic_checksum", None)
    if checksum != digest(value) or value.get("admission_id") != admission_identifier(value):
        return False
    return (
        value.get("admission_decision") == "ACCEPTED"
        and value.get("repository_identity") == expected_repository
        and value.get("validator_version") == VALIDATOR_VERSION
        and value.get("validation_failures") == []
        and value.get("validation_summary") == {
            "failure_count": 0, "reason_codes": []
        }
        and (expected_wop is None or value.get("wop_id") == expected_wop)
    )


def _parse_time(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    admit = sub.add_parser("admit")
    admit.add_argument("--submission", required=True)
    admit.add_argument("--repository", required=True)
    admit.add_argument("--ledger", required=True)
    admit.add_argument("--at")
    verify = sub.add_parser("verify-record")
    verify.add_argument("--record", required=True)
    verify.add_argument("--repository", required=True)
    verify.add_argument("--wop")
    args = parser.parse_args(argv)
    if args.command == "verify-record":
        return 0 if verify_accepted_record(
            args.record, expected_repository=args.repository, expected_wop=args.wop
        ) else 78
    try:
        submission = load_submission(args.submission)
        decision = AdmissionController().decide(
            submission,
            expected_repository=args.repository,
            evaluated_at=_parse_time(args.at),
        )
        path = AdmissionLedger(args.ledger).record(decision)
        sys.stdout.write(decision.to_json())
        print(f"Admission record: {path}", file=sys.stderr)
        return 0 if decision.data["admission_decision"] == "ACCEPTED" else 78
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        print(f"admission validation failed closed: {error}", file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
