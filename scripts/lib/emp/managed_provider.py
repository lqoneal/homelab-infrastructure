"""Zeus-owned non-interactive Codex execution boundary."""
from __future__ import annotations
import json, os, signal, subprocess, time, uuid
from pathlib import Path
from typing import Any, Iterable

class ManagedProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None):
        self.code, self.details = code, details or {}
        super().__init__(message)

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
    out_of_scope = sorted(path for path in changed if not any(path == item or path.startswith(item.rstrip("/") + "/") for item in allowed))
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
              "protected_actions_performed": [], "provider_completion_is_qualification": False}
    if output_path:
        path = Path(output_path).resolve(); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(record, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    if timing_root:
        try:
            from scripts.lib.emp.codex_session_timing import record_passive_managed_timing
            record_passive_managed_timing(repository_root=root, duration_seconds=record["duration_seconds"], execution_session_id=execution, log_root=timing_root)
        except Exception: pass
    return record
