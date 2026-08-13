"""Recognition corrective qualification and fail-closed vectors."""

from pathlib import Path
import hashlib
import json
import shutil
from unittest.mock import patch

import pytest

from scripts.lib.emp.repository_state_view import project
from scripts.lib.eos import maturity_recognition as recognition


ROOT = Path(__file__).resolve().parents[2]


def test_complete_maturity_chain_is_recognized_without_authority_promotion():
    value = recognition.resolve(ROOT)
    assert value["result"] == "PASS"
    assert value["roadmap"]["id"] == "ESC-ROADMAP-001"
    assert value["roadmap"]["role"] == "CURRENT_CANONICAL_ENGINEERING_ROADMAP"
    assert value["roadmap"]["approval"] == "APPROVED"
    assert value["roadmap"]["adoption"] == "ACTIVE"
    assert value["roadmap"]["executable"] is True
    assert value["wop"]["recognized"] and value["eens"]["recognized"]
    assert value["integration"]["recognized"]
    assert value["qualification"]["recognized"]
    assert value["c06_review"]["consumed"]
    assert value["integration"]["accepted"] is True
    assert value["approval"]["decision"] == "APPROVE"
    assert value["c18_state"]["after"] == "ACCEPTED_FOR_CANONICAL_INTEGRATION_ADOPTION"
    assert value["authority"]["c18_separate_authority_required"] is False
    assert value["authority"]["cr48_execution_authorized"] is False
    assert value["next_authorized_action"] == "REVIEW_REBASED_C06_WOP_EENS_FOUNDATIONAL_DEVELOPMENT_BOUNDARY"


def test_repository_projection_exposes_the_same_recognition():
    value = project(ROOT)
    maturity = value["canonical_maturity"]
    assert maturity["result"] == "PASS"
    assert maturity["roadmap"]["id"] == "ESC-ROADMAP-001"
    assert maturity["next_authorized_action"] == "REVIEW_REBASED_C06_WOP_EENS_FOUNDATIONAL_DEVELOPMENT_BOUNDARY"


def test_next_action_is_derived_from_canonical_state():
    original = recognition._load

    def altered(root, relative):
        value, digest = original(root, relative)
        if relative == recognition.STATE:
            value = dict(value)
            value["next_authorized_action"] = "REVIEW_C18_INTEGRATION_AUTHORITY_BOUNDARY_TEST_VECTOR"
        return value, digest

    with patch.object(recognition, "_load", side_effect=altered):
        value = recognition.resolve(ROOT)
    assert value["next_authorized_action"] == "REVIEW_REBASED_C06_WOP_EENS_FOUNDATIONAL_DEVELOPMENT_BOUNDARY"


def test_c18_receipt_integrity_missing_and_bounded_authority_fail_closed(tmp_path):
    receipt_path = tmp_path / recognition.APPROVAL_RECEIPT
    receipt_path.parent.mkdir(parents=True)
    source = ROOT / recognition.APPROVAL_RECEIPT
    shutil.copy2(source, receipt_path)

    receipt, _ = recognition._load_approval_receipt(
        tmp_path, "e4e2164d20386c0643f307f39161db81263e714cd0ff75578516ce4f318119ed"
    )
    assert receipt["integration_accepted"] is True

    receipt_path.unlink()
    with pytest.raises(recognition.MaturityRecognitionError, match="unavailable"):
        recognition._load_approval_receipt(tmp_path, "x")

    shutil.copy2(source, receipt_path)
    receipt_path.write_text("{malformed", encoding="utf-8")
    with pytest.raises(recognition.MaturityRecognitionError, match="malformed"):
        recognition._load_approval_receipt(tmp_path, "x")

    value = json.loads(source.read_text(encoding="utf-8"))
    value["implementation_authorized"] = True
    unsigned = {key: item for key, item in value.items() if key != "receipt_digest"}
    value["receipt_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    receipt_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(recognition.MaturityRecognitionError, match="exceeds"):
        recognition._load_approval_receipt(
            tmp_path, "e4e2164d20386c0643f307f39161db81263e714cd0ff75578516ce4f318119ed"
        )

    value["implementation_authorized"] = False
    value["object_sha256"] = "0" * 64
    unsigned = {key: item for key, item in value.items() if key != "receipt_digest"}
    value["receipt_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    receipt_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(recognition.MaturityRecognitionError, match="bound"):
        recognition._load_approval_receipt(
            tmp_path, "e4e2164d20386c0643f307f39161db81263e714cd0ff75578516ce4f318119ed"
        )


@pytest.mark.parametrize("failure", [
    "missing_wop", "missing_eens", "wop_digest", "eens_digest", "malformed",
    "wrong_roadmap", "failed_c18_qualification", "missing_c06_review",
    "invalid_manifest",
])
def test_recognition_fail_closed(failure):
    original = recognition._load

    def altered(root, relative):
        if failure == "missing_wop" and relative == recognition.WOP:
            raise recognition.MaturityRecognitionError("authoritative maturity source unavailable")
        if failure == "missing_eens" and relative == recognition.EENS:
            raise recognition.MaturityRecognitionError("authoritative maturity source unavailable")
        value, digest = original(root, relative)
        if failure == "wop_digest" and relative == recognition.WOP:
            return value, "0" * 64
        if failure == "eens_digest" and relative == recognition.EENS:
            return value, "0" * 64
        if failure == "malformed" and relative == recognition.WOP:
            raise recognition.MaturityRecognitionError("malformed maturity source")
        if failure == "wrong_roadmap" and relative == recognition.ROADMAP:
            value = dict(value)
            value["roadmap_id"] = "WRONG"
        if failure == "failed_c18_qualification" and relative == recognition.QUALIFICATION:
            value = dict(value)
            value["status"] = "FAIL"
        if failure == "missing_c06_review" and relative == recognition.C06_REVIEW:
            value = dict(value)
            value["decision"] = ""
        if failure == "invalid_manifest" and relative == recognition.BINDING_MANIFEST:
            value = dict(value)
            value["sources"] = [{"path": recognition.WOP, "sha256": "0" * 64}]
        return value, digest

    with patch.object(recognition, "_load", side_effect=altered):
        with pytest.raises(recognition.MaturityRecognitionError):
            recognition.resolve(ROOT)
