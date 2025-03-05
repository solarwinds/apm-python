import socket
import time

import pytest
from unittest.mock import patch, MagicMock

from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider, AlwaysOnExemplarFilter
from opentelemetry.sdk.metrics._internal.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from solarwinds_apm.oboe.http_sampler import HttpSampler, DAEMON_THREAD_JOIN_TIMEOUT
from solarwinds_apm.oboe.configuration import Configuration, Otlp, TransactionSetting

# def test_valid_service_key_samples_created_spans():
#     meter_provider = MeterProvider(
#         metric_readers=[InMemoryMetricReader()],
#         exemplar_filter=AlwaysOnExemplarFilter()
#     )
#     sampler = HttpSampler(
#         meter_provider=meter_provider,
#         config=Configuration(
#             collector="https://apm.collector.na-01.cloud.solarwinds.com",
#             service="apm-python-test",
#             headers={
#                 "Authorization": "Bearer good"
#             },
#             enabled=True,
#             otlp=Otlp(traces="", metrics="", logs=""),
#             log_level=0,
#             trigger_trace_enabled=True,
#             export_logs_enabled=True,
#             tracing_mode=None,
#             transaction_settings=[],
#             token=None,
#             transaction_name=None,
#         ),
#         initial=None
#     )
#     memory_exporter = InMemorySpanExporter()
#     tracer_provider = TracerProvider(sampler=sampler)
#     tracer_provider.add_span_processor(span_processor=SimpleSpanProcessor(span_exporter=memory_exporter))
#     tracer = trace.get_tracer("test", tracer_provider=tracer_provider)
#     sampler.wait_until_ready(1)
#     # time.sleep(10)
#     with tracer.start_as_current_span("test") as span:
#         assert span.is_recording()
#     spans = memory_exporter.get_finished_spans()
#     assert len(spans) == 1
#     assert "SampleRate" in spans[0].attributes
#     assert "SampleSource" in spans[0].attributes
#     assert "BucketCapacity" in spans[0].attributes
#     assert "BucketRate" in spans[0].attributes

def test_invalid_service_key_does_not_sample_created_spans():
    meter_provider = MeterProvider(
        metric_readers=[InMemoryMetricReader()],
        exemplar_filter=AlwaysOnExemplarFilter()
    )
    sampler = HttpSampler(
        meter_provider=meter_provider,
        config=Configuration(
            collector="https://apm.collector.na-01.cloud.solarwinds.com",
            service="apm-python-test",
            headers={
                "Authorization": "Bearer oh-no"
            },
            enabled=True,
            otlp=Otlp(traces="", metrics="", logs=""),
            log_level=6,
            trigger_trace_enabled=True,
            export_logs_enabled=True,
            tracing_mode=None,
            transaction_settings=[],
            token=None,
            transaction_name=None,
        ),
        initial=None
    )
    memory_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider(sampler=sampler)
    tracer_provider.add_span_processor(span_processor=SimpleSpanProcessor(span_exporter=memory_exporter))
    tracer = trace.get_tracer("test", tracer_provider=tracer_provider)
    sampler.wait_until_ready(1)
    with tracer.start_as_current_span("test") as span:
        assert not span.is_recording()
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 0

def test_invalid_collector_does_not_sample_created_spans():
    meter_provider = MeterProvider(
        metric_readers=[InMemoryMetricReader()],
        exemplar_filter=AlwaysOnExemplarFilter()
    )
    sampler = HttpSampler(
        meter_provider=meter_provider,
        config=Configuration(
            collector="https://collector.invalid",
            service="apm-python-test",
            headers={
            },
            enabled=True,
            otlp=Otlp(traces="", metrics="", logs=""),
            log_level=6,
            trigger_trace_enabled=True,
            export_logs_enabled=True,
            tracing_mode=None,
            transaction_settings=[],
            token=None,
            transaction_name=None,
        ),
        initial=None
    )
    memory_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider(sampler=sampler)
    tracer_provider.add_span_processor(span_processor=SimpleSpanProcessor(span_exporter=memory_exporter))
    tracer = trace.get_tracer("test", tracer_provider=tracer_provider)
    sampler.wait_until_ready(1)
    with tracer.start_as_current_span("test") as span:
        assert not span.is_recording()
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 0

@pytest.fixture
def config():
    return Configuration(
        collector="https://apm.collector.na-01.cloud.solarwinds.com",
        service="test_service",
        headers={"Authorization": "Bearer test_token"},
        otlp=Otlp(traces="", metrics="", logs=""),
        log_level=0,
        trigger_trace_enabled=True,
        export_logs_enabled=True,
        enabled=True,
        transaction_name=None,
        transaction_settings=[],
        token=None,
        tracing_mode=None,
    )

@pytest.fixture
def meter_provider():
    return MeterProvider()

@patch('requests.get')
def test_fetch_from_collector_success(mock_get, config, meter_provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": 1000000,
        "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
        "timestamp": 1740592341,
        "ttl": 120,
        "arguments": {
            "BucketCapacity": 2,
            "BucketRate": 1,
            "TriggerRelaxedBucketCapacity": 20,
            "TriggerRelaxedBucketRate": 1,
            "TriggerStrictBucketCapacity": 6,
            "TriggerStrictBucketRate": 0.1,
            "SignatureKey": "0sftj1EYX7JJp01DblJwkccYCIZ91fbU"
        }
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    sampler = HttpSampler(meter_provider=meter_provider, config=config, initial=None)
    result = sampler._fetch_from_collector()
    assert result == {
        "value": 1000000,
        "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
        "timestamp": 1740592341,
        "ttl": 120,
        "arguments": {
            "BucketCapacity": 2,
            "BucketRate": 1,
            "TriggerRelaxedBucketCapacity": 20,
            "TriggerRelaxedBucketRate": 1,
            "TriggerStrictBucketCapacity": 6,
            "TriggerStrictBucketRate": 0.1,
            "SignatureKey": "0sftj1EYX7JJp01DblJwkccYCIZ91fbU"
        }
    }
    mock_get.assert_called_with(
        f"https://apm.collector.na-01.cloud.solarwinds.com/v1/settings/test_service/{socket.gethostname()}",
        headers={"Authorization": "Bearer test_token"},
        timeout=10)
    # one in constructor and one in test case
    assert mock_get.call_count == 2

# @patch('requests.get')
# def test_fetch_from_collector_failure(mock_get, config, meter_provider):
#     mock_get.side_effect = Exception("Network error")
#
#     sampler = HttpSampler(meter_provider=meter_provider, config=config, initial=None)
#
#     with pytest.raises(Exception, match="Network error"):
#         sampler._fetch_from_collector()

def test_shutdown(config, meter_provider):
    sampler = HttpSampler(meter_provider=meter_provider, config=config, initial=None)
    sampler.shutdown()
    assert sampler._shutdown_event.is_set()
    sampler._daemon_thread.join(timeout=DAEMON_THREAD_JOIN_TIMEOUT)
    assert not sampler._daemon_thread.is_alive()