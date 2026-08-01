"""Integrity-bound provenance manifests for append-only engineering evidence."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping

EENS_SOURCE = Path(__file__).resolve().parents[3] / "services" / "eens" / "src"
if str(EENS_SOURCE) not in sys.path:
    sys.path.insert(0, str(EENS_SOURCE))

from eens.events import EngineeringEvent  # noqa: E402
from eens.store import AppendResult, EventStore  # noqa: E402


class EvidenceProvenanceError(ValueError):
    """Evidence cannot be bound unambiguously to its authoritative subject."""


def digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class EvidenceProvenance:
    """Persist deterministic, replay-safe evidence-to-authority bindings."""

    REQUIRED_BINDINGS = (
        "repository_identity", "repository_commit", "authority_identity",
        "mission_id", "wop_id", "execution_id", "gate_id", "agent_identity",
    )

    def __init__(self, database_path: str | Path):
        self.store = EventStore(database_path)

    def bind(
        self,
        *,
        evidence_record: Mapping[str, Any],
        repository_identity: str,
        repository_commit: str,
        authority_identity: str,
        mission_id: str,
        wop_id: str,
        execution_id: str,
        gate_id: str,
        agent_identity: str,
        timestamp: str,
    ) -> AppendResult:
        bindings = {
            "repository_identity": repository_identity,
            "repository_commit": repository_commit,
            "authority_identity": authority_identity,
            "mission_id": mission_id,
            "wop_id": wop_id,
            "execution_id": execution_id,
            "gate_id": gate_id,
            "agent_identity": agent_identity,
        }
        if any(not isinstance(bindings[key], str) or not bindings[key] for key in self.REQUIRED_BINDINGS):
            raise EvidenceProvenanceError("all provenance bindings must be non-empty strings")
        if not isinstance(timestamp, str) or not timestamp:
            raise EvidenceProvenanceError("timestamp binding is required")
        if not re.fullmatch(r"[0-9a-f]{40}", repository_commit):
            raise EvidenceProvenanceError("repository commit must be an exact lowercase Git object id")
        record = dict(evidence_record)
        checksum = record.get("checksum")
        if not isinstance(checksum, str) or len(checksum) != 64:
            raise EvidenceProvenanceError("evidence checksum is absent or malformed")
        unsigned = {key: value for key, value in record.items() if key != "checksum"}
        if digest(unsigned) != checksum:
            raise EvidenceProvenanceError("evidence checksum does not match record content")
        identity_matches = {
            "repository_identity": record.get("repository_identity") == repository_identity,
            "repository_commit": record.get("baseline_commit") == repository_commit,
            "mission_id": record.get("mission_id") == mission_id,
            "wop_id": record.get("wop_id") == wop_id,
            "agent_identity": record.get("agent_identity") == agent_identity,
        }
        if not all(identity_matches.values()):
            raise EvidenceProvenanceError("evidence subject does not match authoritative bindings")
        manifest = {
            "schema_version": 1,
            "evidence_checksum": checksum,
            "bindings": bindings,
            "timestamp": timestamp,
        }
        manifest["binding_digest"] = digest(manifest)
        identity = f"{gate_id}:{execution_id}:{checksum}"
        event = EngineeringEvent(
            event_type="zeus.evidence.provenance.bound",
            source="zeus.oa20",
            subject=execution_id,
            idempotency_key=identity,
            occurred_at=timestamp,
            event_id=str(uuid.uuid5(uuid.NAMESPACE_URL, identity)),
            payload=manifest,
        )
        return self.store.append(event)

    def replay(self):
        return self.store.replay()
