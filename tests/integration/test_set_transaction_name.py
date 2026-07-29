# © 2026 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import time
from unittest import mock

from solarwinds_apm.api import set_transaction_name
from solarwinds_apm.apm_constants import INTL_SWO_TRANSACTION_ATTR_KEY
from solarwinds_apm.trace.serviceentry_processor import ServiceEntrySpanProcessor

from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestSetTransactionNameBasic(TestBaseSwHeadersAndAttributes):
    """Basic functionality tests for set_transaction_name()"""

    def setUp(self):
        super().setUp()
        self.tracer_provider.add_span_processor(ServiceEntrySpanProcessor())

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
        """Test that single call to set_transaction_name sets sw.transaction attribute"""
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
                s for s in spans 
                if not (s.parent and s.parent.is_valid and not s.parent.is_remote)
            ]
            assert len(entry_spans) == 1
            entry_span = entry_spans[0]
            assert entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "custom-name"

    def test_multiple_calls_last_wins(self):
        """Test that multiple calls to set_transaction_name, last one wins"""
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
                s for s in spans 
                if not (s.parent and s.parent.is_valid and not s.parent.is_remote)
            ]
            assert len(entry_spans) == 1
            entry_span = entry_spans[0]
            assert entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY) == "second"


class TestSetTransactionNameEdgeCases(TestBaseSwHeadersAndAttributes):
    """Edge case tests for set_transaction_name()"""

    def setUp(self):
        super().setUp()
        self.tracer_provider.add_span_processor(ServiceEntrySpanProcessor())

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
        """Test that empty string is rejected and original name preserved"""
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
                s for s in spans 
                if not (s.parent and s.parent.is_valid and not s.parent.is_remote)
            ]
            assert len(entry_spans) == 1
            
            entry_span = entry_spans[0]
            txn_name = entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
            assert txn_name is not None
            assert txn_name != ""
            assert "/test_empty_string/" == txn_name

    def test_none_value_rejected(self):
        """Test that None value is rejected and original name preserved"""
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
                s for s in spans 
                if not (s.parent and s.parent.is_valid and not s.parent.is_remote)
            ]
            assert len(entry_spans) == 1
            
            entry_span = entry_spans[0]
            txn_name = entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
            assert txn_name is not None
            assert "test_none_value" in txn_name or "/test_none_value/" == txn_name

    def test_no_active_span_returns_false(self):
        """Test that calling set_transaction_name outside request context returns False"""
        result = set_transaction_name("test")
        assert result is False

    def test_long_name_truncated(self):
        """Test that long transaction names are truncated to 256 characters"""
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
                s for s in spans 
                if not (s.parent and s.parent.is_valid and not s.parent.is_remote)
            ]
            assert len(entry_spans) == 1
            
            entry_span = entry_spans[0]
            txn_name = entry_span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
            assert txn_name is not None
            assert len(txn_name) == 256
            assert txn_name == "a" * 256
