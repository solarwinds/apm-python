# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

"""OpenTelemetry Resource creation for SolarWinds APM."""

from __future__ import annotations

from opentelemetry.sdk.resources import Resource

from solarwinds_apm.version import __version__


def create_detector_resource() -> Resource:
    """Create Resource from all configured detectors.

    Runs all detectors configured in OTEL_EXPERIMENTAL_RESOURCE_DETECTORS.
    Should be called after SolarWindsDistro has configured default detector list.

    Returns:
        Resource: Resource with attributes from service_instance, process, OS, cloud, k8s, etc. detectors.
    """
    return Resource.create()


def create_apm_resource(
    detector_resource: Resource,
    service_name: str,
) -> Resource:
    """Create final APM Resource by merging SolarWinds attributes into detector resource.

    Adds sw.apm.version, sw.data.module, and service.name.

    Args:
        detector_resource: Resource from detectors with all their attributes.
        service_name: Service name should have been calculated by precedence rules

    Returns:
        Resource: Final resource for telemetry providers (TracerProvider, MeterProvider, LoggerProvider).
    """
    sw_attributes = {
        "sw.apm.version": __version__,
        "sw.data.module": "apm",
        "service.name": service_name,
    }

    # Merge sw_attributes into detector_resource.
    # Resource.merge(other) means other.attributes override self.attributes on conflicts.
    # This preserves all detector attributes (cloud.*, k8s.*, etc.) while ensuring
    # service.name (calculated via precedence) overrides any service.name from detectors.
    apm_resource = detector_resource.merge(Resource(sw_attributes))

    return apm_resource
