# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0
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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy token-and-name keys return true and log a warning."""
    monkeypatch.setattr(logging.getLogger("solarwinds_apm"), "propagate", True)
    caplog.set_level(logging.WARNING, logger="solarwinds_apm.apm_config")

    assert calculate_service_key_format_deprecated("token:service") is True

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert "SW_APM_SERVICE_KEY is deprecated" in caplog.records[0].message
    assert "token" not in caplog.records[0].message
