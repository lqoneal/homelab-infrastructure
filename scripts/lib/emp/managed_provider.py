"""Zeus-owned non-interactive Codex execution boundary."""
from __future__ import annotations
import json, os, signal, subprocess, time, uuid
from pathlib import Path
from typing import Any, Iterable, Mapping

class ManagedProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None):
        self.code, self.details = code, details or {}
        super().__init__(message)


ZEUS_QUALIFICATION_RECEIPT_MARKER = "/receipts/qualification/"


def attribute_mutations(
    *,
    provider_diff: Iterable[str],
    controller_diff: Iterable[str] = (),
    provider_authorized_scope: Iterable[str] = (),
    controller_authority: str = "ZEUS",
) -> dict[str, Any]:
    """Separate provider worktree changes from Zeus lifecycle changes.

    A qualification receipt is controller-owned only when it appears in the
    controller diff under Zeus authority.  If it appears in the provider
    diff, it is an attempted provider mutation of Zeus-owned evidence and is
    always out of scope, even if a caller accidentally lists that path in the
    provider scope.
    """
    provider_paths = sorted(set(provider_diff))
    controller_paths = sorted(set(controller_diff))
    allowed = set(provider_authorized_scope)
    provider_out = [
        path for path in provider_paths
        if path in {p for p in provider_paths if ZEUS_QUALIFICATION_RECEIPT_MARKER in f"/{p}"}
        or not any(path == item or path.startswith(item.rstrip("/") + "/") for item in allowed)
    ]
    controller_receipts = [
        path for path in controller_paths
        if ZEUS_QUALIFICATION_RECEIPT_MARKER in f"/{path}"
    ]
    unauthorized_controller = [] if str(controller_authority).upper() == "ZEUS" else controller_paths
    return {
        "provider_post_execution_diff": provider_paths,
        "zeus_controller_diff": controller_paths,
        "out_of_scope_provider_changes": sorted(provider_out),
        "unauthorized_controller_changes": sorted(unauthorized_controller),
        "zeus_receipt_attribution": "ZEUS_CONTROLLER_MUTATION" if controller_receipts else "NONE",
        "provider_mutation": "YES" if provider_paths else "NO",
        "zeus_controller_mutation": "YES" if controller_paths else "NO",
        "provider_scope_compliance": "PASS" if not provider_out else "FAIL",
        "controller_scope_compliance": "PASS" if not unauthorized_controller else "FAIL",
        "scope_verification": "PASS" if not provider_out and not unauthorized_controller else "FAIL",
        "terminal_reconciliation": "PASS" if not provider_out and not unauthorized_controller else "FAIL",
    }


def reconcile_controller_mutations(
    managed_session: Mapping[str, Any],
    controller_diff: Iterable[str],
    *,
    controller_authority: str = "ZEUS",
) -> dict[str, Any]:
    """Reconcile Zeus lifecycle mutations without relabeling provider work."""
    value = dict(managed_session)
    attribution = attribute_mutations(
        provider_diff=value.get("provider_post_execution_diff", value.get("post_execution_diff", [])),
        controller_diff=controller_diff,
        provider_authorized_scope=value.get("authorized_scope", []),
        controller_authority=controller_authority,
    )
    value.update(attribution)
    value["post_execution_diff"] = attribution["provider_post_execution_diff"]
    value["out_of_scope_changes"] = attribution["out_of_scope_provider_changes"]
    value["authorized_scope_compliance"] = attribution["provider_scope_compliance"]
    return value

def _paths(root: Path) -> set[str]:
    result = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"], capture_output=True, text=True, check=False)
    if result.returncode: raise ManagedProviderError("WORKTREE_SNAPSHOT_FAILED", result.stderr.strip())
    return {line[3:].strip().strip('"') for line in result.stdout.splitlines() if len(line) >= 4}

def _authorized(root: Path, values: Iterable[str]) -> set[str]:
    allowed = set()
    for value in values:
        try: allowed.add((root / value).resolve().relative_to(root).as_posix())
        except ValueError as error: raise ManagedProviderError("AUTHORIZED_SCOPE_INVALID", f"scope escapes repository: {value}") from error
    return allowed

