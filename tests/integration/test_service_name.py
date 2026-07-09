# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import time
from unittest import mock

from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestServiceNamePrecedence1OtelServiceName(TestBaseSwHeadersAndAttributes):

    def setUp(self):
        os.environ["OTEL_SERVICE_NAME"] = "otel-override"
        os.environ["WEBSITE_SITE_NAME"] = "azure-app"
        os.environ["WEBSITE_RESOURCE_GROUP"] = "azure-rg"
        super().setUp()

    def tearDown(self):
        os.environ.pop("OTEL_SERVICE_NAME", None)
        os.environ.pop("WEBSITE_SITE_NAME", None)
        os.environ.pop("WEBSITE_RESOURCE_GROUP", None)
        super().tearDown()

    def test_otel_service_name_over_azure(self):
        # Mock JSON read to guarantee sample decision
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
            resp = self.client.get("/test_trace/", headers={"x-test": "value"})
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0

            # Verify service.name from OTEL_SERVICE_NAME
            resource_attrs = spans[0].resource.attributes
            assert resource_attrs["service.name"] == "otel-override"
            # Verify Azure detector still ran and set cloud attributes
            assert resource_attrs["cloud.provider"] == "azure"
            assert resource_attrs["cloud.platform"] == "azure_app_service"


class TestServiceNamePrecedence2ResourceAttributes(TestBaseSwHeadersAndAttributes):

    def setUp(self):
        os.environ[
            "OTEL_RESOURCE_ATTRIBUTES"
        ] = "service.name=resource-attr-name,deployment.environment=prod"
        os.environ["WEBSITE_SITE_NAME"] = "azure-app"
        super().setUp()

    def tearDown(self):
        os.environ.pop("OTEL_RESOURCE_ATTRIBUTES", None)
        os.environ.pop("WEBSITE_SITE_NAME", None)
        super().tearDown()

    def test_resource_attributes_over_detector(self):
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
            resp = self.client.get("/test_trace/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0

            resource_attrs = spans[0].resource.attributes
            assert resource_attrs["service.name"] == "resource-attr-name"
            assert resource_attrs["deployment.environment"] == "prod"
            assert resource_attrs["cloud.provider"] == "azure"


class TestServiceNamePrecedence3AzureDetector(TestBaseSwHeadersAndAttributes):

    def setUp(self):
        os.environ["WEBSITE_SITE_NAME"] = "azure-production-app"
        os.environ["WEBSITE_RESOURCE_GROUP"] = "prod-rg"
        os.environ["SW_APM_SERVICE_KEY"] = "token:should-be-ignored"
        super().setUp()

    def tearDown(self):
        os.environ.pop("WEBSITE_SITE_NAME", None)
        os.environ.pop("WEBSITE_RESOURCE_GROUP", None)
        os.environ.pop("SW_APM_SERVICE_KEY", None)
        super().tearDown()

    def test_azure_detector_over_sw_key(self):
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
            resp = self.client.get("/test_trace/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0

            resource_attrs = spans[0].resource.attributes
            # Verify Azure detector set service.name (overriding base class SW_APM_SERVICE_KEY="foo:bar")
            assert resource_attrs["service.name"] == "azure-production-app"
            # Verify basic Azure cloud attributes are set
            assert resource_attrs["cloud.provider"] == "azure"
            assert resource_attrs["cloud.platform"] == "azure_app_service"


class TestServiceNamePrecedence4SwKeyFallback(TestBaseSwHeadersAndAttributes):

    def setUp(self):
        # Base class will set SW_APM_SERVICE_KEY="foo:bar"
        super().setUp()

    def test_sw_key_fallback(self):
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
            resp = self.client.get("/test_trace/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0

            resource_attrs = spans[0].resource.attributes
            # Base class sets SW_APM_SERVICE_KEY="foo:bar", so service.name should be "bar"
            assert resource_attrs["service.name"] == "bar"
            # Verify process/host detector attributes are present
            assert "process.pid" in resource_attrs
            assert isinstance(resource_attrs["process.pid"], int)
            assert "host.name" in resource_attrs
            assert isinstance(resource_attrs["host.name"], str)


class TestServiceNameAzureDetectorFullEnvironment(TestBaseSwHeadersAndAttributes):

    def setUp(self):
        os.environ["WEBSITE_SITE_NAME"] = "my-azure-app"
        os.environ["WEBSITE_RESOURCE_GROUP"] = "production-rg"
        os.environ["WEBSITE_OWNER_NAME"] = "subscription-id+webspace-name"
        os.environ["WEBSITE_INSTANCE_ID"] = "abc123def456"
        os.environ["WEBSITE_SLOT_NAME"] = "staging"
        os.environ["REGION_NAME"] = "eastus"
        os.environ["SW_APM_SERVICE_KEY"] = "token:ignored"
        super().setUp()

    def tearDown(self):
        os.environ.pop("WEBSITE_SITE_NAME", None)
        os.environ.pop("WEBSITE_RESOURCE_GROUP", None)
        os.environ.pop("WEBSITE_OWNER_NAME", None)
        os.environ.pop("WEBSITE_INSTANCE_ID", None)
        os.environ.pop("WEBSITE_SLOT_NAME", None)
        os.environ.pop("REGION_NAME", None)
        os.environ.pop("SW_APM_SERVICE_KEY", None)
        super().tearDown()

    def test_azure_detector_full_environment(self):
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
            resp = self.client.get("/test_trace/")
            assert resp.status_code == 200
            spans = self.memory_exporter.get_finished_spans()
            assert len(spans) > 0

            resource_attrs = spans[0].resource.attributes
            # Verify Azure detector set service.name from WEBSITE_SITE_NAME
            assert resource_attrs["service.name"] == "my-azure-app"
            # Verify core Azure cloud attributes are set
            assert resource_attrs["cloud.provider"] == "azure"
            assert resource_attrs["cloud.platform"] == "azure_app_service"
            # Verify process/host detector attributes also present
            assert "process.pid" in resource_attrs
            assert "host.name" in resource_attrs
            # Verify SW attributes are always present
            assert "sw.apm.version" in resource_attrs
            assert "sw.data.module" in resource_attrs
            assert resource_attrs["sw.data.module"] == "apm"
