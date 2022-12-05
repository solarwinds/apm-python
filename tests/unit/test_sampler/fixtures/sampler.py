import pytest

from solarwinds_apm.sampler import _SwSampler

@pytest.fixture(name="sw_sampler")
def fixture_swsampler(mocker):
    mock_apm_config = mocker.Mock()
    mock_get = mocker.Mock(
        return_value=1  # enabled
    )
    mock_apm_config.configure_mock(
        **{
            "agent_enabled": True,
            "get": mock_get,
            "tracing_mode": None,  # mapped to -1
        }
    )
    return _SwSampler(mock_apm_config)
