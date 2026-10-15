# © 2026 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
"""Tests for service-key format deprecation detection."""

import logging

import pytest

from solarwinds_apm.apm_config import calculate_service_key_format_deprecated


@pytest.mark.parametrize("service_key", ["a", "token", ""])
def test_token_only_service_key_is_not_deprecated(
    service_key: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Token-only and empty service keys do not emit deprecation warnings."""
    caplog.set_level(logging.WARNING, logger="solarwinds_apm.apm_config")

    assert calculate_service_key_format_deprecated(service_key) is False
    assert not caplog.records


def test_legacy_service_key_is_deprecated_and_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Legacy token-and-name keys return true and log a warning."""
    caplog.set_level(logging.WARNING, logger="solarwinds_apm.apm_config")

    assert calculate_service_key_format_deprecated("token:service") is True

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert "SW_APM_SERVICE_KEY is deprecated" in caplog.records[0].message
    assert "token" not in caplog.records[0].message
