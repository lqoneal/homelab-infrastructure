#!/usr/bin/env python3
"""Disposable qualification for the Zeus autonomous lifecycle ledger."""

import json
import tempfile
from pathlib import Path

from scripts.lib.emp.autonomous_delivery import AutonomousDeliveryError, reconcile
from scripts.lib.emp.stage1_runtime import Stage1Store


def stage1(tmp: Path) -> tuple[Path, str]:
    directory = tmp / "stage1"
    transaction = {
        "schema_version": 2, "lifecycle_integrity": "RECEIPT_BACKED_V1",
        "instance_id": "ZEUS-DEVELOPMENT-AUTONOMOUS-FIXTURE",
        "mission_id": "MISSION-AUTONOMOUS-FIXTURE", "wop_id": "WOP-AUTONOMOUS-FIXTURE",
        "state": "DISPATCHED", "repository": str(tmp), "repository_baseline": "baseline",
        "package_digest": "package", "source_digest": "source",
        "authority_snapshot": {"authority_snapshot_digest": "authority"},
        "receipts": {
            "admission": {"admission_id": "EMM-DEV-ADMISSION-AUTONOMOUS"},
            "dispatch": {"receipt_id": "ZEUS-RECEIPT-DISPATCH-AUTONOMOUS", "provider_id": "provider"},
        },
    }
    saved = Stage1Store(directory).save(transaction)
    return directory, saved["instance_id"]


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage1_directory, transaction_id = stage1(tmp)
        runtime = tmp / "runtime"
        first = reconcile(tmp, stage1_directory, runtime, identifier=transaction_id)
        assert first["result"] == "PASS"
        assert first["snapshot"]["classification"] == "BLOCKED"
        assert first["snapshot"]["blockers"][0]["code"] == "RUNTIME_PROJECTION_INCOMPLETE"
        second = reconcile(tmp, stage1_directory, runtime, identifier=transaction_id)
        assert second["replayed"] is True
        assert second["snapshot"]["state_digest"] == first["snapshot"]["state_digest"]
        try:
            reconcile(tmp, stage1_directory, runtime, identifier="unrelated")
        except AutonomousDeliveryError:
            pass
        else:
            raise AssertionError("unrelated identity did not fail closed")
        print("PASS: autonomous delivery ledger qualification (3 assertions)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
