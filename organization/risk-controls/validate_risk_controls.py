"""Fail-closed structural checks for the organisation risk policy."""
from __future__ import annotations

import json
from pathlib import Path

POLICY_PATH = Path(__file__).with_name("risk-control-policy.json")
REQUIRED_DIVISIONS = {
    "Executive Management", "AI Revenue", "Technology and Infrastructure",
    "Research and Intelligence", "Finance and Treasury",
    "Risk, Security and Recovery", "Crypto and PolyBot", "Ecommerce",
    "Animora and Future Creative Studio",
    "Trader Intelligence & Strategy Replication", "Business & Commercial",
}
REQUIRED_STOPS = {
    "credential_or_secret_exposure_suspected",
    "unauthorised_access_or_action_detected",
    "data_provenance_or_licence_unknown_for_intended_use",
    "market_data_stale_delayed_indicative_reference_only_or_incomplete",
    "instrument_or_venue_mapping_ambiguous",
    "position_or_order_state_uncertain",
    "unreconciled_fill_or_transaction",
    "risk_limit_missing_or_invalid",
    "deterministic_validation_failed",
    "required_owner_approval_missing",
    "material_dependency_unavailable",
    "incident_severity_critical",
}
FORBIDDEN_AUTHORITY = {"approve_trades", "waive_controls", "approve_spending"}


def validate(policy: dict) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != "1.0.0":
        errors.append("unsupported schema_version")
    if policy.get("status") != "draft_control_baseline":
        errors.append("policy must remain a draft control baseline until operational evidence exists")
    authority = policy.get("authority", {})
    if authority.get("risk_division") != "stop_and_challenge_only":
        errors.append("risk authority must be stop_and_challenge_only")
    if authority.get("trade_authority") != "not_granted":
        errors.append("trade authority must remain not_granted")
    defaults = policy.get("default_permissions", {})
    for key in ("external_actions", "financial_actions", "wallet_signing", "live_trading",
                "publishing", "account_changes", "paid_services_and_trials"):
        if defaults.get(key) != "disabled":
            errors.append(f"{key} must be disabled by default")
    if defaults.get("github_actions") != "hold_until_usage_reset":
        errors.append("GitHub Actions must remain on hold until usage reset")
    if not FORBIDDEN_AUTHORITY.issubset(set(policy.get("mandatory_owner_approval", []))):
        # The approval list uses action names, not authority names; validate the exact high-risk gates below.
        required = {"spending", "financial_transactions", "wallet_actions", "live_trading",
                    "merges", "deployments", "production_launches"}
        if not required.issubset(set(policy.get("mandatory_owner_approval", []))):
            errors.append("mandatory owner-approval gates are incomplete")
    if not set(policy.get("global_stop_conditions", [])).issuperset(REQUIRED_STOPS):
        errors.append("global stop-condition coverage is incomplete")
    if policy.get("never_request_or_store") != [
        "passwords", "mfa_codes", "seed_phrases", "private_keys", "api_secrets"
    ]:
        errors.append("secret-handling denylist is incomplete or altered")
    market = policy.get("market_data_controls", {})
    for key in ("fail_closed_on_stale_data", "fail_closed_on_unknown_provenance",
                "fail_closed_on_unlicensed_use"):
        if market.get(key) is not True:
            errors.append(f"{key} must be true")
    if market.get("production_sources_approved") != []:
        errors.append("no production market-data source is approved by this draft")
    trading = policy.get("trading_controls", {})
    if trading.get("mode") != "research_and_paper_only":
        errors.append("trading mode must remain research_and_paper_only")
    for key in ("live_execution_enabled", "wallet_signing_enabled",
                "automatic_recovery_trading_enabled", "risk_advisor_can_authorise_trade",
                "agent_can_override_deterministic_control"):
        if trading.get(key) is not False:
            errors.append(f"{key} must be false")
    incidents = policy.get("incident_controls", {})
    required_incident_fields = {
        "incident_id", "detected_at_utc", "reporting_division", "category", "severity",
        "facts", "hypotheses", "evidence_references", "containment", "owner",
        "status", "next_review_at_utc",
    }
    if not required_incident_fields.issubset(set(incidents.get("required_fields", []))):
        errors.append("incident record fields are incomplete")
    if incidents.get("preserve_original_evidence") is not True:
        errors.append("original evidence preservation must be enabled")
    return errors


def main() -> int:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    errors = validate(policy)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Risk policy structural validation passed; this is not operational readiness evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
