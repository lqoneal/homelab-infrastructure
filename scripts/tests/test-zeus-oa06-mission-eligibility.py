#!/usr/bin/env python3
"""OA-06 deterministic mission eligibility qualification."""

from __future__ import annotations

import unittest

from scripts.lib.emp.mission_eligibility import MissionEligibilityError, classify


def candidate(**changes):
    value = {
        "mission_id": "MISSION-A",
        "candidate_state": "STAGED",
        "dependencies": [],
        "deferred": False,
        "admission_status": "ACCEPTED",
        "authority_status": "AUTHORIZED",
        "repository_match": True,
        "baseline_match": True,
        "resources_available": True,
        "blocking_conditions": [],
    }
    value.update(changes)
    return value


class OA06MissionEligibilityTests(unittest.TestCase):
    def test_all_four_classifications_are_deterministic(self):
        cases = (
            ("ELIGIBLE", candidate()),
            ("BLOCKED", candidate(dependencies=["MISSION-Z"])),
            ("DEFERRED", candidate(deferred=True)),
            ("INELIGIBLE", candidate(authority_status="UNAUTHORIZED")),
        )
        for expected, request in cases:
            first = classify(request, completed_missions=[])
            self.assertEqual(expected, first["classification"])
            self.assertEqual(first, classify(request, completed_missions=[]))
            self.assertEqual("NONE", first["protected_effect"])

    def test_ineligible_precedes_deferred_and_blocked(self):
        result = classify(
            candidate(
                deferred=True, dependencies=["MISSING"],
                admission_status="REJECTED",
            ),
            completed_missions=[],
        )
        self.assertEqual("INELIGIBLE", result["classification"])

    def test_deferred_precedes_blocked(self):
        result = classify(
            candidate(deferred=True, dependencies=["MISSING"]),
            completed_missions=[],
        )
        self.assertEqual("DEFERRED", result["classification"])

    def test_completed_dependency_becomes_eligible(self):
        result = classify(
            candidate(dependencies=["MISSION-Z"]),
            completed_missions=["MISSION-Z"],
        )
        self.assertEqual("ELIGIBLE", result["classification"])

    def test_malformed_and_unknown_inputs_fail_closed(self):
        for request in (
            {},
            candidate(deferred="false"),
            candidate(authority_status="MAYBE"),
            {**candidate(), "unexpected": True},
        ):
            with self.assertRaises(MissionEligibilityError):
                classify(request, completed_missions=[])


if __name__ == "__main__":
    unittest.main()
