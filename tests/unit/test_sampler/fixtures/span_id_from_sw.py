import pytest

@pytest.fixture(autouse=True)
def fixture_mock_span_id_from_sw(mocker):
    mocker.patch(
        "solarwinds_apm.w3c_transformer.W3CTransformer.span_id_from_sw",
        return_value="1111222233334444"
    )