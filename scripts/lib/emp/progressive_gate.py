"""Canonical, read-only query and verification primitives for Progressive OA.

This module deliberately has no CLI routing or compatibility dependencies. It
is the stable surface that later migration units can consume without changing
the current consumers of ``progressive_oa`` or the gate-specific verifiers.
"""

from __future__ import annotations

import importlib
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_runtime_support

# Keep the established internal name while the dependency now resolves to the
# foundational shared utility instead of the compatibility adapter.
progressive_oa = progressive_runtime_support


class ProgressiveGateError(ValueError):
    """Progressive state cannot be proved from repository-owned records."""


@dataclass(frozen=True)
class GateState:
    package_id: str
    repository: str
    current_gate: str | None
    gate_id: str
    gate_state: str
    verification_state: str
    predecessor_state: str
    receipt_state: str
    receipt: str | None

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


_VERIFIERS = {
    **{
        f"OA-{number:02d}": f"scripts.lib.emp.oa{number:02d}_gate_verification"
        for number in range(1, 6)
    },
    "OA-06": "scripts.lib.emp.oa06_gate_verification",
    "OA-07": "scripts.lib.emp.oa07_gate_verification",
    "OA-09": "scripts.lib.emp.oa09_gate_verification",
    "OA-10": "scripts.lib.emp.oa10_gate_verification",
    "OA-11": "scripts.lib.emp.oa11_gate_verification",
    "OA-12": "scripts.lib.emp.oa12_gate_verification",
    "OA-13": "scripts.lib.emp.oa13_gate_verification",
    "OA-14": "scripts.lib.emp.oa14_gate_verification",
    "OA-15": "scripts.lib.emp.oa15_gate_verification",
    "OA-16": "scripts.lib.emp.oa16_gate_verification",
    "OA-17": "scripts.lib.emp.oa17_gate_verification",
    "OA-18": "scripts.lib.emp.oa18_gate_verification",
}


def _repository(root: Path | str) -> Path:
    repository = Path(root).resolve()
    package = (repository / progressive_oa.PACKAGE_PATH).resolve()
    if repository not in package.parents or not package.is_dir():
        raise ProgressiveGateError(
            "Progressive package is absent from the qualified repository"
        )
    return repository


def _gate_id(root: Path, gate_id: str) -> str:
    normalized = gate_id.upper()
    try:
        progressive_oa.gate(root, normalized)
    except (KeyError, OSError, progressive_oa.ProgressiveOAError) as error:
        raise ProgressiveGateError(str(error)) from error
    return normalized


def _marker(root: Path, gate_id: str) -> tuple[Path, dict[str, Any]]:
    try:
        path, marker = progressive_oa._marker_binding(root, gate_id)
    except (OSError, json.JSONDecodeError, progressive_oa.ProgressiveOAError) as error:
        raise ProgressiveGateError(str(error)) from error
    return path, marker


def verification_state(root: Path | str, gate_id: str) -> dict[str, Any]:
    """Validate and return the repository-bound Progressive verification marker."""
    repository = _repository(root)
    normalized = _gate_id(repository, gate_id)
    path, marker = _marker(repository, normalized)
    return {
        "package_id": progressive_oa.PACKAGE,
        "repository": str(repository),
        "gate_id": normalized,
        "verification_state": "VERIFIED",
        "verification_record": str(path.parent / "VERIFICATION.json"),
        "verification_marker": str(path),
        "evidence_digest": marker["evidence_digest"],
        "marker_digest": marker["marker_digest"],
    }


