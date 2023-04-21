import pytest

from solarwinds_apm.sampler import _SwSampler

def side_effect_fn(param):
    if param == "tracing_mode":
        return -1
    elif param == "transaction_filters":
        return []

@pytest.fixture(name="sw_sampler")
def fixture_swsampler(mocker):
    mock_apm_config = mocker.Mock()
    mock_get = mocker.Mock(
        side_effect=side_effect_fn
    )
    mock_apm_config.configure_mock(
        **{
            "agent_enabled": True,
            "get": mock_get,
        }
    )
    return _SwSampler(mock_apm_config)
