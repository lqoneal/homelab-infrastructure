"""Zeus-owned reconciliation of Codex session and listener projections.

The controller is intentionally small and fail-closed.  It inventories only
receipt-backed session records, validates recorded process identity before any
signal is sent, and writes reconciliation receipts through Zeus.  A dry run
never mutates runtime state; mutation requires explicit operator approval.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import socket
import time
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.production_execution import atomic_write, digest, load_json


RECEIPT_DIR = "codex-reconciliation-receipts"
SESSION_DIRS = ("codex-sessions", "codex-interactive-sessions")
PROCESS_FIELDS = ("pid", "provider_pid", "listener_pid", "remote_client_pid")
TERMINAL_STATES = {"STOPPED", "FAILED", "DETACHED", "INTERRUPTED"}
ACTIVE_STATES = {"ACTIVE", "ATTACHED", "ATTACHING", "READY", "RESUMED",
                 "THREAD_READY", "AWAITING_OPERATOR_INPUT", "TURN_ACTIVE",
                 "INTERACTIVE_SESSION_OPEN"}
CONTROLLER_VERSION = 2
IDENTITY_SCHEMA_VERSION = 2
LISTENER_RE = re.compile(r"(?P<endpoint>ws://127\.0\.0\.1:\d+)")


class ReconciliationError(ValueError):
    def __init__(self, code: str, message: str, *, next_action: str = "STOP_FAIL_CLOSED"):
        self.code, self.message, self.next_action = code, message, next_action
        super().__init__(message)


def _runtime(root: Path, runtime_root: Path | str | None) -> Path:
    if runtime_root is None:
        from scripts.lib.emp.runtime_paths import resolve_runtime
        return Path(resolve_runtime(root, require_writable=False)["root"]).resolve()
    runtime = Path(runtime_root).resolve()
    try:
        runtime.relative_to(root)
    except ValueError:
        return runtime
    raise ReconciliationError("RUNTIME_INSIDE_REPOSITORY", "runtime must not be inside the repository")


def process_identity(pid: Any) -> dict[str, Any]:
    """Return the one canonical Linux process identity used by Zeus.

    ``/proc/<pid>/stat`` start time is clock ticks since boot.  It is never
    compared with a wall-clock timestamp.  ``starttime`` remains as a legacy
    alias in the returned object so old receipts can still be inspected.
    """
    if not isinstance(pid, int) or pid <= 0:
        return {"pid": pid, "alive": False, "identity": "INVALID"}
    proc = Path("/proc") / str(pid)
    try:
        stat = (proc / "stat").read_text(encoding="utf-8")
        fields = stat.rsplit(")", 1)[1].split()
        start_ticks = int(fields[19])
        process_group = int(fields[2])
        ppid = int(fields[1])
        session_id = int(fields[3])
        executable = os.readlink(proc / "exe")
        command = (proc / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace").strip()
        state = fields[0]
    except (OSError, IndexError, ValueError):
        return {"pid": pid, "alive": False, "identity": "NOT_RUNNING"}
    # Process state changes from running to sleeping without changing identity;
    # keep it observable but exclude it from the stable identity digest.
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError:
        boot_id = None
    command_digest = hashlib.sha256(command.encode()).hexdigest()
    material = {"boot_id": boot_id, "pid": pid, "process_start_ticks": start_ticks,
                "executable": executable, "command_digest": command_digest,
                "process_group": process_group}
    # A zombie has a /proc entry but is no longer a live listener process.
    return {**material, "ppid": ppid, "session_id": session_id, "command_line": command, "command": command,
            "starttime": str(start_ticks), "process_state": state, "state": state,
            "alive": state != "Z", "process_identity_digest":
            hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest(),
            "identity": hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()}


def _canonical_identity(value: Mapping[str, Any] | None) -> dict[str, Any]:
    value = value or {}
    ticks = value.get("process_start_ticks", value.get("starttime", value.get("start_time")))
    try:
        ticks = int(ticks) if ticks is not None else None
    except (TypeError, ValueError):
        ticks = None
    command = value.get("command_line", value.get("command", ""))
    command_digest = value.get("command_digest") or value.get("command_digest_sha256")
    if not command_digest and command:
        command_digest = hashlib.sha256(str(command).encode()).hexdigest()
    return {"boot_id": value.get("boot_id"), "pid": value.get("pid"),
            "process_start_ticks": ticks, "executable": value.get("executable"),
            "command_digest": command_digest, "process_group": value.get("process_group"),
            "endpoint_uri": value.get("endpoint_uri"),
            "process_identity_digest": value.get("process_identity_digest", value.get("identity"))}


def _start_time_match(expected: Mapping[str, Any] | None, observed: Mapping[str, Any] | None) -> str:
    if not observed or not observed.get("alive"):
        return "FAIL"
    if not expected:
        return "UNAVAILABLE"
    expected_id = _canonical_identity(expected)
    observed_id = _canonical_identity(observed)
    if expected_id.get("process_start_ticks") is not None:
        if expected_id.get("process_start_ticks") != observed_id.get("process_start_ticks"):
            return "FAIL"
        if expected_id.get("boot_id") and expected_id.get("boot_id") != observed_id.get("boot_id"):
            return "FAIL"
        return "PASS"
    # Legacy receipts are recoverable only if all available immutable evidence
    # agrees.  A wall-clock timestamp is deliberately not used as a tick value.
    if expected_id.get("boot_id") and expected_id["boot_id"] != observed_id.get("boot_id"):
        return "FAIL"
    if expected_id.get("pid") not in (None, observed_id.get("pid")):
        return "FAIL"
    if expected_id.get("process_group") not in (None, observed_id.get("process_group")):
        return "FAIL"
    if expected_id.get("command_digest") and expected_id["command_digest"] != observed_id.get("command_digest"):
        return "FAIL"
    return "RECOVERED_PASS" if expected_id.get("pid") or expected_id.get("process_group") else "FAIL"


def _identity_matches(expected: Mapping[str, Any] | None, observed: Mapping[str, Any]) -> str:
    if not observed.get("alive"):
        return "NOT_RUNNING"
    if not expected:
        return "UNVERIFIED"
    expected_id, observed_id = _canonical_identity(expected), _canonical_identity(observed)
    if _start_time_match(expected, observed) == "FAIL":
        return "FAIL"
    checks = ("pid", "executable", "process_group", "command_digest")
    return "PASS" if all(not expected_id.get(key) or expected_id.get(key) == observed_id.get(key)
                          for key in checks) else "FAIL"


def _process_identity_result(expected: Mapping[str, Any] | None,
                             observed: Mapping[str, Any] | None) -> str:
    """Classify availability separately from ownership qualification."""
    if not observed or not observed.get("alive"):
        return "UNAVAILABLE"
    required = ("boot_id", "pid", "process_start_ticks", "executable",
                "command_digest", "process_group", "process_identity_digest")
    if any(observed.get(key) in (None, "") for key in required):
        return "UNAVAILABLE"
    if expected is None:
        return "VERIFIED"
    match = _identity_matches(expected, observed)
    if match == "PASS":
        return "VERIFIED" if _start_time_match(expected, observed) == "PASS" else "RECOVERED_VERIFIED"
    if _start_time_match(expected, observed) == "FAIL":
        return "MISMATCH"
    return "PARTIAL"


def _resolve_codex_home(value: Mapping[str, Any], receipt: Mapping[str, Any] | None = None,
                        ready_receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    candidates = [("session.codex_home", value.get("codex_home")),
                  ("endpoint_receipt.environment.codex_home", (receipt or {}).get("environment", {}).get("codex_home")),
                  ("ready_receipt.environment.codex_home", (ready_receipt or {}).get("environment", {}).get("codex_home"))]
    command = str(value.get("command_line", value.get("command", "")))
    match = re.search(r"(?:--codex-home|CODEX_HOME=)(?:=|\s+)([^\s]+)", command)
    if match:
        candidates.append(("broker.command_line", match.group(1)))
    for source, path in candidates:
        if path:
            return {"codex_home": str(path), "codex_home_source": source,
                    "codex_home_source_digest": digest({"source": source, "value": str(path)})}
    return {"codex_home": None, "codex_home_source": None, "codex_home_source_digest": None}


def _socket_open(endpoint: str | None) -> bool:
    if not endpoint:
        return False
    match = re.match(r"ws://127\.0\.0\.1:(\d+)", endpoint)
    if not match:
        return False
    try:
        with socket.create_connection(("127.0.0.1", int(match.group(1))), timeout=0.25):
            return True
    except OSError:
        return False


def _discover_listeners() -> list[dict[str, Any]]:
    """Discover loopback Codex listeners, including records absent from Zeus."""
    listeners: list[dict[str, Any]] = []
    proc_root = Path("/proc")
    for directory in proc_root.iterdir() if proc_root.is_dir() else ():
        if not directory.name.isdigit():
            continue
        observed = process_identity(int(directory.name))
        if not observed.get("alive"):
            continue
        for match in LISTENER_RE.finditer(str(observed.get("command", ""))):
            listeners.append({"endpoint_uri": match.group("endpoint"), "listener_pid": int(directory.name),
                              "child_pid": int(directory.name), "process_group": observed.get("process_group"),
                              "command_line": observed.get("command"), "start_time": observed.get("starttime"),
                              "process_identity": observed, "socket_listening": _socket_open(match.group("endpoint"))})
    return listeners


def _termination_units(listeners: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize all listener observations into one unit per endpoint.

    A broker, Node launcher, and native child may expose the same endpoint.
    They are one controlled Zeus termination unit, never three independent
    actions.  The unit retains every member identity for pre-signal checks.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for listener in listeners:
        grouped.setdefault(str(listener["endpoint_uri"]), []).append(listener)
    units: list[dict[str, Any]] = []
    for endpoint, members in sorted(grouped.items()):
        expanded = list(members)
        known = {int(item["listener_pid"]) for item in members}
        for seed in list(members):
            for child in _process_tree(seed.get("listener_pid")):
                child_pid = int(child.get("pid", 0))
                command = str(child.get("command_line", child.get("command", "")))
                if child_pid in known or not ("codex" in command or "node" in command or "app-server" in command):
                    continue
                expanded.append({"endpoint_uri": endpoint, "listener_pid": child_pid,
                                 "child_pid": child_pid, "process_group": child.get("process_group"),
                                 "command_line": command, "process_identity": child})
                known.add(child_pid)
        members = expanded
        identities = [item.get("process_identity", {}) for item in members]
        member_pids = sorted({int(item["listener_pid"]) for item in members})
        groups = sorted({int(item["process_group"]) for item in members if item.get("process_group")})
        member_by_pid = {int(item["listener_pid"]): item for item in members}
        roots = sorted(pid for pid, item in member_by_pid.items()
                       if item.get("process_identity", {}).get("ppid") not in member_by_pid)
        listener_members = [item for item in members
                            if "--listen" in str(item.get("command_line", ""))]
        listener_pid = min((int(item["listener_pid"]) for item in listener_members), default=member_pids[0])
        broker = [item for item in members if "codex_app_server_broker" in str(item.get("command_line", ""))]
        units.append({"endpoint_uri": endpoint, "listener_pid": listener_pid,
                      "child_pid": listener_pid, "root_pids": roots or [listener_pid],
                      "process_groups": groups, "process_group": groups[0] if len(groups) == 1 else None,
                      "member_pids": member_pids, "member_processes": identities,
                      "broker_pid": int(broker[0]["listener_pid"]) if broker else None,
                      "listener_root_pid": listener_pid,
                      "command_line": " | ".join(sorted({str(item.get("command_line", "")) for item in members})),
                      "start_time": member_by_pid.get(listener_pid, {}).get("start_time"),
                      "process_identity": member_by_pid.get(listener_pid, {}).get("process_identity", {}),
                      "socket_listening": any(item.get("socket_listening") for item in members),
                      "termination_unit_id": "P5G6-UNIT-" + digest({"endpoint": endpoint,
                                                                      "groups": groups,
                                                                      "members": member_pids})[:16]})
    return units


def _ownership(value: Mapping[str, Any], observed: Mapping[str, Any] | None,
               endpoint: str | None, repository: Path,
               *, members: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    receipt = value.get("endpoint_receipt") if isinstance(value.get("endpoint_receipt"), Mapping) else {}
    expected_endpoint = value.get("endpoint_uri") or value.get("remote_endpoint") or receipt.get("endpoint_uri")
    home = _resolve_codex_home(value, receipt, value.get("ready_receipt"))
    expected = value.get("listener_process_identity") or receipt.get("listener_process_identity")
    start_result = _start_time_match(expected, observed)
    observed_id = _canonical_identity(observed)
    expected_id = _canonical_identity(expected)
    member_values = list(members or ([observed] if observed else []))
    role = "broker" if observed and ("codex_app_server_broker" in str(observed.get("command_line", observed.get("command", "")))
                                     or "python" in str(observed.get("executable", ""))) else "listener"
    endpoint_process = str(observed.get("command_line", observed.get("command", ""))) if observed else ""
    command_ok = ("app-server" in endpoint_process and "--listen" in endpoint_process)
    executable_ok = bool(observed and ("node" in str(observed.get("executable", ""))
                                       or "codex" in str(observed.get("executable", ""))
                                       or "/codex" in endpoint_process
                                       or role == "broker"))
    receipt_environment = receipt.get("environment", {}) if isinstance(receipt, Mapping) else {}
    transaction_result = "UNAVAILABLE"
    if value.get("endpoint_creation_transaction_id") and receipt.get("endpoint_creation_transaction_id") == value.get("endpoint_creation_transaction_id"):
        transaction_result = "PASS"
    elif receipt.get("endpoint_uri") == endpoint and (receipt.get("endpoint_owner_session_id") or value.get("session_id")):
        transaction_result = "RECOVERED_PASS"
    home_match = bool(home["codex_home"] and (
        home["codex_home"] == value.get("codex_home") or
        home["codex_home"] == receipt_environment.get("codex_home") or
        home["codex_home"] in endpoint_process or
        any(home["codex_home"] in str(member.get("command_line", member.get("command", "")))
            for member in member_values)))
    unit_command_match = command_ok or any("app-server" in str(member.get("command_line", member.get("command", "")))
                                      and "--listen" in str(member.get("command_line", member.get("command", "")))
                                      and endpoint in str(member.get("command_line", member.get("command", "")))
                                      for member in member_values)
    checks = {
        "pid_exists": bool(observed and observed.get("alive")),
        "boot_id_matches": (not expected_id.get("boot_id") or expected_id.get("boot_id") == observed_id.get("boot_id")),
        "start_time_matches": start_result in {"PASS", "RECOVERED_PASS"},
        "start_time_result": start_result,
        "executable_matches": executable_ok,
        "command_line_matches": unit_command_match,
        "command_digest_matches": (not expected_id.get("command_digest") or
                                     expected_id.get("command_digest") == observed_id.get("command_digest")),
        "endpoint_matches": bool(endpoint and expected_endpoint == endpoint),
        "repository_identity_matches": (receipt_environment.get("cwd") == str(repository)
                                         or value.get("repository") == str(repository)),
        "codex_home_matches": home_match,
        "transaction_matches": transaction_result in {"PASS", "RECOVERED_PASS"},
        "transaction_result": transaction_result,
        "process_group_matches": (not expected_id.get("process_group") or
                                   expected_id.get("process_group") == observed_id.get("process_group")),
        "ownership_receipt": bool(receipt and receipt.get("result") == "PASS"),
    }
    identity = _process_identity_result(expected, observed)
    checks["process_identity"] = {"result": identity, "role": role,
                                   "canonical": observed_id, "schema_version": IDENTITY_SCHEMA_VERSION}
    # Evidence is intentionally split into immutable identity, recoverable
    # legacy metadata, and availability.  Missing ticks/transactions in old
    # receipts are not PID-reuse evidence and must not become mismatches.
    immutable = ("pid_exists", "boot_id_matches", "endpoint_matches",
                 "command_digest_matches", "process_group_matches")
    recoverable = ("start_time_matches", "executable_matches", "command_line_matches",
                   "repository_identity_matches", "codex_home_matches", "ownership_receipt",
                   "transaction_matches")
    conflicts = [key for key in immutable if checks.get(key) is False]
    immutable_conflict = (start_result == "FAIL" or checks.get("boot_id_matches") is False or
                          checks.get("command_digest_matches") is False or
                          checks.get("endpoint_matches") is False or
                          checks.get("process_group_matches") is False or identity == "MISMATCH")
    if start_result == "FAIL" and "start_time_matches" not in conflicts:
        conflicts.append("start_time_matches")
    if identity == "MISMATCH" and "process_identity" not in conflicts:
        conflicts.append("process_identity")
    missing = [key for key in recoverable if checks.get(key) is not True]
    recoverable_evidence = [key for key in recoverable if checks.get(key) is True]
    recovered = bool(missing) or start_result == "RECOVERED_PASS" or transaction_result == "RECOVERED_PASS" or not expected_id.get("boot_id")
    # A receipt-backed endpoint with a live, coherent process tree is enough
    # to recover legacy fields.  The receipt itself remains evidence; no
    # historical value is fabricated.
    core_evidence = all(checks.get(key) is True for key in (
        "pid_exists", "endpoint_matches", "executable_matches",
        "command_line_matches", "repository_identity_matches", "codex_home_matches",
        "process_group_matches", "ownership_receipt", "transaction_matches"))
    if not checks.get("endpoint_matches") and expected_endpoint == endpoint:
        checks["endpoint_matches"] = True
        core_evidence = all(checks.get(key) is True for key in (
            "pid_exists", "endpoint_matches", "executable_matches",
            "command_line_matches", "repository_identity_matches", "codex_home_matches",
            "process_group_matches", "ownership_receipt", "transaction_matches"))
    if immutable_conflict:
        result = "OWNERSHIP_MISMATCH"
    elif core_evidence and identity in {"VERIFIED", "RECOVERED_VERIFIED"}:
        result = "OWNERSHIP_RECOVERED_VERIFIED" if recovered else "OWNERSHIP_VERIFIED"
    elif checks["pid_exists"] and any(checks.get(key) is True for key in immutable):
        result = "OWNERSHIP_PARTIAL"
    else:
        result = "OWNERSHIP_UNKNOWN"
    promotion_reason = []
    if result == "OWNERSHIP_RECOVERED_VERIFIED":
        promotion_reason = ["LEGACY_EVIDENCE_RECOVERED"] + [key for key in missing if key != "transaction_matches"]
        if transaction_result == "RECOVERED_PASS":
            promotion_reason.append("LEGACY_TRANSACTION_RECOVERED")
    missing_evidence = [key for key in recoverable if checks.get(key) is not True]
    report = {"boot_id_result": "PASS" if checks.get("boot_id_matches") else "FAIL",
              "start_tick_result": start_result, "transaction_result": transaction_result,
              "command_result": "PASS" if checks.get("command_line_matches") else "UNAVAILABLE",
              "codex_home_result": "PASS" if checks.get("codex_home_matches") else "UNAVAILABLE",
              "endpoint_result": "PASS" if checks.get("endpoint_matches") else "FAIL",
              "process_tree_result": "PASS" if checks.get("process_group_matches") else "FAIL",
              "process_identity_result": identity,
              "session_binding_result": "PASS" if checks.get("transaction_matches") else transaction_result,
              "missing_evidence": missing_evidence,
              "recoverable_evidence": recoverable_evidence,
              "immutable_conflicts": conflicts,
              "promotion_reason": sorted(set(promotion_reason))}
    return {"result": result, "checks": checks, "codex_home": home,
            "recovered_fields": (["boot_id"] if not expected_id.get("boot_id") else []),
            "ownership_report": report, "missing_evidence": missing_evidence,
            "recoverable_evidence": recoverable_evidence,
            "immutable_conflicts": conflicts, "promotion_reason": report["promotion_reason"]}


def _dimensions(value: Mapping[str, Any], listener: Mapping[str, Any] | None,
                ownership: Mapping[str, Any]) -> dict[str, Any]:
    endpoint = value.get("endpoint_uri") or value.get("remote_endpoint")
    listener_alive = bool(listener and listener.get("process_identity", {}).get("alive"))
    socket_listening = bool(listener and listener.get("socket_listening"))
    client_pid = value.get("remote_client_pid")
    client_alive = bool(process_identity(client_pid).get("alive")) if isinstance(client_pid, int) else False
    diagnostic = bool(endpoint and value.get("remote_client_pid") is None and
                      (value.get("endpoint_receipt") or {}).get("readiness_probe", {}).get("initialize") == "PASS")
    if diagnostic:
        session_state, client_state, attachment_state, provider_state = "COMPLETED_DIAGNOSTIC", "NOT_LAUNCHED", "NOT_APPLICABLE", "READY" if listener_alive else "STOPPED"
        recommended = "STOP_DIAGNOSTIC" if listener_alive else "NONE"
    elif listener_alive and client_alive:
        session_state, client_state, attachment_state, provider_state, recommended = "ACTIVE", "RUNNING", "ATTACHED", "READY", "NONE"
    elif listener_alive:
        session_state, client_state, attachment_state, provider_state, recommended = "DETACHED", "EXITED", "DETACHED", "READY", "ATTACH_OR_STOP"
    else:
        session_state, client_state, attachment_state, provider_state, recommended = "STOPPED", "EXITED_OR_STOPPED", "NOT_APPLICABLE", "STOPPED", "NONE"
    return {"session_state": session_state, "client_state": client_state,
            "listener_state": "READY" if listener_alive else "STOPPED",
            "attachment_state": attachment_state, "provider_state": provider_state,
            "listener_alive": listener_alive, "socket_listening": socket_listening,
            "recommended_disposition": recommended, "session_next_authorized_action":
            "ATTACH_OR_STOP" if session_state == "DETACHED" else
            ("STOP_DIAGNOSTIC" if recommended == "STOP_DIAGNOSTIC" else "BEGIN_CONTROLLED_MISSION_WORK"),
            "ownership_result": ownership.get("result"), "endpoint_uri": endpoint,
            "remote_client_pid": client_pid}


def _load_record(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = load_json(path)
        supplied = value.get("state_digest")
        unsigned = {key: item for key, item in value.items() if key != "state_digest"}
        if supplied != digest(unsigned):
            return None, "DIGEST_MISMATCH"
        return value, None
    except (OSError, ValueError, json.JSONDecodeError):
        return None, "MALFORMED_RECORD"


def _record_digest(value: Mapping[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "state_digest"}
    return digest(unsigned)


def _inventory(runtime: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for directory_name in SESSION_DIRS:
        directory = runtime / directory_name
        for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
            value, error = _load_record(path)
            if error:
                entries.append({"path": str(path), "record_type": directory_name,
                                "disposition": "ORPHAN_CORRUPT_RECORD", "reason": error,
                                "eligible_for_mutation": False})
                continue
            assert value is not None
            processes = []
            for field in PROCESS_FIELDS:
                pid = value.get(field)
                if not isinstance(pid, int) or pid <= 0:
                    continue
                observed = process_identity(pid)
                match = _identity_matches(value.get(f"{field}_identity"), observed)
                processes.append({"field": field, "pid": pid, "observed": observed,
                                  "identity_validation": match})
            state = value.get("state")
            live = [item for item in processes if item["observed"].get("alive")]
            verified_live = [item for item in live if item["identity_validation"] == "PASS"]
            unverified_live = [item for item in live if item["identity_validation"] != "PASS"]
            if unverified_live:
                disposition, eligible, reason = "ORPHAN_IDENTITY_UNVERIFIED", False, "live process identity is not receipt-bound"
            elif state in ACTIVE_STATES and verified_live:
                disposition, eligible, reason = "RETAIN_ACTIVE", False, "active receipt-bound process"
            elif verified_live and state in TERMINAL_STATES | {None}:
                disposition, eligible, reason = "ORPHAN_LIVE_PROCESS", True, "terminal session retains a live receipt-bound process"
            elif state in ACTIVE_STATES and not live:
                disposition, eligible, reason = "ORPHAN_STALE_SESSION", False, "active receipt has no live process"
            else:
                disposition, eligible, reason = "RECONCILED", False, "no live process remains"
            entries.append({"path": str(path), "session_id": value.get("session_id"),
                            "mission_id": value.get("mission_id"), "state": state,
                            "record_type": directory_name, "record_digest": _record_digest(value),
                            "processes": processes, "disposition": disposition,
                            "reason": reason, "eligible_for_mutation": eligible})
    by_mission: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        mission = entry.get("mission_id")
        if mission:
            by_mission.setdefault(str(mission), []).append(entry)
    for mission, matches in by_mission.items():
        if len(matches) > 1:
            for entry in matches:
                entry["cardinality_conflict"] = {"mission_id": mission, "observed": len(matches), "required": 1}
                entry["disposition"] = "ORPHAN_CARDINALITY_CONFLICT"
                entry["eligible_for_mutation"] = False
                entry["reason"] = "more than one session record claims the same mission"
    return entries


def _inventory_v2(runtime: Path, repository: Path) -> dict[str, Any]:
    """Build the published post-publication inventory projection."""
    records: list[dict[str, Any]] = []
    paths: dict[str, Path] = {}
    listeners = _termination_units(_discover_listeners())
    for directory_name in SESSION_DIRS:
        directory = runtime / directory_name
        for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
            value, error = _load_record(path)
            if error or value is None:
                continue
            endpoint = value.get("endpoint_uri") or value.get("remote_endpoint")
            if not endpoint or value.get("execution_mode") != "REMOTE_INTERACTIVE":
                continue
            paths[str(value.get("session_id"))] = path
            listener_pid = value.get("listener_pid") or value.get("provider_pid") or value.get("pid")
            observed = process_identity(listener_pid) if isinstance(listener_pid, int) else None
            endpoint_listener = None
            for candidate in listeners:
                if candidate["endpoint_uri"] == endpoint or (listener_pid and candidate["listener_pid"] == listener_pid):
                    endpoint_listener = candidate
                    break
            owner = _ownership(value, endpoint_listener["process_identity"] if endpoint_listener else observed,
                               endpoint, repository,
                               members=(endpoint_listener or {}).get("member_processes"))
            dimensions = _dimensions(value, endpoint_listener, owner)
            record = {"session_id": value.get("session_id"), "mission_id": value.get("mission_id"),
                      "execution_mode": value.get("execution_mode"), "provider_mode": value.get("provider_mode"),
                      "session_state": dimensions["session_state"], "client_state": dimensions["client_state"],
                      "listener_state": dimensions["listener_state"], "attachment_state": dimensions["attachment_state"],
                      "provider_state": dimensions["provider_state"], "endpoint_uri": endpoint,
                      "listener_pid": listener_pid, "remote_client_pid": value.get("remote_client_pid"),
                      "listener_alive": dimensions["listener_alive"], "socket_listening": dimensions["socket_listening"],
                      "ownership_result": owner["result"], "ownership": owner,
                      "recommended_disposition": dimensions["recommended_disposition"],
                      "session_next_authorized_action": dimensions["session_next_authorized_action"],
                      "process_group": (endpoint_listener or {}).get("process_group") or value.get("process_group"),
                      "process_groups": (endpoint_listener or {}).get("process_groups", []),
                      "member_pids": (endpoint_listener or {}).get("member_pids", [listener_pid]),
                      "root_pids": (endpoint_listener or {}).get("root_pids", [listener_pid]),
                      "termination_unit_id": (endpoint_listener or {}).get("termination_unit_id"),
                      "command_line": (endpoint_listener or {}).get("command_line"),
                      "start_time": (endpoint_listener or {}).get("start_time"),
                      "codex_home": value.get("codex_home"), "ready_receipt": value.get("endpoint_receipt"),
                      "exit_receipt": value.get("exit_receipt"), "path": str(path),
                      "record_digest": _record_digest(value)}
            record["_value"] = value
            records.append(record)
    termination_units = _canonical_termination_units(runtime, repository, records, listeners)
    endpoints = {item["endpoint_uri"] for item in records}
    owned = [item for item in termination_units if item["endpoint_uri"] in endpoints]
    orphan_listeners = [item for item in termination_units if item["endpoint_uri"] not in endpoints]
    remote_active = [item for item in records if item["listener_alive"] and item["recommended_disposition"] != "STOP_DIAGNOSTIC"]
    preserved_orphans = [item for item in termination_units
                         if item.get("classification") == "HISTORICAL_OPERATIONAL_ORPHAN"
                         and item.get("ownership_result") not in {"OWNERSHIP_VERIFIED", "OWNERSHIP_RECOVERED_VERIFIED"}]
    verified_orphans = [item for item in termination_units
                        if item.get("classification") == "HISTORICAL_OPERATIONAL_ORPHAN"
                        and item.get("ownership_result") in {"OWNERSHIP_VERIFIED", "OWNERSHIP_RECOVERED_VERIFIED"}]
    detached = [item for item in records if item["listener_alive"] and item["session_state"] == "DETACHED"]
    diagnostic_active = [item for item in records
                         if item["listener_alive"] and item["recommended_disposition"] == "STOP_DIAGNOSTIC"]
    cardinality = {"result": "PASS" if len(remote_active) <= 1 else "CONFLICT",
                   "observed": len(remote_active), "required_maximum": 1,
                   "remote_active_sessions": len(remote_active),
                   "active_remote_sessions": len(remote_active),
                   "detached_remote_sessions": len(detached),
                   "diagnostic_listeners_active": len(diagnostic_active),
                   "preserved_orphan_listeners": len(preserved_orphans),
                   "verified_owned_orphan_listeners": len(verified_orphans),
                   "unknown_orphan_listeners": sum(item.get("ownership_result") in {"OWNERSHIP_UNKNOWN", "OWNERSHIP_MISMATCH"}
                                                   for item in preserved_orphans)}
    return {"runtime_root": str(runtime), "matching_sessions": records, "live_listeners": termination_units,
            "termination_units": termination_units, "owned_listeners": owned,
            "orphan_listeners": orphan_listeners,
            "stale_sessions": [item for item in records if item["session_state"] == "STOPPED" and item["listener_alive"]],
            "detached_sessions": [item for item in records if item["session_state"] == "DETACHED"],
            "diagnostic_sessions": [item for item in records if item["recommended_disposition"] == "STOP_DIAGNOSTIC"],
            "cardinality": cardinality, "preserved_orphan_listeners": preserved_orphans,
            "verified_owned_orphan_listeners": verified_orphans, "paths": paths}


def _receipt_path(runtime: Path, reconciliation_id: str) -> Path:
    return runtime / RECEIPT_DIR / f"{reconciliation_id}.json"


def _reconciliation_id(entries: list[dict[str, Any]]) -> str:
    material = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return "CODEX-RECON-" + hashlib.sha256(material.encode()).hexdigest()[:24]


def _jsonable(value: Any) -> Any:
    """Remove internal record handles before hashing or returning a plan."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items() if key != "_value"}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


