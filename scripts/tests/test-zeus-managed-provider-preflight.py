"""Focused qualification for Zeus-owned managed Codex preflight resolution."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
import copy
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.lib.emp import codex_adapter


ROOT = Path(__file__).resolve().parents[2]


class ManagedProviderPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="zeus-provider-preflight-")
        self.base = Path(self.temporary.name)
        self.codex_home = self.base / "codex-home"
        self.codex_home.mkdir()
        (self.codex_home / "auth.json").write_text("{}\n", encoding="utf-8")
        (self.codex_home / "config.toml").write_text("model = \"test\"\n", encoding="utf-8")
        self.contract = self.base / "contract.yaml"
        self.contract.write_text(yaml.safe_dump({
            "work_contract_id": "TEST-CONTRACT", "work_type": "ENGINEERING_IMPLEMENTATION",
            "repository": {"path": str(ROOT)},
            "authority": {"engineering_implementation": True, "command_execution": True},
            "prohibited_operations": list(codex_adapter.ZEUS_OWNED_PROHIBITED_OPERATIONS),
        }), encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def _run(command, **kwargs):
        if command[-1] == "--version":
            output = "codex-cli 0.147.0\n"
        elif command[1:3] == ["exec", "resume"]:
            output = "Usage SESSION_ID --last --strict-config"
        elif command[1:2] == ["exec"]:
            output = "--json --output-last-message --sandbox"
        else:
            output = "app-server --strict-config --listen stdio://"
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    def _resolve(self, **kwargs):
        with patch.dict(os.environ, {"CODEX_HOME": str(self.codex_home)}), \
             patch.object(codex_adapter.shutil, "which", return_value="/bin/true"), \
             patch.object(codex_adapter.subprocess, "run", side_effect=self._run):
            return codex_adapter.resolve_provider_invocation_contract(
                ROOT, work_contract=self.contract, runtime_root=self.base / "runtime", **kwargs)

    def test_valid_managed_preflight_resolves_required_options_without_provider_start(self):
        with patch.object(codex_adapter.subprocess, "Popen",
                          side_effect=AssertionError("provider dispatch attempted")):
            value = self._resolve()
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["execution_mode"], "ZEUS_MANAGED")
        self.assertEqual(value["provider_mode"], "APP_SERVER_MANAGED")
        self.assertEqual(value["provider_transport"], "STDIO")
        self.assertEqual(value["required_codex_invocation_arguments"],
                         ["app-server", "--strict-config", "--listen", "stdio://"])
        self.assertFalse(value["provider_started"])
        self.assertFalse(value["mission_work_started"])
        self.assertFalse(value["repository_work_started"])
        self.assertEqual(value["work_contract_capabilities"], "PASS")

    def test_invalid_provider_configuration_fails_before_dispatch(self):
        (self.codex_home / "config.toml").write_text("invalid = [\n", encoding="utf-8")
        with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
            self._resolve()
        self.assertEqual(raised.exception.code, "CODEX_INCOMPATIBILITY")
        self.assertEqual(raised.exception.details["incompatibility"], "MISCONFIGURED")

    def test_unsupported_option_is_an_explicit_blocker(self):
        with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
            self._resolve(requested_options=["--full-auto"])
        self.assertEqual(raised.exception.code, "CODEX_INCOMPATIBILITY")
        self.assertIn("--full-auto", raised.exception.details["unsupported_options"])

    def test_work_contract_capability_incompatibility_fails_closed(self):
        value = yaml.safe_load(self.contract.read_text(encoding="utf-8"))
        value["authority"]["command_execution"] = False
        self.contract.write_text(yaml.safe_dump(value), encoding="utf-8")
        with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
            self._resolve()
        self.assertEqual(raised.exception.code, "WORK_CONTRACT_INCOMPATIBLE")

    def test_qualification_requires_explicit_zeus_authority(self):
        value = yaml.safe_load(self.contract.read_text(encoding="utf-8"))
        value["requested_operations"] = ["qualification"]
        self.contract.write_text(yaml.safe_dump(value), encoding="utf-8")
        with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
            self._resolve()
        self.assertEqual(raised.exception.details["incompatibility"], "QUALIFICATION_AUTHORITY_MISSING")

    def test_qualification_authority_is_projected_when_granted(self):
        value = yaml.safe_load(self.contract.read_text(encoding="utf-8"))
        value["requested_operations"] = ["qualification"]
        value["authority"]["qualification_execution"] = True
        self.contract.write_text(yaml.safe_dump(value), encoding="utf-8")
        resolved = self._resolve()
        self.assertEqual(resolved["qualification_authority"], "AVAILABLE")
        self.assertEqual(resolved["requested_operations"], ["qualification"])

    def test_mismatched_mission_and_transaction_context_fail_closed(self):
        value = yaml.safe_load(self.contract.read_text(encoding="utf-8"))
        value.update({"mission_id": "MISSION-A", "transaction_id": "TX-A"})
        self.contract.write_text(yaml.safe_dump(value), encoding="utf-8")
        with self.assertRaises(codex_adapter.CodexAdapterError) as mission:
            self._resolve(mission_id="MISSION-B")
        self.assertEqual(mission.exception.details["incompatibility"], "MISSION_CONTEXT_MISMATCH")
        with self.assertRaises(codex_adapter.CodexAdapterError) as transaction:
            self._resolve(transaction_id="TX-B")
        self.assertEqual(transaction.exception.details["incompatibility"], "TRANSACTION_CONTEXT_MISMATCH")

    def test_repository_binding_incompatibility_fails_closed(self):
        value = yaml.safe_load(self.contract.read_text(encoding="utf-8"))
        value["repository"]["path"] = str(self.base)
        self.contract.write_text(yaml.safe_dump(value), encoding="utf-8")
        with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
            self._resolve()
        self.assertEqual(raised.exception.code, "WORK_CONTRACT_INCOMPATIBLE")

    def test_no_direct_interactive_fallback_is_present_in_plan(self):
        value = self._resolve()
        self.assertNotEqual(value["execution_mode"], "DIRECT_INTERACTIVE")
        self.assertNotEqual(value["provider_mode"], "CODEX_CLI")

    def test_session_and_execution_bindings_remain_required(self):
        value = self._resolve()
        self.assertTrue(value["session_binding_required"])
        self.assertTrue(value["provider_session_binding_required"])
        self.assertTrue(value["execution_binding_required"])

    def test_managed_start_consumes_the_canonical_resolved_plan(self):
        package = {
            "provider_id": codex_adapter.PROVIDER_ID, "package_digest": "digest",
            "execution_id": "EXECUTION", "repository_identity": "homelab",
            "authority": {"integrity": "PASS"},
        }
        plan = self._resolve()
        diagnostics = {"provider_pid": os.getpid(), "command": plan["command"],
                       "environment": {}, "control_socket": None, "remote_endpoint": None}
        process = type("Process", (), {"pid": os.getpid()})()
        with patch.object(codex_adapter, "_package", return_value=package), \
             patch.object(codex_adapter, "resolve_provider_invocation_contract", return_value=plan) as resolver, \
             patch.object(codex_adapter, "_existing", return_value=None), \
             patch.object(codex_adapter, "_append_event"), \
             patch.object(codex_adapter, "_save", side_effect=lambda runtime, value: value), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, diagnostics)) as launch, \
             patch.object(codex_adapter, "_result", return_value={"result": "PASS"}):
            value = codex_adapter.start(ROOT, "MISSION-TEST", runtime_root=self.base / "runtime")
        self.assertEqual(value["result"], "PASS")
        resolver.assert_called_once()
        self.assertIs(launch.call_args.args[5], plan)

    def test_resume_propagates_the_exact_work_contract(self):
        with patch.object(codex_adapter, "_existing", return_value={"session_id": "A"}), \
             patch.object(codex_adapter, "_provider_control_ready", return_value=False), \
             patch.object(codex_adapter, "start", return_value={"result": "PASS"}) as start:
            value = codex_adapter.resume(ROOT, "MISSION-TEST", runtime_root=self.base / "runtime",
                                         work_contract=self.contract)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(start.call_args.kwargs["work_contract"], self.contract)

    def test_contract_is_required_and_malformed_contracts_fail_closed(self):
        with patch.dict(os.environ, {"CODEX_HOME": str(self.codex_home)}), \
             patch.object(codex_adapter.shutil, "which", return_value="/bin/true"), \
             patch.object(codex_adapter.subprocess, "run", side_effect=self._run):
            with self.assertRaises(codex_adapter.CodexAdapterError) as missing:
                codex_adapter.resolve_provider_invocation_contract(ROOT, runtime_root=self.base / "runtime")
        self.assertEqual(missing.exception.code, "WORK_CONTRACT_REQUIRED")
        for material, incompatibility in (("[]\n", "INVALID_WORK_CONTRACT_ROOT"),
                                          ("work_contract_id: X\nauthority: []\n", "REPOSITORY_BINDING_MISSING")):
            self.contract.write_text(material, encoding="utf-8")
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                self._resolve()
            self.assertEqual(raised.exception.code, "WORK_CONTRACT_INCOMPATIBLE")
            self.assertEqual(raised.exception.details["incompatibility"], incompatibility)

    def test_missing_repository_binding_never_inherits_cwd(self):
        value = yaml.safe_load(self.contract.read_text(encoding="utf-8"))
        value["repository"] = {"path": ""}
        self.contract.write_text(yaml.safe_dump(value), encoding="utf-8")
        with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
            self._resolve()
        self.assertEqual(raised.exception.details["incompatibility"], "REPOSITORY_BINDING_MISSING")

    def test_unsupported_version_authentication_and_config_conflict_fail_closed(self):
        def unsupported(command, **kwargs):
            result = self._run(command, **kwargs)
            if command[-1] == "--version":
                result.stdout = "codex-cli 0.148.0\n"
            return result
        with patch.dict(os.environ, {"CODEX_HOME": str(self.codex_home)}), \
             patch.object(codex_adapter.shutil, "which", return_value="/bin/true"), \
             patch.object(codex_adapter.subprocess, "run", side_effect=unsupported), \
             self.assertRaises(codex_adapter.CodexAdapterError) as version:
            codex_adapter.resolve_provider_invocation_contract(ROOT, work_contract=self.contract,
                                                                runtime_root=self.base / "runtime")
        self.assertEqual(version.exception.details["incompatibility"], "UNSUPPORTED_CODEX_VERSION")
        (self.codex_home / "auth.json").unlink()
        with self.assertRaises(codex_adapter.CodexAdapterError) as auth:
            self._resolve()
        self.assertEqual(auth.exception.details["incompatibility"], "UNAUTHENTICATED")
        (self.codex_home / "auth.json").write_text("{}\n", encoding="utf-8")
        (self.codex_home / "config.toml").write_text('approval_policy = "on-request"\n', encoding="utf-8")
        with self.assertRaises(codex_adapter.CodexAdapterError) as conflict:
            self._resolve()
        self.assertEqual(conflict.exception.details["incompatibility"], "CONFIGURATION_CONFLICT")

    def test_nested_runtime_path_uses_nearest_existing_ancestor_without_mutation(self):
        runtime = self.base / "one" / "two" / "runtime"
        with patch.dict(os.environ, {"CODEX_HOME": str(self.codex_home)}), \
             patch.object(codex_adapter.shutil, "which", return_value="/bin/true"), \
             patch.object(codex_adapter.subprocess, "run", side_effect=self._run):
            value = codex_adapter.resolve_provider_invocation_contract(
                ROOT, work_contract=self.contract, runtime_root=runtime)
        self.assertEqual(value["runtime_materialization_anchor"], str(self.base))
        self.assertEqual(value["runtime_missing_components"], ["one", "two", "runtime"])
        self.assertFalse(runtime.exists())

    def test_cli_managed_preflight_is_read_only_and_returns_to_contract_boundary(self):
        before = subprocess.run(["git", "status", "--porcelain=v1"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout
        nested = self.base / "cli" / "nested" / "runtime"
        environment = dict(os.environ, CODEX_HOME=str(self.codex_home), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([
            str(ROOT / "scripts/zeus"), "--runtime-root", str(nested), "codex", "start",
            "--mode", "ZEUS_MANAGED", "--work-contract", str(self.contract),
            "--preflight", "--dry-run", "--json"], cwd=ROOT, env=environment,
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["result"], "PASS")
        self.assertFalse(value["provider_started"])
        self.assertEqual(value["next_authorized_action"], "RETURN_TO_AUTHORIZED_OPERATOR_BOUNDARY")
        self.assertFalse(nested.exists())
        after = subprocess.run(["git", "status", "--porcelain=v1"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout
        self.assertEqual(after, before)

    def _succession_context(self):
        package = {
            "provider_id": codex_adapter.PROVIDER_ID, "provider_session_id": "LIFECYCLE-SESSION",
            "provider_invocation_id": "LIFECYCLE-INVOCATION", "package_digest": "package-digest",
            "execution_id": "EXECUTION", "execution_session_id": "EXECUTION-SESSION",
            "repository_identity": "homelab", "mission_id": "MISSION-TEST", "wop_id": "WOP-TEST",
            "authority": {"integrity": "PASS"},
        }
        plan = self._resolve(lifecycle_binding=package)
        process = type("Process", (), {"pid": 99999991})()
        diagnostics = {"provider_pid": 99999992, "command": plan["command"],
                       "environment": {}, "control_socket": None, "remote_endpoint": None}
        return package, plan, process, diagnostics

    def test_normal_abnormal_historical_and_repeated_session_succession(self):
        package, plan, process, diagnostics = self._succession_context()
        runtime = self.base / "succession"
        with patch.object(codex_adapter, "_package", return_value=package), \
             patch.object(codex_adapter, "resolve_provider_invocation_contract", return_value=plan), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, diagnostics)):
            a = codex_adapter.start(ROOT, "MISSION-TEST", runtime_root=runtime, work_contract=self.contract)
            codex_adapter.stop(ROOT, "MISSION-TEST", runtime_root=runtime)
            b = codex_adapter.start(ROOT, "MISSION-TEST", runtime_root=runtime, work_contract=self.contract)
            current_b = codex_adapter.current_session(ROOT, "MISSION-TEST", runtime_root=runtime)
            self.assertNotEqual(a["session_id"], b["session_id"])
            self.assertNotEqual(a["provider_invocation_id"], b["provider_invocation_id"])
            self.assertEqual(current_b["session_id"], b["session_id"])
            failed = dict(current_b, state="FAILED", session_disposition="HISTORICAL")
            codex_adapter._save(runtime, failed)
            c = codex_adapter.start(ROOT, "MISSION-TEST", runtime_root=runtime, work_contract=self.contract)
            self.assertNotEqual(c["session_id"], b["session_id"])
            codex_adapter.stop(ROOT, "MISSION-TEST", runtime_root=runtime)
            d = codex_adapter.start(ROOT, "MISSION-TEST", runtime_root=runtime, work_contract=self.contract)
            self.assertNotEqual(d["session_id"], c["session_id"])
        history = codex_adapter._all_sessions(runtime, "MISSION-TEST")
        self.assertEqual(len(history), 4)

    def test_active_collision_fails_closed_without_fallback(self):
        package, plan, process, diagnostics = self._succession_context()
        runtime = self.base / "collision"
        changed = copy.deepcopy(plan)
        changed["work_contract_digest"] = "different-authority"
        changed["plan_digest"] = "different-plan"
        with patch.object(codex_adapter, "_package", return_value=package), \
             patch.object(codex_adapter, "_launch_handshake", return_value=(process, diagnostics)), \
             patch.object(codex_adapter, "resolve_provider_invocation_contract", side_effect=[plan, changed]):
            codex_adapter.start(ROOT, "MISSION-TEST", runtime_root=runtime, work_contract=self.contract)
            with self.assertRaises(codex_adapter.CodexAdapterError) as raised:
                codex_adapter.start(ROOT, "MISSION-TEST", runtime_root=runtime, work_contract=self.contract)
        self.assertEqual(raised.exception.code, "ACTIVE_SESSION_PROTECTION")

    def test_broker_preserves_argument_vector_and_classifies_completion(self):
        for exit_code, expected in ((0, "NORMAL"), (7, "ABNORMAL")):
            case = self.base / f"broker-{exit_code}"
            case.mkdir()
            provider = case / "provider"
            provider.write_text(
                "#!/usr/bin/env python3\nimport json,sys\n"
                "line=sys.stdin.readline(); request=json.loads(line)\n"
                "print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':{}}),flush=True)\n"
                f"raise SystemExit({exit_code})\n", encoding="utf-8")
            provider.chmod(0o755)
            ready, exited = case / "ready.json", case / "exited.json"
            arguments = ["app-server", "--strict-config", "--listen", "stdio://"]
            command = ["python3", "-m", "scripts.lib.emp.codex_app_server_broker",
                       "--root", str(ROOT), "--codex-home", str(case / "home"),
                       "--log", str(case / "log"), "--ready", str(ready),
                       "--exited", str(exited), "--control", str(case / "control.sock"),
                       "--codex-bin", str(provider)]
            command.extend(f"--provider-argument={item}" for item in arguments)
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=10)
            if result.returncode == 1 and ready.exists() and json.loads(ready.read_text(encoding="utf-8")).get("error_type") == "PermissionError":
                self.skipTest("sandbox does not permit broker Unix control socket")
            self.assertEqual(result.returncode, exit_code if exit_code else 0,
                             result.stderr + (ready.read_text(encoding="utf-8") if ready.exists() else "no ready record"))
            self.assertEqual(json.loads(ready.read_text(encoding="utf-8"))["command"],
                             [str(provider), *arguments])
            completion = json.loads(exited.read_text(encoding="utf-8"))
            self.assertEqual(completion["completion"], expected)
            self.assertEqual(completion["result"], "PASS" if exit_code == 0 else "FAIL")


if __name__ == "__main__":
    unittest.main()
