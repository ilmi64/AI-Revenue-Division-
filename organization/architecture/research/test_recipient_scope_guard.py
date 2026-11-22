"""Authored offline R&I guard cases; NOT EXECUTED."""
import unittest
from recipient_scope_guard import Recipient, PublicationScope, scope_blockers


class RecipientScopeGuardTests(unittest.TestCase):
    def setUp(self):
        self.good = dict(
            publication_id="synthetic-001", recipient=Recipient.AI_REVENUE,
            audience=Recipient.AI_REVENUE, independently_reviewed=True,
            approved_for_publication=True, fresh=True, digest_verified=True,
            private_company_scopes=frozenset({Recipient.AI_REVENUE}),
        )

    def test_company_scoped_clean_publication(self):
        self.assertEqual(scope_blockers(PublicationScope(**self.good), Recipient.AI_REVENUE), ())

    def test_cross_company_context_blocks(self):
        item = PublicationScope(**dict(self.good, private_company_scopes=frozenset({
            Recipient.AI_REVENUE, Recipient.TRADING_TECHNOLOGY
        })))
        self.assertIn("cross_company_private_context", scope_blockers(item, Recipient.AI_REVENUE))

    def test_wrong_recipient_blocks(self):
        item = PublicationScope(**self.good)
        self.assertIn("wrong_recipient", scope_blockers(item, Recipient.TRADING_TECHNOLOGY))

    def test_unreviewed_and_stale_block(self):
        item = PublicationScope(**dict(self.good, independently_reviewed=False, fresh=False))
        self.assertEqual(
            scope_blockers(item, Recipient.AI_REVENUE),
            ("independent_review_missing", "stale"),
        )


    def test_malformed_scope_fails_closed(self):
        self.assertEqual(scope_blockers(None, Recipient.AI_REVENUE), ("invalid_publication_scope",))
        self.assertEqual(scope_blockers(PublicationScope(**self.good), "AI_REVENUE"), ("invalid_expected_recipient",))
        bad = PublicationScope(**dict(self.good, publication_id=None))
        self.assertIn("missing_publication_id", scope_blockers(bad, Recipient.AI_REVENUE))
        bad = PublicationScope(**dict(self.good, private_company_scopes=["AI_REVENUE"]))
        self.assertIn("invalid_private_scope", scope_blockers(bad, Recipient.AI_REVENUE))
        bad = PublicationScope(**dict(self.good, independently_reviewed=1))
        self.assertIn("invalid_independently_reviewed", scope_blockers(bad, Recipient.AI_REVENUE))
        bad = PublicationScope(**dict(self.good, recipient="AI_REVENUE"))
        self.assertIn("invalid_recipient_type", scope_blockers(bad, Recipient.AI_REVENUE))

if __name__ == "__main__":
    unittest.main()
