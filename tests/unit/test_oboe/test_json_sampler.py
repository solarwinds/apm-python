# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import json
import os
import tempfile
import time

import pytest
from opentelemetry import trace
from opentelemetry.sdk.metrics import AlwaysOnExemplarFilter, MeterProvider
from opentelemetry.sdk.metrics._internal.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from solarwinds_apm.oboe.configuration import Configuration, Otlp
from solarwinds_apm.oboe.json_sampler import JsonSampler

PATH = os.path.join(tempfile.gettempdir(), "solarwinds-apm-settings.json")


@pytest.fixture
def json_sampler_tracer_memory_exporter():
    meter_provider = MeterProvider(
        metric_readers=[InMemoryMetricReader()],
        exemplar_filter=AlwaysOnExemplarFilter()
    )
    sampler = JsonSampler(
        meter_provider=meter_provider,
        config=Configuration(enabled=True, service="test", token=None, collector="", headers={},
                             otlp=Otlp(traces="", metrics="", logs=""), log_level=0, tracing_mode=True,
                             trigger_trace_enabled=True, export_logs_enabled=True, transaction_name=None,
                             transaction_settings=[]),
        path=PATH
    )
    memory_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider(sampler=sampler)
    tracer_provider.add_span_processor(span_processor=SimpleSpanProcessor(span_exporter=memory_exporter))
    tracer = trace.get_tracer("test", tracer_provider=tracer_provider)
    return tracer, memory_exporter


def test_valid_file_samples_created_spans(json_sampler_tracer_memory_exporter):
    with open(PATH, "w") as f:
        json.dump([{
            "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,TRIGGER_TRACE,OVERRIDE",
            "value": 1_000_000,
            "arguments": {
                "BucketCapacity": 100,
                "BucketRate": 10,
            },
            "timestamp": int(time.time()),
            "ttl": 60,
        }], f)
    tracer, memory_exporter = json_sampler_tracer_memory_exporter
    with tracer.start_as_current_span("test") as span:
        assert span.is_recording()
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    assert 'SampleRate' in spans[0].attributes
    assert 'SampleSource' in spans[0].attributes
    assert 'BucketCapacity' in spans[0].attributes
    assert 'BucketRate' in spans[0].attributes
    os.remove(PATH)


def test_invalid_file_no_samples_created_spans(json_sampler_tracer_memory_exporter):
    with open(PATH, "w") as f:
        json.dump({"hello": "world"}, f)
    tracer, memory_exporter = json_sampler_tracer_memory_exporter
    with tracer.start_as_current_span("test") as span:
        assert not span.is_recording()
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 0
    os.remove(PATH)


def test_missing_file_no_samples_created_spans(json_sampler_tracer_memory_exporter):
    try:
        os.remove(PATH)
    except FileNotFoundError:
        # It's okay if the file does not exist
        pass
    tracer, memory_exporter = json_sampler_tracer_memory_exporter
    with tracer.start_as_current_span("test") as span:
        assert not span.is_recording()
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 0


def test_expired_file_no_samples_created_spans(json_sampler_tracer_memory_exporter):
    with open(PATH, "w") as f:
        json.dump([{
            "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,TRIGGER_TRACE,OVERRIDE",
            "value": 1_000_000,
            "arguments": {
                "BucketCapacity": 100,
                "BucketRate": 10,
            },
            "timestamp": int(time.time()) - 120,
            "ttl": 60,
        }], f)
    tracer, memory_exporter = json_sampler_tracer_memory_exporter
    with tracer.start_as_current_span("test") as span:
        assert not span.is_recording()
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 0
    os.remove(PATH)


def test_samples_after_reading_new_settings(json_sampler_tracer_memory_exporter):
    with open(PATH, "w") as f:
        json.dump([{
            "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,TRIGGER_TRACE,OVERRIDE",
            "value": 1_000_000,
            "arguments": {
                "BucketCapacity": 100,
                "BucketRate": 10,
            },
            "timestamp": int(time.time()),
            "ttl": 60,
        }], f)
    tracer, memory_exporter = json_sampler_tracer_memory_exporter
    with tracer.start_as_current_span("test") as span:
        assert span.is_recording()
    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 1
    assert 'SampleRate' in spans[0].attributes
    assert 'SampleSource' in spans[0].attributes
    assert 'BucketCapacity' in spans[0].attributes
    assert 'BucketRate' in spans[0].attributes
