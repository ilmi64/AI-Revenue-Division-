import unittest
import tempfile
from pathlib import Path

from specialist_research.unified_intake import build_unified_intake, validate_handover
from specialist_research.test_replay import NOW, obs, source_registry, flow_event, flow_review, FLOW_REGISTRY
from specialist_research.snapshot_history import append_snapshot
from specialist_research.incident_event_ledger import append_event


class UnifiedIntakeTests(unittest.TestCase):
    def four_desk_rows(self):
        return [
            obs("crypto_spot", "SOL-USDC"),
            obs("fx_spot", "EUR-USD"),
            obs("index_cash", "FIXTURE500"),
            obs("xauusd_spot", "XAUUSD-FIXTURE"),
        ]

    def build(self, rows=None, **kwargs):
        rows = rows or self.four_desk_rows()
        version = kwargs.pop("expected_portfolio_version", 7)
        return build_unified_intake(rows, NOW, source_registry(rows),
                                    expected_portfolio_version=version, **kwargs)

    def oanda_closeout_transaction_replay(self, post_orders=None):
        return {
            "account_id": "acct-1",
            "pre_closeout_pending_orders": [{
                "id": "sl-gold", "state": "PENDING", "type": "STOP_LOSS", "tradeID": "trade-gold",
            }],
            "post_closeout_pending_orders": [] if post_orders is None else post_orders,
            "transactions": [
                {"id": "101", "accountID": "acct-1", "time": "2026-11-17T11:59:57Z",
                 "type": "ORDER_FILL", "reason": "MARKET_ORDER_MARGIN_CLOSEOUT",
                 "orderID": "100", "tradesClosed": [{"tradeID": "trade-gold", "units": "1"}]},
                {"id": "102", "accountID": "acct-1", "time": "2026-11-17T11:59:57Z",
                 "type": "ORDER_CANCEL", "orderID": "sl-gold", "reason": "LINKED_TRADE_CLOSED"},
            ],
            "transaction_id_start_exclusive": "100", "transaction_id_end_inclusive": "102",
            "reported_last_transaction_id": "102",
            "transaction_range_complete": True, "transaction_range_unfiltered": True,
            "pre_closeout_orders_complete": True, "post_closeout_orders_complete": True,
            "pre_closeout_snapshot_timestamp_utc": "2026-11-17T11:59:56Z",
            "post_closeout_snapshot_timestamp_utc": "2026-11-17T11:59:58Z",
            "evaluated_at_utc": "2026-11-17T12:00:00Z", "max_snapshot_age_seconds": 60,
        }

    def oanda_pending_snapshot(self, orders=None):
        return {
            "pending_orders": [] if orders is None else orders,
            "liquidated_trade_ids": ["trade-gold"], "remaining_open_trade_ids": [],
            "remaining_open_trade_ids_complete": True, "reported_pending_order_count": len(orders or []),
            "account_hedging_enabled": False,
            "source_timestamp_utc": "2026-11-17T11:59:58Z",
            "evaluated_at_utc": "2026-11-17T12:00:00Z", "max_snapshot_age_seconds": 60,
            "pending_orders_complete": True, "closeout_occurred": True,
        }

    def test_builds_one_snapshot_across_all_four_specialist_desks(self):
        result = self.build()
        self.assertEqual(result["desk_coverage"],
                         {"crypto": 1, "forex": 1, "indices": 1, "gold": 1})
        self.assertTrue(result["coverage_complete"])
        self.assertEqual(result["status"], "unverified")
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertEqual(result["authority"], "research_only_no_execution_authority")


    def test_portfolio_risk_unknown_is_visible_in_unified_snapshot(self):
        result = self.build()
        self.assertEqual(result["portfolio_risk"]["status"], "UNKNOWN")
        self.assertEqual(result["portfolio_risk"]["coverage"]["missing_risk_desks"],
                         ["crypto", "forex", "gold", "indices"])
        self.assertEqual(result["status"], "unverified")
        self.assertFalse(result["portfolio_risk"]["trade_authority"])

    def test_portfolio_limit_breach_escalates_to_global_occ_stop(self):
        rows = self.four_desk_rows()
        for index, row in enumerate(rows):
            row["portfolio_risk"] = {"positions": [{
                "position_id": "risk-position-" + str(index),
                "instrument_id": row["instrument_id"],
                "asset_class": ["crypto", "forex", "indices", "gold"][index],
                "instrument_type": row["instrument_type"],
                "valuation_basis": {
                    "crypto_spot": "spot_mark_to_market",
                    "fx_spot": "base_currency_units",
                    "index_cash": "cash_index_mark_to_market",
                    "xauusd_spot": "spot_ounces_or_grams",
                }[row["instrument_type"]],
                "units": 1.0,
                "side": "long",
                "notional": 100.0,
                "currency": "USD",
                "valuation_currency": "USD",
                "valuation_amount": 100.0,
                "exposure_group": "fixture-portfolio",
                "evidence_refs": ["fixture:risk:" + str(index)],
                "source_timestamp_utc": NOW,
            }]}
        risk_config = {"schema_version": "1.0.0", "limits": [{
            "scope": "portfolio", "metric": "gross_exposure",
            "valuation_currency": "USD", "max_value": 399.0,
        }], "stress_scenarios": [{
            "scenario_id": "fixture-risk-off",
            "shocks_by_asset_class": {"crypto": -0.2, "forex": 0.05, "indices": -0.1, "gold": 0.08},
        }]}
        correlations = [{
            "instrument_id_a": "SOL-USDC", "instrument_id_b": "EUR-USD",
            "correlation": 0.25, "observed_at_utc": NOW,
            "source_id": "fixture-correlation", "sample_count": 30,
            "lookback_window": "30d", "methodology": "pearson_returns",
            "evidence_refs": ["fixture:corr"],
        }]
        result = self.build(rows, portfolio_risk_config=risk_config,
                            correlation_evidence=correlations)
        self.assertEqual(result["portfolio_risk"]["status"], "HALT")
        self.assertEqual(result["portfolio_risk"]["instrument_normalization"]["status"], "INPUTS_VALIDATED_NOT_REPRICED")
        self.assertEqual(result["portfolio_risk"]["stress_testing"]["status"], "ASSESSED")
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any(stop["source"] == "portfolio_risk" for stop in result["active_stops"]))

    def test_oanda_margin_call_escalates_to_global_occ_stop(self):
        account_replay = {
            "account_currency": "CAD",
            "initial_positions": [
                {"position_id": "gold", "desk_id": "gold", "instrument_id": "XAUUSD"},
                {"position_id": "fx", "desk_id": "forex", "instrument_id": "EURUSD"},
            ],
            "observations": [{
                "timestamp_utc": "2026-11-17T11:59:56Z",
                "nav_mid": 900, "margin_used": 1000,
                "position_market_status": {"gold": "open", "fx": "open"},
                "trading_day_check": False,
            }],
        }
        result = self.build(oanda_account_margin_replay=account_replay)
        self.assertEqual(result["oanda_account_margin_audit"]["status"], "HALT")
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any(stop["source"] == "oanda_account_margin" for stop in result["active_stops"]))
        self.assertFalse(result["oanda_account_margin_audit"]["trade_authority"])

    def test_oanda_closeout_without_pending_order_snapshot_escalates_missing_reconciliation(self):
        account_replay = {
            "account_currency": "CAD",
            "initial_positions": [{"position_id": "gold", "desk_id": "gold", "instrument_id": "XAUUSD"}],
            "observations": [{
                "timestamp_utc": "2026-11-17T11:59:56Z", "nav_mid": 400, "margin_used": 1000,
                "position_market_status": {"gold": "open"}, "trading_day_check": False,
            }],
        }
        result = self.build(oanda_account_margin_replay=account_replay)
        self.assertEqual(result["oanda_account_margin_audit"]["report"]["status"], "CLOSEOUT_TRIGGERED")
        self.assertEqual(result["oanda_pending_order_audit"]["status"], "HALT")
        self.assertTrue(any(stop["reason"] == "POST_CLOSEOUT_PENDING_ORDER_RECONCILIATION_MISSING"
                            for stop in result["active_stops"]))

    def test_oanda_closeout_transaction_reconciliation_passes_through_unified_intake(self):
        result = self.build(
            oanda_pending_order_snapshot=self.oanda_pending_snapshot(),
            oanda_closeout_transaction_replay=self.oanda_closeout_transaction_replay(),
        )
        audit = result["oanda_closeout_transaction_audit"]
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["report"]["orders_confirmed_cancelled"][0]["order_id"], "sl-gold")
        self.assertFalse(audit["trade_authority"])
        self.assertFalse(result["trade_authority"])

    def test_oanda_closeout_transaction_snapshot_mismatch_escalates_occ(self):
        result = self.build(
            oanda_pending_order_snapshot=self.oanda_pending_snapshot([{
                "id": "new-entry", "state": "PENDING", "type": "STOP",
                "instrument": "XAU_USD", "units": "1", "positionFill": "OPEN_ONLY",
            }]),
            oanda_closeout_transaction_replay=self.oanda_closeout_transaction_replay(),
        )
        self.assertEqual(result["oanda_closeout_transaction_audit"]["status"], "HALT")
        self.assertTrue(result["global_stop_active"])
        self.assertTrue(any("snapshot differs" in error for error in result["oanda_closeout_transaction_audit"]["errors"]))

    def test_margin_closeout_requires_transaction_history_reconciliation(self):
        account_replay = {
            "account_currency": "CAD",
            "initial_positions": [{"position_id": "gold", "desk_id": "gold", "instrument_id": "XAUUSD"}],
            "observations": [{
                "timestamp_utc": "2026-11-17T11:59:56Z", "nav_mid": 400, "margin_used": 1000,
                "position_market_status": {"gold": "open"}, "trading_day_check": False,
            }],
        }
        result = self.build(
            oanda_account_margin_replay=account_replay,
            oanda_pending_order_snapshot=self.oanda_pending_snapshot(),
        )
        self.assertEqual(result["oanda_closeout_transaction_audit"]["status"], "HALT")
        self.assertTrue(any(stop["reason"] == "POST_CLOSEOUT_TRANSACTION_RECONCILIATION_MISSING"
                            for stop in result["active_stops"]))

    def test_margin_closeout_transaction_pass_does_not_clear_margin_stop(self):
        account_replay = {
            "account_currency": "CAD",
            "initial_positions": [{"position_id": "gold", "desk_id": "gold", "instrument_id": "XAUUSD"}],
            "observations": [{
                "timestamp_utc": "2026-11-17T11:59:56Z", "nav_mid": 400, "margin_used": 1000,
                "position_market_status": {"gold": "open"}, "trading_day_check": False,
            }],
        }
        result = self.build(
            oanda_account_margin_replay=account_replay,
            oanda_pending_order_snapshot=self.oanda_pending_snapshot(),
            oanda_closeout_transaction_replay=self.oanda_closeout_transaction_replay(),
        )
        self.assertEqual(result["oanda_closeout_transaction_audit"]["status"], "PASS")
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["status"], "halt")

    def test_oanda_margin_replay_rejects_future_observations(self):
        account_replay = {
            "account_currency": "CAD",
            "initial_positions": [{"position_id": "gold", "desk_id": "gold", "instrument_id": "XAUUSD"}],
            "observations": [{
                "timestamp_utc": "2026-11-17T12:00:01Z", "nav_mid": 1200, "margin_used": 1000,
                "position_market_status": {"gold": "open"}, "trading_day_check": False,
            }],
        }
        result = self.build(oanda_account_margin_replay=account_replay)
        self.assertEqual(result["oanda_account_margin_audit"]["status"], "HALT")
        self.assertTrue(any("later than the unified snapshot" in error
                            for error in result["oanda_account_margin_audit"]["errors"]))

    def test_oanda_pending_order_audit_rejects_future_evaluation_time(self):
        snapshot = self.oanda_pending_snapshot()
        snapshot["evaluated_at_utc"] = "2026-11-17T12:00:01Z"
        result = self.build(oanda_pending_order_snapshot=snapshot)
        self.assertEqual(result["oanda_pending_order_audit"]["status"], "HALT")

    def test_oanda_transaction_audit_rejects_future_evaluation_time(self):
        replay = self.oanda_closeout_transaction_replay()
        replay["evaluated_at_utc"] = "2026-11-17T12:00:01Z"
        result = self.build(oanda_closeout_transaction_replay=replay)
        self.assertEqual(result["oanda_closeout_transaction_audit"]["status"], "HALT")

    def test_oanda_recovered_margin_call_still_latches_occ_stop(self):
        account_replay = {
            "account_currency": "CAD",
            "initial_positions": [{"position_id": "gold", "desk_id": "gold", "instrument_id": "XAUUSD"}],
            "observations": [
                {"timestamp_utc": "2026-11-17T11:59:56Z", "nav_mid": 900, "margin_used": 1000,
                 "position_market_status": {"gold": "open"}, "trading_day_check": False},
                {"timestamp_utc": "2026-11-17T11:59:58Z", "nav_mid": 1200, "margin_used": 1000,
                 "position_market_status": {"gold": "open"}, "trading_day_check": False},
            ],
        }
        result = self.build(oanda_account_margin_replay=account_replay)
        self.assertEqual(result["oanda_account_margin_audit"]["status"], "HALT")
        self.assertEqual(result["oanda_account_margin_audit"]["report"]["status"], "MARGIN_CALL_OBSERVED_RECOVERED")
        self.assertTrue(result["global_stop_active"])

    def test_oanda_account_margin_within_requirements_is_pass(self):
        account_replay = {
            "account_currency": "CAD",
            "initial_positions": [{"position_id": "gold", "desk_id": "gold", "instrument_id": "XAUUSD"}],
            "observations": [{
                "timestamp_utc": "2026-11-17T11:59:56Z",
                "nav_mid": 1200, "margin_used": 1000,
                "position_market_status": {"gold": "open"},
                "trading_day_check": False,
            }],
        }
        result = self.build(oanda_account_margin_replay=account_replay)
        self.assertEqual(result["oanda_account_margin_audit"]["status"], "PASS")
        self.assertFalse(any(stop["source"] == "oanda_account_margin" for stop in result["active_stops"]))

    def test_oanda_account_margin_not_provided_is_explicit(self):
        result = self.build()
        self.assertEqual(result["oanda_account_margin_audit"]["status"], "NOT_PROVIDED")
        self.assertIsNone(result["oanda_account_margin_audit"]["report"])

    def test_multiple_instruments_per_desk_are_supported(self):
        rows = self.four_desk_rows() + [obs("crypto_spot", "BTC-USDC")]
        rows[-1].update(base_asset="BTC", market_pair="BTC/USDC",
                        contract_address="fixture-btc")
        result = self.build(rows)
        self.assertEqual(result["desk_coverage"]["crypto"], 2)
        self.assertEqual(result["occ"]["packet_count"], 5)
        self.assertEqual(result["occ"]["desk_count"], 4)

    def test_missing_desk_is_visible_and_full_coverage_can_be_required(self):
        rows = [obs("crypto_spot", "SOL-USDC")]
        partial = self.build(rows)
        self.assertEqual(partial["missing_desks"], ["forex", "indices", "gold"])
        self.assertEqual(partial["status"], "unverified")
        strict = self.build(rows, require_full_coverage=True)
        self.assertEqual(strict["status"], "halt")
        self.assertTrue(strict["packet_validation_errors"])

    def test_any_specialist_halt_propagates_to_global_stop(self):
        rows = self.four_desk_rows()
        rows[0]["token_identity_status"] = "unverified"
        result = self.build(rows)
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any(x["source"] == "crypto" for x in result["active_stops"]))

    def test_halt_from_forex_indices_or_gold_propagates_to_global_stop(self):
        cases = [
            ("forex", lambda row: row.update(quote_convention="base_per_quote")),
            ("indices", lambda row: row.update(index_calculation_currency="EUR")),
            ("gold", lambda row: row.update(gold_price_basis="comex_futures")),
        ]
        for desk, invalidate in cases:
            with self.subTest(desk=desk):
                rows = self.four_desk_rows()
                target = next(row for row in rows if row["instrument_id"] in {
                    "EUR-USD", "FIXTURE500", "XAUUSD-FIXTURE"
                } and (
                    (desk == "forex" and row["instrument_type"] == "fx_spot")
                    or (desk == "indices" and row["instrument_type"] == "index_cash")
                    or (desk == "gold" and row["instrument_type"] == "xauusd_spot")
                ))
                invalidate(target)
                result = self.build(rows)
                self.assertTrue(result["global_stop_active"])
                self.assertEqual(result["status"], "halt")
                self.assertTrue(any(stop["source"] == desk for stop in result["active_stops"]))

    def test_gold_specialist_context_survives_unified_intake(self):
        rows = self.four_desk_rows()
        gold = next(row for row in rows if row["instrument_type"] == "xauusd_spot")
        gold.update(
            gold_price_basis="synthetic_test",
            gold_session={"session_name": "london", "market_timezone": "Europe/London",
                          "calendar_status": "verified"},
            bid=1999.9, ask=2000.1, spread=0.2,
            quote_age_seconds=1, stale_threshold_seconds=30, is_stale=False,
            macro_evidence=[],
        )
        result = self.build(rows)
        audit = result["gold_specialist_audit"]
        self.assertEqual(audit["instrument_count"], 1)
        self.assertEqual(audit["status"], "WARN")
        self.assertEqual(audit["instruments"][0]["macro_factor_count"], 0)
        self.assertFalse(audit["trade_authority"])
        self.assertFalse(audit["live_readiness"])
        self.assertIn("gold_specialist_research",
                      next(p for p in result["specialist_packets"]
                           if p["desk_id"] == "gold")["context"])

    def test_gold_specialist_audit_summary_never_grants_authority(self):
        rows = self.four_desk_rows()
        gold = next(row for row in rows if row["instrument_type"] == "xauusd_spot")
        gold.update(
            gold_price_basis="synthetic_test",
            gold_session={"session_name": "london", "market_timezone": "Europe/London",
                          "calendar_status": "verified"},
            bid=1999.9, ask=2000.1, spread=0.2,
            quote_age_seconds=1, stale_threshold_seconds=30, is_stale=False,
            macro_evidence=[],
        )
        # The engine contract is independently tested; this assertion protects
        # the unified intake's explicit no-authority summary shape.
        result = self.build(rows)
        self.assertIs(result["gold_specialist_audit"]["trade_authority"], False)
        self.assertIs(result["gold_specialist_audit"]["live_readiness"], False)

    def test_prior_stop_cannot_be_cleared_by_clear_observation(self):
        result = self.build(previous_global_stop=True, occ_stop_state="CLEAR")
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any(x["source"] == "prior_occ_state" for x in result["active_stops"]))

    def test_explicit_occ_halt_propagates(self):
        result = self.build(occ_stop_state="HALT")
        self.assertTrue(result["global_stop_active"])
        self.assertTrue(any(x["source"] == "occ_control" for x in result["active_stops"]))

    def test_evidence_index_preserves_desk_and_instrument_provenance(self):
        result = self.build()
        refs = result["evidence_index"]["fixture:SOL-USDC"]
        self.assertEqual(refs[0]["desk_id"], "crypto")
        self.assertEqual(refs[0]["instrument_id"], "SOL-USDC")
        self.assertEqual(refs[0]["evidence_type"], "market_observation")

    def test_handover_requires_both_acknowledgements_and_reconciliation(self):
        record = {
            "outgoing_shift_id": "day", "incoming_shift_id": "night",
            "handover_at_utc": NOW, "snapshot_id": "snapshot-1",
            "portfolio_version": 7, "active_veto_ids": [],
            "unresolved_critical_items": [], "dependency_health": "healthy",
            "desk_coverage": {"crypto": 1, "forex": 1, "indices": 1, "gold": 1},
            "positions_reconciled_by_desk": {"crypto": True, "forex": True, "indices": True, "gold": True},
            "outgoing_acknowledged": True, "incoming_acknowledged": True,
            "positions_reconciled": True,
        }
        result = validate_handover(record, NOW, 7)
        self.assertTrue(result["accepted"])
        record["incoming_acknowledged"] = False
        self.assertFalse(validate_handover(record, NOW, 7)["accepted"])

    def test_handover_requires_every_desk_and_per_desk_position_reconciliation(self):
        record = {
            "outgoing_shift_id": "day", "incoming_shift_id": "night",
            "handover_at_utc": NOW, "snapshot_id": "snapshot-1",
            "portfolio_version": 7, "active_veto_ids": [],
            "unresolved_critical_items": [], "dependency_health": "healthy",
            "outgoing_acknowledged": True, "incoming_acknowledged": True,
            "positions_reconciled": True,
            "desk_coverage": {"crypto": 1, "forex": 1, "indices": 1},
            "positions_reconciled_by_desk": {"crypto": True, "forex": True, "indices": True, "gold": False},
        }
        result = validate_handover(record, NOW, 7)
        self.assertFalse(result["accepted"])
        self.assertTrue(any("desk_coverage" in error for error in result["errors"]))
        self.assertTrue(any("positions_reconciled_by_desk" in error for error in result["errors"]))

    def test_missing_handover_is_not_assumed_accepted(self):
        result = self.build()
        self.assertEqual(result["handover"]["status"], "not_provided")
        self.assertFalse(result["handover"]["accepted"])

    def test_handover_veto_remains_active(self):
        record = {
            "outgoing_shift_id": "day", "incoming_shift_id": "night",
            "handover_at_utc": NOW, "snapshot_id": "snapshot-1",
            "portfolio_version": 7, "active_veto_ids": ["veto-1"],
            "unresolved_critical_items": [], "dependency_health": "healthy",
            "desk_coverage": {"crypto": 1, "forex": 1, "indices": 1, "gold": 1},
            "positions_reconciled_by_desk": {"crypto": True, "forex": True, "indices": True, "gold": True},
            "outgoing_acknowledged": True, "incoming_acknowledged": True,
            "positions_reconciled": True,
        }
        result = self.build(handover=record)
        self.assertTrue(result["global_stop_active"])
        self.assertTrue(any("veto-1" in x["reason"] for x in result["active_stops"]))

    def test_wrong_portfolio_version_fails_before_replay(self):
        rows = self.four_desk_rows()
        with self.assertRaisesRegex(ValueError, "portfolio version mismatch"):
            self.build(rows, expected_portfolio_version=99)

    def test_partial_capital_flow_inputs_are_rejected(self):
        rows = self.four_desk_rows()
        with self.assertRaisesRegex(ValueError, "must be supplied together"):
            self.build(rows, capital_flow_events=[])

    def test_unified_intake_connects_audits_to_exact_persisted_snapshot(self):
        rows = self.four_desk_rows()
        base = self.build(rows)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot_path = root / "snapshots.jsonl"
            event_path = root / "events.jsonl"
            record = append_snapshot(snapshot_path, base, NOW)
            event = {
                "event_id": "handover-event-1",
                "event_type": "handover_recorded",
                "occurred_at_utc": NOW,
                "recorded_at_utc": NOW,
                "actor_id": "day-shift",
                "subject_id": "day-to-night",
                "summary": "Synthetic accepted shift handover",
                "evidence_refs": ["fixture:handover"],
                "details": {
                    "handover_id": "handover-1",
                    "outgoing_shift_id": "day",
                    "incoming_shift_id": "night",
                    "snapshot_id": record["snapshot_id"],
                    "portfolio_version": 7,
                    "outgoing_acknowledged": True,
                    "incoming_acknowledged": True,
                    "positions_reconciled": True,
                    "desk_coverage": {"crypto": 1, "forex": 1, "indices": 1, "gold": 1},
                    "positions_reconciled_by_desk": {"crypto": True, "forex": True, "indices": True, "gold": True},
                    "dependency_health": "healthy",
                    "active_veto_ids": [],
                    "unresolved_critical_items": [],
                },
            }
            append_event(event_path, event)
            integrated = self.build(
                rows,
                control_health_snapshot_history=snapshot_path,
                control_health_event_ledger=event_path,
            )
            self.assertEqual(integrated["control_health"]["status"], "PASS_AUDIT")
            self.assertEqual(integrated["control_health"]["handover_acceptance"], "accepted")
            self.assertEqual(integrated["control_health"]["latest_verified_snapshot_id"], record["snapshot_id"])
            self.assertFalse(integrated["trade_authority"])
            self.assertFalse(integrated["live_readiness"])

    def test_control_health_is_explicitly_not_provided_without_audit_paths(self):
        result = self.build()
        self.assertEqual(result["control_health"]["status"], "NOT_PROVIDED")
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])

    def test_control_health_paths_must_be_supplied_together(self):
        rows = self.four_desk_rows()
        with self.assertRaisesRegex(ValueError, "must be supplied together"):
            self.build(rows, control_health_snapshot_history=Path("snapshots.jsonl"))

    def test_control_health_integration_fails_closed_when_history_is_missing(self):
        rows = self.four_desk_rows()
        result = self.build(
            rows,
            control_health_snapshot_history=Path("/definitely/missing/occ-snapshots.jsonl"),
            control_health_event_ledger=Path("/definitely/missing/occ-events.jsonl"),
        )
        self.assertEqual(result["control_health"]["status"], "HALT_AUDIT")
        self.assertEqual(result["status"], "halt")
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])

    def test_duplicate_evidence_refs_are_indexed_without_losing_sources(self):
        rows = self.four_desk_rows()
        rows[1]["evidence_refs"] = ["fixture:SOL-USDC"]
        result = self.build(rows)
        entries = result["evidence_index"]["fixture:SOL-USDC"]
        self.assertEqual({x["desk_id"] for x in entries}, {"crypto", "forex"})


    def test_capital_flow_acceptance_is_audited_per_crypto_instrument(self):
        rows = self.four_desk_rows()
        result = self.build(
            rows,
            capital_flow_events=[flow_event(contract_address="fixture-mint")],
            capital_flow_reviews=[flow_review()],
            capital_flow_source_registry=FLOW_REGISTRY,
        )
        audit = result["capital_flow_audit"]
        self.assertEqual(audit["status"], "consumed_research_context")
        self.assertEqual(audit["accepted_event_count"], 1)
        self.assertEqual(audit["instrument_count"], 1)
        self.assertEqual(audit["instruments"][0]["instrument_id"], "SOL-USDC")
        self.assertEqual(len(audit["instruments"][0]["accepted_event_ids"]), 1)
        summary = audit["instruments"][0]["accepted_event_summaries"][0]
        self.assertEqual(summary["event_classification"]["category"], "whale_movement")
        self.assertFalse(summary["event_classification"]["source_independence_verified"])
        self.assertEqual(summary["evidence_provenance"]["status"], "incomplete")
        self.assertFalse(summary["evidence_provenance"]["independent_corroboration_established"])
        self.assertEqual(summary["research_priority"]["priority"], "insufficient_provenance")
        self.assertTrue(summary["research_priority"]["not_a_directional_signal"])
        self.assertFalse(audit["trade_authority"])
        self.assertFalse(audit["live_readiness"])

    def test_blocked_capital_flow_handoff_is_visible_in_unified_audit(self):
        rows = self.four_desk_rows()
        bad_review = flow_review()
        bad_review["reason"] = "tampered after signing"
        result = self.build(
            rows,
            capital_flow_events=[flow_event(contract_address="fixture-mint")],
            capital_flow_reviews=[bad_review],
            capital_flow_source_registry=FLOW_REGISTRY,
        )
        audit = result["capital_flow_audit"]
        self.assertEqual(audit["status"], "blocked")
        self.assertEqual(audit["accepted_event_count"], 0)
        self.assertEqual(audit["instrument_count"], 1)
        self.assertIn("CAPITAL_FLOW_HANDOFF_REJECTED",
                      result["specialist_packets"][0]["risk_flags"])
        self.assertFalse(audit["trade_authority"])


    def test_oanda_pending_entry_order_survives_closeout_and_escalates_occ(self):
        snapshot = {
            "pending_orders": [{
                "id": "pending-gold-entry", "state": "PENDING", "type": "STOP",
                "instrument": "XAU_USD", "units": "10", "positionFill": "OPEN_ONLY",
            }],
            "liquidated_trade_ids": ["trade-gold"],
            "account_hedging_enabled": False,
            "source_timestamp_utc": NOW,
            "evaluated_at_utc": NOW,
            "max_snapshot_age_seconds": 60,
            "pending_orders_complete": True,
            "remaining_open_trade_ids": [],
            "remaining_open_trade_ids_complete": True,
            "reported_pending_order_count": 1,
            "closeout_occurred": True,
        }
        result = self.build(oanda_pending_order_snapshot=snapshot)
        self.assertEqual(result["oanda_pending_order_audit"]["status"], "HALT")
        self.assertTrue(result["global_stop_active"])
        self.assertTrue(any(stop["source"] == "oanda_pending_orders" for stop in result["active_stops"]))
        self.assertFalse(result["oanda_pending_order_audit"]["trade_authority"])

    def test_oanda_pending_snapshot_with_no_orders_is_pass(self):
        snapshot = {
            "pending_orders": [], "liquidated_trade_ids": ["trade-gold"],
            "account_hedging_enabled": False, "source_timestamp_utc": NOW,
            "evaluated_at_utc": NOW, "max_snapshot_age_seconds": 60,
            "remaining_open_trade_ids": [], "remaining_open_trade_ids_complete": True,
            "reported_pending_order_count": 0,
            "closeout_occurred": True,
        }
        result = self.build(oanda_pending_order_snapshot=snapshot)
        self.assertEqual(result["oanda_pending_order_audit"]["status"], "PASS")
        self.assertFalse(any(stop["source"] == "oanda_pending_orders" for stop in result["active_stops"]))

    def test_oanda_pending_order_audit_is_not_provided_without_snapshot(self):
        result = self.build()
        self.assertEqual(result["oanda_pending_order_audit"]["status"], "NOT_PROVIDED")
        self.assertIsNone(result["oanda_pending_order_audit"]["report"])

if __name__ == "__main__":
    unittest.main()
