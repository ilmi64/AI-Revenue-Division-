import pytest
from occ.market_source_registry import (
    MarketSourceRegistryError, validate_source_registry, compare_source_independence)

IDENTITY={"market_class":"METALS","product_type":"SPOT","venue":"ExampleFeed",
 "symbol":"XAUUSD","quote_currency":"USD","contract_unit":"troy_ounce",
 "settlement_method":"UNKNOWN"}

def entry(**overrides):
    value={"source_id":"provider-a","adapter_id":"adapter-v1","venue":"ExampleFeed",
      "endpoint":"https://feed.invalid/quotes","transport":"HTTPS","parser_version":"1.0",
      "independence_group":"group-a","instrument_identity":dict(IDENTITY),
      "review_state":"UNREVIEWED"}
    value.update(overrides)
    return value

def test_empty_registry_is_valid_but_not_authorized():
    result=validate_source_registry([],now_epoch=100)
    assert result["registry_shape_valid"] is True
    assert result["paper_use_authorized"] is False
    assert result["any_source_trusted"] is False

def test_approved_claim_requires_reviewer_evidence_and_timestamp():
    value=entry(review_state="APPROVED_FOR_PAPER",reviewer_id="reviewer-1",
      review_evidence_ref="audit:123",reviewed_at_epoch=90)
    result=validate_source_registry([value],now_epoch=100)
    assert result["entries"][0]["approval_claim_structurally_valid"] is True
    assert result["entries"][0]["approval_authority_authenticated"] is False
    assert result["paper_use_authorized"] is False

@pytest.mark.parametrize("field",["reviewer_id","review_evidence_ref","reviewed_at_epoch"])
def test_approved_entry_requires_review_fields(field):
    value=entry(review_state="APPROVED_FOR_PAPER",reviewer_id="r",
      review_evidence_ref="e",reviewed_at_epoch=90)
    value.pop(field)
    with pytest.raises(MarketSourceRegistryError): validate_source_registry([value],now_epoch=100)

def test_rejects_future_review_timestamp():
    value=entry(review_state="APPROVED_FOR_PAPER",reviewer_id="r",
      review_evidence_ref="e",reviewed_at_epoch=101)
    with pytest.raises(MarketSourceRegistryError,match="future"):
        validate_source_registry([value],now_epoch=100)

def test_revoked_entry_requires_reason():
    with pytest.raises(MarketSourceRegistryError,match="revocation_reason"):
        validate_source_registry([entry(review_state="REVOKED")],now_epoch=100)

def test_rejects_venue_identity_mismatch():
    with pytest.raises(MarketSourceRegistryError,match="venue"):
        validate_source_registry([entry(venue="OtherVenue")],now_epoch=100)

def test_rejects_duplicate_identity():
    with pytest.raises(MarketSourceRegistryError,match="duplicate"):
        validate_source_registry([entry(),entry()],now_epoch=100)

def test_rejects_unsupported_transport():
    with pytest.raises(MarketSourceRegistryError,match="transport"):
        validate_source_registry([entry(transport="HTTP")],now_epoch=100)

def test_declared_groups_are_not_claimed_as_verified():
    values=[entry(review_state="APPROVED_FOR_PAPER",reviewer_id="r",
      review_evidence_ref="e",reviewed_at_epoch=90),
      entry(source_id="provider-b",adapter_id="adapter-b",independence_group="group-b",
      review_state="APPROVED_FOR_PAPER",reviewer_id="r2",review_evidence_ref="e2",
      reviewed_at_epoch=90)]
    result=compare_source_independence(values)
    assert result["declared_group_count"]==2
    assert result["independence_verified"] is False
    assert result["multi_source_consensus_authorized"] is False

def test_rejects_string_as_registry_sequence():
    with pytest.raises(MarketSourceRegistryError):
        validate_source_registry("not-a-registry",now_epoch=100)
