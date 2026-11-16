"""Offline regression tests; no network or GitHub Actions required."""
import unittest
from validator import validate, load

class WorkforceContractTests(unittest.TestCase):
    def test_registry_and_roles_are_consistent(self):
        self.assertEqual(validate(), [])

    def test_qwen_and_llama_states_are_not_overstated(self):
        models = {m["id"]: m for m in load("model-registry.json")["models"]}
        self.assertEqual(models["qwen-primary-pilot"]["status"],
                         "integrated_in_main_unverified_end_to_end")
        self.assertEqual(models["llama-review-candidate"]["status"],
                         "evaluation_candidate")
        self.assertEqual(models["llama-review-candidate"]["deployment"],
                         "not_installed_or_verified")

    def test_no_paid_services_are_enabled(self):
        policy = load("model-registry.json")["policy"]
        self.assertEqual(policy["incremental_spend_cad"], 0)
        self.assertFalse(policy["paid_apis"])
        self.assertFalse(policy["paid_trials"])

    def test_all_eleven_divisions_are_present(self):
        self.assertEqual(len(load("agent-roles.json")["divisions"]), 11)

if __name__ == "__main__":
    unittest.main()
