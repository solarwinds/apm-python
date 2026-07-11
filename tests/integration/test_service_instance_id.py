# © 2026 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import time
import uuid
from unittest import mock

from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestServiceInstanceIdPrecedence1ResourceAttributes(TestBaseSwHeadersAndAttributes):
    """Test that OTEL_RESOURCE_ATTRIBUTES service.instance.id has highest priority."""

    def setUp(self):
        os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.instance.id=resource-attr-instance-123"
        os.environ["WEBSITE_INSTANCE_ID"] = "azure-instance-456"
        super().setUp()

    def tearDown(self):
        os.environ.pop("OTEL_RESOURCE_ATTRIBUTES", None)
        os.environ.pop("WEBSITE_INSTANCE_ID", None)
        super().tearDown()

    def test_resource_attributes_over_azure_detector(self):
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
            resource = self.configurator.apm_config.resource
            assert resource.attributes["service.instance.id"] == "resource-attr-instance-123"


class TestServiceInstanceIdPrecedence2AzureAppService(TestBaseSwHeadersAndAttributes):
    """Test that Azure App Service WEBSITE_INSTANCE_ID overrides UUID fallback."""

    def setUp(self):
        os.environ["WEBSITE_INSTANCE_ID"] = "azure-app-instance-abc123"
        os.environ["WEBSITE_SITE_NAME"] = "my-azure-app"
        os.environ["WEBSITE_RESOURCE_GROUP"] = "prod-rg"
        super().setUp()

    def tearDown(self):
        os.environ.pop("WEBSITE_INSTANCE_ID", None)
        os.environ.pop("WEBSITE_SITE_NAME", None)
        os.environ.pop("WEBSITE_RESOURCE_GROUP", None)
        super().tearDown()

    def test_azure_app_service_instance_id_over_uuid(self):
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
            resource = self.configurator.apm_config.resource
            assert resource.attributes["service.instance.id"] == "azure-app-instance-abc123"


class TestServiceInstanceIdPrecedence4UUIDFallback(TestBaseSwHeadersAndAttributes):
    """Test that non-platform environments get UUID from ServiceInstanceIdResourceDetector."""

    def setUp(self):
        # No Azure nor AWS environment variables
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_uuid_fallback_in_non_platform_environment(self):
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
            resource = self.configurator.apm_config.resource
            assert "service.instance.id" in resource.attributes
            instance_id = resource.attributes["service.instance.id"]
            try:
                uuid.UUID(instance_id)
                is_valid_uuid = True
            except (ValueError, AttributeError):
                is_valid_uuid = False
            assert is_valid_uuid, f"service.instance.id '{instance_id}' is not a valid UUID"


class TestServiceInstanceIdWithCustomDetectors(TestBaseSwHeadersAndAttributes):
    """Test service.instance.id with custom OTEL_EXPERIMENTAL_RESOURCE_DETECTORS that excludes service_instance."""

    def setUp(self):
        # Custom detector list WITHOUT service_instance - SDK should auto-append it
        os.environ["OTEL_EXPERIMENTAL_RESOURCE_DETECTORS"] = "process,os"
        super().setUp()

    def tearDown(self):
        os.environ.pop("OTEL_EXPERIMENTAL_RESOURCE_DETECTORS", None)
        super().tearDown()

    def test_sdk_auto_appends_service_instance_detector(self):
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
            resource = self.configurator.apm_config.resource
            assert "service.instance.id" in resource.attributes
            instance_id = resource.attributes["service.instance.id"]
            try:
                uuid.UUID(instance_id)
                is_valid_uuid = True
            except (ValueError, AttributeError):
                is_valid_uuid = False
            assert is_valid_uuid, f"service.instance.id '{instance_id}' is not a valid UUID"