_VOLATILE_PLAN_KEYS = {"at", "timestamp", "generated_at", "duration", "reconciled_at",
                       "temporary_report_path", "identity_validation_time", "state",
                       "process_state", "alive", "starttime", "command", "command_line"}


def _stable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _stable(item) for key, item in value.items()
                if key not in _VOLATILE_PLAN_KEYS and key != "_value"}
    if isinstance(value, (list, tuple)):
        return [_stable(item) for item in value]
    return value


def _stable_digest(value: Any) -> str:
    return digest(_stable(value))


def _process_tree(pid: int | None) -> list[dict[str, Any]]:
    if not isinstance(pid, int) or pid <= 0:
        return []
    values = {item["pid"]: item for item in (_process_identity_safe(p) for p in _proc_pids())
              if item.get("alive")}
    result: list[dict[str, Any]] = []
    pending = [pid]
    seen: set[int] = set()
    while pending:
        current = pending.pop(0)
        if current in seen:
            continue
        seen.add(current)
        item = values.get(current) or process_identity(current)
        if item.get("alive"):
            result.append(item)
        pending.extend(item["pid"] for item in values.values() if item.get("ppid") == current)
    return result


def _proc_pids() -> list[int]:
    root = Path("/proc")
    return [int(item.name) for item in root.iterdir() if item.name.isdigit()] if root.is_dir() else []


