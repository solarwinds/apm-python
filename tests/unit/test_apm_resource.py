# © 2026 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from opentelemetry.sdk.resources import Resource

from solarwinds_apm import apm_resource
from solarwinds_apm.version import __version__


class TestCreateDetectorResource:

    def test_create_detector_resource_calls_resource_create(self, mocker):
        mock_resource = Resource.create({"test.attr": "test-value"})
        mock_resource_create = mocker.patch(
            "solarwinds_apm.apm_resource.Resource.create",
            return_value=mock_resource,
        )
        result = apm_resource.create_detector_resource()
        mock_resource_create.assert_called_once_with()
        assert result == mock_resource

    def test_create_detector_resource_returns_resource(self):
        result = apm_resource.create_detector_resource()
        assert isinstance(result, Resource)
        assert hasattr(result, "attributes")

    def test_create_detector_resource_includes_detector_attributes(self, mocker):
        detector_attrs = {
            "process.pid": 12345,
            "process.executable.name": "python",
            "host.name": "test-host",
        }
        mock_resource = Resource.create(detector_attrs)
        mocker.patch(
            "solarwinds_apm.apm_resource.Resource.create",
            return_value=mock_resource,
        )
        result = apm_resource.create_detector_resource()
        assert result.attributes["process.pid"] == 12345
        assert result.attributes["process.executable.name"] == "python"
        assert result.attributes["host.name"] == "test-host"


class TestCreateApmResource:

    def test_create_apm_resource_adds_sw_attributes(self):
        detector_resource = Resource.create({"host.name": "test-host"})
        service_name = "test-service"
        result = apm_resource.create_apm_resource(detector_resource, service_name)
        attrs = result.attributes
        assert attrs["sw.apm.version"] == __version__
        assert attrs["sw.data.module"] == "apm"
        assert attrs["service.name"] == service_name

    def test_create_apm_resource_preserves_detector_attributes(self):
        detector_resource = Resource.create({
            "cloud.provider": "azure",
            "cloud.resource_id": "/subscriptions/test/resourceGroups/test",
            "host.name": "test-host",
            "process.pid": 12345,
            "k8s.namespace.name": "default",
            "k8s.pod.name": "test-pod",
        })
        service_name = "test-service"
        result = apm_resource.create_apm_resource(detector_resource, service_name)

        attrs = result.attributes
        # SW attributes present
        assert attrs["sw.apm.version"] == __version__
        assert attrs["sw.data.module"] == "apm"
        assert attrs["service.name"] == service_name
        # All detector attributes preserved
        assert attrs["cloud.provider"] == "azure"
        assert attrs["cloud.resource_id"] == "/subscriptions/test/resourceGroups/test"
        assert attrs["host.name"] == "test-host"
        assert attrs["process.pid"] == 12345
        assert attrs["k8s.namespace.name"] == "default"
        assert attrs["k8s.pod.name"] == "test-pod"

    def test_create_apm_resource_overrides_detector_service_name(self):
        detector_resource = Resource.create({
            "service.name": "detector-service",
            "host.name": "test-host",
        })
        service_name = "override-service"

        result = apm_resource.create_apm_resource(detector_resource, service_name)

        attrs = result.attributes
        # Service name should be overridden
        assert attrs["service.name"] == "override-service"
        # Other detector attributes preserved
        assert attrs["host.name"] == "test-host"

    def test_create_apm_resource_generates_service_instance_id(self):
        detector_resource = Resource.create({"host.name": "test-host"})
        service_name = "test-service"

        result = apm_resource.create_apm_resource(detector_resource, service_name)

        attrs = result.attributes
        assert "service.instance.id" in attrs
        # Should be a UUID string (36 chars with dashes)
        instance_id = attrs["service.instance.id"]
        assert isinstance(instance_id, str)
        assert len(instance_id) == 36

    def test_create_apm_resource_preserves_existing_service_instance_id(self):
        existing_instance_id = "existing-instance-id-123"
        detector_resource = Resource.create({
            "host.name": "test-host",
            "service.instance.id": existing_instance_id,
        })
        service_name = "test-service"
        result = apm_resource.create_apm_resource(detector_resource, service_name)
        attrs = result.attributes
        assert attrs["service.instance.id"] == existing_instance_id

    def test_create_apm_resource_with_empty_detector_resource(self):
        detector_resource = Resource.create()
        service_name = "test-service"
        result = apm_resource.create_apm_resource(detector_resource, service_name)
        attrs = result.attributes
        assert attrs["sw.apm.version"] == __version__
        assert attrs["sw.data.module"] == "apm"
        assert attrs["service.name"] == service_name
        assert "service.instance.id" in attrs

    def test_create_apm_resource_with_empty_service_name(self):
        detector_resource = Resource.create({"host.name": "test-host"})
        service_name = ""
        result = apm_resource.create_apm_resource(detector_resource, service_name)
        attrs = result.attributes
        assert attrs["service.name"] == ""
        assert attrs["sw.apm.version"] == __version__
        assert attrs["sw.data.module"] == "apm"

    def test_create_apm_resource_with_azure_detector_attributes(self):
        detector_resource = Resource.create({
            "cloud.provider": "azure",
            "cloud.platform": "azure_app_service",
            "cloud.resource_id": "/subscriptions/sub-id/resourceGroups/rg-name/providers/Microsoft.Web/sites/app-name",
            "service.name": "app-name",
            "service.instance.id": "instance-123",
            "host.id": "host-id-123",
        })
        service_name = "azure-app-service"
        result = apm_resource.create_apm_resource(detector_resource, service_name)
        attrs = result.attributes
        # SW attributes
        assert attrs["sw.apm.version"] == __version__
        assert attrs["sw.data.module"] == "apm"
        assert attrs["service.name"] == "azure-app-service"
        # Azure detector attributes preserved
        assert attrs["cloud.provider"] == "azure"
        assert attrs["cloud.platform"] == "azure_app_service"
        assert attrs["cloud.resource_id"] == "/subscriptions/sub-id/resourceGroups/rg-name/providers/Microsoft.Web/sites/app-name"
        assert attrs["host.id"] == "host-id-123"
        # Existing service.instance.id preserved
        assert attrs["service.instance.id"] == "instance-123"

    def test_create_apm_resource_with_k8s_detector_attributes(self):
        detector_resource = Resource.create({
            "k8s.cluster.name": "test-cluster",
            "k8s.namespace.name": "default",
            "k8s.pod.name": "test-pod-12345",
            "k8s.pod.uid": "pod-uid-12345",
            "k8s.deployment.name": "test-deployment",
            "k8s.node.name": "node-1",
            "container.id": "container-id-12345",
            "container.name": "test-container",
        })
        service_name = "k8s-service"
        result = apm_resource.create_apm_resource(detector_resource, service_name)

        attrs = result.attributes
        # SW attributes
        assert attrs["service.name"] == "k8s-service"
        # K8s detector attributes preserved
        assert attrs["k8s.cluster.name"] == "test-cluster"
        assert attrs["k8s.namespace.name"] == "default"
        assert attrs["k8s.pod.name"] == "test-pod-12345"
        assert attrs["k8s.pod.uid"] == "pod-uid-12345"
        assert attrs["k8s.deployment.name"] == "test-deployment"
        assert attrs["k8s.node.name"] == "node-1"
        assert attrs["container.id"] == "container-id-12345"
        assert attrs["container.name"] == "test-container"
