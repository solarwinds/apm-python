import pytest

@pytest.fixture
def fixture_cnf_dict():
    return {
        "agentEnabled": True,
        "tracingMode": "enabled",
        "triggerTrace": "enabled",
        "collector": "foo-bar",
        "reporter": "udp",
        "debugLevel": 6,
        "logFilepath": "foo-bar",
        "serviceKey": "not-good-to-put-here:still-could-be-used",
        "hostnameAlias": "foo-bar",
        "trustedpath": "foo-bar",
        "eventsFlushInterval": 2,
        "maxRequestSizeBytes": 2,
        "ec2MetadataTimeout": 1234,
        "maxFlushWaitTime": 2,
        "maxTransactions": 2, 
        "traceMetrics": 2,
        "bufsize": 2,
        "histogramPrecision": 2,
        "reporterFileSingle": 2,
        "logTraceId": "always",
        "proxy": "http://foo-bar",
        "export_logs_enabled": True,
    }

@pytest.fixture
def fixture_cnf_dict_enabled_false():
    return {
        "agentEnabled": False,
        "tracingMode": "enabled",
        "triggerTrace": "enabled",
        "collector": "foo-bar",
        "reporter": "udp",
        "debugLevel": 6,
        "logFilepath": "foo-bar",
        "serviceKey": "not-good-to-put-here:still-could-be-used",
        "hostnameAlias": "foo-bar",
        "trustedpath": "foo-bar",
        "eventsFlushInterval": 2,
        "maxRequestSizeBytes": 2,
        "ec2MetadataTimeout": 1234,
        "maxFlushWaitTime": 2,
        "maxTransactions": 2,
        "traceMetrics": 2,
        "bufsize": 2,
        "histogramPrecision": 2,
        "reporterFileSingle": 2,
        "logTraceId": "always",
        "proxy": "http://foo-bar",
        "export_logs_enabled": False,
    }

@pytest.fixture
def fixture_cnf_dict_enabled_false_mixed_case():
    return {
        "agentEnabled": "fALsE",
        "tracingMode": "enabled",
        "triggerTrace": "enabled",
        "collector": "foo-bar",
        "reporter": "udp",
        "debugLevel": 6,
        "logFilepath": "foo-bar",
        "serviceKey": "not-good-to-put-here:still-could-be-used",
        "hostnameAlias": "foo-bar",
        "trustedpath": "foo-bar",
        "eventsFlushInterval": 2,
        "maxRequestSizeBytes": 2,
        "ec2MetadataTimeout": 1234,
        "maxFlushWaitTime": 2,
        "maxTransactions": 2,
        "traceMetrics": 2,
        "bufsize": 2,
        "histogramPrecision": 2,
        "reporterFileSingle": 2,
        "proxy": "http://foo-bar",
        "export_logs_enabled": False,
    }