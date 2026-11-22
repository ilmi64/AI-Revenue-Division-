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


if __name__ == "__main__":
    unittest.main()
