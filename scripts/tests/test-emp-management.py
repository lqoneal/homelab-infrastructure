#!/usr/bin/env python3
"""Regression tests for EMP Phase 1.3 operational management services."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "scripts/lib/emp"
sys.path.insert(0, str(LIBRARY))

from management import ManagementServices  # noqa: E402
from registry import RegistryError, WorkRegistry  # noqa: E402


class ManagementServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.registry_path = Path(self.temporary.name) / "work-registry.yaml"
        shutil.copy2(ROOT / "engineering/registry/work-registry.yaml", self.registry_path)
        self.schema_path = ROOT / "engineering/registry/work-registry.schema.yaml"
        self.registry = WorkRegistry(self.registry_path, self.schema_path)
        self.service = ManagementServices(self.registry)
        self.initial_revision = self.registry.data["revision"]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def reload(self) -> ManagementServices:
        return ManagementServices(WorkRegistry(self.registry_path, self.schema_path))

    def test_registry_update_transition_create_and_archive_are_atomic(self) -> None:
        original = self.registry_path.read_bytes()
        with self.assertRaises(RegistryError):
            self.registry.transition(
                "EMP-WORK-PHASE-1-3", "completed", "test", "invalid direct completion"
            )
        self.assertEqual(original, self.registry_path.read_bytes())

        self.registry.update(
            "EMP-WORK-PHASE-1-3", "priority", 2, "test", "exercise controlled update"
        )
        service = self.reload()
        self.assertEqual(service.registry.objects["EMP-WORK-PHASE-1-3"]["priority"], 2)
        self.assertEqual(service.registry.data["revision"], self.initial_revision + 1)
        self.assertEqual(service.registry.data["mutation_history"][-1]["actor"], "test")

        project = {
            "registry_id": "EMP-PROJECT-TEST",
            "object_type": "Project",
            "title": "Test Project",
            "management_state": "planned",
            "owner": "EMP tests",
            "scope": "EMP-PORTFOLIO-0001",
            "authority_reference": None,
            "source_records": ["PROJ-0001"],
            "relationships": [],
            "created_at": "2026-07-13T00:00:00+00:00",
            "updated_at": "2026-07-13T00:00:00+00:00",
            "revision": 1,
            "transition_history": [{
                "from": None, "to": "planned", "at": "2026-07-13T00:00:00+00:00",
                "actor": "test", "reason": "registration test", "authority_reference": None,
            }],
            "slug": "test",
            "portfolio_id": "EMP-PORTFOLIO-0001",
            "order": 4,
            "repository": {"name": "test", "presence": "planned", "path": None},
        }
        service.registry.create("projects", project, "test", "registration test")
        service = self.reload()
        service.registry.archive("EMP-PROJECT-TEST", "test", "archive test fixture")
        archived = self.reload().registry.objects["EMP-PROJECT-TEST"]
        self.assertTrue(archived["archived"])

    def test_portfolio_project_and_queue_operations(self) -> None:
        self.service.portfolio_order("EMP-PROJECT-PRIVATE-AI-ASSISTANT", 2)
        service = self.reload()
        projects = service.portfolio_summary()["portfolios"][0]["projects"]
        self.assertEqual([project["registry_id"] for project in projects][1], "EMP-PROJECT-PRIVATE-AI-ASSISTANT")

        service.registry.transition(
            "EMP-PROJECT-HOMELAB", "on_hold", "test", "suspension test"
        )
        service = self.reload()
        service.registry.transition(
            "EMP-PROJECT-HOMELAB", "active", "test", "activation test", "PROJ-0001"
        )
        service = self.reload()
        service.reorder("EMP-QUEUE-PORTFOLIO-ROADMAP", "EMP-WORK-PRIVATE-AI-PRODUCT", 1)
        service = self.reload()
        self.assertEqual(
            service.queue_entries("EMP-QUEUE-PORTFOLIO-ROADMAP")[0]["work_item_id"],
            "EMP-WORK-PRIVATE-AI-PRODUCT",
        )
        service.dequeue("EMP-QUEUE-PORTFOLIO-ROADMAP", "EMP-WORK-SPRINTEROS-PRODUCT")
        service = self.reload()
        service.enqueue("EMP-QUEUE-PORTFOLIO-ROADMAP", "EMP-WORK-SPRINTEROS-PRODUCT", 2)
        service = self.reload()
        service.registry.update("EMP-WORK-PHASE-1-3", "priority", 3, "test", "reprioritize")
        self.assertEqual(self.reload().registry.objects["EMP-WORK-PHASE-1-3"]["priority"], 3)

    def test_dependency_milestone_deferral_and_status_operations(self) -> None:
        blockers = self.service.blocked_work()
        self.assertEqual(len(blockers), 1)
        qualification = self.service.milestone_qualification("EMP-MILESTONE-ROADMAP-COMPLETE")
        self.assertFalse(qualification["qualified"])

        milestone = {
            "registry_id": "EMP-MILESTONE-TEST",
            "object_type": "Milestone",
            "title": "Management Test Milestone",
            "management_state": "planned",
            "owner": "EMP tests",
            "scope": "EMP-PROJECT-HOMELAB",
            "authority_reference": None,
            "source_records": ["PROJ-0001"],
            "relationships": [{"type": "evidenced_by", "target": "PROJ-0001"}],
            "created_at": "2026-07-13T00:00:00+00:00",
            "updated_at": "2026-07-13T00:00:00+00:00",
            "revision": 1,
            "transition_history": [{
                "from": None, "to": "planned", "at": "2026-07-13T00:00:00+00:00",
                "actor": "test", "reason": "milestone test", "authority_reference": None,
            }],
            "scope_id": "EMP-PROJECT-HOMELAB",
            "success_criteria": "Regression test evidence exists.",
            "target_date": "2026-07-13",
            "evidence_records": ["PROJ-0001"],
        }
        self.service.registry.create("milestones", milestone, "test", "milestone test")
        service = self.reload()
        service.complete_milestone(
            "EMP-MILESTONE-TEST", "test", "milestone qualification test", "PROJ-0001"
        )
        service = self.reload()
        report = service.dependency_report(
            service.registry.objects["EMP-DEPENDENCY-PRIVATE-AI-ON-EMP"]
        )
        self.assertTrue(report["prerequisite_qualified"])
        self.assertFalse(report["satisfied"])
        service.registry.transition(
            "EMP-DEPENDENCY-PRIVATE-AI-ON-EMP", "satisfied", "test",
            "dependency satisfaction test", "PROJ-0001",
        )
        service = self.reload()
        service.resume_work(
            "EMP-WORK-PRIVATE-AI-PRODUCT", "proposed", "re-entry test", "test", "PROJ-0001"
        )
        service = self.reload()
        self.assertEqual(service.registry.objects["EMP-WORK-PRIVATE-AI-PRODUCT"]["management_state"], "proposed")
        self.assertEqual(service.deferral_history("EMP-WORK-PRIVATE-AI-PRODUCT")[0]["management_state"], "resolved")

        service.defer_work(
            "EMP-WORK-PRIVATE-AI-PRODUCT", "EMP-DEFERRAL-PRIVATE-AI-TEST", "deferral test",
            "explicit test re-entry", "test", "PROJ-0001",
        )
        service = self.reload()
        self.assertIn("EMP-WORK-PRIVATE-AI-PRODUCT", service.portfolio_status("EMP-PROJECT-PRIVATE-AI-ASSISTANT")["deferred_work"])
        service.resume_work(
            "EMP-WORK-PRIVATE-AI-PRODUCT", "ready", "resume test", "test", "PROJ-0001"
        )
        self.assertEqual(self.reload().registry.objects["EMP-WORK-PRIVATE-AI-PRODUCT"]["management_state"], "ready")

    def test_engctl_management_routes_use_configured_registry(self) -> None:
        environment = os.environ.copy()
        environment["EMP_REGISTRY_PATH"] = str(self.registry_path)
        environment["EMP_REGISTRY_SCHEMA_PATH"] = str(self.schema_path)
        commands = (
            ("portfolio", "summary"),
            ("project", "list"),
            ("queue", "validate"),
            ("dependency", "check"),
            ("milestone", "qualify", "EMP-MILESTONE-ROADMAP-COMPLETE"),
            ("defer", "history", "EMP-WORK-SPRINTEROS-PRODUCT"),
        )
        for arguments in commands:
            result = subprocess.run(
                [str(ROOT / "scripts/engctl"), *arguments],
                cwd=ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
