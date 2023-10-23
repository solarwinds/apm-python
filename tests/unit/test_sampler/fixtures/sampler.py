import pytest
import re
from typing import Any

from solarwinds_apm.sampler import _SwSampler


# Basic Sampler fixture =====================================

def config_get(param) -> Any:
    if param == "tracing_mode":
        return -1
    elif param == "transaction_filters":
        return []
    else:
        return None

@pytest.fixture(name="fixture_swsampler")
def fixture_swsampler(mocker):
    mock_apm_config = mocker.Mock()
    mock_get = mocker.Mock(
        side_effect=config_get
    )
    mock_get_decisions = mocker.patch(
        "solarwinds_apm.extension.oboe.Context.getDecisions"
    )
    mock_get_decisions.configure_mock(
        # returns 11 values
        return_value=list(range(11))
    )
    mock_context = mocker.Mock()
    mock_context.configure_mock(
        **{
            "getDecisions": mock_get_decisions
        }
    )
    mock_extension = mocker.Mock()
    mock_extension.configure_mock(
        **{
            "Context": mock_context,
        }
    )
    mock_apm_config.configure_mock(
        **{
            "agent_enabled": True,
            "get": mock_get,
            "extension": mock_extension,
            "is_lambda": False,
        }
    )
    return _SwSampler(mock_apm_config)


# Sampler fixtures with Transaction Filters =================

def config_get_txn_filters(param)  -> Any:
    if param == "tracing_mode":
        return -1
    elif param == "transaction_filters":
        return [
            {
                "regex": re.compile("http://foo/bar"),
                "tracing_mode": 1,
            },
            {
                "regex": re.compile(r"http://foo/[a-z]*/bar"),
                "tracing_mode": 1,
            },
            {
                "regex": re.compile("http://foo/bar-baz"),
                "tracing_mode": 1,
            },
            {
                "regex": re.compile("http://foo/bar-baz"),
                "tracing_mode": 0,
            },
            {
                "regex": re.compile("CLIENT:foo"),
                "tracing_mode": 1,
            },
            {
                "regex": re.compile(r"CLIENT:f[a-z]*o"),
                "tracing_mode": 1,
            },
            {
                "regex": re.compile("CLIENT:foo_bar"),
                "tracing_mode": 1,
            },
            {
                "regex": re.compile("CLIENT:foo_bar"),
                "tracing_mode": 0,
            }
        ]
    else:
        return None

@pytest.fixture(name="fixture_swsampler_txnfilters")
def fixture_swsampler_txnfilters(mocker):
    mock_apm_config = mocker.Mock()
    mock_get = mocker.Mock(
        side_effect=config_get_txn_filters
    )
    mock_apm_config.configure_mock(
        **{
            "agent_enabled": True,
            "get": mock_get,
        }
    )
    return _SwSampler(mock_apm_config)
