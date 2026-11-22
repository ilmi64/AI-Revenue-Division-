"""Authored verification cases; NOT EXECUTED. Requires separate approval."""
from decimal import Decimal
import unittest

from mini_review_evidence import EffortEntry, summarize_effort


class MiniReviewEvidenceTests(unittest.TestCase):
    def test_distinct_targets_and_rework(self):
        rows = [
            EffortEntry("S1", "producer", "draft", Decimal("150")),
            EffortEntry("S1", "reviewer", "qa", Decimal("30")),
            EffortEntry("S1", "producer", "correction", Decimal("15"), True),
        ]
        result = summarize_effort("S1", rows)
        self.assertEqual(result.active_minutes, Decimal("195"))
        self.assertEqual(result.rework_minutes, Decimal("15"))
        self.assertEqual(result.rework_share, Decimal("15") / Decimal("195"))
        self.assertEqual(result.target_180_variance_minutes, Decimal("15"))
        self.assertEqual(result.rehearsal_210_variance_minutes, Decimal("-15"))

    def test_reject_mixed_exercises(self):
        with self.assertRaises(ValueError):
            summarize_effort("S1", [EffortEntry("S2", "p", "draft", Decimal("1"))])

    def test_reject_invalid_minutes(self):
        for value in (Decimal("-1"), Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize_effort("S1", [EffortEntry("S1", "p", "draft", value)])

    def test_zero_effort_does_not_invent_rework_share(self):
        result = summarize_effort("S1", [EffortEntry("S1", "p", "draft", Decimal("0"))])
        self.assertIsNone(result.rework_share)


if __name__ == "__main__":
    unittest.main()
