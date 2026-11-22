"""Synthetic offline R&I recipient-scope guard cases."""
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

    def test_audience_must_match_expected_recipient(self):
        item = PublicationScope(**dict(self.good, audience=Recipient.TRADING_TECHNOLOGY))
        self.assertIn("wrong_recipient", scope_blockers(item, Recipient.AI_REVENUE))

    def test_organization_cannot_receive_company_private_context(self):
        item = PublicationScope(**dict(
            self.good, recipient=Recipient.ORGANIZATION, audience=Recipient.ORGANIZATION,
        ))
        self.assertIn("organization_private_context", scope_blockers(item, Recipient.ORGANIZATION))

    def test_unknown_or_raw_recipient_values_block(self):
        for overrides, expected in (
            ({"recipient": "AI_REVENUE"}, Recipient.AI_REVENUE),
            ({"audience": "AI_REVENUE"}, Recipient.AI_REVENUE),
            ({}, "AI_REVENUE"),
            ({}, []),
            ({"recipient": "UNKNOWN", "audience": "UNKNOWN"}, "UNKNOWN"),
        ):
            with self.subTest(overrides=overrides, expected=expected):
                item = PublicationScope(**dict(self.good, **overrides))
                self.assertIn("invalid_recipient_scope", scope_blockers(item, expected))

    def test_malformed_private_scope_blocks(self):
        for value in (None, set(), frozenset({"AI_REVENUE"}),
                      frozenset({Recipient.ORGANIZATION})):
            with self.subTest(value=value):
                item = PublicationScope(**dict(self.good, private_company_scopes=value))
                self.assertIn("invalid_private_company_scopes",
                              scope_blockers(item, Recipient.AI_REVENUE))

    def test_truthy_values_are_not_verified_evidence(self):
        item = PublicationScope(**dict(
            self.good, independently_reviewed="false", approved_for_publication=1,
            fresh="false", digest_verified="false",
        ))
        self.assertEqual(scope_blockers(item, Recipient.AI_REVENUE), (
            "independent_review_missing", "publication_not_approved", "stale", "digest_unverified",
        ))

    def test_non_text_publication_id_blocks(self):
        item = PublicationScope(**dict(self.good, publication_id=None))
        self.assertIn("missing_publication_id", scope_blockers(item, Recipient.AI_REVENUE))


if __name__ == "__main__":
    unittest.main()