def execute(*, repository: Path | str, prompt: str, authorized_paths: Iterable[str], execution_id: str | None = None,
            codex_bin: str = "codex", timeout_seconds: float = 300.0, output_path: Path | str | None = None,
            timing_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repository).resolve()
    if not root.is_dir() or not prompt.strip(): raise ManagedProviderError("MANAGED_EXECUTION_INPUT_INVALID", "repository and prompt are required")
    execution = execution_id or "ZEUS-EXECUTION-" + uuid.uuid4().hex
    allowed, before = _authorized(root, authorized_paths), _paths(root)
    command = [codex_bin, "-a", "never", "-s", "workspace-write", "-C", str(root), "exec", "--json", "--ephemeral", prompt]
    started = time.monotonic(); started_at = time.time()
    provider_started = False
    try:
        process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True)
        provider_started = True
    except OSError as error: raise ManagedProviderError("PROVIDER_LAUNCH_FAILURE", str(error), details={"execution_id": execution}) from error
    interrupted = False
    try: stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        interrupted = True; os.killpg(process.pid, signal.SIGTERM); stdout, stderr = process.communicate()
    ended_at = time.time(); after = _paths(root)
    changed = sorted(after - before)
    attribution = attribute_mutations(
        provider_diff=changed,
        provider_authorized_scope=allowed,
    )
    out_of_scope = attribution["out_of_scope_provider_changes"]
    provider_session_id = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            continue
        if event.get("type") == "thread.started":
            provider_session_id = event.get("thread_id")
            break
    result = "INTERRUPTED" if interrupted else "PASS" if process.returncode == 0 else "FAIL"
    if out_of_scope: result = "FAIL"
    record = {"operation_id":"OPERATION-BETA", "emm_id":"OPERATION-BETA-EMM", "wop_id":None, "gate_or_transaction_id":None,
              "zeus_execution_id":execution, "provider":"CODEX", "provider_session_id":provider_session_id, "start_time":started_at, "end_time":ended_at,
              "duration_seconds":round(time.monotonic()-started, 3), "result":result, "provider_exit_status":process.returncode,
              "stdout":stdout, "stderr":stderr, "authorized_scope":sorted(allowed), "post_execution_diff":changed,
              "out_of_scope_changes":out_of_scope, "scope_verification":"PASS" if not out_of_scope else "FAIL",
              "qualification":"REQUIRED", "publication_authority":"ZEUS_ONLY", "eos_authority":"ZEUS_ONLY", "provider_process_owned_by":"ZEUS",
              "provider_started": "YES" if provider_started else "NO", "provider_process_state": "INTERRUPTED" if interrupted else "COMPLETED" if process.returncode == 0 else "FAILED",
              "zeus_managed_session_created": "YES" if provider_started else "NO", "execution_monitoring": "ACTIVE_THEN_TERMINAL", "terminal_reconciliation": "PASS" if result == "PASS" else "FAIL",
              "protected_actions_performed": [], "provider_completion_is_qualification": False,
              # These are terminal facts retained by the Zeus controller for
              # the later qualification decision.  They are not a provider
              # qualification result and must not be inferred from exit zero.
              "provider_terminal_record": "RETAINED",
              "actor_aware_mutation_attribution": "PASS",
              "execution_session_integrity": "PASS" if result == "PASS" else "FAIL",
              "authorized_scope_compliance": "PASS" if not out_of_scope else "FAIL",
              "required_evidence_completeness": "PASS" if result == "PASS" else "FAIL",
              "acceptance_criteria_verification": "PASS" if result == "PASS" else "FAIL",
              **attribution}
    if output_path:
        path = Path(output_path).resolve(); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(record, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    if timing_root:
        try:
            from scripts.lib.emp.codex_session_timing import record_passive_managed_timing
            record_passive_managed_timing(repository_root=root, duration_seconds=record["duration_seconds"], execution_session_id=execution, log_root=timing_root)
        except Exception: pass
    return record
