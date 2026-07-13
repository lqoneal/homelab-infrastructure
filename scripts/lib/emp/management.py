#!/usr/bin/env python3
"""Operational EMP services over the canonical Engineering Work Registry."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from registry import RegistryError, WorkRegistry, build_registry, load_mapping, timestamp


TERMINAL_PREREQUISITE_STATES = {"completed", "achieved", "satisfied", "waived"}


def default_actor() -> str:
    return os.environ.get("EMP_ACTOR") or os.environ.get("USER") or "EMP operator"


class ManagementServices:
    """One service facade; all writes delegate to WorkRegistry.mutate."""

    def __init__(self, registry: WorkRegistry) -> None:
        self.registry = registry
        self.registry.require_valid()

    @staticmethod
    def _visible(item: dict[str, Any]) -> bool:
        return not item.get("archived", False)

    def _require_project(self, project_id: str) -> dict[str, Any]:
        project = self.registry._require_object(project_id)
        if project.get("object_type") != "Project":
            raise RegistryError(f"not a project: {project_id}")
        return project

    def portfolio_summary(self) -> dict[str, Any]:
        portfolios = [item for item in self.registry.collections["portfolios"] if self._visible(item)]
        projects = [item for item in self.registry.collections["projects"] if self._visible(item)]
        return {
            "registry_revision": self.registry.data["revision"],
            "generated_at": str(self.registry.data["updated_at"]),
            "portfolios": [
                {
                    "registry_id": portfolio["registry_id"],
                    "title": portfolio["title"],
                    "management_state": portfolio["management_state"],
                    "projects": [
                        {
                            "registry_id": project["registry_id"],
                            "title": project["title"],
                            "management_state": project["management_state"],
                            "order": project["order"],
                        }
                        for project in sorted(projects, key=lambda value: (value["order"], value["registry_id"]))
                        if project["portfolio_id"] == portfolio["registry_id"]
                    ],
                }
                for portfolio in portfolios
            ],
            "authority_note": "Portfolio management state does not establish project authority.",
        }

    def portfolio_order(self, project_id: str, position: int) -> str:
        if position < 1:
            raise RegistryError("portfolio position must be positive")

        def operation(current: WorkRegistry) -> str:
            project = current._require_object(project_id)
            if project.get("object_type") != "Project":
                raise RegistryError(f"not a project: {project_id}")
            siblings = sorted(
                [
                    item for item in current.collections["projects"]
                    if item["portfolio_id"] == project["portfolio_id"] and not item.get("archived", False)
                ],
                key=lambda value: (value["order"], value["registry_id"]),
            )
            if position > len(siblings):
                raise RegistryError(f"portfolio position exceeds project count: {position}")
            siblings.remove(project)
            siblings.insert(position - 1, project)
            for order, item in enumerate(siblings, start=1):
                if item["order"] != order:
                    item["order"] = order
                    current._touch(item)
            return project_id

        return self.registry.mutate(operation)

    def queue_entries(self, queue_id: str) -> list[dict[str, Any]]:
        queue = self.registry._require_object(queue_id)
        if queue.get("object_type") != "Queue":
            raise RegistryError(f"not a queue: {queue_id}")
        return sorted(queue["entries"], key=lambda value: value["position"])

    @staticmethod
    def _normalize_queue(queue: dict[str, Any]) -> None:
        for position, entry in enumerate(queue["entries"], start=1):
            entry["position"] = position

    def enqueue(self, queue_id: str, work_id: str, position: int | None) -> str:
        def operation(current: WorkRegistry) -> str:
            queue = current._require_object(queue_id)
            work = current._require_object(work_id)
            if queue.get("object_type") != "Queue" or work.get("object_type") != "WorkItem":
                raise RegistryError("enqueue requires a queue and work item")
            if queue.get("management_state") != "active":
                raise RegistryError(f"queue is not active: {queue_id}")
            if queue_id in work["queue_ids"]:
                raise RegistryError(f"work item is already queued: {work_id}")
            insert_at = len(queue["entries"]) + 1 if position is None else position
            if insert_at < 1 or insert_at > len(queue["entries"]) + 1:
                raise RegistryError(f"invalid queue position: {insert_at}")
            queue["entries"].insert(insert_at - 1, {"position": insert_at, "work_item_id": work_id})
            self._normalize_queue(queue)
            work["queue_ids"].append(queue_id)
            work["queue_ids"].sort()
            current._touch(queue)
            current._touch(work)
            return work_id

        return self.registry.mutate(operation)

    def dequeue(self, queue_id: str, work_id: str) -> str:
        def operation(current: WorkRegistry) -> str:
            queue = current._require_object(queue_id)
            work = current._require_object(work_id)
            before = len(queue.get("entries", []))
            queue["entries"] = [entry for entry in queue.get("entries", []) if entry.get("work_item_id") != work_id]
            if len(queue["entries"]) == before or queue_id not in work.get("queue_ids", []):
                raise RegistryError(f"work item is not queued in {queue_id}: {work_id}")
            self._normalize_queue(queue)
            work["queue_ids"].remove(queue_id)
            current._touch(queue)
            current._touch(work)
            return work_id

        return self.registry.mutate(operation)

    def reorder(self, queue_id: str, work_id: str, position: int) -> str:
        def operation(current: WorkRegistry) -> str:
            queue = current._require_object(queue_id)
            entries = queue.get("entries", [])
            selected = next((entry for entry in entries if entry.get("work_item_id") == work_id), None)
            if selected is None:
                raise RegistryError(f"work item is not queued in {queue_id}: {work_id}")
            if position < 1 or position > len(entries):
                raise RegistryError(f"invalid queue position: {position}")
            entries.remove(selected)
            entries.insert(position - 1, selected)
            self._normalize_queue(queue)
            current._touch(queue)
            return work_id

        return self.registry.mutate(operation)

    def dependency_report(self, dependency: dict[str, Any]) -> dict[str, Any]:
        prerequisite = self.registry._require_object(dependency["prerequisite_id"])
        disposition = dependency["management_state"]
        prerequisite_qualified = prerequisite["management_state"] in TERMINAL_PREREQUISITE_STATES
        satisfied = disposition in {"satisfied", "waived"}
        return {
            "registry_id": dependency["registry_id"],
            "dependent_id": dependency["dependent_id"],
            "prerequisite_id": dependency["prerequisite_id"],
            "prerequisite_state": prerequisite["management_state"],
            "prerequisite_qualified": prerequisite_qualified,
            "management_state": disposition,
            "satisfied": satisfied,
            "blocks_work": disposition == "active" and not satisfied,
            "authority_note": "Dependency evaluation does not grant execution authority.",
        }

    def blocked_work(self, project_id: str | None = None) -> list[dict[str, Any]]:
        if project_id:
            self._require_project(project_id)
        reports = []
        for dependency in self.registry.collections["dependencies"]:
            if dependency.get("archived", False):
                continue
            report = self.dependency_report(dependency)
            if not report["blocks_work"]:
                continue
            if project_id and self.registry.project_for_object(report["dependent_id"]) != project_id:
                continue
            reports.append(report)
        return sorted(reports, key=lambda value: (value["dependent_id"], value["registry_id"]))

    def milestone_qualification(self, milestone_id: str) -> dict[str, Any]:
        milestone = self.registry._require_object(milestone_id)
        if milestone.get("object_type") != "Milestone":
            raise RegistryError(f"not a milestone: {milestone_id}")
        findings = []
        if milestone["management_state"] != "planned":
            findings.append("milestone is not planned")
        if not milestone.get("success_criteria"):
            findings.append("success criteria are absent")
        if not milestone.get("evidence_records"):
            findings.append("evidence records are absent")
        if milestone.get("scope_id") not in self.registry.objects:
            findings.append("scope does not resolve")
        return {
            "registry_id": milestone_id,
            "qualified": not findings,
            "findings": findings,
            "evidence_records": milestone.get("evidence_records", []),
            "authority_note": "Qualification projects evidence; it does not accept the engineering outcome.",
        }

    def complete_milestone(
        self, milestone_id: str, actor: str, reason: str, authority_reference: str
    ) -> str:
        if not authority_reference:
            raise RegistryError("milestone completion requires an authority reference")
        def operation(current: WorkRegistry) -> str:
            service = ManagementServices.__new__(ManagementServices)
            service.registry = current
            qualification = service.milestone_qualification(milestone_id)
            if not qualification["qualified"]:
                raise RegistryError("milestone is not qualified: " + "; ".join(qualification["findings"]))
            current._apply_transition(
                milestone_id, "achieved", actor, reason, authority_reference, service="milestone"
            )
            return milestone_id

        return self.registry.mutate(operation)

    def defer_work(
        self,
        work_id: str,
        deferral_id: str,
        reason: str,
        reentry_conditions: str,
        actor: str,
        authority_reference: str,
        target_horizon: str | None = None,
    ) -> str:
        if not deferral_id.startswith("EMP-DEFERRAL-"):
            raise RegistryError("deferral identifier must use EMP-DEFERRAL- prefix")

        def operation(current: WorkRegistry) -> str:
            work = current._require_object(work_id)
            if work.get("object_type") != "WorkItem":
                raise RegistryError(f"not a work item: {work_id}")
            if work["management_state"] in {"completed", "cancelled", "deferred"}:
                raise RegistryError(f"work item cannot be deferred from {work['management_state']}")
            if deferral_id in current.objects:
                raise RegistryError(f"registry_id already exists: {deferral_id}")
            current._apply_transition(
                work_id, "deferred", actor, reason, authority_reference, service="deferral"
            )
            now = timestamp()
            current.data["entities"]["deferrals"].append(
                {
                    "registry_id": deferral_id,
                    "object_type": "Deferral",
                    "title": f"Deferral of {work_id}",
                    "management_state": "active",
                    "owner": work["owner"],
                    "scope": work["scope"],
                    "authority_reference": authority_reference,
                    "source_records": list(work["source_records"]),
                    "relationships": [{"type": "related_to", "target": work_id}],
                    "created_at": now,
                    "updated_at": now,
                    "revision": 1,
                    "transition_history": [{
                        "from": None, "to": "active", "at": now, "actor": actor,
                        "reason": reason, "authority_reference": authority_reference,
                    }],
                    "work_item_id": work_id,
                    "reason": reason,
                    "reentry_conditions": reentry_conditions,
                    "target_horizon": target_horizon,
                    "resolution_reference": None,
                }
            )
            return deferral_id

        return self.registry.mutate(operation)

    def resume_work(
        self,
        work_id: str,
        target_state: str,
        reason: str,
        actor: str,
        authority_reference: str,
    ) -> str:
        def operation(current: WorkRegistry) -> str:
            active = [
                item for item in current.collections["deferrals"]
                if item["work_item_id"] == work_id and item["management_state"] == "active"
            ]
            if len(active) != 1:
                raise RegistryError(f"work item must have one active deferral: {work_id}")
            blockers = [
                item["registry_id"] for item in current.collections["dependencies"]
                if item["dependent_id"] == work_id and item["management_state"] == "active"
            ]
            if blockers:
                raise RegistryError("re-entry blocked by active dependencies: " + ",".join(sorted(blockers)))
            deferral = active[0]
            deferral["resolution_reference"] = authority_reference
            current._apply_transition(
                deferral["registry_id"], "resolved", actor, reason, authority_reference,
                service="deferral",
            )
            current._apply_transition(
                work_id, target_state, actor, reason, authority_reference, service="deferral"
            )
            return work_id

        return self.registry.mutate(operation)

    def deferral_history(self, work_id: str) -> list[dict[str, Any]]:
        return sorted(
            [item for item in self.registry.collections["deferrals"] if item["work_item_id"] == work_id],
            key=lambda value: (str(value["created_at"]), value["registry_id"]),
        )

    def portfolio_status(self, project_id: str | None = None) -> dict[str, Any]:
        if project_id:
            self._require_project(project_id)
        work = [
            item for item in self.registry.collections["work_items"]
            if self._visible(item)
            and (project_id is None or item["project_id"] == project_id)
        ]
        blocked = {item["registry_id"] for item in work if item["management_state"] == "blocked"}
        blocked.update(report["dependent_id"] for report in self.blocked_work(project_id))

        def selected(states: set[str]) -> list[str]:
            return sorted(item["registry_id"] for item in work if item["management_state"] in states)

        return {
            "registry_revision": self.registry.data["revision"],
            "generated_at": str(self.registry.data["updated_at"]),
            "scope": project_id or "portfolio",
            "active_work": selected({"active"}),
            "planned_work": selected({"proposed", "ready"}),
            "deferred_work": selected({"deferred"}),
            "blocked_work": sorted(blocked),
            "completed_work": selected({"completed"}),
            "authority_note": "Status is derived only from registry state and grants no authority.",
        }


def dump(value: Any) -> None:
    print(yaml.safe_dump(value, sort_keys=False).rstrip())


def list_objects(service: ManagementServices, collection: str) -> None:
    print("registry_id\tmanagement_state\ttitle")
    for _, item in service.registry.iter_objects(collection):
        if service._visible(item):
            print(f"{item['registry_id']}\t{item['management_state']}\t{item['title']}")


def parser_for(command: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, prog=f"engctl {command}")
    actions = parser.add_subparsers(dest="action") if command != "status" else None
    if command == "portfolio":
        actions.add_parser("summary")
        actions.add_parser("status")
        order = actions.add_parser("order")
        order.add_argument("project_id")
        order.add_argument("position", type=int)
    elif command == "project":
        actions.add_parser("list")
        register = actions.add_parser("register")
        register.add_argument("record", type=Path)
        for name in ("activate", "suspend"):
            transition = actions.add_parser(name)
            transition.add_argument("project_id")
            transition.add_argument("reason")
            transition.add_argument("--authority-reference")
    elif command == "queue":
        actions.add_parser("list")
        actions.add_parser("validate")
        show = actions.add_parser("show")
        show.add_argument("queue_id")
        enqueue = actions.add_parser("enqueue")
        enqueue.add_argument("queue_id"); enqueue.add_argument("work_id")
        enqueue.add_argument("position", nargs="?", type=int)
        dequeue = actions.add_parser("dequeue")
        dequeue.add_argument("queue_id"); dequeue.add_argument("work_id")
        reorder = actions.add_parser("reorder")
        reorder.add_argument("queue_id"); reorder.add_argument("work_id"); reorder.add_argument("position", type=int)
        priority = actions.add_parser("reprioritize")
        priority.add_argument("work_id"); priority.add_argument("priority", type=int)
    elif command == "dependency":
        actions.add_parser("list"); actions.add_parser("validate")
        check = actions.add_parser("check"); check.add_argument("dependency_id", nargs="?")
        blocked = actions.add_parser("blocked"); blocked.add_argument("project_id", nargs="?")
        satisfy = actions.add_parser("satisfy")
        satisfy.add_argument("dependency_id"); satisfy.add_argument("reason")
        satisfy.add_argument("--authority-reference", required=True)
    elif command == "milestone":
        actions.add_parser("list")
        for name in ("get", "status", "qualify"):
            child = actions.add_parser(name); child.add_argument("milestone_id")
        complete = actions.add_parser("complete")
        complete.add_argument("milestone_id"); complete.add_argument("reason")
        complete.add_argument("--authority-reference", required=True)
    elif command == "defer":
        actions.add_parser("list"); actions.add_parser("validate")
        apply = actions.add_parser("apply")
        apply.add_argument("work_id"); apply.add_argument("deferral_id")
        apply.add_argument("reason"); apply.add_argument("reentry_conditions")
        apply.add_argument("--authority-reference", required=True); apply.add_argument("--target-horizon")
        resume = actions.add_parser("resume")
        resume.add_argument("work_id"); resume.add_argument("reason")
        resume.add_argument("--target-state", choices=("proposed", "ready"), default="proposed")
        resume.add_argument("--authority-reference", required=True)
        history = actions.add_parser("history"); history.add_argument("work_id")
    elif command == "status":
        parser.add_argument("project_id", nargs="?")
    return parser


def main() -> int:
    if len(sys.argv) < 2:
        print("FAIL: management command required", file=sys.stderr)
        return 1
    command = sys.argv[1]
    parser = parser_for(command)
    args = parser.parse_args(sys.argv[2:])
    actor = default_actor()
    try:
        service = ManagementServices(build_registry())
        action = getattr(args, "action", None)
        if command == "portfolio":
            if action in (None, "summary"): dump(service.portfolio_summary())
            elif action == "status": dump(service.portfolio_status())
            elif action == "order": print(service.portfolio_order(args.project_id, args.position))
        elif command == "project":
            if action in (None, "list"): list_objects(service, "projects")
            elif action == "register": print(service.registry.create("projects", load_mapping(args.record, "project record"), actor, "Project registration"))
            elif action == "activate": print(service.registry.transition(args.project_id, "active", actor, args.reason, args.authority_reference))
            elif action == "suspend": print(service.registry.transition(args.project_id, "on_hold", actor, args.reason, args.authority_reference))
        elif command == "queue":
            if action in (None, "list"): list_objects(service, "queues")
            elif action == "validate": service.registry.require_valid(); print("PASS: deterministic queue membership and ordering")
            elif action == "show": dump(service.queue_entries(args.queue_id))
            elif action == "enqueue": print(service.enqueue(args.queue_id, args.work_id, args.position))
            elif action == "dequeue": print(service.dequeue(args.queue_id, args.work_id))
            elif action == "reorder": print(service.reorder(args.queue_id, args.work_id, args.position))
            elif action == "reprioritize":
                if args.priority < 1: raise RegistryError("priority must be positive")
                print(service.registry.update(args.work_id, "priority", args.priority))
        elif command == "dependency":
            if action in (None, "list"): list_objects(service, "dependencies")
            elif action == "validate": service.registry.require_valid(); print("PASS: dependency endpoints and active graph")
            elif action == "check":
                dependencies = service.registry.collections["dependencies"]
                if args.dependency_id: dependencies = [service.registry._require_object(args.dependency_id)]
                dump([service.dependency_report(item) for item in dependencies])
            elif action == "blocked": dump(service.blocked_work(args.project_id))
            elif action == "satisfy":
                dependency = service.registry._require_object(args.dependency_id)
                report = service.dependency_report(dependency)
                if not report["prerequisite_qualified"]: raise RegistryError("dependency prerequisite is not qualified")
                print(service.registry.transition(args.dependency_id, "satisfied", actor, args.reason, args.authority_reference))
        elif command == "milestone":
            if action in (None, "list"): list_objects(service, "milestones")
            elif action in ("get", "status"): dump(service.registry._require_object(args.milestone_id))
            elif action == "qualify": dump(service.milestone_qualification(args.milestone_id))
            elif action == "complete": print(service.complete_milestone(args.milestone_id, actor, args.reason, args.authority_reference))
        elif command == "defer":
            if action in (None, "list"): list_objects(service, "deferrals")
            elif action == "validate": service.registry.require_valid(); print("PASS: deferral state and re-entry records")
            elif action == "apply": print(service.defer_work(args.work_id, args.deferral_id, args.reason, args.reentry_conditions, actor, args.authority_reference, args.target_horizon))
            elif action == "resume": print(service.resume_work(args.work_id, args.target_state, args.reason, actor, args.authority_reference))
            elif action == "history": dump(service.deferral_history(args.work_id))
        elif command == "status": dump(service.portfolio_status(args.project_id))
        else:
            raise RegistryError(f"unknown management command: {command}")
    except RegistryError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
