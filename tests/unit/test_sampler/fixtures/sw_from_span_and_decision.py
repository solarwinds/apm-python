import pytest

@pytest.fixture(autouse=True)
def fixture_mock_sw_from_span_and_decision(mocker):
    mocker.patch(
        "solarwinds_apm.w3c_transformer.W3CTransformer.sw_from_span_and_decision",
        return_value="1111222233334444-01"
    )
