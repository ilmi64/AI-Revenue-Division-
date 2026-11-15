import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_division_integrations import build_report

class DivisionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        cls.registry=json.loads((root/"division-registry.json").read_text())
        cls.dependencies=json.loads((root/"dependency-map.json").read_text())
        cls.framework=json.loads((root/"operating-framework.json").read_text())

    def test_every_dependency_has_provider_link_and_triggered_handoff(self):
        report=build_report(self.registry,self.dependencies,self.framework)
        self.assertTrue(report["validated"],report["errors"])
        self.assertEqual(report["dependency_edge_count"],32)
        self.assertEqual(report["connected_edge_count"],32)
        self.assertEqual(report["disconnected_edge_count"],0)

    def test_tisrd_is_a_separate_research_only_division_with_connected_handoffs(self):
        tisrd = next(x for x in self.registry["divisions"] if x["id"] == "tisrd")
        assessment = next(x for x in json.loads((Path(__file__).resolve().parents[1] / "readiness-register.json").read_text())["division_assessments"] if x["division_id"] == "tisrd")
        self.assertEqual(tisrd["status"], "building")
        self.assertEqual(assessment["verified_status"], "building")
        self.assertTrue(tisrd["approval_boundary"].startswith("Read-only research and paper replication only"))
        tisrd_edges = [edge for edge in build_report(self.registry, self.dependencies, self.framework)["edges"] if edge["consumer_division"] == "tisrd"]
        self.assertEqual(len(tisrd_edges), 4)
        self.assertTrue(all(edge["connected"] for edge in tisrd_edges))

    def test_missing_provider_link_is_reported(self):
        dependencies=json.loads(json.dumps(self.dependencies))
        provider=next(x for x in dependencies["divisions"] if x["division_id"]=="ai-revenue")
        provider["provides_to"].remove("ecommerce")
        report=build_report(self.registry,dependencies,self.framework)
        self.assertFalse(report["validated"])
        self.assertTrue(any("provides_to" in error for error in report["errors"]))

    def test_missing_handoff_is_reported(self):
        framework=json.loads(json.dumps(self.framework))
        consumer=next(x for x in framework["divisions"] if x["id"]=="finance")
        consumer["handoffs"]=[h for h in consumer["handoffs"] if h["to"]!="research"]
        report=build_report(self.registry,self.dependencies,framework)
        self.assertFalse(report["validated"])
        self.assertTrue(any("no triggered artifact handoff" in error for error in report["errors"]))

if __name__=="__main__":
    unittest.main()