def verify(root: Path | str, gate_id: str) -> dict[str, Any]:
    """Run the one canonical Progressive verification entry point.

    Unsupported gates fail closed until their gate-specific implementation is
    installed.  Gate-specific implementations remain intact and callable so
    this infrastructure addition does not redirect existing consumers.
    """
    repository = _repository(root)
    normalized = _gate_id(repository, gate_id)
    module_name = _VERIFIERS.get(normalized)
    if module_name is None:
        raise ProgressiveGateError(
            f"canonical verifier is not implemented for {normalized}"
        )
    try:
        result = importlib.import_module(module_name).verify(repository)
        binding = verification_state(repository, normalized)
    except (OSError, ValueError) as error:
        raise ProgressiveGateError(
            f"{normalized} verification failed closed: {error}"
        ) from error
    return {
        **binding,
        "result": result,
        "verification_result": "PASS",
    }


def validate_receipt(root: Path | str, gate_id: str) -> dict[str, Any]:
    """Centrally validate receipt integrity, replay, predecessor, and state."""
    repository = _repository(root)
    normalized = _gate_id(repository, gate_id)
    state = progressive_oa.load_state(repository)
    item = state.get("gates", {}).get(normalized)
    if not isinstance(item, dict):
        raise ProgressiveGateError(f"Progressive state omits {normalized}")
    if normalized == "OA-08":
        # OA-08 predates the JSON VERIFIED marker contract and records its
        # immutable qualification as WOP-RESOLUTION-QUALIFIED. Preserve that
        # historical receipt as a read-only compatibility path.
        legacy = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-08/WOP-RESOLUTION-QUALIFIED"
        if item.get("state") != "ACCEPTED" or not legacy.is_file():
            raise ProgressiveGateError("OA-08 historical qualification is unavailable")
        return {
            "package_id": progressive_oa.PACKAGE,
            "repository": str(repository),
            "gate_id": normalized,
            "receipt_state": "VALID",
            "receipt": str(repository / progressive_oa.PACKAGE_PATH / "runtime/decisions/OA-08/accepted-oa08-deterministic-resolution.json"),
            "receipt_digest": hashlib.sha256(legacy.read_bytes()).hexdigest(),
            "evidence_digest": hashlib.sha256(legacy.read_bytes()).hexdigest(),
            "predecessor": {"predecessor_gate": "OA-07", "predecessor_state": "HISTORICALLY_VALID"},
            "replay_safe": True,
            "state_consistent": True,
        }
    locator = item.get("acceptance_receipt")
    if item.get("state") != "ACCEPTED" or not isinstance(locator, str) or not locator:
        raise ProgressiveGateError(
            f"current acceptance receipt does not exist for {normalized}"
        )
    try:
        progressive_oa._validate_replay_lifecycle(state, normalized)
        path = progressive_oa._resolve_receipt_path(
            repository, locator, normalized
        )
        if not path.is_file():
            raise ProgressiveGateError(
                f"acceptance receipt does not exist: {path}"
            )
        value = json.loads(path.read_text())
        marker_path, marker = progressive_oa._marker_binding(
            repository, normalized
        )
        progressive_oa._validate_receipt_bindings(
            repository, normalized, path, value, marker_path, marker
        )
        predecessor = predecessor_state(repository, normalized)
    except (
        OSError,
        json.JSONDecodeError,
        progressive_oa.ProgressiveOAError,
    ) as error:
        raise ProgressiveGateError(str(error)) from error
    return {
        "package_id": progressive_oa.PACKAGE,
        "repository": str(repository),
        "gate_id": normalized,
        "receipt_state": "VALID",
        "receipt": str(path),
        "receipt_digest": value["receipt_digest"],
        "evidence_digest": marker["evidence_digest"],
        "predecessor": predecessor,
        "replay_safe": True,
        "state_consistent": True,
    }


