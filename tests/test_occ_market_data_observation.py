import pytest
from occ.market_data_observation import MarketDataObservationError, validate_market_data_observation

IDENTITY = {"market_class":"METALS","product_type":"SPOT","venue":"ExampleFeed",
 "symbol":"XAUUSD","quote_currency":"USD","contract_unit":"troy_ounce",
 "settlement_method":"UNKNOWN"}

def observation(**overrides):
    value = {"instrument_identity":dict(IDENTITY),"provider_id":"feed-a",
      "venue":"ExampleFeed","bid":2000.0,"ask":2001.0,"observed_at_epoch":1000.0,
      "received_at_epoch":1001.0,"sequence":7,"event_id":"evt-7"}
    value.update(overrides)
    return value

def validate(value=None, expected=IDENTITY, **kwargs):
    return validate_market_data_observation(observation() if value is None else value,
        expected, now_epoch=1002.0, **kwargs)

def test_valid_observation_never_becomes_trusted():
    result=validate()
    assert result["observation_shape_valid"] is True
    assert result["source_authenticated"] is False
    assert result["independent_source_verified"] is False
    assert result["market_data_trusted"] is False
    assert result["execution_eligible"] is False

def test_rejects_identity_mismatch():
    with pytest.raises(MarketDataObservationError, match="does not match"):
        validate(observation(instrument_identity={**IDENTITY,"quote_currency":"CAD"}))

def test_rejects_wrong_venue():
    with pytest.raises(MarketDataObservationError, match="venue"):
        validate(observation(venue="OtherFeed"))

@pytest.mark.parametrize("bid,ask",[(0,1),(-1,1),(2,1),(float("nan"),3),(1,float("inf"))])
def test_rejects_bad_quotes(bid,ask):
    with pytest.raises(MarketDataObservationError): validate(observation(bid=bid,ask=ask))

def test_rejects_stale():
    with pytest.raises(MarketDataObservationError,match="stale"):
        validate(observation(observed_at_epoch=900),max_age_seconds=30)

def test_rejects_future_timestamp():
    with pytest.raises(MarketDataObservationError,match="future"):
        validate(observation(observed_at_epoch=1010))

def test_rejects_receive_before_observation():
    with pytest.raises(MarketDataObservationError,match="predates"):
        validate(observation(observed_at_epoch=1001,received_at_epoch=990))

@pytest.mark.parametrize("sequence",[0,-1,True,1.5,"7"])
def test_rejects_bad_sequence(sequence):
    with pytest.raises(MarketDataObservationError,match="sequence"):
        validate(observation(sequence=sequence))

def test_rejects_missing_provider():
    value=observation(); del value["provider_id"]
    with pytest.raises(MarketDataObservationError,match="provider_id"): validate(value)

def test_rejects_negative_age_limit():
    with pytest.raises(MarketDataObservationError,match="cannot be negative"):
        validate(max_age_seconds=-1)

def test_does_not_mutate_input():
    value=observation(); before={**value,"instrument_identity":dict(value["instrument_identity"])}
    validate(value)
    assert value==before
