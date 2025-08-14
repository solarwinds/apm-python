import pytest


@pytest.fixture
def fixture_cnf_dict():
    return {
        "agentEnabled": True,
        "tracingMode": "enabled",
        "triggerTrace": "enabled",
        "collector": "foo-bar",
        "debugLevel": 6,
        "serviceKey": "not-good-to-put-here:still-could-be-used",
        "logTraceId": "always",
        "exportLogsEnabled": True,
    }


@pytest.fixture
def fixture_cnf_dict_enabled_false():
    return {
        "agentEnabled": False,
        "tracingMode": "enabled",
        "triggerTrace": "enabled",
        "collector": "foo-bar",
        "debugLevel": 6,
        "serviceKey": "not-good-to-put-here:still-could-be-used",
        "logTraceId": "always",
        "exportLogsEnabled": False,
    }


@pytest.fixture
def fixture_cnf_dict_enabled_false_mixed_case():
    return {
        "agentEnabled": "fALsE",
        "tracingMode": "enabled",
        "triggerTrace": "enabled",
        "collector": "foo-bar",
        "debugLevel": 6,
        "serviceKey": "not-good-to-put-here:still-could-be-used",
        "exportLogsEnabled": "fALsE",
    }
