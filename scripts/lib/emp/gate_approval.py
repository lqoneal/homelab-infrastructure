#!/usr/bin/env python3
"""Human-oriented, verification-first Zeus gate acceptance workflow."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from scripts.lib.emp.authority_resolution import AuthorityResolutionError, authoritative_source_path


GATE_PATTERN = re.compile(r"OA-(0[1-9]|[12][0-9]|30)")
RUN_PATTERN = re.compile(r"PMCT-\d{8}T\d{6}Z-[0-9a-f]{12}")


class GateApprovalError(RuntimeError):
    """A safe gate verification or acceptance refusal."""


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateApprovalError(f"invalid JSON artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise GateApprovalError(f"JSON artifact is not an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def _git(repository: Path, *arguments: str) -> str:
    result = _run(["git", *arguments], cwd=repository)
    if result.returncode:
        raise GateApprovalError(result.stderr.strip() or "Git inspection failed")
    return result.stdout.strip()


def validate_gate(gate: str) -> str:
    value = gate.upper()
    if not GATE_PATTERN.fullmatch(value):
        raise GateApprovalError(f"invalid gate: {gate}")
    return value


def completion_marker_valid(text: str) -> bool:
    return text.strip() in {"COMPLETE", "PMCT_COMPLETION_MARKER=COMPLETE"}


@dataclass(frozen=True)
class GateBinding:
    gate: str
    run_id: str
    evidence_directory: Path
    repository: Path
    qualified_head: str
    evidence_digest: str
    evidence_manifest_digest: str
    wop_identity: str
    wop_manifest_digest: str
    operator: str

    def record(self, *, result: str, verified_at: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "gate": self.gate,
            "pmct_run_id": self.run_id,
            "repository": str(self.repository),
            "qualified_repository_head": self.qualified_head,
            "evidence_directory": str(self.evidence_directory),
            "evidence_digest": self.evidence_digest,
            "evidence_manifest_digest": self.evidence_manifest_digest,
            "wop_identity": self.wop_identity,
            "wop_manifest_digest": self.wop_manifest_digest,
            "operator": self.operator,
            "verified_at": verified_at,
            "verification_result": result,
        }


class GateApprovalService:
    def __init__(
        self,
        repository: Path,
        wop: Path,
        *,
        runtime: Path | None = None,
        capability_state: Path | None = None,
        operator: str | None = None,
        clock: Callable[[], datetime] | None = None,
        authority_binding: dict[str, str] | None = None,
    ):
        self.repository = repository.resolve()
        self.wop = wop.resolve()
        self.runtime = (
            runtime
            or self.repository / "engineering/runtime/pmct/runs"
        ).resolve()
        self.capability_state = (
            capability_state
            or self.repository / "engineering/runtime/pmct/capability-state.yaml"
        ).resolve()
        self.operator = operator or getpass.getuser()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.authority_binding = authority_binding

    @classmethod
    def configured(cls, repository: Path) -> "GateApprovalService":
        return cls(
            Path(os.environ.get("ZEUS_GATE_REPOSITORY", repository)),
            Path(
                os.environ.get(
                    "ZEUS_GATE_WOP",
                    "/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP",
                )
            ),
            runtime=(
                Path(os.environ["ZEUS_GATE_PMCT_RUNTIME"])
                if os.environ.get("ZEUS_GATE_PMCT_RUNTIME")
                else None
            ),
            capability_state=(
                Path(os.environ["ZEUS_GATE_CAPABILITY_STATE"])
                if os.environ.get("ZEUS_GATE_CAPABILITY_STATE")
                else None
            ),
            operator=os.environ.get("ZEUS_GATE_OPERATOR"),
        )

    def _legacy_receipt_path(self, gate: str) -> Path:
        return self.wop / "operator-approvals" / f"{gate}.approved"

    def receipt_exists(self, gate: str) -> bool:
        return bool(self._receipt_paths(validate_gate(gate)))

    def _receipt_paths(self, gate: str) -> list[Path]:
        gate = validate_gate(gate)
        paths: list[Path] = []
        legacy = self._legacy_receipt_path(gate)
        if legacy.is_file():
            paths.append(legacy)
        directory = self.wop / "operator-approvals" / gate
        if directory.is_dir():
            paths.extend(sorted(directory.glob("*.approved")))
        return paths

    def _valid_receipts(self, gate: str) -> list[tuple[Path, dict[str, str]]]:
        receipts: list[tuple[Path, dict[str, str]]] = []
        for path in self._receipt_paths(gate):
            checksum = path.with_suffix(path.suffix + ".sha256")
            if not checksum.is_file():
                continue
            words = checksum.read_text(encoding="utf-8").split()
            if not words or words[0] != _sha256(path):
                continue
            fields = self._receipt_fields_from(path)
            if path != self._legacy_receipt_path(gate):
                predecessor = receipts[-1][0] if receipts else None
                lineage_valid = (
                    fields.get("predecessor_receipt") == "NONE"
                    and fields.get("predecessor_receipt_digest") == "NONE"
                    if predecessor is None
                    else (
                        fields.get("predecessor_receipt") == str(predecessor)
                        and fields.get("predecessor_receipt_digest")
                        == _sha256(predecessor)
                    )
                )
                if not lineage_valid:
                    continue
            receipts.append((path, fields))
        return receipts

    def _verification_path(self, gate: str) -> Path:
        return self.wop / "operator-verifications" / f"{gate}.verification.json"

    def verification_command(self, gate: str) -> str:
        return f"zeus verify {validate_gate(gate)}"

    @staticmethod
    def _receipt_fields_from(path: Path) -> dict[str, str]:
        fields: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                fields[key] = value
        return fields

    def _matching_receipt(
        self, binding: GateBinding
    ) -> tuple[Path, dict[str, str]] | None:
        for path, fields in self._valid_receipts(binding.gate):
            if (
                fields.get("pmct_run_id") == binding.run_id
                and fields.get("approved_head") == binding.qualified_head
                and fields.get("evidence_digest") == binding.evidence_digest
                and fields.get("repository") == str(binding.repository)
            ):
                return path, fields
        return None

    def _successor_receipt_path(
        self, binding: GateBinding
    ) -> tuple[Path, tuple[Path, dict[str, str]] | None]:
        history = self._valid_receipts(binding.gate)
        sequence = len(history) + 1
        receipt_id = (
            f"{binding.gate}-R{sequence:04d}-"
            f"{binding.qualified_head[:12]}-{binding.run_id[-12:]}"
        )
        target = (
            self.wop / "operator-approvals" / binding.gate / f"{receipt_id}.approved"
        )
        return target, (history[-1] if history else None)

    def _candidate_directories(self, gate: str) -> list[Path]:
        current = self._current_authority_binding()
        candidates: list[Path] = []
        if self.runtime.is_dir():
            for directory in sorted(self.runtime.glob("PMCT-*")):
                result_path = directory / "capability-result.json"
                manifest_path = directory / "run-manifest.json"
                if not result_path.is_file() or not manifest_path.is_file():
                    continue
                result = _json(result_path)
                manifest = _json(manifest_path)
                if (
                    result.get("gate") == gate
                    and result.get("result") == "PASS"
                    and Path(str(manifest.get("repository", ""))).resolve()
                    == self.repository
                    and manifest.get("head") == current["head"]
                    and manifest.get("implementation_baseline") == current["head"]
                    and manifest.get("published_baseline")
                    == current["published_baseline"]
                    and manifest.get("active_authority_publication")
                    == current["active_authority_publication"]
                ):
                    candidates.append(directory)
        return candidates

    def _current_authority_binding(self) -> dict[str, str]:
        if self.authority_binding is not None:
            return dict(self.authority_binding)
        head = _git(self.repository, "rev-parse", "HEAD")
        try:
            source = authoritative_source_path(self.repository)
        except AuthorityResolutionError as error:
            raise GateApprovalError(
                f"cannot resolve current authority publication: {error}"
            ) from error
        try:
            authority = yaml.safe_load(source.read_text(encoding="utf-8"))
            repositories = authority["repositories"]
        except (OSError, yaml.YAMLError, KeyError, TypeError) as error:
            raise GateApprovalError(
                "current authority publication is unavailable"
            ) from error
        matching = [
            value for value in repositories.values()
            if isinstance(value, dict)
            and Path(str(value.get("canonical_locator", ""))).resolve()
            == self.repository
        ]
        if len(matching) != 1:
            raise GateApprovalError(
                "current authority publication repository binding is ambiguous"
            )
        published = str(matching[0].get("baseline_commit", ""))
        pointer = self.repository / ".zeus/runtime/authority/active-publication.json"
        active = (
            str(_json(pointer).get("transaction_id", ""))
            if pointer.is_file()
            else "TRACKED-AUTHORITY-FALLBACK"
        )
        if not re.fullmatch(r"[0-9a-f]{40}", published) or not active:
            raise GateApprovalError("current authority publication binding is invalid")
        return {
            "head": head,
            "published_baseline": published,
            "active_authority_publication": active,
        }

    def _state_run_id(self, gate: str) -> str | None:
        try:
            state = yaml.safe_load(self.capability_state.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return None
        if not isinstance(state, dict):
            return None
        run_id = state.get("last_run_id")
        if not isinstance(run_id, str) or not RUN_PATTERN.fullmatch(run_id):
            return None
        for directory in self._candidate_directories(gate):
            if directory.name == run_id:
                return run_id
        return None

    def resolve_run(self, gate: str) -> Path:
        gate = validate_gate(gate)
        state_run = self._state_run_id(gate)
        if state_run:
            return self.runtime / state_run
        candidates = self._candidate_directories(gate)
        if not candidates:
            raise GateApprovalError(f"no PMCT PASS run found for {gate}")
        if len(candidates) != 1:
            names = ", ".join(item.name for item in candidates)
            raise GateApprovalError(f"ambiguous PMCT PASS runs for {gate}: {names}")
        return candidates[0]

    def _verify_artifacts(self, directory: Path) -> None:
        manifest = directory / "artifacts.sha256"
        if not manifest.is_file():
            raise GateApprovalError("PMCT evidence manifest is missing")
        for line in manifest.read_text(encoding="utf-8").splitlines():
            expected, separator, name = line.partition("  ")
            if not separator or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise GateApprovalError("PMCT evidence manifest is malformed")
            artifact = directory / name.removeprefix("./")
            if not artifact.is_file() or _sha256(artifact) != expected:
                raise GateApprovalError(f"PMCT evidence integrity failure: {name}")

    def _tracked_state_is_qualified(
        self,
        *,
        directory: Path,
        result: dict[str, Any],
        manifest: dict[str, Any],
    ) -> bool:
        status = _git(
            self.repository, "status", "--porcelain=v1", "--untracked-files=no"
        ).splitlines()
        if not status:
            return True
        try:
            relative_state = self.capability_state.relative_to(self.repository)
        except ValueError as error:
            raise GateApprovalError(
                "PMCT capability state is outside the repository"
            ) from error
        # _git() strips outer whitespace, including porcelain's leading
        # unstaged-column space. A staged change retains its second separator.
        expected_status = f"M {relative_state.as_posix()}"
        if status != [expected_status]:
            return False
        try:
            committed = yaml.safe_load(
                _git(
                    self.repository,
                    "show",
                    f"HEAD:{relative_state.as_posix()}",
                )
            )
            current = yaml.safe_load(
                self.capability_state.read_text(encoding="utf-8")
            )
        except (OSError, yaml.YAMLError) as error:
            raise GateApprovalError(
                "PMCT capability-state reconciliation is unreadable"
            ) from error
        if not isinstance(committed, dict) or not isinstance(current, dict):
            raise GateApprovalError(
                "PMCT capability-state reconciliation is malformed"
            )
        gate = str(result.get("gate", ""))
        run_result = str(result.get("result", ""))
        run_id = directory.name
        reasons = result.get("reasons", [])
        if (
            gate not in committed.get("gates", {})
            or not isinstance(reasons, list)
            or not all(isinstance(reason, str) for reason in reasons)
            or manifest.get("run_id") != run_id
            or manifest.get("completed_at") in (None, "")
        ):
            return False
        expected = json.loads(json.dumps(committed))
        gate_state = expected["gates"][gate]
        gate_state["status"] = run_result
        gate_state["reason"] = "; ".join(reasons)
        if run_result == "PASS":
            gate_state["codex_validation"] = "PASS"
            if gate_state.get("operator_acceptance") != "RECORDED":
                gate_state["gate_status"] = "AWAITING_OPERATOR_VERIFICATION"
        expected["last_run_id"] = run_id
        expected["last_evaluated_gate"] = gate
        expected["updated_at"] = manifest["completed_at"]
        expected["overall_result"] = (
            "PASS"
            if all(
                value.get("status") == "PASS"
                for value in expected["gates"].values()
            )
            else "NOT_READY"
        )
        return current == expected

    def _wop_digest(self) -> str:
        manifest = self.wop / "MANIFEST.sha256"
        if not manifest.is_file():
            raise GateApprovalError("authoritative WOP manifest is missing")
        result = _run(["sha256sum", "-c", manifest.name], cwd=self.wop)
        if result.returncode:
            raise GateApprovalError("authoritative WOP manifest verification failed")
        return _sha256(manifest)

    def _verify_resume_and_blocker(self, gate: str) -> None:
        resume = self.wop / "bin/resume-status"
        eligibility = self.wop / "bin/check-gate-eligibility"
        if not resume.is_file() or not eligibility.is_file():
            raise GateApprovalError("authoritative WOP lifecycle commands are missing")
        resume_result = _run([str(resume)], cwd=self.wop)
        if resume_result.returncode:
            raise GateApprovalError("authoritative WOP resume status failed")
        if gate == "OA-30":
            return
        next_gate = f"OA-{int(gate[3:]) + 1:02d}"
        eligibility_result = _run([str(eligibility), next_gate], cwd=self.wop)
        if eligibility_result.returncode != 77:
            raise GateApprovalError(
                f"{next_gate} is not blocked before {gate} acceptance"
            )
        expected = f"BLOCKING_REASON={gate}_OPERATOR_ACCEPTANCE_REQUIRED"
        combined = eligibility_result.stdout + eligibility_result.stderr
        if expected not in combined:
            raise GateApprovalError("next-gate blocker does not match the current gate")

    def next_gate_eligibility(self, gate: str) -> str:
        if gate == "OA-30":
            return "NONE"
        next_gate = f"OA-{int(gate[3:]) + 1:02d}"
        command = self.wop / "bin/check-gate-eligibility"
        result = _run([str(command), next_gate], cwd=self.wop)
        combined = result.stdout + result.stderr
        if result.returncode or "ELIGIBILITY=CONDITIONALLY_ELIGIBLE" not in combined:
            raise GateApprovalError(
                f"{next_gate} did not become conditionally eligible"
            )
        return next_gate

    def qualified_binding(
        self,
        gate: str,
        *,
        require_clean: bool = True,
        require_wop_manifest: bool = True,
    ) -> GateBinding:
        """Resolve and verify a current PMCT-qualified gate binding.

        The optional WOP-manifest check is deliberately separate from PMCT
        evidence validation so controlled WOP tooling can validate a pending
        reseal without weakening the qualified-run evidence boundary.
        """
        gate = validate_gate(gate)
        if Path(_git(self.repository, "rev-parse", "--show-toplevel")).resolve() != self.repository:
            raise GateApprovalError("repository identity mismatch")
        directory = self.resolve_run(gate)
        result = _json(directory / "capability-result.json")
        manifest = _json(directory / "run-manifest.json")
        if result.get("gate") != gate or result.get("result") != "PASS":
            raise GateApprovalError("resolved PMCT run is not a PASS for the gate")
        if result.get("manual_review_required") is not True:
            raise GateApprovalError("PMCT manual_review_required contract is absent")
        if result.get("run_id") != directory.name or manifest.get("run_id") != directory.name:
            raise GateApprovalError("PMCT run identity mismatch")
        if Path(str(manifest.get("repository", ""))).resolve() != self.repository:
            raise GateApprovalError("PMCT repository identity mismatch")
        marker = directory / "COMPLETE"
        if not marker.is_file() or not completion_marker_valid(
            marker.read_text(encoding="utf-8")
        ):
            raise GateApprovalError("PMCT completion marker is missing or invalid")
        self._verify_artifacts(directory)
        current_head = _git(self.repository, "rev-parse", "HEAD")
        qualified_head = str(manifest.get("head", ""))
        if current_head != qualified_head:
            raise GateApprovalError(
                f"qualified repository HEAD mismatch: expected={qualified_head} "
                f"actual={current_head}"
            )
        if require_clean and not self._tracked_state_is_qualified(
            directory=directory, result=result, manifest=manifest
        ):
            raise GateApprovalError(
                "tracked repository worktree is neither clean nor an exact "
                "authenticated PMCT capability-state reconciliation"
            )
        evidence_digest = str(manifest.get("evidence_digest", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", evidence_digest):
            raise GateApprovalError("PMCT evidence digest is invalid")
        return GateBinding(
            gate=gate,
            run_id=directory.name,
            evidence_directory=directory,
            repository=self.repository,
            qualified_head=qualified_head,
            evidence_digest=evidence_digest,
            evidence_manifest_digest=_sha256(directory / "artifacts.sha256"),
            wop_identity=str(self.wop),
            wop_manifest_digest=(
                self._wop_digest()
                if require_wop_manifest else "NOT_REQUIRED_FOR_READ_ONLY_VALIDATION"
            ),
            operator=self.operator,
        )

    def binding(self, gate: str, *, require_clean: bool = True) -> GateBinding:
        """Resolve a qualified binding for a WOP-bound gate operation."""
        return self.qualified_binding(gate, require_clean=require_clean)

    def validate_carry_forward(self, gate: str) -> dict[str, Any]:
        """Return an integrity-valid durable carry-forward record or fail closed."""
        gate = validate_gate(gate)
        if gate != "OA-01":
            raise GateApprovalError("carry-forward validation is governed for OA-01 only")
        binding = self.qualified_binding(
            gate, require_clean=False, require_wop_manifest=False
        )
        from scripts.lib.emp.gate_carry_forward import resolve_record

        record = resolve_record(self.repository, binding)
        if record is None:
            raise GateApprovalError("no integrity-valid OA-01 carry-forward record")
        previous = [
            fields for path, fields in self._valid_receipts(gate)
            if str(path) == record["prior_accepted_receipt"]
            and _sha256(path) == record["prior_accepted_receipt_digest"]
        ]
        if len(previous) != 1:
            raise GateApprovalError("carry-forward predecessor receipt is invalid")
        prior = previous[0]
        if (
            prior.get("approved_head") != record["prior_accepted_baseline"]
            or prior.get("authority_publication", "HISTORICAL")
            != record["prior_accepted_publication"]
            or record.get("successor_publication")
            != self._current_authority_binding()["active_authority_publication"]
            or record.get("carry_forward_decision") != "CARRY_FORWARD"
            or record.get("oa01_revalidation_required") is not False
        ):
            raise GateApprovalError("carry-forward publication or decision binding is invalid")
        return record

    def lifecycle(self, gate: str) -> dict[str, str]:
        try:
            state = yaml.safe_load(self.capability_state.read_text(encoding="utf-8"))
            value = state["gates"][gate]
        except (OSError, yaml.YAMLError, KeyError, TypeError) as error:
            raise GateApprovalError("PMCT lifecycle state is unavailable") from error
        return {
            "implementation": str(value.get("implementation_status", "UNKNOWN")),
            "codex_validation": str(value.get("codex_validation", value.get("status", "UNKNOWN"))),
            "operator_verification": str(value.get("operator_verification", "PENDING")),
            "operator_acceptance": str(value.get("operator_acceptance", "NOT_RECORDED")),
        }

    def verification_record(self, binding: GateBinding) -> dict[str, Any] | None:
        path = self._verification_path(binding.gate)
        checksum = path.with_suffix(path.suffix + ".sha256")
        if not path.is_file() or not checksum.is_file():
            return None
        expected = checksum.read_text(encoding="utf-8").split()[0]
        if expected != _sha256(path):
            return None
        record = _json(path)
        try:
            verified_at = datetime.fromisoformat(
                str(record.get("verified_at", "")).replace("Z", "+00:00")
            )
        except ValueError:
            return None
        now = self.clock()
        if verified_at.tzinfo is None or verified_at > now:
            return None
        expected_values = binding.record(
            result="PASS", verified_at=str(record["verified_at"])
        )
        return record if all(record.get(key) == value for key, value in expected_values.items()) else None

    def gate_milestone(self, binding: GateBinding) -> dict[str, Any]:
        verification = self.verification_record(binding)
        receipt = self._matching_receipt(binding)
        if verification is not None and receipt is not None:
            return {
                "verification": "PASS",
                "acceptance": "RECORDED",
                "source": "CURRENT_BINDING",
                "carry_forward": None,
            }
        if binding.gate == "OA-01":
            from scripts.lib.emp.gate_carry_forward import resolve_record

            carry = resolve_record(self.repository, binding)
            if carry is not None:
                return {
                    "verification": "PASS",
                    "acceptance": "RECORDED",
                    "source": "CARRY_FORWARD",
                    "carry_forward": carry,
                }
        return {
            "verification": "PASS" if verification is not None else "ABSENT",
            "acceptance": "RECORDED" if receipt is not None else "NOT_RECORDED",
            "source": "NONE",
            "carry_forward": None,
        }

    def verify(self, gate: str) -> GateBinding:
        binding = self.binding(gate)
        if self._matching_receipt(binding):
            raise GateApprovalError(
                f"approval receipt already exists for this {binding.gate} binding"
            )
        self._verify_resume_and_blocker(binding.gate)
        before = _git(self.repository, "rev-parse", "HEAD")
        if before != binding.qualified_head:
            raise GateApprovalError("repository HEAD changed before verification")
        record = binding.record(
            result="PASS",
            verified_at=self.clock().isoformat().replace("+00:00", "Z"),
        )
        path = self._verification_path(binding.gate)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
        checksum = path.with_suffix(path.suffix + ".sha256")
        checksum.write_text(f"{_sha256(path)}  {path.name}\n", encoding="utf-8")
        if _git(self.repository, "rev-parse", "HEAD") != before:
            path.unlink(missing_ok=True)
            checksum.unlink(missing_ok=True)
            raise GateApprovalError("repository HEAD changed during verification")
        return binding

    def record_verification_failure(self, gate: str, error: Exception) -> None:
        gate = validate_gate(gate)
        path = self._verification_path(gate)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": 1,
            "gate": gate,
            "pmct_run_id": None,
            "repository": str(self.repository),
            "qualified_repository_head": None,
            "evidence_directory": None,
            "evidence_digest": None,
            "evidence_manifest_digest": None,
            "wop_identity": str(self.wop),
            "wop_manifest_digest": None,
            "operator": self.operator,
            "verified_at": self.clock().isoformat().replace("+00:00", "Z"),
            "verification_result": "FAIL",
            "failure_reason": str(error),
        }
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        checksum = path.with_suffix(path.suffix + ".sha256")
        checksum.write_text(f"{_sha256(path)}  {path.name}\n", encoding="utf-8")

    def approve(
        self,
        gate: str,
        *,
        assume_yes: bool,
        confirmation: Callable[[str], str] = input,
    ) -> tuple[str, GateBinding]:
        gate = validate_gate(gate)
        binding = self.binding(gate)
        if self._matching_receipt(binding):
            raise GateApprovalError(
                f"approval receipt already exists for this {gate} binding"
            )
        if self.verification_record(binding) is None:
            return "VERIFICATION_REQUIRED", binding
        if not assume_yes:
            try:
                response = confirmation(f"Approve {gate}? [y/N]: ")
            except (EOFError, KeyboardInterrupt):
                return "CANCELLED", binding
            if response.strip().lower() not in {"y", "yes"}:
                return "CANCELLED", binding
        confirmed_binding = self.binding(gate)
        if confirmed_binding != binding or self.verification_record(confirmed_binding) is None:
            raise GateApprovalError(
                "approval binding changed after confirmation; verification must be rerun"
            )
        primitive = self.wop / "bin/record-operator-approval"
        receipt, predecessor = self._successor_receipt_path(binding)
        predecessor_path = predecessor[0] if predecessor else None
        predecessor_digest = _sha256(predecessor_path) if predecessor_path else "NONE"
        result = subprocess.run(
            [
                str(primitive),
                gate,
                binding.run_id,
                "NONINTERACTIVE" if assume_yes else "INTERACTIVE",
            ],
            cwd=self.wop,
            env={
                **os.environ,
                "ZEUS_APPROVAL_REPOSITORY": str(self.repository),
                "ZEUS_APPROVAL_OPERATOR": self.operator,
                "ZEUS_APPROVAL_RECEIPT": str(receipt),
                "ZEUS_APPROVAL_PREDECESSOR": (
                    str(predecessor_path) if predecessor_path else "NONE"
                ),
                "ZEUS_APPROVAL_PREDECESSOR_DIGEST": predecessor_digest,
            },
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise GateApprovalError(result.stderr.strip() or "approval primitive failed")
        checksum = receipt.with_suffix(receipt.suffix + ".sha256")
        if not receipt.is_file() or not checksum.is_file():
            raise GateApprovalError("approval primitive did not create a receipt")
        expected = checksum.read_text(encoding="utf-8").split()[0]
        if expected != _sha256(receipt):
            raise GateApprovalError("approval receipt checksum verification failed")
        fields = self._receipt_fields_from(receipt)
        expected_fields = {
            "gate": gate,
            "pmct_run_id": binding.run_id,
            "repository": str(self.repository),
            "approved_head": binding.qualified_head,
            "evidence_digest": binding.evidence_digest,
            "operator": self.operator,
            "operator_verification_record": str(self._verification_path(gate)),
            "operator_verification_digest": _sha256(self._verification_path(gate)),
            "confirmation_mode": "NONINTERACTIVE" if assume_yes else "INTERACTIVE",
            "predecessor_receipt": (
                str(predecessor_path) if predecessor_path else "NONE"
            ),
            "predecessor_receipt_digest": predecessor_digest,
        }
        if any(fields.get(key) != value for key, value in expected_fields.items()):
            raise GateApprovalError("approval receipt binding verification failed")
        return "RECORDED", binding


def print_verification_instruction(service: GateApprovalService, gate: str) -> None:
    print("\nIndependent verification is required before approval.")
    print("\nCOPY AND RUN THIS VERIFICATION COMMAND:\n")
    print("-" * 60)
    print(service.verification_command(gate))
    print("-" * 60)
    print(f"\nAfter the command reports:\n\n{gate}_SECOND_WINDOW_VERIFICATION=PASS")
    print(f"\nrun:\n\nzeus approve {gate}")


def verify_command(service: GateApprovalService, gate: str) -> int:
    gate = validate_gate(gate)
    try:
        binding = service.verify(gate)
    except GateApprovalError as error:
        service.record_verification_failure(gate, error)
        raise
    print(f"Gate: {gate}")
    print(f"PMCT run: {binding.run_id}")
    print(f"Qualified repository HEAD: {binding.qualified_head}")
    print(f"Evidence directory: {binding.evidence_directory}")
    print("PMCT_RESULT=PASS")
    print("PMCT_MANUAL_REVIEW_REQUIRED=true")
    print("PMCT_COMPLETION_MARKER=COMPLETE")
    print("EVIDENCE_INTEGRITY=PASS")
    print("WOP_MANIFEST_VERIFICATION=PASS")
    print("WOP_RESUME_STATUS=PASS")
    print("NEXT_GATE_BLOCKED_PENDING_ACCEPTANCE=PASS")
    print(f"{gate}_SECOND_WINDOW_VERIFICATION=PASS")
    return 0


def approve_command(
    service: GateApprovalService,
    gate: str,
    *,
    assume_yes: bool,
    confirmation: Callable[[str], str] = input,
) -> int:
    gate = validate_gate(gate)
    lifecycle = service.lifecycle(gate)
    binding = service.binding(gate)
    if service._matching_receipt(binding):
        raise GateApprovalError(
            f"approval receipt already exists for this {gate} binding"
        )
    print(f"Gate: {gate}")
    print(f"Implementation: {lifecycle['implementation']}")
    print(f"Codex validation: {lifecycle['codex_validation']}")
    verification = service.verification_record(binding)
    verification_status = "PASS" if verification is not None else lifecycle["operator_verification"]
    print(f"Operator verification: {verification_status}")
    print(f"Operator acceptance: {lifecycle['operator_acceptance']}")
    print(f"\nAuthoritative PMCT run:\n{binding.run_id}")
    print(f"\nQualified repository HEAD:\n{binding.qualified_head}")
    if verification is None:
        print_verification_instruction(service, gate)
        return 77
    print(f"\nGate: {gate}")
    print(f"PMCT run: {binding.run_id}")
    print(f"Qualified HEAD: {binding.qualified_head}")
    print("Verification: PASS")
    print("Acceptance: NOT_RECORDED\n")
    result, binding = service.approve(
        gate, assume_yes=assume_yes, confirmation=confirmation
    )
    if result == "CANCELLED":
        print(f"{gate}_OPERATOR_ACCEPTANCE=NOT_RECORDED")
        print("APPROVAL_RESULT=CANCELLED")
        return 0
    next_gate = service.next_gate_eligibility(gate)
    print(f"{gate}_OPERATOR_ACCEPTANCE=RECORDED")
    print("APPROVAL_RECEIPT_VERIFICATION=PASS")
    print(f"{next_gate}_ELIGIBILITY=CONDITIONALLY_ELIGIBLE")
    print(
        f"NEXT_ACTION=RUN_{next_gate}_PRE_EXECUTION_VERIFICATION"
        if next_gate != "NONE"
        else "NEXT_ACTION=OPERATIONAL_ALPHA_CLOSEOUT_REVIEW"
    )
    return 0
