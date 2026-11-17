import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_organisation_dashboard import build_ai_workforce_report
class AIWorkforceIntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  ai=ROOT/"ai-workforce"
  cls.models=json.loads((ai/"model-registry.json").read_text(encoding="utf-8"))
  cls.roles=json.loads((ai/"agent-roles.json").read_text(encoding="utf-8"))
  cls.registry=json.loads((ROOT/"division-registry.json").read_text(encoding="utf-8"))
 def test_registry_and_roles_match_all_divisions(self):
  report=build_ai_workforce_report(self.models,self.roles,self.registry)
  self.assertEqual(report["status"],"validated",report["errors"])
  self.assertEqual(report["model_count"],3);self.assertEqual(report["role_count"],5)
 def test_qwen_remains_unverified(self):
  report=build_ai_workforce_report(self.models,self.roles,self.registry)
  self.assertEqual(next(m for m in report["models"] if m["id"]=="qwen-primary-pilot")["status"],"integrated_in_main_unverified_end_to_end")
 def test_llama_remains_candidate(self):
  report=build_ai_workforce_report(self.models,self.roles,self.registry)
  llama=next(m for m in report["models"] if m["id"]=="llama-review-candidate")
  self.assertEqual(llama["status"],"evaluation_candidate");self.assertEqual(llama["deployment"],"not_installed_or_verified")
 def test_nonzero_spend_is_rejected(self):
  models=json.loads(json.dumps(self.models));models["policy"]["incremental_spend_cad"]=1
  self.assertEqual(build_ai_workforce_report(models,self.roles,self.registry)["status"],"invalid")
 def test_unknown_model_reference_is_rejected(self):
  roles=json.loads(json.dumps(self.roles));roles["roles"][1]["model_id"]="unknown-model"
  self.assertEqual(build_ai_workforce_report(self.models,roles,self.registry)["status"],"invalid")
 def test_unconfigured_call_is_safe(self):
  self.assertEqual(build_ai_workforce_report()["status"],"not_configured")
if __name__=="__main__":unittest.main()
