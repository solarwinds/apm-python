# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

import os

import pytest

from solarwinds_apm import configurator


class TestConfiguratorPropagators:
    def test_configure_propagator_none_uses_default(
        self,
        mocker,
        mock_composite_propagator,
        mock_set_global_textmap,
    ):
        # Save any PROPAGATOR env var for later
        old_propagators = os.environ.get("OTEL_PROPAGATORS", None)
        if old_propagators:
            del os.environ["OTEL_PROPAGATORS"]

        # Mock entry points
        mock_propagator_class = mocker.MagicMock()
        mock_propagator_entry_point = mocker.Mock()
        mock_propagator_entry_point.configure_mock(load=mock_propagator_class)
        mock_points = iter(
            [
                mock_propagator_entry_point,
                mock_propagator_entry_point,
                mock_propagator_entry_point,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(return_value=mock_points)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_propagator()
        mock_entry_points.assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_propagator",
                    name="solarwinds_propagator",
                ),
                mocker.call(group="opentelemetry_propagator", name="baggage"),
            ]
        )
        mock_composite_propagator.assert_called_once()
        mock_set_global_textmap.assert_called_once()

        # Restore old PROPAGATOR
        if old_propagators:
            os.environ["OTEL_PROPAGATORS"] = old_propagators

    def test_configure_propagator_invalid(
        self,
        mocker,
        mock_composite_propagator,
        mock_set_global_textmap,
    ):
        # Save any PROPAGATOR env var for later
        old_propagators = os.environ.get("OTEL_PROPAGATORS", None)
        if old_propagators:
            del os.environ["OTEL_PROPAGATORS"]

        mocker.patch.dict(
            os.environ, {"OTEL_PROPAGATORS": "invalid_propagator"}
        )

        # Test!
        mock_composite_propagator.assert_not_called()
        mock_set_global_textmap.assert_not_called()

        # Restore old PROPAGATOR
        if old_propagators:
            os.environ["OTEL_PROPAGATORS"] = old_propagators

    def test_configure_propagator_valid(
        self,
        mocker,
        mock_composite_propagator,
        mock_set_global_textmap,
    ):
        # Save any PROPAGATOR env var for later
        old_propagators = os.environ.get("OTEL_PROPAGATORS", None)
        if old_propagators:
            del os.environ["OTEL_PROPAGATORS"]

        # Mock entry points
        mock_propagator_class = mocker.MagicMock()
        mock_propagator_entry_point = mocker.Mock()
        mock_propagator_entry_point.configure_mock(load=mock_propagator_class)
        mock_points = iter(
            [
                mock_propagator_entry_point,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(return_value=mock_points)

        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "valid_propagator"})

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_propagator()
        mock_entry_points.assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_propagator", name="valid_propagator"
                ),
            ]
        )
        mock_composite_propagator.assert_called_once()
        mock_set_global_textmap.assert_called_once()

        # Restore old PROPAGATOR
        if old_propagators:
            os.environ["OTEL_PROPAGATORS"] = old_propagators

    def test_configure_propagator_valid_baggage_sw(
        self,
        mocker,
        mock_composite_propagator,
        mock_set_global_textmap,
    ):
        # Save any PROPAGATOR env var for later
        old_propagators = os.environ.get("OTEL_PROPAGATORS", None)
        if old_propagators:
            del os.environ["OTEL_PROPAGATORS"]

        # Mock entry points
        mock_propagator_class = mocker.MagicMock()
        mock_propagator_entry_point = mocker.Mock()
        mock_propagator_entry_point.configure_mock(load=mock_propagator_class)
        mock_points = iter(
            [
                mock_propagator_entry_point,
                mock_propagator_entry_point,
                mock_propagator_entry_point,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(return_value=mock_points)

        mocker.patch.dict(
            os.environ, {"OTEL_PROPAGATORS": "baggage,solarwinds_propagator"}
        )

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_propagator()
        mock_entry_points.assert_has_calls(
            [
                mocker.call(group="opentelemetry_propagator", name="baggage"),
                mocker.call(
                    group="opentelemetry_propagator",
                    name="solarwinds_propagator",
                ),
            ]
        )
        mock_composite_propagator.assert_called_once()
        mock_set_global_textmap.assert_called_once()

        # Restore old PROPAGATOR
        if old_propagators:
            os.environ["OTEL_PROPAGATORS"] = old_propagators

    def test_configure_propagator_valid_sw_baggage(
        self,
        mocker,
        mock_composite_propagator,
        mock_set_global_textmap,
    ):
        # Save any PROPAGATOR env var for later
        old_propagators = os.environ.get("OTEL_PROPAGATORS", None)
        if old_propagators:
            del os.environ["OTEL_PROPAGATORS"]

        # Mock entry points
        mock_propagator_class = mocker.MagicMock()
        mock_propagator_entry_point = mocker.Mock()
        mock_propagator_entry_point.configure_mock(load=mock_propagator_class)
        mock_points = iter(
            [
                mock_propagator_entry_point,
                mock_propagator_entry_point,
                mock_propagator_entry_point,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(return_value=mock_points)

        mocker.patch.dict(
            os.environ, {"OTEL_PROPAGATORS": "solarwinds_propagator,baggage"}
        )

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_propagator()
        mock_entry_points.assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_propagator",
                    name="solarwinds_propagator",
                ),
                mocker.call(group="opentelemetry_propagator", name="baggage"),
            ]
        )
        mock_composite_propagator.assert_called_once()
        mock_set_global_textmap.assert_called_once()

        # Restore old PROPAGATOR
        if old_propagators:
            os.environ["OTEL_PROPAGATORS"] = old_propagators

    def test_configure_propagator_valid_invalid_mixed(
        self,
        mocker,
        mock_composite_propagator,
        mock_set_global_textmap,
    ):
        # Save any PROPAGATOR env var for later
        old_propagators = os.environ.get("OTEL_PROPAGATORS", None)
        if old_propagators:
            del os.environ["OTEL_PROPAGATORS"]

        # Mock entry points
        mock_propagator_class = mocker.MagicMock()
        mock_propagator_entry_point = mocker.Mock()
        mock_propagator_entry_point.configure_mock(load=mock_propagator_class)
        mock_points = iter(
            [
                mock_propagator_entry_point,
                Exception("mock error invalid propagator"),
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(return_value=mock_points)

        mocker.patch.dict(
            os.environ,
            {"OTEL_PROPAGATORS": "valid_propagator,invalid_propagator"},
        )

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(AttributeError):
            test_configurator._configure_propagator()
        mock_entry_points.assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_propagator",
                    name="valid_propagator",
                ),
                mocker.call(
                    group="opentelemetry_propagator",
                    name="invalid_propagator",
                ),
            ]
        )
        mock_composite_propagator.assert_not_called()
        mock_set_global_textmap.assert_not_called()

        # Restore old PROPAGATOR
        if old_propagators:
            os.environ["OTEL_PROPAGATORS"] = old_propagators

    def test_configure_response_propagator(
        self,
        mocker,
        mock_set_global_response_propagator,
    ):
        mock_resp_propagator = mocker.patch(
            "solarwinds_apm.configurator.SolarWindsTraceResponsePropagator"
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_response_propagator()

        mock_resp_propagator.assert_called_once()
        mock_set_global_response_propagator.assert_called_once()