def _process_identity_safe(pid: int) -> dict[str, Any]:
    try:
        return process_identity(pid)
    except OSError:
        return {"pid": pid, "alive": False}


def _historical_orphan_ownership(runtime: Path, orphan: Mapping[str, Any], repository: Path) -> dict[str, Any]:
    """Find receipt-backed evidence for a listener with no current session record."""
    endpoint = orphan.get("endpoint_uri")
    pid = orphan.get("listener_pid")

    def contains_pid(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(str(value.get(key)) == str(pid)
                       for key in ("pid", "listener_pid", "provider_pid", "child_pid", "socket_owner_pid")) \
                or any(contains_pid(item) for item in value.values())
        if isinstance(value, list):
            return any(contains_pid(item) for item in value)
        return False

    evidence: list[dict[str, Any]] = []
    for path in runtime.rglob("*.json") if runtime.is_dir() else ():
        try:
            value = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        text = json.dumps(value, sort_keys=True, default=str)
        if endpoint and endpoint not in text and not contains_pid(value):
            continue
        receipt = value.get("endpoint_receipt") if isinstance(value, Mapping) else None
        if isinstance(value, Mapping) and (value.get("endpoint_uri") == endpoint or value.get("remote_endpoint") == endpoint):
            receipt = receipt or value
        if isinstance(receipt, Mapping) and receipt.get("result") == "PASS":
            environment = receipt.get("environment", {})
            if environment.get("cwd") == str(repository) or value.get("repository") == str(repository):
                evidence.append({"path": str(path), "receipt": receipt, "session_id": value.get("session_id")})
    if not evidence:
        return {"result": "OWNERSHIP_UNKNOWN", "evidence": []}
    receipt = evidence[0]["receipt"]
    resolved_home = _resolve_codex_home({"endpoint_receipt": receipt}, receipt)
    value = {"endpoint_uri": endpoint, "remote_endpoint": endpoint,
             "repository": str(repository), "codex_home": resolved_home.get("codex_home"),
             "endpoint_receipt": receipt,
             "endpoint_creation_transaction_id": receipt.get("endpoint_creation_transaction_id"),
             "listener_process_identity": receipt.get("listener_process_identity")}
    owner = _ownership(value, orphan.get("process_identity"), endpoint, repository,
                       members=orphan.get("member_processes"))
    owner["evidence"] = evidence
    owner["legacy_recovery"] = not bool(_canonical_identity(value.get("listener_process_identity")).get("process_start_ticks"))
    owner["recovery_sources"] = [item["path"] for item in evidence]
    return owner


def _canonical_termination_units(runtime: Path, repository: Path,
                                 records: list[dict[str, Any]],
                                 listeners: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach lifecycle and ownership semantics to the endpoint units."""
    by_endpoint = {str(item["endpoint_uri"]): item for item in records}
    units: list[dict[str, Any]] = []
    for listener in listeners:
        endpoint = str(listener["endpoint_uri"])
        record = by_endpoint.get(endpoint)
        if record:
            owner = record["ownership"]
            session_id = record.get("session_id")
            historical_session_id = None
            if record.get("recommended_disposition") == "STOP_DIAGNOSTIC":
                classification, recommended, required_action = "COMPLETED_DIAGNOSTIC", "STOP_DIAGNOSTIC", "STOP_DIAGNOSTIC_LISTENER"
            elif record.get("session_state") == "DETACHED":
                classification, recommended, required_action = "RETAINED_DETACHED_SESSION", "ATTACH_OR_STOP", None
            else:
                classification, recommended, required_action = "BOUND_OPERATIONAL_SESSION", record.get("recommended_disposition"), None
        else:
            owner = _historical_orphan_ownership(runtime, listener, repository)
            evidence = owner.get("evidence", [])
            historical_session_id = next((item.get("session_id") for item in evidence if item.get("session_id")), None)
            session_id = None
            classification = "HISTORICAL_OPERATIONAL_ORPHAN"
            recommended = "STOP_ORPHAN_ENDPOINT" if owner["result"] in {"OWNERSHIP_VERIFIED", "OWNERSHIP_RECOVERED_VERIFIED"} else "PRESERVE_TARGET"
            required_action = "STOP_ORPHAN_ENDPOINT" if owner["result"] in {"OWNERSHIP_VERIFIED", "OWNERSHIP_RECOVERED_VERIFIED"} else "PRESERVE_TARGET"
        process_tree_digest = digest(_jsonable(sorted((_canonical_identity(item) for item in listener.get("member_processes", [])),
                                                       key=lambda item: int(item.get("pid", 0)))))
        unit = {key: listener.get(key) for key in (
            "termination_unit_id", "endpoint_uri", "root_pids", "member_pids", "process_groups",
            "broker_pid", "listener_root_pid", "socket_listening", "member_processes")}
        unit.update({"classification": classification, "session_id": session_id,
                     "historical_session_id": historical_session_id,
                     "socket_owner_pid": listener.get("listener_pid"),
                     "process_tree_digest": process_tree_digest,
                     "ownership_result": owner.get("result"),
                     "ownership": owner,
                     "ownership_report": owner.get("ownership_report", {}),
                     "missing_evidence": owner.get("missing_evidence", []),
                     "recoverable_evidence": owner.get("recoverable_evidence", []),
                     "immutable_conflicts": owner.get("immutable_conflicts", []),
                     "promotion_reason": owner.get("promotion_reason", []),
                     "ownership_evidence_digest": _stable_digest(owner),
                     "recommended_disposition": recommended,
                     "required_action": required_action,
                     "required_action_enabled": required_action is not None,
                     "listener_pid": listener.get("listener_pid"),
                     "process_identity": listener.get("process_identity", {}),
                     "process_group": listener.get("process_group"),
                     "command_line": listener.get("command_line")})
        units.append(unit)
    return sorted(units, key=lambda item: (str(item.get("endpoint_uri")), str(item.get("termination_unit_id"))))


def _action_plan(projection: Mapping[str, Any], repository: Path, target_session_id: str | None) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for unit in projection.get("termination_units", []):
        if target_session_id and unit.get("session_id") != target_session_id:
            continue
        if not unit.get("required_action_enabled"):
            continue
        ownership = unit.get("ownership", {})
        allowed_ownership = unit.get("ownership_result") in {"OWNERSHIP_VERIFIED", "OWNERSHIP_RECOVERED_VERIFIED"}
        action_type = unit["required_action"] if allowed_ownership else (
            "PRESERVE_IDENTITY_MISMATCH" if unit.get("ownership_result") == "OWNERSHIP_MISMATCH" else "PRESERVE_TARGET")
        action = {"action_type": action_type, "target_type": "TERMINATION_UNIT",
                  "termination_unit_id": unit["termination_unit_id"],
                  "session_id": unit.get("session_id"), "historical_session_id": unit.get("historical_session_id"),
                  "listener_pid": unit.get("listener_pid"), "child_pid": unit.get("listener_pid"),
                  "root_pids": unit.get("root_pids", []), "process_groups": unit.get("process_groups", []),
                  "member_pids": unit.get("member_pids", []), "process_group": unit.get("process_group"),
                  "endpoint_uri": unit["endpoint_uri"], "ownership_result": unit["ownership_result"],
                  "ownership": ownership, "ownership_evidence_digest": unit.get("ownership_evidence_digest"),
                  "process_tree_digest": unit.get("process_tree_digest"),
                  "identity_digest": _canonical_identity(unit.get("process_identity", {})).get("process_identity_digest"),
                  "precondition_digest": _stable_digest({"unit": unit, "classification": unit.get("classification")}),
                  "current_state": {"listener_state": "READY" if unit.get("socket_listening") else "ORPHANED",
                                    "socket_listening": unit.get("socket_listening")},
                  "desired_state": {"listener_state": "STOPPED", "socket_listening": False},
                  "authority": "ZEUS_CONTROLLER", "requires_approval": True,
                  "allowed": allowed_ownership}
        actions.append(action)
    actions.sort(key=lambda item: (str(item.get("endpoint_uri")), str(item.get("termination_unit_id"))))
    for index, action in enumerate(actions, 1):
        stable = {key: action.get(key) for key in ("termination_unit_id", "endpoint_uri", "session_id",
                                                   "action_type", "member_pids", "process_groups",
                                                   "precondition_digest", "ownership_evidence_digest")}
        action["action_id"] = f"P5G6-ACTION-{index:04d}-{digest(_jsonable(stable))[:12]}"
    return actions


def _plan_blockers(actions: list[dict[str, Any]]) -> list[str]:
    if not actions:
        return []
    if any(item.get("allowed") for item in actions):
        return []
    return ["OWNERSHIP_QUALIFICATION_REQUIRED", "PLAN_NOT_EXECUTABLE"]


def _plan_digest(projection: Mapping[str, Any], actions: list[dict[str, Any]],
                 repository: Path, mode: str | None) -> tuple[str, dict[str, Any]]:
    units = []
    for unit in projection.get("termination_units", []):
        units.append({key: unit.get(key) for key in (
            "termination_unit_id", "endpoint_uri", "classification", "session_id",
            "historical_session_id", "root_pids", "member_pids", "process_groups",
            "broker_pid", "listener_root_pid", "socket_owner_pid", "process_tree_digest",
            "ownership_result", "ownership_evidence_digest", "recommended_disposition",
            "required_action", "required_action_enabled")})
    payload = {"plan_schema_version": 1, "controller_version": CONTROLLER_VERSION,
               "execution_mode": mode or "REMOTE_INTERACTIVE",
               "repository": str(repository), "runtime_root": projection.get("runtime_root"),
               "policy": "ONE_DETACHED_OR_ZERO", "termination_units": units,
               "proposed_actions": [{key: action.get(key) for key in (
                   "action_id", "action_type", "termination_unit_id", "endpoint_uri", "session_id",
                   "historical_session_id", "root_pids", "member_pids", "process_groups",
                   "ownership_result", "ownership_evidence_digest", "process_tree_digest",
                   "identity_digest", "precondition_digest", "allowed", "desired_state")}
                                    for action in actions],
               "blockers": _plan_blockers(actions)}
    return digest(payload), payload


def _update_session_record(path: Path, receipt: Mapping[str, Any], new_state: Mapping[str, Any]) -> bool:
    value, error = _load_record(path)
    if error or value is None:
        return False
    previous = {key: value.get(key) for key in ("state", "process_alive", "listener_alive", "socket_listening",
                                                "remote_client_state", "session_state", "client_state", "listener_state",
                                                "attachment_state", "provider_state")}
    value.update(new_state)
    value.update({"lifecycle_schema_version": 2, "legacy_state_preserved": True,
                  "reconciled_from_legacy": True, "reconciliation_id": receipt["reconciliation_id"],
                  "reconciled_at": time.time(), "previous_projection": previous,
                  "current_projection": dict(new_state)})
    value.pop("state_digest", None)
    value["state_digest"] = digest(value)
    try:
        atomic_write(path, value)
        return True
    except OSError:
        return False


def _verify_terminal(projection: Mapping[str, Any], actions: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    unresolved: list[dict[str, Any]] = []
    live_by_endpoint = {item["endpoint_uri"]: item for item in projection["live_listeners"]}
    for action in actions:
        if action["action_type"].startswith("PRESERVE_"):
            unresolved.append({"action_id": action["action_id"], "target": action["endpoint_uri"],
                               "reason": "ownership is not verified"})
        elif action["action_type"] in {"STOP_LISTENER", "STOP_DIAGNOSTIC_LISTENER", "STOP_ORPHAN_ENDPOINT", "STOP_ORPHAN_LISTENER"} and action["endpoint_uri"] in live_by_endpoint:
            unresolved.append({"action_id": action["action_id"], "target": action["endpoint_uri"],
                               "reason": "listener remains live"})
    diagnostics = [item for item in projection["matching_sessions"] if item["recommended_disposition"] == "STOP_DIAGNOSTIC"]
    if diagnostics:
        unresolved.extend({"target": item["endpoint_uri"], "reason": "diagnostic listener remains active"} for item in diagnostics)
    return not unresolved and projection["cardinality"]["result"] == "PASS", unresolved


def _preserved_targets(projection: Mapping[str, Any], actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return non-mutated targets as explicit dispositions, never failed mutations."""
    units = {item.get("termination_unit_id"): item for item in projection.get("termination_units", [])}
    preserved = []
    for action in actions:
        if not action.get("action_type", "").startswith("PRESERVE_"):
            continue
        unit = units.get(action.get("termination_unit_id"), {})
        preserved.append({
            "termination_unit_id": action.get("termination_unit_id"),
            "endpoint_uri": action.get("endpoint_uri"),
            "classification": unit.get("classification"),
            "ownership_result": action.get("ownership_result"),
            "preservation_reason": "OWNERSHIP_PARTIAL" if action.get("ownership_result") == "OWNERSHIP_PARTIAL" else action.get("action_type"),
            "required_missing_evidence": unit.get("missing_evidence", []),
            "recoverable_evidence": unit.get("recoverable_evidence", []),
            "immutable_conflicts": unit.get("immutable_conflicts", []),
            "operator_action_available": False,
            "next_authorized_action": "RECONCILE_HISTORICAL_OWNERSHIP_OR_ACCEPT_PRESERVATION",
        })
    return preserved


def _find_receipt_by_plan_digest(runtime: Path, plan_digest: str | None) -> tuple[Path, dict[str, Any]] | None:
    matches = _completed_receipt_matches(runtime, plan_digest)
    return matches[0] if len(matches) == 1 else None


def _completed_receipt_matches(runtime: Path, plan_digest: str | None) -> list[tuple[Path, dict[str, Any]]]:
    """Return successful authoritative mutation receipts for a historical plan."""
    if not plan_digest:
        return []
    receipt_dir = runtime / RECEIPT_DIR
    if not receipt_dir.is_dir():
        return []
    matches = []
    for path in sorted(receipt_dir.glob("CODEX-RECON-*.json")):
        try:
            value = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if (value.get("controller_version") == CONTROLLER_VERSION and
                value.get("plan_digest") == plan_digest and
                value.get("operator_approved") and
                (value.get("reconciliation_applied") or
                 any(item.get("result") == "PASS" for item in value.get("actions_completed", [])))):
            matches.append((path, value))
    return matches


def _replay_failure_response(root: Path, runtime: Path, projection: Mapping[str, Any],
                             actions: list[dict[str, Any]], current_plan_digest: str,
                             *, requested_plan_digest: str, replay_result: str, blocker: str) -> dict[str, Any]:
    """Return a non-mutating replay lookup failure with current-state context."""
    receipt = {"result": "FAIL", "plan_digest": current_plan_digest,
               "proposed_actions": _jsonable(actions), "blockers": [blocker],
               "termination_units": _jsonable(projection.get("termination_units", [])),
               "matching_sessions": projection.get("matching_sessions", []),
               "live_listeners": projection.get("live_listeners", []),
               "cardinality": projection.get("cardinality", {}),
               "preserved_targets": _preserved_targets(projection, actions),
               "reconciliation_applied": False, "reconciliation_required": False,
               "reconciliation_fully_converged": False}
    return _response(root, runtime, projection, actions, receipt, replay=True,
                     read_only=False, current_plan_digest=current_plan_digest,
                     requested_plan_digest=requested_plan_digest,
                     replay_result=replay_result)


def _has_applied_reconciliation(runtime: Path) -> bool:
    """Report whether this runtime has an earlier successful mutation receipt."""
    receipt_dir = runtime / RECEIPT_DIR
    if not receipt_dir.is_dir():
        return False
    for path in sorted(receipt_dir.glob("CODEX-RECON-*.json")):
        try:
            value = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if not value.get("operator_approved"):
            continue
        if value.get("reconciliation_applied"):
            return True
        if any(item.get("result") == "PASS" for item in value.get("actions_completed", [])):
            return True
    return False


def reconcile(repository: Path | str, *, runtime_root: Path | str | None = None,
              approve: bool = False, terminate: bool = True, mode: str | None = None,
              dry_run: bool | None = None, target_session_id: str | None = None,
              expected_plan_digest: str | None = None) -> dict[str, Any]:
    """Inventory or explicitly reconcile one controller-owned runtime."""
    root = Path(repository).resolve()
    runtime = _runtime(root, runtime_root)
    if dry_run is None:
        dry_run = not approve
    if dry_run:
        approve = False
    projection = _inventory_v2(runtime, root)
    if not projection["matching_sessions"] and not projection["live_listeners"]:
        if expected_plan_digest and expected_plan_digest != digest([]):
            raise ReconciliationError("PLAN_STALE", "runtime changed since the reviewed plan was created",
                                      next_action="RUN_NEW_DRY_RUN")
        return _legacy_reconcile(root, runtime, approve=approve)
    actions = _action_plan(projection, root, target_session_id)
    plan_digest, plan_payload = _plan_digest(projection, actions, root, mode)
    if approve and not expected_plan_digest:
        raise ReconciliationError("PLAN_DIGEST_MISSING", "approved reconciliation requires the reviewed plan digest",
                                  next_action="RUN_NEW_DRY_RUN")
    if expected_plan_digest and expected_plan_digest != plan_digest:
        # A completed reviewed transaction may be replayed after its action has
        # disappeared from the live plan.  Bind the replay to the old digest,
        # but never re-enter the mutation loop.
        prior_matches = _completed_receipt_matches(runtime, expected_plan_digest)
        if approve and len(prior_matches) == 1:
            prior_path, prior_receipt = prior_matches[0]
            return _response(root, runtime, projection, actions, prior_receipt, replay=True, read_only=False,
                             current_plan_digest=plan_digest, requested_plan_digest=expected_plan_digest,
                             completed_receipt_path=prior_path, replay_result="IDEMPOTENT")
        if approve and not prior_matches:
            return _replay_failure_response(root, runtime, projection, actions, plan_digest,
                                             requested_plan_digest=expected_plan_digest,
                                             replay_result="NOT_FOUND",
                                             blocker="COMPLETED_RECONCILIATION_RECEIPT_NOT_FOUND")
        if approve:
            return _replay_failure_response(root, runtime, projection, actions, plan_digest,
                                             requested_plan_digest=expected_plan_digest,
                                             replay_result="CONFLICT",
                                             blocker="COMPLETED_RECONCILIATION_RECEIPT_CONFLICT")
        raise ReconciliationError("PLAN_DIGEST_MISMATCH", "runtime changed since the reviewed plan was created",
                                  next_action="RUN_NEW_DRY_RUN")
    reconciliation_id = "CODEX-RECON-" + plan_digest[:24]
    receipt_path = _receipt_path(runtime, reconciliation_id)
    if receipt_path.is_file():
        prior = load_json(receipt_path)
        if prior.get("controller_version") == CONTROLLER_VERSION and prior.get("plan_digest") == plan_digest:
            return _response(root, runtime, projection, actions, prior, replay=True, read_only=not approve,
                             current_plan_digest=plan_digest, requested_plan_digest=plan_digest,
                             completed_receipt_path=receipt_path, replay_result="IDEMPOTENT")
    phases = [{"phase": "RECONCILIATION_REQUEST_ACCEPTED", "at": time.time()},
              {"phase": "APPROVAL_VERIFIED", "at": time.time(), "approved": approve},
              {"phase": "PLAN_LOADED", "at": time.time(), "plan_digest": plan_digest},
              {"phase": "PLAN_DIGEST_VERIFIED", "at": time.time(), "result": "PASS"},
              {"phase": "ACTION_SET_RESOLVED", "at": time.time(), "count": len(actions)}]
    attempted: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    updated: list[str] = []
    if approve and terminate:
        for action in actions:
            if action["action_type"].startswith("PRESERVE_") or not action["allowed"]:
                skipped.append({"action_id": action["action_id"], "target": action["endpoint_uri"],
                                "skip_reason": "OWNERSHIP_NOT_VERIFIED", "authority_result": action["authority"],
                                "ownership_result": action["ownership_result"], "current_state": action["current_state"],
                                "requested_state": action["desired_state"]})
                continue
            attempted.append(action)
            phases.append({"phase": "TARGET_IDENTITY_REVALIDATION_STARTED", "at": time.time(), "action_id": action["action_id"]})
            observed = process_identity(action["listener_pid"])
            expected_digest = action.get("identity_digest")
            members_before = {pid: process_identity(pid) for pid in action.get("member_pids", [action["listener_pid"]])
                              if isinstance(pid, int)}
            member_groups = {item.get("process_group") for item in members_before.values() if item.get("alive")}
            groups_expected = set(action.get("process_groups", [])) - {None}
            identity_ok = (observed.get("alive") and
                           (not expected_digest or observed.get("process_identity_digest", observed.get("identity")) == expected_digest) and
                           (not groups_expected or groups_expected.issuperset(member_groups)))
            if not identity_ok:
                failed.append({"action_id": action["action_id"], "blocker": "TARGET_IDENTITY_REVALIDATION_FAILED",
                               "identity_validation_time": time.time(), "expected_identity": expected_digest,
                               "actual_identity": observed, "member_identities": members_before})
                phases.append({"phase": "TARGET_IDENTITY_REVALIDATION_PASSED", "at": time.time(), "action_id": action["action_id"], "result": "FAIL"})
                continue
            phases.append({"phase": "TARGET_IDENTITY_REVALIDATION_PASSED", "at": time.time(), "action_id": action["action_id"], "result": "PASS"})
            tree_before = [item for pid in action.get("member_pids", [action["listener_pid"]])
                           for item in _process_tree(pid)]
            tree_before = {item["pid"]: item for item in tree_before}.values()
            tree_before = list(tree_before)
            phases.append({"phase": "MUTATION_STARTED", "at": time.time(), "action_id": action["action_id"]})
            signal_sequence = ["SIGTERM"]
            try:
                groups = sorted({int(group) for group in action.get("process_groups", []) if isinstance(group, int) and group > 0})
                if not groups and isinstance(action.get("process_group"), int):
                    groups = [action["process_group"]]
                if groups:
                    for group in groups:
                        os.killpg(group, signal.SIGTERM)
                else:
                    os.kill(action["listener_pid"], signal.SIGTERM)
                phases.append({"phase": "SIGNAL_SENT", "at": time.time(), "action_id": action["action_id"], "signal": "SIGTERM"})
            except (ProcessLookupError, OSError) as error:
                failed.append({"action_id": action["action_id"], "blocker": "LISTENER_TERMINATION_FAILED", "error": str(error)})
                continue
            phases.append({"phase": "PROCESS_EXIT_WAIT_STARTED", "at": time.time(), "action_id": action["action_id"]})
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline and any(process_identity(pid).get("alive")
                                                     for pid in action.get("member_pids", [action["listener_pid"]])):
                time.sleep(0.03)
            tree_after = [process_identity(pid) for pid in action.get("member_pids", [action["listener_pid"]])
                          if process_identity(pid).get("alive")]
            exited = not tree_after
            phases.append({"phase": "PROCESS_EXIT_CONFIRMED", "at": time.time(), "action_id": action["action_id"], "result": exited})
            socket_closed = not _socket_open(action["endpoint_uri"])
            phases.append({"phase": "SOCKET_CLOSURE_CONFIRMED", "at": time.time(), "action_id": action["action_id"], "result": socket_closed})
            mutation = {"reconciliation_id": reconciliation_id, "action_id": action["action_id"],
                        "session_id": action.get("session_id"), "listener_pid": action["listener_pid"],
                        "endpoint_uri": action["endpoint_uri"], "ownership_result": action["ownership_result"],
                        "identity_validation_result": "PASS", "signal_sequence": signal_sequence,
                        "target_processes": [item["pid"] for item in tree_before],
                        "pre_signal_process_tree": tree_before, "post_signal_process_tree": tree_after,
                        "process_exit_result": exited, "socket_closure_result": socket_closed,
                        "previous_state": action["current_state"], "new_state": action["desired_state"],
                        "action": action["action_type"], "result": "PASS" if exited and socket_closed else "FAIL",
                        "replay": "NEW", "timestamp": time.time(), "authority": "ZEUS_CONTROLLER",
                        "operator_approval": True}
            if mutation["result"] != "PASS":
                failed.append({"action_id": action["action_id"], "blocker": "SOCKET_CLOSURE_FAILED" if exited else "LISTENER_TERMINATION_FAILED", "receipt": mutation})
                continue
            phases.append({"phase": "SESSION_RECORD_UPDATE_STARTED", "at": time.time(), "action_id": action["action_id"]})
            record_path = projection["paths"].get(action.get("session_id"))
            state = {"state": "STOPPED", "process_alive": False, "listener_alive": False,
                     "remote_client_state": "NOT_LAUNCHED", "session_state": "STOPPED",
                     "client_state": "NOT_LAUNCHED", "listener_state": "STOPPED",
                     "attachment_state": "NOT_APPLICABLE", "provider_state": "STOPPED",
                     "socket_listening": False, "session_next_authorized_action": "NONE"}
            state["reconciliation_receipt_consumed"] = True
            if record_path and not _update_session_record(record_path, {"reconciliation_id": reconciliation_id}, state):
                failed.append({"action_id": action["action_id"], "blocker": "SESSION_STATE_UPDATE_FAILED", "receipt": mutation})
                continue
            if record_path:
                updated.append(action["session_id"])
            phases.append({"phase": "SESSION_RECORD_UPDATE_COMPLETED", "at": time.time(), "action_id": action["action_id"]})
            mutation["replay"] = "IDEMPOTENT"
            completed.append(mutation)
            action_receipt_path = runtime / RECEIPT_DIR / f"{reconciliation_id}-{action['action_id']}.json"
            try:
                action_receipt_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(action_receipt_path, mutation)
            except OSError as error:
                failed.append({"action_id": action["action_id"], "blocker": "RECEIPT_PERSISTENCE_FAILED", "error": str(error)})
                completed.pop()
    elif not approve:
        phases.append({"phase": "READ_ONLY_INVENTORY", "at": time.time(), "result": "PASS"})
    post = _inventory_v2(runtime, root) if approve and terminate else projection
    terminal, unresolved = _verify_terminal(post, actions) if approve else (not actions, [])
    blockers = _plan_blockers(actions) if not approve else []
    notices: list[str] = []
    preserved_targets = _preserved_targets(post if approve and terminate else projection, actions)
    if approve:
        if not actions:
            terminal = True
        if skipped:
            blockers.append("UNRESOLVED_PARTIAL_OWNERSHIP_TARGETS")
            blockers.extend("PARTIAL_OWNERSHIP_TARGET_" + str(item["endpoint_uri"]).rsplit(":", 1)[-1]
                            for item in preserved_targets if item.get("ownership_result") == "OWNERSHIP_PARTIAL")
            if not attempted and not completed:
                blockers.append("RECONCILIATION_NOT_APPLIED")
        if failed:
            blockers.extend(item["blocker"] for item in failed)
        if unresolved:
            blockers.append("TERMINAL_STATE_NOT_REACHED")
    executable_count = sum(bool(item.get("allowed")) for item in actions)
    preserved_only = bool(preserved_targets) and executable_count == 0 and all(
        item.get("action_type", "").startswith("PRESERVE_") for item in actions
    )
    prior_reconciliation_applied = _has_applied_reconciliation(runtime)
    if not approve:
        if executable_count:
            result = "BLOCKED_PENDING_APPROVAL"
        elif preserved_only:
            # Preserved targets are an explicit safe disposition, not failed
            # mutation attempts.  Strict convergence remains independently
            # visible through reconciliation_fully_converged/terminal_state.
            result = "PASS"
            blockers = []
            notices.append("PRESERVED_TARGETS_REMAIN")
        elif not actions and not blockers:
            result = "PASS"
        else:
            result = "FAIL"
    else:
        result = "PASS" if terminal and not failed and not skipped else ("PARTIAL" if completed and not failed else "FAIL")
    reconciliation_applied_this_invocation = bool(completed or updated)
    reconciliation_already_applied = bool(prior_reconciliation_applied)
    reconciliation_applied = bool(reconciliation_applied_this_invocation or
                                  reconciliation_already_applied)
    fully_converged = bool(terminal and not failed and not skipped)
    if approve and reconciliation_applied and not fully_converged and "RECONCILIATION_NOT_APPLIED" in blockers:
        blockers.remove("RECONCILIATION_NOT_APPLIED")
    phases.extend([{"phase": "POST_MUTATION_INVENTORY_STARTED", "at": time.time()},
                   {"phase": "POST_MUTATION_INVENTORY_COMPLETED", "at": time.time(), "remaining": len(post["live_listeners"])},
                   {"phase": "TERMINAL_STATE_VERIFIED", "at": time.time(), "result": terminal},
                   {"phase": "RECONCILIATION_COMPLETED", "at": time.time(), "result": result}])
    receipt = {"controller_version": CONTROLLER_VERSION, "schema_version": 2, "plan_schema_version": 1,
               "contract": "ZEUS-P5-G6-CODEX-RECONCILIATION",
               "reconciliation_id": reconciliation_id, "repository": str(root), "runtime_root": str(runtime),
               "read_only": not approve, "operator_approved": approve, "execution_mode": mode or "REMOTE_INTERACTIVE",
               "plan_digest_algorithm": "SHA256", "plan_digest": plan_digest,
               "plan_digest_match": "PASS", "reviewed_plan_digest": expected_plan_digest,
               "reviewed_plan": plan_payload, "policy": "ONE_DETACHED_OR_ZERO",
               "matching_sessions": projection["matching_sessions"], "termination_units": _jsonable(projection["termination_units"]),
               "pre_action_inventory": _jsonable(projection),
               "live_listeners": projection["live_listeners"], "owned_listeners": projection["owned_listeners"],
               "orphan_listeners": projection["orphan_listeners"], "stale_sessions": projection["stale_sessions"],
               "detached_sessions": projection["detached_sessions"], "diagnostic_sessions": projection["diagnostic_sessions"],
               "cardinality": post["cardinality"], "proposed_actions": _jsonable(actions), "actions_attempted": _jsonable(attempted),
               "actions_completed": _jsonable(completed), "actions_failed": _jsonable(failed), "skipped_actions": _jsonable(skipped),
               "post_action_inventory": _jsonable(post), "remaining_live_listeners": _jsonable(post["live_listeners"]),
               "remaining_orphans": _jsonable(post["orphan_listeners"]), "unresolved_actions": _jsonable(unresolved),
               "preserved_targets": _jsonable(preserved_targets),
               "termination_receipts": _jsonable(completed), "sessions_updated": updated, "receipts_written": len(completed),
               "phases": phases, "blockers": sorted(set(blockers)), "notices": sorted(set(notices)), "terminal_state_result": terminal,
               "reconciliation_applied": reconciliation_applied,
               "reconciliation_applied_this_invocation": reconciliation_applied_this_invocation,
               "reconciliation_already_applied": reconciliation_already_applied,
               "reconciliation_required": bool(executable_count or failed),
               "reconciliation_fully_converged": fully_converged,
               "required_action_count": len(actions), "executable_action_count": executable_count,
               "blocked_action_count": len(actions) - executable_count,
               "ownership_summary": {name: sum(item.get("ownership_result") == name for item in projection["termination_units"])
                                     for name in ("OWNERSHIP_VERIFIED", "OWNERSHIP_RECOVERED_VERIFIED", "OWNERSHIP_PARTIAL", "OWNERSHIP_UNKNOWN", "OWNERSHIP_MISMATCH")},
               "next_authorized_action": ("NO_RECONCILIATION_REQUIRED" if not executable_count and not preserved_targets and not failed else
                                          ("REVIEW_AND_APPROVE_RECONCILIATION" if not approve and executable_count else
                                           ("REVIEW_PRESERVED_TARGETS" if preserved_targets and not executable_count else
                                            ("RECONCILE_PROCESS_IDENTITY_AND_OWNERSHIP" if not approve else
                                             ("RECONCILE_REMAINING_ORPHAN_OWNERSHIP" if preserved_targets else "VERIFY_RECONCILIATION"))))),
               "authoritative_runtime_updates": "ZEUS_CONTROLLER_ONLY", "result": result, "receipt_digest": None}
    receipt["receipt_digest"] = digest(receipt)
    if approve:
        try:
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(receipt_path, receipt)
        except OSError as error:
            receipt["result"] = "FAIL"; receipt["blockers"] = sorted(set(receipt["blockers"] + ["RECEIPT_PERSISTENCE_FAILED"]))
            raise ReconciliationError("RECEIPT_PERSISTENCE_FAILED", str(error)) from error
    return _response(root, runtime, projection, actions, receipt, replay=False, read_only=not approve)


def _response(root: Path, runtime: Path, projection: Mapping[str, Any], actions: list[dict[str, Any]],
              receipt: Mapping[str, Any], *, replay: bool, read_only: bool,
              current_plan_digest: str | None = None, requested_plan_digest: str | None = None,
              completed_receipt_path: Path | None = None,
              replay_result: str | None = None) -> dict[str, Any]:
    from scripts.lib.emp.repository_identity import resolve as resolve_repository
    repository_id = resolve_repository(root).get("repository_id")
    replay_result = replay_result or ("IDEMPOTENT" if replay else "NOT_REQUIRED")
    replay_completed = replay and replay_result == "IDEMPOTENT"
    result = ("PASS" if replay_completed else "FAIL") if replay else receipt.get("result", "PASS")
    current_preserved = _preserved_targets(projection, actions) if replay else list(receipt.get("preserved_targets", []))
    current_actions = list(actions) if replay else list(receipt.get("proposed_actions", actions))
    required_actions = current_actions
    executable_count = sum(bool(item.get("allowed")) for item in required_actions) if replay else int(
        receipt.get("executable_action_count", sum(bool(item.get("allowed")) for item in required_actions)))
    current_blockers = []
    if replay and executable_count:
        current_blockers.append("CURRENT_PLAN_REQUIRES_REVIEW")
    if replay and not executable_count and projection.get("cardinality", {}).get("result") != "PASS":
        current_blockers.append("CARDINALITY_NOT_SATISFIED")
    blockers = current_blockers if replay_completed else list(receipt.get("blockers", []))
    if replay_completed:
        next_action = ("REVIEW_PRESERVED_TARGETS" if current_preserved and not executable_count
                       else ("REVIEW_AND_APPROVE_RECONCILIATION" if executable_count
                             else "NO_RECONCILIATION_REQUIRED"))
    elif not read_only:
        next_action = ("NO_RECONCILIATION_REQUIRED" if receipt.get("terminal_state_result") else
                       receipt.get("next_authorized_action") or
                       ("RECONCILE_REMAINING_ORPHAN_OWNERSHIP" if receipt.get("preserved_targets")
                        else "VERIFY_RECONCILIATION"))
    elif not required_actions and not blockers:
        next_action = "NO_RECONCILIATION_REQUIRED"
    elif executable_count:
        next_action = "REVIEW_AND_APPROVE_RECONCILIATION"
    else:
        next_action = ("REVIEW_PRESERVED_TARGETS" if receipt.get("preserved_targets") and not executable_count
                       else "RECONCILE_PROCESS_IDENTITY_AND_OWNERSHIP")
    already_applied = bool((replay_completed and completed_receipt_path) or
                           receipt.get("reconciliation_already_applied") or
                           receipt.get("reconciliation_applied"))
    applied_this_invocation = bool(receipt.get("reconciliation_applied_this_invocation")) if not replay else False
    notices = list(receipt.get("notices", []))
    if current_preserved and not executable_count and "PRESERVED_TARGETS_REMAIN" not in notices:
        notices.append("PRESERVED_TARGETS_REMAIN")
    current_digest = current_plan_digest or receipt.get("plan_digest")
    historical_digest = receipt.get("plan_digest") if replay else None
    replay_context = None
    if replay:
        completed_phase = next((item for item in reversed(receipt.get("phases", []))
                                if item.get("phase") == "RECONCILIATION_COMPLETED"), {})
        replay_context = {"requested_plan_digest": requested_plan_digest or historical_digest,
                          "matched_completed_plan_digest": historical_digest if replay_completed else None,
                          "current_plan_digest": current_digest,
                          "completed_reconciliation_id": receipt.get("reconciliation_id") if replay_completed else None,
                          "completed_receipt_digest": receipt.get("receipt_digest") if replay_completed else None,
                          "completed_receipt_path": str(completed_receipt_path) if completed_receipt_path else None,
                          "completed_at": (receipt.get("completed_at") or receipt.get("timestamp") or
                                           completed_phase.get("at")) if replay_completed else None,
                          "historical_result": receipt.get("result") if replay_completed else None,
                          "current_result": "PASS" if not current_blockers and not executable_count else "BLOCKED_PENDING_APPROVAL"}
    return {"result": result, "read_only": read_only, "dry_run": read_only,
            "execution_mode": receipt.get("execution_mode", "REMOTE_INTERACTIVE"),
            "repository": str(root), "repository_id": repository_id,
            "matching_sessions": projection.get("matching_sessions", []) if replay else receipt.get("matching_sessions", projection.get("matching_sessions", [])),
            "live_listeners": projection.get("live_listeners", []) if replay else receipt.get("live_listeners", projection.get("live_listeners", [])),
            "owned_listeners": projection.get("owned_listeners", []) if replay else receipt.get("owned_listeners", projection.get("owned_listeners", [])),
            "orphan_listeners": projection.get("orphan_listeners", []) if replay else receipt.get("orphan_listeners", projection.get("orphan_listeners", [])),
            "stale_sessions": projection.get("stale_sessions", []) if replay else receipt.get("stale_sessions", projection.get("stale_sessions", [])),
            "detached_sessions": projection.get("detached_sessions", []) if replay else receipt.get("detached_sessions", projection.get("detached_sessions", [])),
            "diagnostic_sessions": projection.get("diagnostic_sessions", []) if replay else receipt.get("diagnostic_sessions", projection.get("diagnostic_sessions", [])),
            "plan_schema_version": receipt.get("plan_schema_version", 1),
            "plan_digest_algorithm": receipt.get("plan_digest_algorithm", "SHA256"),
            "plan_digest": current_digest,
            "termination_units": projection.get("termination_units", receipt.get("termination_units", [])) if replay else receipt.get("termination_units", projection.get("termination_units", [])),
            "cardinality_result": projection.get("cardinality", receipt.get("cardinality", {})) if replay else receipt.get("cardinality", projection.get("cardinality", {})),
            "proposed_actions": current_actions, "required_actions": required_actions,
            "required_action_count": len(required_actions),
            "executable_action_count": executable_count,
            "blocked_action_count": len(required_actions) - executable_count,
            "ownership_summary": ({name: sum(item.get("ownership_result") == name for item in projection.get("termination_units", []))
                                   for name in ("OWNERSHIP_VERIFIED", "OWNERSHIP_RECOVERED_VERIFIED", "OWNERSHIP_PARTIAL", "OWNERSHIP_UNKNOWN", "OWNERSHIP_MISMATCH")}
                                  if replay else receipt.get("ownership_summary", {})),
            "blockers": blockers,
            "next_authorized_action": next_action,
            "reconciliation": receipt, "replayed": replay,
            "replay_context": replay_context,
            "unreconciled_orphans": len(projection.get("orphan_listeners", [])) if replay else len(receipt.get("remaining_orphans", receipt.get("orphan_listeners", []))),
            "preserved_targets": current_preserved,
            "preserved_target_count": len(current_preserved),
            "reconciliation_applied": bool(receipt.get("reconciliation_applied", False) or already_applied),
            "reconciliation_applied_this_invocation": applied_this_invocation,
            "reconciliation_already_applied": already_applied,
            "reconciliation_required": (bool(executable_count or current_blockers) if replay_completed else bool(receipt.get("reconciliation_required", executable_count > 0))),
            "reconciliation_fully_converged": (bool(not current_preserved and not executable_count and not current_blockers)
                                                if replay_completed else receipt.get("reconciliation_fully_converged", receipt.get("terminal_state_result", False))),
            "actions_attempted": [] if replay else receipt.get("actions_attempted", []),
            "actions_completed": [] if replay else receipt.get("actions_completed", []),
            "actions_failed": [] if replay else receipt.get("actions_failed", []),
            "processes_signaled": 0 if replay else sum(bool(item.get("signal_sequence")) for item in receipt.get("actions_completed", [])),
            "processes_exited": 0 if replay else sum(bool(item.get("process_exit_result")) for item in receipt.get("actions_completed", [])),
            "sockets_closed": 0 if replay else sum(bool(item.get("socket_closure_result")) for item in receipt.get("actions_completed", [])),
            "sessions_updated": [] if replay else receipt.get("sessions_updated", []),
            "receipts_written": 0 if replay else receipt.get("receipts_written", 0),
            "terminal_state": (bool(not current_preserved and not executable_count and not current_blockers)
                                if replay_completed else receipt.get("terminal_state_result", False)),
            "replay_result": replay_result,
            "notices": notices,
            "read_only": read_only}


def _legacy_reconcile(root: Path, runtime: Path, *, approve: bool) -> dict[str, Any]:
    """Compatibility projection for non-remote disposable fixture records."""
    entries = _inventory(runtime)
    reconciliation_id = _reconciliation_id(entries)
    legacy_plan_digest = _stable_digest({"plan_schema_version": 1, "termination_units": [],
                                        "proposed_actions": [], "blockers": []})
    receipt_path = _receipt_path(runtime, reconciliation_id)
    if receipt_path.is_file():
        receipt = load_json(receipt_path)
        return {"result": "PASS", "replayed": True, "read_only": not approve,
                "runtime_root": str(runtime), "plan_schema_version": 1,
                "plan_digest": receipt.get("plan_digest", legacy_plan_digest),
                "termination_units": [], "proposed_actions": [], "required_action_count": 0,
                "executable_action_count": 0, "next_authorized_action": "NO_RECONCILIATION_REQUIRED",
                "reconciliation": receipt}
    record_keys = {(item.get("record_type"), item.get("session_id"), item.get("record_digest"))
                   for item in entries if item.get("record_digest")}
    receipt_dir = runtime / RECEIPT_DIR
    for candidate in sorted(receipt_dir.glob("*.json")) if receipt_dir.is_dir() else ():
        prior = load_json(candidate)
        prior_keys = {(item.get("record_type"), item.get("session_id"), item.get("record_digest"))
                      for item in prior.get("entries", []) if item.get("record_digest")}
        if prior.get("controller_version") == CONTROLLER_VERSION and prior.get("operator_approved") and prior_keys == record_keys:
            return {"result": "PASS", "replayed": True, "read_only": not approve,
                    "runtime_root": str(runtime), "plan_schema_version": 1,
                    "plan_digest": prior.get("plan_digest", legacy_plan_digest),
                    "termination_units": [], "proposed_actions": [], "required_action_count": 0,
                    "executable_action_count": 0, "next_authorized_action": "NO_RECONCILIATION_REQUIRED",
                    "reconciliation": prior}
    terminated = []
    eligible = [entry for entry in entries if entry.get("eligible_for_mutation")]
    if approve:
        for entry in eligible:
            for process in entry["processes"]:
                if process["identity_validation"] != "PASS" or not process["observed"].get("alive"):
                    continue
                pid = process["pid"]
                os.kill(pid, signal.SIGTERM)
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline and process_identity(pid).get("alive"):
                    time.sleep(0.02)
                remaining = process_identity(pid)
                terminated.append({"pid": pid, "field": process["field"], "identity": process["observed"],
                                   "remaining": remaining, "result": "PASS" if not remaining.get("alive") else "TIMEOUT"})
    cardinality = {entry["cardinality_conflict"]["mission_id"]: entry["cardinality_conflict"]
                   for entry in entries if entry.get("cardinality_conflict")}
    receipt = {"controller_version": CONTROLLER_VERSION, "schema_version": 2,
               "contract": "ZEUS-P5-G6-CODEX-RECONCILIATION", "reconciliation_id": reconciliation_id,
               "repository": str(root), "runtime_root": str(runtime), "read_only": not approve,
               "operator_approved": approve, "entries": entries, "cardinality": cardinality,
               "plan_schema_version": 1, "plan_digest": legacy_plan_digest,
               "termination_units": [], "proposed_actions": [],
               "termination_receipts": terminated,
               "authoritative_runtime_updates": "ZEUS_CONTROLLER_ONLY", "result": "PASS",
               "unreconciled_orphans": len(eligible) if not approve else 0, "receipt_digest": None}
    receipt["receipt_digest"] = digest(receipt)
    if approve:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(receipt_path, receipt)
    return {"result": "PASS", "replayed": False, "read_only": not approve,
            "runtime_root": str(runtime), "plan_schema_version": 1,
            "plan_digest": legacy_plan_digest, "termination_units": [],
            "proposed_actions": [], "required_action_count": 0,
            "executable_action_count": 0, "next_authorized_action": "NO_RECONCILIATION_REQUIRED",
            "reconciliation": receipt}


def inventory(repository: Path | str, *, runtime_root: Path | str | None = None) -> dict[str, Any]:
    value = reconcile(repository, runtime_root=runtime_root, approve=False)
    return value

# --- CR46 ZO-061: validation applicability classification ---
VALIDATOR_CLASSES = {
    "PARENT_ROADMAP": {
        "phases": {"PARENT_LIFECYCLE"},
        "topologies": {"LIVE_REPOSITORY"},
    },

    "DETACHED_ROADMAP": {
        "phases": {"DETACHED_CANDIDATE"},
        "topologies": {"DETACHED_TREE"},
    },

    "IMMUTABLE_COMMIT": {
        "phases": {"PREPUBLICATION", "PUBLICATION"},
        "topologies": {"IMMUTABLE_COMMIT"},
    },

    "LIVE_REPOSITORY": {
        "phases": {
            "PREPUBLICATION",
            "POSTPUBLICATION",
            "EXECUTION",
        },
        "topologies": {"LIVE_REPOSITORY"},
    },

    "PUBLICATION": {
        "phases": {
            "PREPUBLICATION",
            "POSTPUBLICATION",
        },
        "topologies": {
            "LIVE_REPOSITORY",
            "IMMUTABLE_COMMIT",
        },
    },

    "EOS_SYNCHRONIZATION": {
        "phases": {
            "POSTPUBLICATION",
            "CLOSEOUT",
        },
        "topologies": {"LIVE_REPOSITORY"},
    },

    "TEST_HARNESS": {
        "phases": {"TEST"},
        "topologies": {
            "TEST_HARNESS",
            "DETACHED_TREE",
            "LIVE_REPOSITORY",
        },
    },
}


def classify_validation_applicability(
    validator_class: str,
    *,
    lifecycle_phase: str,
    repository_topology: str,
    publication_state: str = "UNKNOWN",
    eos_state: str = "UNKNOWN",
    harness_context: str = "PRODUCTION",
) -> dict[str, Any]:
    """Determine validator applicability before defect classification."""
    validator = (
        str(validator_class or "")
        .strip()
        .upper()
        .replace("-", "_")
    )

    phase = (
        str(lifecycle_phase or "")
        .strip()
        .upper()
        .replace("-", "_")
    )

    topology = (
        str(repository_topology or "")
        .strip()
        .upper()
        .replace("-", "_")
    )

    rule = VALIDATOR_CLASSES.get(validator)

    if rule is None or not phase or not topology:
        return {
            "result": "FAIL",
            "read_only": True,
            "validator_class": validator or None,
            "applicability": "AMBIGUOUS",
            "candidate_semantic_defect": "NOT_CLASSIFIED",
            "justification":
                "validator class, lifecycle phase, or repository topology "
                "is unsupported or absent",
            "next_authorized_action":
                "RESOLVE_VALIDATION_APPLICABILITY",
        }

    phase_match = phase in rule["phases"]
    topology_match = topology in rule["topologies"]

    applicable = phase_match and topology_match

    return {
        "result": "PASS",
        "read_only": True,

        "validator_class": validator,
        "lifecycle_phase": phase,
        "repository_topology": topology,
        "publication_state": str(publication_state).upper(),
        "eos_state": str(eos_state).upper(),
        "harness_context": str(harness_context).upper(),

        "applicability":
            "APPLICABLE"
            if applicable
            else "NOT_APPLICABLE",

        "candidate_semantic_defect": (
            "ELIGIBLE_FOR_CLASSIFICATION"
            if applicable
            else "NO"
        ),

        "justification": (
            "validator class matches lifecycle phase and repository topology"
            if applicable
            else
            "validator class does not apply to the supplied "
            "lifecycle/repository context"
        ),

        "applicability_checks": {
            "lifecycle_phase": phase_match,
            "repository_topology": topology_match,
        },

        "next_authorized_action": (
            "RUN_VALIDATOR"
            if applicable
            else "RECORD_NOT_APPLICABLE_WITH_JUSTIFICATION"
        ),
    }
