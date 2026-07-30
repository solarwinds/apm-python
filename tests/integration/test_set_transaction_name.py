# © 2026 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

import threading
import time
from unittest import mock

import flask
import requests
from opentelemetry import trace
from werkzeug.serving import make_server

from solarwinds_apm.api import set_transaction_name
from solarwinds_apm.apm_constants import INTL_SWO_TRANSACTION_ATTR_KEY
from solarwinds_apm.trace.response_time_processor import (
    ResponseTimeProcessor,
)
from solarwinds_apm.trace.serviceentry_processor import (
    ServiceEntrySpanProcessor,
)

from .test_base_sw_headers_attrs import (
    TestBaseSwHeadersAndAttributes,
)


class TestBaseTransactionName(TestBaseSwHeadersAndAttributes):
    """Base class for set_transaction_name() tests with common setup and helpers"""

    def setUp(self):
        super().setUp()
        self.tracer_provider.add_span_processor(ServiceEntrySpanProcessor())
        self.tracer_provider.add_span_processor(
            ResponseTimeProcessor(self.configurator.apm_config)
        )

    def _get_metrics_for_transaction(self, transaction_name):
        """Helper to get metrics data filtered by transaction name"""
        self.metric_reader.collect()
        metrics_data = self.metric_reader.get_metrics_data()
        if not metrics_data or not metrics_data.resource_metrics:
            return []
        
        matching_data_points = []
        for resource_metric in metrics_data.resource_metrics:
            for scope_metric in resource_metric.scope_metrics:
                for metric in scope_metric.metrics:
                    if metric.name == "trace.service.response_time":
                        for data_point in metric.data.data_points:
                            txn = data_point.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
                            if txn == transaction_name:
                                matching_data_points.append(data_point)
        return matching_data_points


