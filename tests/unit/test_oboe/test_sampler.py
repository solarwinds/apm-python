# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from __future__ import annotations


import time
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider, AlwaysOnExemplarFilter
from opentelemetry.sdk.metrics._internal.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv._incubating.attributes.http_attributes import (
    HTTP_METHOD,
    HTTP_STATUS_CODE,
    HTTP_SCHEME,
    HTTP_TARGET,
)
from opentelemetry.semconv._incubating.attributes.net_attributes import NET_HOST_NAME
from opentelemetry.semconv.attributes.http_attributes import (
    HTTP_REQUEST_METHOD,
    HTTP_RESPONSE_STATUS_CODE,
)
from opentelemetry.semconv.attributes.server_attributes import SERVER_ADDRESS
from opentelemetry.semconv.attributes.url_attributes import URL_SCHEME, URL_PATH
from opentelemetry.trace import SpanKind

from solarwinds_apm.oboe.configuration import Configuration, TransactionSetting
from solarwinds_apm.oboe.sampler import http_span_metadata, parse_settings, Sampler
from solarwinds_apm.oboe.settings import (
    Settings,
    SampleSource,
    Flags,
    BucketType,
    BucketSettings,
)


class TestSampler(Sampler):
    def __init__(
        self, meter_provider: MeterProvider, config: Configuration, initial: Any
    ):
        super().__init__(meter_provider=meter_provider, config=config, initial=initial)

    def __str__(self):
        raise Exception("Test sampler")


def options(
    tracing: bool | None,
    trigger_trace: bool,
    transaction_settings: list[TransactionSetting],
) -> Configuration:
    return Configuration(
        tracing_mode=tracing,
        trigger_trace_enabled=trigger_trace,
        transaction_settings=transaction_settings,
        enabled=True,
        service="test",
        collector="localhost",
        headers={},
        transaction_name=None,
    )


def settings(enabled: bool, signature_key: str | None):
    return {
        "value": 1_000_000,
        "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,TRIGGER_TRACE" if enabled else "",
        "arguments": {
            "BucketCapacity": 10,
            "BucketRate": 1,
            "TriggerRelaxedBucketCapacity": 100,
            "TriggerRelaxedBucketRate": 10,
            "TriggerStrictBucketCapacity": 1,
            "TriggerStrictBucketRate": 0.1,
            "SignatureKey": signature_key,
        },
        "timestamp": int(time.time()),
        "ttl": 60,
    }


class TestHTTPSpanMetadataName:
    def test_handles_non_http_spans_properly(self):
        span = {
            "kind": SpanKind.SERVER,
            "attributes": {"network.transport": "udp"},
        }
        output = http_span_metadata(span["kind"], span["attributes"])
        assert output == {"http": False}

    def test_handles_http_client_spans_properly(self):
        span = {
            "kind": SpanKind.CLIENT,
            "attributes": {
                HTTP_REQUEST_METHOD: "GET",
                HTTP_RESPONSE_STATUS_CODE: 200,
                SERVER_ADDRESS: "solarwinds.com",
                URL_SCHEME: "https",
                URL_PATH: "",
            },
        }
        output = http_span_metadata(span["kind"], span["attributes"])
        assert output == {"http": False}

    def test_handles_http_server_spans_properly(self):
        span = {
            "kind": SpanKind.SERVER,
            "attributes": {
                HTTP_REQUEST_METHOD: "GET",
                HTTP_RESPONSE_STATUS_CODE: 200,
                SERVER_ADDRESS: "solarwinds.com",
                URL_SCHEME: "https",
                URL_PATH: "",
            },
        }
        output = http_span_metadata(span["kind"], span["attributes"])
        assert output == {
            "http": True,
            "method": "GET",
            "status": 200,
            "scheme": "https",
            "hostname": "solarwinds.com",
            "path": "",
            "url": "https://solarwinds.com",
        }

    def test_handles_legacy_http_server_spans_properly(self):
        span = {
            "kind": SpanKind.SERVER,
            "attributes": {
                HTTP_METHOD: "GET",
                HTTP_STATUS_CODE: 200,
                HTTP_SCHEME: "https",
                NET_HOST_NAME: "solarwinds.com",
                HTTP_TARGET: "",
            },
        }
        output = http_span_metadata(span["kind"], span["attributes"])
        assert output == {
            "http": True,
            "method": "GET",
            "status": 200,
            "scheme": "https",
            "hostname": "solarwinds.com",
            "path": "",
            "url": "https://solarwinds.com",
        }


