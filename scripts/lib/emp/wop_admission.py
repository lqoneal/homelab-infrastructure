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


DECISIONS = {"ACCEPTED", "RESUBMISSION_REQUIRED"}
VALIDATOR_VERSION = "1"
PROCEDURE = "PROC-0001@1.11"
TEMPLATE = "TPL-0001@1.7"
STANDARDS = ("STD-0000", "STD-0001", "STD-0002", "STD-0003", "STD-0004")
REQUIRED_SECTIONS = (
    "purpose_and_expected_outcome",
    "mission_classification",
    "governing_references",
    "scope",
    "explicit_authority",
    "prohibited_activities",
    "dependencies_and_entry_criteria",
    "deliverables",
    "execution_sequence",
    "success_and_acceptance_criteria",
    "validation_profile",
    "publication_and_synchronization",
    "stop_resume_and_escalation",
    "completion_report_requirement",
)
REQUIRED_EXECUTION_REFERENCES = (
    "authority_node_id",
    "authorization_decision_record",
    "immutable_wop",
)
REQUIRED_SUBMISSION_FORMAT = {
    "schema_version": 1,
    "document_type": "EngineeringWorkOrder",
    "wop_id": "WOP-<UUID>",
    "mission_id": "<mission identifier>",
    "phase_id": "<phase identifier>",
    "revision": "<positive integer>",
    "status": "Active",
    "title": "<title>",
    "repository_identity": "<repository identity>",
    "submitter_identity": "<submitter identity>",
    "approval": {
        "authority": "<approval authority>",
        "reference": "<approval reference>",
        "date": "<ISO-8601 date>",
        "authorized_lifecycle_state": "Active",
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
        if wop_id and not re.fullmatch(
            r"WOP-[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            str(wop_id),
        ):
            failures.append(ValidationFailure(
                "INVALID_WOP_IDENTIFIER", "wop_id",
                "wop_id must be WOP- followed by a lowercase RFC 4122 UUID",
                "Replace wop_id with WOP-<lowercase RFC 4122 UUID>."
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
                "Obtain approval and submit the Active revision."
            ))
        if submission.get("repository_identity") != expected_repository:
            failures.append(ValidationFailure(
                "REPOSITORY_IDENTITY_MISMATCH", "repository_identity",
                "repository identity does not match the admission target",
                f"Set repository_identity to {expected_repository}."
            ))

        approval = submission.get("approval")
        if not isinstance(approval, Mapping):
            failures.append(ValidationFailure(
                "APPROVAL_BLOCK_MISSING", "approval", "approval must be an object",
                "Provide authority, reference, date, and authorized_lifecycle_state."
            ))
        else:
            for field in ("authority", "reference", "date", "authorized_lifecycle_state"):
                require(f"approval.{field}", approval.get(field), f"Provide approval.{field}.")
            if approval.get("authorized_lifecycle_state") != "Active":
                failures.append(ValidationFailure(
                    "APPROVAL_NOT_ACTIVE", "approval.authorized_lifecycle_state",
                    "approval must authorize the Active lifecycle state",
                    "Provide an approval authorizing Active lifecycle state."
                ))
            date = str(approval.get("date", ""))
            try:
                datetime.fromisoformat(date)
            except ValueError:
                failures.append(ValidationFailure(
                    "INVALID_APPROVAL_DATE", "approval.date",
                    "approval.date must use ISO-8601 format",
                    "Provide approval.date as an ISO-8601 date."
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

        sections = submission.get("sections")
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
        allowed = set(REQUIRED_SUBMISSION_FORMAT)
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
