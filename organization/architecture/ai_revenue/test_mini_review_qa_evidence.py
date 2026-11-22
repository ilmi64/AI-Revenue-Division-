"""Synthetic QA evidence unit tests."""
from dataclasses import replace
import unittest

from mini_review_evidence import QA_CRITERIA, QACriterionEvidence, summarize_qa_evidence


class MiniReviewQAEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.criteria = [QACriterionEvidence(key, "PASS", f"fixture/{key}") for key in QA_CRITERIA]

    def assess(self, **overrides):
        args = dict(
            draft_ref="draft-v1",
            producer_id="producer",
            reviewer_id="reviewer",
            evidence_class="SYNTHETIC",
            criteria=self.criteria,
            unresolved_critical_defects=0,
            unresolved_major_defects=0,
        )
        args.update(overrides)
        return summarize_qa_evidence("EXERCISE-1", **args)

    def test_complete_synthetic_record_preserves_draft_identity(self):
        summary = self.assess()
        self.assertEqual(summary.exercise_id, "EXERCISE-1")
        self.assertEqual(summary.draft_ref, "draft-v1")
        self.assertEqual(summary.reviewer_id, "reviewer")
        self.assertEqual(summary.blockers, ())

    def test_open_defects_and_self_review_block(self):
        result = self.assess(
            reviewer_id=" PRODUCER ", unresolved_critical_defects=1, unresolved_major_defects=2,
        )
        self.assertEqual(result.blockers, (
            "reviewer_matches_producer", "unresolved_critical_defects", "unresolved_major_defects",
        ))

    def test_incomplete_and_failed_criteria_report_blockers(self):
        self.criteria[0] = replace(self.criteria[0], evidence_ref=" ")
        self.criteria[1] = replace(self.criteria[1], disposition="FAIL")
        self.criteria[2] = replace(self.criteria[2], disposition="BLOCKED")
        self.criteria.pop()
        self.assertEqual(self.assess().blockers, (
            "missing_evidence:scope_conformity",
            "fail:source_traceability",
            "blocked:calculation_integrity",
            "missing:commercial_honesty",
        ))

    def test_na_requires_rationale_and_cannot_clear_required_scope(self):
        self.criteria[0] = replace(self.criteria[0], disposition="NOT_APPLICABLE", rationale="text")
        idx = QA_CRITERIA.index("halal_or_regulated_issue_flags")
        self.criteria[idx] = replace(self.criteria[idx], disposition="NOT_APPLICABLE")
        self.assertEqual(self.assess().blockers, (
            "required:scope_conformity", "missing_rationale:halal_or_regulated_issue_flags",
        ))
        self.criteria[idx] = replace(self.criteria[idx], rationale="Fixture has no regulated activity")
        self.assertEqual(self.assess().blockers, ("required:scope_conformity",))

    def test_rejects_non_synthetic_and_invalid_defect_count(self):
        for override in (
            {"evidence_class": "CUSTOMER"},
            {"unresolved_critical_defects": False},
            {"unresolved_major_defects": -1},
            {"draft_ref": ""},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.assess(**override)

    def test_rejects_duplicate_unknown_and_invalid_dispositions(self):
        for record in (
            self.criteria[0],
            QACriterionEvidence("unknown", "PASS", "fixture"),
        ):
            with self.subTest(record=record), self.assertRaises(ValueError):
                self.assess(criteria=[*self.criteria, record])
        self.criteria[0] = replace(self.criteria[0], disposition="WAIVED")
        with self.assertRaises(ValueError):
            self.assess()
