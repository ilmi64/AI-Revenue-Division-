"""Offline tests for organisation risk, incident and evidence registers."""
import copy
import json
import unittest

from validate_registers import (
    EVIDENCE_REQUIRED, INCIDENT_REQUIRED, RISK_REQUIRED,
    INCIDENT_PATH, EVIDENCE_PATH, RISK_PATH, validate_registers,
)


class RegisterValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.incidents = json.loads(INCIDENT_PATH.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        cls.risks = json.loads(RISK_PATH.read_text(encoding="utf-8"))

    def test_current_empty_incident_and_evidence_registers_and_risk_baseline_pass(self):
        self.assertEqual(validate_registers(self.incidents, self.evidence, self.risks), [])

    def test_duplicate_incident_id_fails(self):
        incidents = copy.deepcopy(self.incidents)
        incidents["records"] = [
            {key: "2026-11-16T00:00:00Z" for key in INCIDENT_REQUIRED}
        ] * 2
        for row in incidents["records"]:
            row.update({
                "incident_id": "INC-1", "reporting_division": "risk",
                "affected_divisions": [], "severity": "SEV3", "status": "detected",
                "facts": [], "hypotheses": [], "evidence_references": [],
            })
        self.assertTrue(any("incident record IDs must be unique" in e for e in
                            validate_registers(incidents, self.evidence, self.risks)))

    def test_unknown_evidence_reference_fails(self):
        risks = copy.deepcopy(self.risks)
        risks["records"][0]["evidence_references"] = ["EVD-MISSING"]
        self.assertTrue(any("unknown evidence reference" in e for e in
                            validate_registers(self.incidents, self.evidence, risks)))

    def test_unknown_division_fails(self):
        risks = copy.deepcopy(self.risks)
        risks["records"][0]["division_id"] = "made-up"
        self.assertTrue(any("unknown division" in e for e in
                            validate_registers(self.incidents, self.evidence, risks)))

    def test_secret_fields_are_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["api_secret"] = "never-store-this"
        self.assertTrue(any("prohibited secret field" in e for e in
                            validate_registers(self.incidents, evidence, self.risks)))


if __name__ == "__main__":
    unittest.main()