class TestSetTransactionNameBasic(TestBaseTransactionName):
    """Basic functionality tests for set_transaction_name()"""

    def _setup_endpoints(self):
        """Set up test routes before Flask instrumentation"""
        super()._setup_endpoints()

        def route_single_call():
            set_transaction_name("custom-name")
            return "ok"

        def route_multiple_calls():
            set_transaction_name("first")
            set_transaction_name("second")
            return "ok"

        # pylint: disable=no-member
        self.app.route("/test_single_call/")(route_single_call)
        self.app.route("/test_multiple_calls/")(route_multiple_calls)

    def test_single_call_sets_attribute(self):
        """Test single call to set_transaction_name sets
        sw.transaction attribute
        """
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            resp = self.client.get("/test_single_call/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0
            entry_spans = [
                s
                for s in spans
                if not (
                    s.parent and s.parent.is_valid and not s.parent.is_remote
                )
            ]
            assert len(entry_spans) == 1
            entry_span = entry_spans[0]
            assert (
                entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
                == "custom-name"
            )

            # Verify metrics also have correct transaction name
            metrics = self._get_metrics_for_transaction("custom-name")
            assert len(metrics) == 1
            assert metrics[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "custom-name"

    def test_multiple_calls_last_wins(self):
        """Test multiple calls to set_transaction_name, last one wins"""
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            resp = self.client.get("/test_multiple_calls/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0
            entry_spans = [
                s
                for s in spans
                if not (
                    s.parent and s.parent.is_valid and not s.parent.is_remote
                )
            ]
            assert len(entry_spans) == 1
            entry_span = entry_spans[0]
            assert (
                entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
                == "second"
            )

            # Verify metrics also have correct transaction name
            metrics = self._get_metrics_for_transaction("second")
            assert len(metrics) == 1
            assert metrics[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "second"


class TestSetTransactionNameEdgeCases(TestBaseTransactionName):
    """Edge case tests for set_transaction_name()"""

    def _setup_endpoints(self):
        """Set up test routes before Flask instrumentation"""
        super()._setup_endpoints()

        def route_empty_string():
            result = set_transaction_name("")
            assert result is False
            return "ok"

        def route_none_value():
            result = set_transaction_name(None)
            assert result is False
            return "ok"

        def route_long_name():
            long_name = "a" * 300
            set_transaction_name(long_name)
            return "ok"

        # pylint: disable=no-member
        self.app.route("/test_empty_string/")(route_empty_string)
        self.app.route("/test_none_value/")(route_none_value)
        self.app.route("/test_long_name/")(route_long_name)

    def test_empty_string_rejected(self):
        """Test empty string is rejected and original name preserved"""
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            resp = self.client.get("/test_empty_string/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0
            entry_spans = [
                s
                for s in spans
                if not (
                    s.parent and s.parent.is_valid and not s.parent.is_remote
                )
            ]
            assert len(entry_spans) == 1

            entry_span = entry_spans[0]
            txn_name = entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
            assert txn_name is not None
            assert txn_name != ""
            assert txn_name == "/test_empty_string/"

            # Verify metrics also have correct transaction name
            metrics = self._get_metrics_for_transaction("/test_empty_string/")
            assert len(metrics) == 1
            assert metrics[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "/test_empty_string/"

    def test_none_value_rejected(self):
        """Test None value is rejected and original name preserved"""
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            resp = self.client.get("/test_none_value/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0
            entry_spans = [
                s
                for s in spans
                if not (
                    s.parent and s.parent.is_valid and not s.parent.is_remote
                )
            ]
            assert len(entry_spans) == 1

            entry_span = entry_spans[0]
            txn_name = entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
            assert txn_name is not None
            assert (
                "test_none_value" in txn_name
                or txn_name == "/test_none_value/"
            )

            # Verify metrics also have correct transaction name
            metrics = self._get_metrics_for_transaction(txn_name)
            assert len(metrics) == 1
            assert metrics[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == txn_name

    def test_no_active_span_returns_false(self):
        """Test calling set_transaction_name outside request context
        returns False
        """
        result = set_transaction_name("test")
        assert result is False

    def test_long_name_truncated(self):
        """Test long transaction names are truncated to 256 characters"""
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            resp = self.client.get("/test_long_name/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0
            entry_spans = [
                s
                for s in spans
                if not (
                    s.parent and s.parent.is_valid and not s.parent.is_remote
                )
            ]
            assert len(entry_spans) == 1

            entry_span = entry_spans[0]
            txn_name = entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
            assert txn_name is not None
            assert len(txn_name) == 256
            assert txn_name == "a" * 256

            # Verify metrics also have correct transaction name
            metrics = self._get_metrics_for_transaction(txn_name)
            assert len(metrics) == 1
            assert metrics[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == txn_name


class TestSetTransactionNameDistributed(TestBaseTransactionName):
    """Distributed trace tests for set_transaction_name()

    Tests true distributed tracing by setting up two Flask apps where service A
    makes an HTTP request to service B, propagating trace context between them.
    """

    def setUp(self):
        super().setUp()

        # Set up a second app in addition to self.app
        # Should be done before service_a set up with call to this one
        self.app_b = flask.Flask("service_b")
        self.flask_inst.instrument_app(self.app_b)

        # Get tracer for manual span tests
        tracer = trace.get_tracer(__name__)

        def service_b_endpoint():
            set_transaction_name("custom-service-b")
            return "service-b-response"

        def service_b_with_manual_spans():
            with tracer.start_as_current_span("manual-outer-b"):
                current_span = trace.get_current_span()
                current_span.set_attribute("test.custom_attribute", "outer-b")
                with tracer.start_as_current_span("manual-inner-b"):
                    current_span = trace.get_current_span()
                    current_span.set_attribute(
                        "test.custom_attribute", "inner-b"
                    )
                    set_transaction_name("custom-service-b")
                    return "service-b-response"

        # Register all routes before starting server
        self.app_b.route("/service_b/")(service_b_endpoint)
        self.app_b.route("/service_b_manual/")(service_b_with_manual_spans)

        self.server = make_server("127.0.0.1", 5001, self.app_b, threaded=True)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server_thread.join(timeout=1)
        super().tearDown()

    def _setup_endpoints(self):
        """Set up test routes before Flask instrumentation"""
        super()._setup_endpoints()

        # Get tracer for manual span tests
        tracer = trace.get_tracer(__name__)

        def service_a_endpoint():
            set_transaction_name("custom-service-a")
            resp = requests.get("http://127.0.0.1:5001/service_b/", timeout=5)
            return f"service-a-response: {resp.text}"

        def service_a_with_manual_spans():
            with tracer.start_as_current_span("manual-outer-a"):
                current_span = trace.get_current_span()
                current_span.set_attribute("test.custom_attribute", "outer-a")
                with tracer.start_as_current_span("manual-inner-a"):
                    current_span = trace.get_current_span()
                    current_span.set_attribute(
                        "test.custom_attribute", "inner-a"
                    )
                    set_transaction_name("custom-service-a")
                    resp = requests.get(
                        "http://127.0.0.1:5001/service_b_manual/",
                        timeout=5,
                    )
                    return f"service-a-response: {resp.text}"

        # pylint: disable=no-member
        self.app.route("/service_a/")(service_a_endpoint)
        self.app.route("/service_a_manual/")(service_a_with_manual_spans)

    def test_custom_names_at_all_entry_spans(self):
        """Test that custom names are set independently for each service entry span

        Service A calls service B via HTTP, creating a distributed trace where each
        service sets its own custom transaction name on its respective entry span.
        """
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            resp_a = self.client.get("/service_a/")
            assert resp_a.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0
            entry_spans = [
                s
                for s in spans
                if not (
                    s.parent and s.parent.is_valid and not s.parent.is_remote
                )
            ]
            assert len(entry_spans) == 2
            # leaf-most entry span will be first
            assert (
                entry_spans[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
                == "custom-service-b"
            )
            assert (
                entry_spans[1].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
                == "custom-service-a"
            )

            # Verify metrics also have correct transaction names
            metrics_a = self._get_metrics_for_transaction("custom-service-a")
            assert len(metrics_a) == 1
            assert metrics_a[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "custom-service-a"
            
            metrics_b = self._get_metrics_for_transaction("custom-service-b")
            assert len(metrics_b) == 1
            assert metrics_b[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "custom-service-b"

    def test_custom_names_across_more_complex_traces(self):
        """Test custom names work correctly when manual spans are created with OTel SDK

        Each service creates manual child spans using start_as_current_span before calling
        set_transaction_name. The entry spans should still get the custom names, and the
        trace should contain additional manual spans.
        """
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            resp_a = self.client.get("/service_a_manual/")
            assert resp_a.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0

            entry_spans = [
                s
                for s in spans
                if not (
                    s.parent and s.parent.is_valid and not s.parent.is_remote
                )
            ]
            assert len(entry_spans) == 2
            # leaf-most entry span will be first
            assert (
                entry_spans[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
                == "custom-service-b"
            )
            assert (
                entry_spans[1].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
                == "custom-service-a"
            )

            manual_spans = [s for s in spans if s.name.startswith("manual-")]
            assert len(manual_spans) == 4
            assert manual_spans[0].name == "manual-inner-b"
            assert manual_spans[1].name == "manual-outer-b"
            assert manual_spans[2].name == "manual-inner-a"
            assert manual_spans[3].name == "manual-outer-a"

            # Verify metrics also have correct transaction names
            metrics_a = self._get_metrics_for_transaction("custom-service-a")
            assert len(metrics_a) == 1
            assert metrics_a[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "custom-service-a"
            
            metrics_b = self._get_metrics_for_transaction("custom-service-b")
            assert len(metrics_b) == 1
            assert metrics_b[0].attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "custom-service-b"
