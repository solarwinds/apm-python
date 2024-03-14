# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm import configurator


class TestConfiguratorReportInitEvent:
    def test_configurator_report_init(
        self,
        mocker,
        mock_extension,
    ):
        mock_log_info = mocker.Mock()
        mock_logger = mocker.patch(
            "solarwinds_apm.configurator.logger"
        )
        mock_logger.configure_mock(
            **{
                "info": mock_log_info,
            }
        )
        mock_event = mocker.Mock()

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._report_init_event(
            mock_extension.Reporter,
            mock_event,
        )
        mock_extension.Reporter.sendStatus.assert_called_once_with(mock_event)
        mock_log_info.assert_called_once()