def predecessor_state(root: Path | str, gate_id: str) -> dict[str, Any]:
    """Resolve the immediate canonical Progressive predecessor."""
    repository = _repository(root)
    normalized = _gate_id(repository, gate_id)
    number = int(normalized[-2:])
    if number == 1:
        return {
            "package_id": progressive_oa.PACKAGE,
            "repository": str(repository),
            "gate_id": normalized,
            "predecessor_gate": None,
            "predecessor_state": "NOT_REQUIRED",
            "receipt": None,
        }
    predecessor = f"OA-{number - 1:02d}"
    state = progressive_oa.load_state(repository)
    item = state.get("gates", {}).get(predecessor, {})
    if item.get("state") != "ACCEPTED":
        raise ProgressiveGateError(
            f"required predecessor {predecessor} is not accepted"
        )
    receipt = validate_receipt(repository, predecessor)
    return {
        "package_id": progressive_oa.PACKAGE,
        "repository": str(repository),
        "gate_id": normalized,
        "predecessor_gate": predecessor,
        "predecessor_state": "VALID",
        "receipt": receipt["receipt"],
        "receipt_digest": receipt["receipt_digest"],
    }


def gate_state(root: Path | str, gate_id: str | None = None) -> dict[str, Any]:
    """Query current gate, verification, predecessor, and receipt state."""
    repository = _repository(root)
    state = progressive_oa.load_state(repository)
    normalized = _gate_id(repository, gate_id or state.get("active_gate") or "")
    item = state.get("gates", {}).get(normalized)
    if not isinstance(item, dict) or not isinstance(item.get("state"), str):
        raise ProgressiveGateError(f"Progressive state is invalid for {normalized}")

    marker = (
        verification_state(repository, normalized)
        if item["state"] in ("AWAITING_OPERATOR_VERIFICATION", "ACCEPTED")
        else None
    )
    predecessor = predecessor_state(repository, normalized)
    receipt = (
        validate_receipt(repository, normalized)
        if item["state"] == "ACCEPTED"
        else None
    )
    return GateState(
        package_id=progressive_oa.PACKAGE,
        repository=str(repository),
        current_gate=state.get("active_gate"),
        gate_id=normalized,
        gate_state=item["state"],
        verification_state="VERIFIED" if marker else "NOT_VERIFIED",
        predecessor_state=predecessor["predecessor_state"],
        receipt_state="VALID" if receipt else "ABSENT",
        receipt=receipt["receipt"] if receipt else None,
    ).as_dict()


