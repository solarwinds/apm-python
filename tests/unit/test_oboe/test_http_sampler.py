# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
import logging
import os
import socket
from unittest.mock import patch, MagicMock

import pytest
from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider, AlwaysOnExemplarFilter
from opentelemetry.sdk.metrics._internal.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from solarwinds_apm.oboe.configuration import Configuration
from solarwinds_apm.oboe.http_sampler import HttpSampler, DAEMON_THREAD_JOIN_TIMEOUT


def test_valid_service_key_samples_created_spans():
    # This test requires a valid service key to be set in the environment
    service_key = os.getenv("SW_APM_SERVICE_KEY")
    if service_key:
        l = service_key.split(":")
        if len(l) == 2:
            bearer = l[0]
            service = l[1]
            meter_provider = MeterProvider(
                metric_readers=[InMemoryMetricReader()],
                exemplar_filter=AlwaysOnExemplarFilter()
            )
            sampler = HttpSampler(
                meter_provider=meter_provider,
                config=Configuration(
                    collector="https://apm.collector.na-01.cloud.solarwinds.com",
                    service=service,
                    headers={
                        "Authorization": f"Bearer {bearer}"
                    },
                    enabled=True,
                    log_level=0,
                    trigger_trace_enabled=True,
                    tracing_mode=None,
                    transaction_settings=[],
                    token=None,
                    transaction_name=None,
                ),
                logger=logging.getLogger(__name__),
                initial=None
            )
            memory_exporter = InMemorySpanExporter()
            tracer_provider = TracerProvider(sampler=sampler)
            tracer_provider.add_span_processor(span_processor=SimpleSpanProcessor(span_exporter=memory_exporter))
            tracer = trace.get_tracer("test", tracer_provider=tracer_provider)
            sampler.wait_until_ready(1)
            with tracer.start_as_current_span("test") as span:
                assert span.is_recording()
            spans = memory_exporter.get_finished_spans()
            assert len(spans) == 1
            assert "SampleRate" in spans[0].attributes
            assert "SampleSource" in spans[0].attributes
            assert "BucketCapacity" in spans[0].attributes
            assert "BucketRate" in spans[0].attributes


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
            log_level=0,
            trigger_trace_enabled=True,
            tracing_mode=None,
            transaction_settings=[],
            token=None,
            transaction_name=None,
        ),
        logger=logging.getLogger(__name__),
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
            log_level=0,
            trigger_trace_enabled=True,
            tracing_mode=None,
            transaction_settings=[],
            token=None,
            transaction_name=None,
        ),
        logger=logging.getLogger(__name__),
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
        log_level=0,
        trigger_trace_enabled=True,
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
            "SignatureKey": "signature"
        }
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    sampler = HttpSampler(meter_provider=meter_provider, config=config, logger=logging.getLogger(__name__), initial=None)
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
            "SignatureKey": "signature"
        }
    }
    mock_get.assert_called_with(
        f"https://apm.collector.na-01.cloud.solarwinds.com/v1/settings/test_service/{socket.gethostname()}",
        headers={"Authorization": "Bearer test_token"},
        timeout=10)
    # one in constructor and one in test case
    assert mock_get.call_count == 2


def test_shutdown(config, meter_provider):
    sampler = HttpSampler(meter_provider=meter_provider, config=config, logger=logging.getLogger(__name__), initial=None)
    sampler.shutdown()
    assert sampler._shutdown_event.is_set()
    sampler._daemon_thread.join(timeout=DAEMON_THREAD_JOIN_TIMEOUT)
    assert not sampler._daemon_thread.is_alive()