class TestParseSettingsName:
    def test_correctly_parses_JSON_settings(self):
        timestamp = int(time.time())
        settings = {
            "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,TRIGGER_TRACE,OVERRIDE",
            "value": 500_000,
            "arguments": {
                "BucketCapacity": 0.2,
                "BucketRate": 0.1,
                "TriggerRelaxedBucketCapacity": 20,
                "TriggerRelaxedBucketRate": 10,
                "TriggerStrictBucketCapacity": 2,
                "TriggerStrictBucketRate": 1,
                "SignatureKey": "key",
            },
            "timestamp": timestamp,
            "ttl": 120,
            "warning": "warning",
        }
        output, warnings = parse_settings(settings)
        assert output == Settings(
            sample_rate=500_000,
            sample_source=SampleSource.REMOTE,
            flags=Flags.SAMPLE_START
            | Flags.SAMPLE_THROUGH_ALWAYS
            | Flags.TRIGGERED_TRACE
            | Flags.OVERRIDE,
            buckets={
                BucketType.DEFAULT: BucketSettings(capacity=0.2, rate=0.1),
                BucketType.TRIGGER_RELAXED: BucketSettings(capacity=20, rate=10),
                BucketType.TRIGGER_STRICT: BucketSettings(capacity=2, rate=1),
            },
            signature_key="key",
            timestamp=timestamp,
            ttl=120,
        )
        assert warnings == "warning"


