"""Offline regression tests; no network or GitHub Actions required."""
import json
import unittest
from validator import validate, load

class WorkforceContractTests(unittest.TestCase):
    def test_registry_and_roles_are_consistent(self):
        self.assertEqual(validate(), [])

    def test_qwen_and_llama_states_are_not_overstated(self):
        models = {m["id"]: m for m in load("model-registry.json")["models"]}
        self.assertEqual(models["qwen-primary-pilot"]["status"],
                         "integrated_in_main_unverified_end_to_end")
        self.assertEqual(models["qwen-primary-pilot"]["evidence"]["pull_request"], 2)
        self.assertEqual(models["llama-review-candidate"]["status"], "evaluation_candidate")
        self.assertEqual(models["llama-review-candidate"]["deployment"], "not_installed_or_verified")

    def test_no_paid_services_are_enabled(self):
        policy = load("model-registry.json")["policy"]
        self.assertEqual(policy["incremental_spend_cad"], 0)
        self.assertFalse(policy["paid_apis"])
        self.assertFalse(policy["paid_trials"])

    def test_all_eleven_divisions_match_canonical_registry(self):
        roles = load("agent-roles.json")
        with (ROOT.parent / "division-registry.json").open(encoding="utf-8") as handle:
            canonical = json.load(handle)
        self.assertEqual(set(roles["divisions"]), {d["name"] for d in canonical["divisions"]})
        self.assertEqual(set(roles["division_role_map"]), {d["id"] for d in canonical["divisions"]})

    def test_role_map_references_known_roles(self):
        roles = load("agent-roles.json")
        known = {r["id"] for r in roles["roles"]}
        self.assertTrue(set(roles["division_role_map"].values()).issubset(known))

if __name__ == "__main__":
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent
    unittest.main()
