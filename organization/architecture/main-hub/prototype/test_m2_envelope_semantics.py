"""Authored only, not executed: offline envelope semantic regression cases."""
import copy
import json
import unittest
from pathlib import Path

from m2_envelope_semantics import EnvelopeSemanticError, check_m2_envelope_semantics

ENVELOPE = Path(__file__).resolve().parents[1] / "fixtures" / "main-hub-envelope.example.json"


class M2EnvelopeSemanticTests(unittest.TestCase):
    def setUp(self):
        self.envelope = json.loads(ENVELOPE.read_text(encoding="utf-8"))

    def test_exact_fixture_semantics(self):
        check_m2_envelope_semantics(self.envelope)

    def test_duplicate_company_record(self):
        self.envelope["company_registry"][1] = copy.deepcopy(self.envelope["company_registry"][0])
        with self.assertRaises(EnvelopeSemanticError):
            check_m2_envelope_semantics(self.envelope)

    def test_unknown_workstream_dependency(self):
        self.envelope["workstreams"][0]["depends_on"] = ["WS-DOES-NOT-EXIST"]
        with self.assertRaisesRegex(EnvelopeSemanticError, "unknown workstream dependency"):
            check_m2_envelope_semantics(self.envelope)

    def test_self_dependency(self):
        item = self.envelope["workstreams"][0]
        item["depends_on"] = [item["workstream_id"]]
        with self.assertRaisesRegex(EnvelopeSemanticError, "self-dependent"):
            check_m2_envelope_semantics(self.envelope)

    def test_decision_unknown_workstream(self):
        # The committed fixture intentionally has no decisions; inject a synthetic one.
        self.envelope["decisions"].append({"decision_id": "DEC-SYNTHETIC", "workstream_ids": ["WS-UNKNOWN"]})
        with self.assertRaisesRegex(EnvelopeSemanticError, "decision references unknown"):
            check_m2_envelope_semantics(self.envelope)


if __name__ == "__main__":
    unittest.main()