class TestSamplerName:
    def test_respects_enabled_settings_when_no_config_or_transaction_settings(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(tracing=None, trigger_trace=False, transaction_settings=[]),
            initial=settings(enabled=True, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "respects_enabled_settings_when_no_config_or_transaction_settings",
            tracer_provider=tracer_provider,
        )
        with tracer.start_as_current_span("test") as span:
            assert span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes == {
            "SampleRate": 1_000_000,
            "SampleSource": 6,
            "BucketCapacity": 10,
            "BucketRate": 1,
        }

    def test_respects_disabled_settings_when_no_config_or_transaction_settings(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(tracing=None, trigger_trace=True, transaction_settings=[]),
            initial=settings(enabled=False, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "respects_disabled_settings_when_no_config_or_transaction_settings",
            tracer_provider=tracer_provider,
        )
        with tracer.start_as_current_span("test") as span:
            assert not span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_respects_enabled_config_when_no_transaction_settings(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(tracing=True, trigger_trace=True, transaction_settings=[]),
            initial=settings(enabled=False, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "respects_enabled_config_when_no_transaction_settings",
            tracer_provider=tracer_provider,
        )
        with tracer.start_as_current_span("test") as span:
            assert span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes == {
            "SampleRate": 1_000_000,
            "SampleSource": 6,
            "BucketCapacity": 10,
            "BucketRate": 1,
        }

    def test_respects_disabled_config_when_no_transaction_settings(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(tracing=False, trigger_trace=False, transaction_settings=[]),
            initial=settings(enabled=True, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "respects_disabled_config_when_no_transaction_settings",
            tracer_provider=tracer_provider,
        )
        with tracer.start_as_current_span("test") as span:
            assert not span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_respects_enabled_matching_transaction_setting(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(
                tracing=False,
                trigger_trace=False,
                transaction_settings=[
                    TransactionSetting(tracing=True, matcher=lambda s: True)
                ],
            ),
            initial=settings(enabled=False, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "respects_enabled_matching_transaction_setting",
            tracer_provider=tracer_provider,
        )
        with tracer.start_as_current_span("test") as span:
            assert span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes == {
            "SampleRate": 1_000_000,
            "SampleSource": 6,
            "BucketCapacity": 10,
            "BucketRate": 1,
        }

    def test_respects_disabled_matching_transaction_setting(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(
                tracing=True,
                trigger_trace=True,
                transaction_settings=[
                    TransactionSetting(tracing=False, matcher=lambda s: True)
                ],
            ),
            initial=settings(enabled=True, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "respects_disabled_matching_transaction_setting",
            tracer_provider=tracer_provider,
        )
        with tracer.start_as_current_span("test") as span:
            assert not span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_respects_first_matching_transaction_setting(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(
                tracing=False,
                trigger_trace=False,
                transaction_settings=[
                    TransactionSetting(tracing=True, matcher=lambda s: True),
                    TransactionSetting(tracing=False, matcher=lambda s: True),
                ],
            ),
            initial=settings(enabled=False, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "respects_first_matching_transaction_setting",
            tracer_provider=tracer_provider,
        )
        with tracer.start_as_current_span("test") as span:
            assert span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes == {
            "SampleRate": 1_000_000,
            "SampleSource": 6,
            "BucketCapacity": 10,
            "BucketRate": 1,
        }

    def test_matches_non_http_spans(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(
                tracing=False,
                trigger_trace=False,
                transaction_settings=[
                    TransactionSetting(
                        tracing=True, matcher=lambda s: s == "CLIENT:test"
                    ),
                ],
            ),
            initial=settings(enabled=False, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "matches_non_http_spans", tracer_provider=tracer_provider
        )
        with tracer.start_as_current_span("test", kind=SpanKind.CLIENT) as span:
            assert span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes == {
            "SampleRate": 1_000_000,
            "SampleSource": 6,
            "BucketCapacity": 10,
            "BucketRate": 1,
        }

    def test_matches_http_spans(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(
                tracing=False,
                trigger_trace=False,
                transaction_settings=[
                    TransactionSetting(
                        tracing=True, matcher=lambda s: s == "http://localhost/test"
                    ),
                ],
            ),
            initial=settings(enabled=False, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer("matches_http_spans", tracer_provider=tracer_provider)
        with tracer.start_as_current_span(
            "test",
            kind=SpanKind.SERVER,
            attributes={
                HTTP_METHOD: "GET",
                URL_SCHEME: "http",
                SERVER_ADDRESS: "localhost",
                URL_PATH: "/test",
            },
        ) as span:
            assert span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes["SampleRate"] == 1_000_000
        assert spans[0].attributes["SampleSource"] == 6
        assert spans[0].attributes["BucketCapacity"] == 10
        assert spans[0].attributes["BucketRate"] == 1

    def test_matches_deprecated_http_spans(self):
        meter_provider = MeterProvider(
            metric_readers=[InMemoryMetricReader()],
            exemplar_filter=AlwaysOnExemplarFilter(),
        )
        sampler = TestSampler(
            meter_provider=meter_provider,
            config=options(
                tracing=False,
                trigger_trace=False,
                transaction_settings=[
                    TransactionSetting(
                        tracing=True, matcher=lambda s: s == "http://localhost/test"
                    ),
                ],
            ),
            initial=settings(enabled=False, signature_key=None),
        )
        memory_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(sampler=sampler)
        tracer_provider.add_span_processor(
            span_processor=SimpleSpanProcessor(span_exporter=memory_exporter)
        )
        tracer = trace.get_tracer(
            "matches_deprecated_http_spans", tracer_provider=tracer_provider
        )
        with tracer.start_as_current_span(
            "test",
            kind=SpanKind.SERVER,
            attributes={
                HTTP_REQUEST_METHOD: "GET",
                URL_SCHEME: "http",
                SERVER_ADDRESS: "localhost",
                URL_PATH: "/test",
            },
        ) as span:
            assert span.is_recording()
        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes["SampleRate"] == 1_000_000
        assert spans[0].attributes["SampleSource"] == 6
        assert spans[0].attributes["BucketCapacity"] == 10
        assert spans[0].attributes["BucketRate"] == 1
