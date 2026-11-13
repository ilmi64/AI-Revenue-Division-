import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_execution_log import build_report

class ExecutionLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.registry = json.loads((root / "division-registry.json").read_text())
        cls.queue = json.loads((root / "work-queue.json").read_text())
    def event(self, kind, stamp="2026-11-12T12:00:00-05:00", evidence=None):
        return {"event_id":"EV-1","task_id":"TECH-001","event_type":kind,"timestamp":stamp,
                "actor":"owner-confirmed-test","summary":"Test event","evidence":evidence or []}
    def test_empty_log_is_valid_and_reports_no_activity(self):
        r = build_report(self.registry, self.queue, {"events":[]})
        self.assertTrue(r["validated"], r["errors"]); self.assertEqual(r["event_count"], 0)
        self.assertEqual(len(r["divisions"]), 9)
    def test_started_requires_assigned_owner(self):
        r = build_report(self.registry, self.queue, {"events":[self.event("started")]})
        self.assertFalse(r["validated"])
        self.assertTrue(any("requires an assigned task owner" in e for e in r["errors"]))
    def test_completion_requires_evidence(self):
        queue = json.loads(json.dumps(self.queue))
        next(t for t in queue["tasks"] if t["id"]=="TECH-001")["owner_assignment"]="owner-confirmed"
        events=[self.event("started"), self.event("completed", "2026-11-12T13:00:00-05:00")]
        r=build_report(self.registry, queue, {"events":events})
        self.assertFalse(r["validated"])
        self.assertTrue(any("requires evidence" in e for e in r["errors"]))
    def test_valid_started_progress_completion_sequence(self):
        queue=json.loads(json.dumps(self.queue))
        next(t for t in queue["tasks"] if t["id"]=="TECH-001")["owner_assignment"]="owner-confirmed"
        events=[self.event("started"), self.event("progress","2026-11-12T12:30:00-05:00"),
                self.event("completed","2026-11-12T13:00:00-05:00",["https://example.invalid/evidence"])]
        for i,e in enumerate(events): e["event_id"]=f"EV-{i+1}"
        r=build_report(self.registry,queue,{"events":events})
        self.assertTrue(r["validated"],r["errors"]); self.assertEqual(r["task_state_from_events"]["TECH-001"],"completed")
    def test_timezone_required_and_duplicate_ids_rejected(self):
        a=self.event("started"); b=self.event("started", "2026-11-12T13:00:00-05:00")
        r=build_report(self.registry,self.queue,{"events":[a,b]})
        self.assertFalse(r["validated"])
        self.assertTrue(any("unique" in e for e in r["errors"]))
    def test_invalid_state_transition_rejected(self):
        r=build_report(self.registry,self.queue,{"events":[self.event("completed",evidence=["ref"])]})
        self.assertFalse(r["validated"])
        self.assertTrue(any("not allowed" in e for e in r["errors"]))
if __name__ == "__main__": unittest.main()
