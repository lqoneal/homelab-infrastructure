"""Read-only Operational Alpha capability-registry services."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any
import yaml
PATH = "engineering/capabilities/operational-alpha-capability-registry.yaml"
class CapabilityRegistryError(ValueError): pass
def load(root: Path | str) -> dict[str, Any]:
    root=Path(root)
    try: value=yaml.safe_load((root/PATH).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error: raise CapabilityRegistryError(str(error)) from error
    if not isinstance(value,dict) or value.get("registry_id") != "OPERATIONAL-ALPHA-CAPABILITY-REGISTRY" or not isinstance(value.get("capabilities"),list): raise CapabilityRegistryError("capability registry is invalid")
    # Capability services consume the EMM-bound source rather than a path-only copy.
    from scripts.lib.eos.convergence_runtime import ConvergenceRuntime, ConvergenceRuntimeError
    try:
        entity=ConvergenceRuntime(root)._entity("CapabilityRegistry", value["registry_id"], value["revision"])
        ConvergenceRuntime(root)._source(entity)
    except ConvergenceRuntimeError as error: raise CapabilityRegistryError(str(error)) from error
    return value
def _digest(root): return hashlib.sha256((Path(root)/PATH).read_bytes()).hexdigest()
def list_capabilities(root):
    value=load(root); return {"registry_id":value["registry_id"],"revision":str(value["revision"]),"digest":_digest(root),"capabilities":[{key:item[key] for key in ("capability_id","name","lifecycle","runtime_availability","regression_status")} for item in value["capabilities"]]}
def show(root, capability_id):
    value=load(root); matches=[item for item in value["capabilities"] if item.get("capability_id")==capability_id]
    if len(matches)!=1: raise CapabilityRegistryError("capability not found")
    return {"registry_id":value["registry_id"],"digest":_digest(root),"capability":matches[0]}
def verify(root, capability_id=None):
    value=load(root); items=value["capabilities"] if capability_id is None else [show(root,capability_id)["capability"]]
    required={"capability_id","name","description","lifecycle","mission_introduced","verification_commands","expected_verification_results","dependencies","owning_controlled_documentation","runtime_availability","associated_evidence","regression_status","capability_history"}
    failures=[item.get("capability_id","UNKNOWN") for item in items if not required.issubset(item)]
    return {"registry_id":value["registry_id"],"digest":_digest(root),"verified":[item["capability_id"] for item in items],"result":"PASS" if not failures else "FAIL","failures":failures}
def history(root):
    value=load(root); return {"registry_id":value["registry_id"],"history":[{"capability_id":item["capability_id"],"history":item["capability_history"]} for item in value["capabilities"]]}
def diff(root,left,right):
    value=load(root)
    if left != right: raise CapabilityRegistryError("only the current authoritative registry revision is available")
    return {"registry_id":value["registry_id"],"from":left,"to":right,"added":[],"removed":[],"changed":[],"result":"NO_DIFFERENCE"}
