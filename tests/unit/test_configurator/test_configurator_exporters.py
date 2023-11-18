# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from solarwinds_apm.configurator import SolarWindsConfigurator

# otel fixtures
from .fixtures.batch_span_processor import fixture_mock_bsprocessor
from .fixtures.trace import fixture_mock_trace

# apm python fixtures
from .fixtures.apm_config import (
    fixture_mock_apmconfig_disabled,
    fixture_mock_apmconfig_enabled,
)
from .fixtures.extension import (
    fixture_mock_reporter,
)
from .fixtures.fwkv_manager import fixture_mock_fwkv_manager
from .fixtures.meter_manager import fixture_mock_meter_manager
from .fixtures.txn_name_manager import fixture_mock_txn_name_manager


class TestConfiguratorExporters:
    def test_configure_traces_exporter_disabled(
        self,
        mocker,
        mock_reporter,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_apmconfig_disabled,
        mock_trace,
        mock_bsprocessor,
    ):
        configurator = SolarWindsConfigurator()
        configurator._configure_traces_exporter(
            mock_reporter,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_disabled,
        )
        mock_trace.assert_not_called()
        mock_bsprocessor.assert_not_called()

    def test_configure_traces_exporter_none(
        self,
        mocker,
        mock_reporter,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_apmconfig_enabled,
        mock_trace,
        mock_bsprocessor,
    ):
        # Save any EXPORTER env var for later
        old_traces_exporter = os.environ.get("OTEL_TRACES_EXPORTER", None)
        if old_traces_exporter:
            del os.environ["OTEL_TRACES_EXPORTER"]

        configurator = SolarWindsConfigurator()
        configurator._configure_traces_exporter(
            mock_reporter,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_enabled,
        )
        mock_trace.assert_not_called()
        mock_bsprocessor.assert_not_called()

        # Restore old EXPORTER
        if old_traces_exporter:
            os.environ["OTEL_TRACES_EXPORTER"] = old_traces_exporter

    def test_configure_traces_exporter_invalid(
        self,
        mocker,
        mock_reporter,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_apmconfig_enabled,
        mock_trace,
        mock_bsprocessor,
    ):
        # Save any EXPORTER env var for later
        old_traces_exporter = os.environ.get("OTEL_TRACES_EXPORTER", None)
        if old_traces_exporter:
            del os.environ["OTEL_TRACES_EXPORTER"]

        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = []
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        mocker.patch.dict(
            os.environ,
            {
                "OTEL_TRACES_EXPORTER": "invalid_exporter"
            }
        )

        configurator = SolarWindsConfigurator()
        configurator._configure_traces_exporter(
            mock_reporter,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_enabled,
        )
        mock_trace.assert_not_called()
        mock_bsprocessor.assert_not_called()

        # Restore old EXPORTER
        if old_traces_exporter:
            os.environ["OTEL_TRACES_EXPORTER"] = old_traces_exporter

    def test_configure_traces_exporter_valid(
        self,
        mocker,
        mock_reporter,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_apmconfig_enabled,
        mock_trace,
        mock_bsprocessor,
    ):
        # Save any EXPORTER env var for later
        old_traces_exporter = os.environ.get("OTEL_TRACES_EXPORTER", None)
        if old_traces_exporter:
            del os.environ["OTEL_TRACES_EXPORTER"]

        # TODO

        # Restore old EXPORTER
        if old_traces_exporter:
            os.environ["OTEL_TRACES_EXPORTER"] = old_traces_exporter

    def test_configure_traces_exporter_mixed(self, mocker):
        # Save any EXPORTER env var for later
        old_traces_exporter = os.environ.get("OTEL_TRACES_EXPORTER", None)
        if old_traces_exporter:
            del os.environ["OTEL_TRACES_EXPORTER"]

        # TODO

        # Restore old EXPORTER
        if old_traces_exporter:
            os.environ["OTEL_TRACES_EXPORTER"] = old_traces_exporter