class ProgressiveGateService:
    """Canonical Progressive verification, query, and decision authority.

    Module-level functions remain compatibility adapters.  New Progressive
    consumers use this façade so record formats and lifecycle mechanics can
    evolve without creating another decision owner.
    """

    def __init__(self, root: Path | str):
        self.repository = _repository(root)

    def verify(self, gate_id: str) -> dict[str, Any]:
        return verify(self.repository, gate_id)

    def verification_state(self, gate_id: str) -> dict[str, Any]:
        return verification_state(self.repository, gate_id)

    def validate_receipt(self, gate_id: str) -> dict[str, Any]:
        return validate_receipt(self.repository, gate_id)

    def predecessor_state(self, gate_id: str) -> dict[str, Any]:
        return predecessor_state(self.repository, gate_id)

    def gate_state(self, gate_id: str | None = None) -> dict[str, Any]:
        return gate_state(self.repository, gate_id)

    def approve(
        self, gate_id: str, operator: str | None, at: str | None = None
    ) -> tuple[dict[str, Any], bool]:
        return self.decide(gate_id, "ACCEPTED", operator, at)

    def decline(
        self, gate_id: str, operator: str | None, at: str | None = None
    ) -> tuple[dict[str, Any], bool]:
        return self.decide(gate_id, "REJECTED", operator, at)

    def record_acceptance(
        self, gate_id: str, operator: str | None, at: str | None = None
    ) -> tuple[dict[str, Any], bool]:
        return self.approve(gate_id, operator, at)

    def decide(
        self,
        gate_id: str,
        decision: str,
        operator: str | None,
        at: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        """Persist one ACCEPTED/REJECTED decision or replay it deterministically."""
        normalized = _gate_id(self.repository, gate_id)
        if decision not in {"ACCEPTED", "REJECTED"}:
            raise ProgressiveGateError(
                "Progressive decision must be ACCEPTED or REJECTED"
            )
        value = progressive_oa.load_state(self.repository)
        gates = value.get("gates")
        if not isinstance(gates, dict) or not isinstance(
            gates.get(normalized), dict
        ):
            raise ProgressiveGateError(
                f"Progressive state is invalid for {normalized}"
            )
        receipt_dir = (
            self.repository
            / progressive_oa.PACKAGE_PATH
            / "runtime"
            / "decisions"
            / normalized
        )
        current = gates[normalized]
        try:
            if decision == "ACCEPTED" and current.get("state") == "ACCEPTED":
                if not operator:
                    raise ProgressiveGateError("--operator is required")
                progressive_oa._validate_replay_lifecycle(value, normalized)
                locator = current.get("acceptance_receipt")
                if not isinstance(locator, str) or not locator:
                    raise ProgressiveGateError(
                        "accepted gate has no current acceptance receipt"
                    )
                receipt_path = progressive_oa._resolve_receipt_path(
                    self.repository, locator, normalized
                )
                if not receipt_path.is_file():
                    raise ProgressiveGateError(
                        "current acceptance receipt does not exist"
                    )
                marker_path, marker = progressive_oa._marker_binding(
                    self.repository, normalized
                )
                receipt = json.loads(receipt_path.read_text())
                progressive_oa._validate_receipt_bindings(
                    self.repository,
                    normalized,
                    receipt_path,
                    receipt,
                    marker_path,
                    marker,
                    operator,
                )
                return receipt, True

            if value.get("active_gate") != normalized:
                raise ProgressiveGateError(
                    f"{normalized} is not the sole active gate "
                    f"({value.get('active_gate')})"
                )
            if current.get("state") not in (
                "AWAITING_OPERATOR_VERIFICATION",
                decision,
            ):
                raise ProgressiveGateError(
                    f"{normalized} is not awaiting operator verification; "
                    f"state={current.get('state')}"
                )
            if not operator:
                raise ProgressiveGateError("--operator is required")

            marker_path, marker = progressive_oa._marker_binding(
                self.repository, normalized
            )
            self._require_decision_boundary(normalized)

            if decision == "REJECTED":
                receipt_path = receipt_dir / "rejected.json"
                if receipt_path.exists():
                    receipt = json.loads(receipt_path.read_text())
                    self._validate_rejection(
                        normalized, receipt_path, receipt, marker_path, marker
                    )
                    if receipt.get("operator") != operator:
                        raise ProgressiveGateError(
                            "conflicting decision receipt"
                        )
                    return receipt, True

            receipt = self._create_receipt(
                normalized, decision, operator, at, marker_path, marker
            )
            receipt_path = (
                receipt_dir / f"accepted-{receipt['receipt_digest']}.json"
                if decision == "ACCEPTED"
                else receipt_dir / "rejected.json"
            )
            if decision == "ACCEPTED":
                receipt_path, receipt = self._recover_or_persist_acceptance(
                    normalized, receipt_dir, receipt_path, receipt,
                    marker_path, marker, operator
                )
                progressive_oa._advance_after_acceptance(
                    value, normalized, receipt_path
                )
            else:
                progressive_oa._persist_receipt(receipt_path, receipt)
                self._validate_rejection(
                    normalized, receipt_path, receipt, marker_path, marker
                )
                current["state"] = decision
                current["acceptance_receipt"] = None
                value["status"] = "STOPPED_FAIL_CLOSED"
            progressive_oa._write_state(self.repository, value)
            return receipt, False
        except ProgressiveGateError:
            raise
        except (
            KeyError,
            TypeError,
            json.JSONDecodeError,
            progressive_oa.ProgressiveOAError,
        ) as error:
            raise ProgressiveGateError(str(error)) from error

    def _require_decision_boundary(self, gate_id: str) -> None:
        if gate_id != "OA-02":
            return
        try:
            from scripts.lib.emp.controlled_mission_authority import (
                ControlledMissionAuthority,
            )

            ControlledMissionAuthority(self.repository).require(
                boundary="oa02_operator_acceptance"
            )
        except ValueError as error:
            raise ProgressiveGateError(
                f"verified evidence marker invalid: {error}"
            ) from error

    def _create_receipt(
        self,
        gate_id: str,
        decision: str,
        operator: str,
        at: str | None,
        marker_path: Path,
        marker: dict[str, Any],
    ) -> dict[str, Any]:
        manifest = (
            self.repository / progressive_oa.PACKAGE_PATH / "MANIFEST.sha256"
        )
        receipt = {
            "schema_version": 2,
            "package_id": progressive_oa.PACKAGE,
            "gate_id": gate_id,
            "decision": decision,
            "operator": operator,
            "decided_at": at or datetime.now(timezone.utc).isoformat(),
            "package_manifest_sha256": hashlib.sha256(
                manifest.read_bytes()
            ).hexdigest(),
            "evidence_marker_sha256": hashlib.sha256(
                marker_path.read_bytes()
            ).hexdigest(),
            "evidence_digest": marker["evidence_digest"],
            "marker_digest": marker["marker_digest"],
        }
        receipt["receipt_digest"] = progressive_oa._receipt_digest(receipt)
        return receipt

    def _recover_or_persist_acceptance(
        self,
        gate_id: str,
        receipt_dir: Path,
        receipt_path: Path,
        receipt: dict[str, Any],
        marker_path: Path,
        marker: dict[str, Any],
        operator: str,
    ) -> tuple[Path, dict[str, Any]]:
        recoverable: list[tuple[Path, dict[str, Any]]] = []
        for candidate in sorted(receipt_dir.glob("accepted-*.json")):
            candidate_receipt = json.loads(candidate.read_text())
            try:
                progressive_oa._validate_receipt_bindings(
                    self.repository,
                    gate_id,
                    candidate,
                    candidate_receipt,
                    marker_path,
                    marker,
                    operator,
                )
            except progressive_oa.ProgressiveOAError:
                continue
            recoverable.append((candidate, candidate_receipt))
        if len(recoverable) > 1:
            raise ProgressiveGateError(
                "multiple recoverable acceptance receipts"
            )
        if recoverable:
            receipt_path, receipt = recoverable[0]
        else:
            progressive_oa._persist_receipt(receipt_path, receipt)
        progressive_oa._validate_receipt_bindings(
            self.repository,
            gate_id,
            receipt_path,
            receipt,
            marker_path,
            marker,
            operator,
        )
        return receipt_path, receipt

    def _validate_rejection(
        self,
        gate_id: str,
        path: Path,
        receipt: dict[str, Any],
        marker_path: Path,
        marker: dict[str, Any],
    ) -> None:
        manifest = (
            self.repository / progressive_oa.PACKAGE_PATH / "MANIFEST.sha256"
        )
        if receipt.get("receipt_digest") != progressive_oa._receipt_digest(receipt):
            raise ProgressiveGateError("decision receipt integrity failure")
        if (
            receipt.get("package_id") != progressive_oa.PACKAGE
            or receipt.get("gate_id") != gate_id
            or receipt.get("decision") != "REJECTED"
            or not manifest.is_file()
            or receipt.get("package_manifest_sha256")
            != hashlib.sha256(manifest.read_bytes()).hexdigest()
            or receipt.get("evidence_marker_sha256")
            != hashlib.sha256(marker_path.read_bytes()).hexdigest()
            or receipt.get("evidence_digest") != marker.get("evidence_digest")
            or receipt.get("marker_digest") != marker.get("marker_digest")
        ):
            raise ProgressiveGateError("conflicting decision receipt")


def decision_service(root: Path | str) -> ProgressiveGateService:
    """Construct the canonical Progressive service façade."""
    return ProgressiveGateService(root)
