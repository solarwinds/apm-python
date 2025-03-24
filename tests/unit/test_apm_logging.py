# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm import apm_logging

class TestApmLoggingType:
    def test_default_type(self):
        assert apm_logging.ApmLoggingType.default_type() == 0
    
    def test_disabled_type(self):
        assert apm_logging.ApmLoggingType.disabled_type() == 4

    def test_file_type(self):
        assert apm_logging.ApmLoggingType.file_type() == 2

    def test_is_valid_type_ok(self):
        assert apm_logging.ApmLoggingType.is_valid_log_type(0)
        assert apm_logging.ApmLoggingType.is_valid_log_type(2)
        assert apm_logging.ApmLoggingType.is_valid_log_type(4)

    def test_is_valid_type_not_int_ret_default(self):
        assert apm_logging.ApmLoggingType.is_valid_log_type("abc") == 0

    def test_is_valid_type_int_out_of_range_ret_default(self):
        assert apm_logging.ApmLoggingType.is_valid_log_type(-9999) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(-1) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(1) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(3) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(5) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(9999) == 0

class TestApmLoggingLevel:
    def test_default_level(self):
        assert apm_logging.ApmLoggingLevel.default_level() == 2

    def test_is_valid_level_ok(self):
        assert apm_logging.ApmLoggingLevel.is_valid_level(-1)
        assert apm_logging.ApmLoggingLevel.is_valid_level(0)
        assert apm_logging.ApmLoggingLevel.is_valid_level(1)
        assert apm_logging.ApmLoggingLevel.is_valid_level(2)
        assert apm_logging.ApmLoggingLevel.is_valid_level(3)
        assert apm_logging.ApmLoggingLevel.is_valid_level(4)
        assert apm_logging.ApmLoggingLevel.is_valid_level(5)
        assert apm_logging.ApmLoggingLevel.is_valid_level(6)

    def test_is_valid_level_not_int(self):
        assert not apm_logging.ApmLoggingLevel.is_valid_level("abc")

    def test_is_valid_level_int_out_of_range(self):
        assert not apm_logging.ApmLoggingLevel.is_valid_level(-9999)
        assert not apm_logging.ApmLoggingLevel.is_valid_level(-2)
        assert not apm_logging.ApmLoggingLevel.is_valid_level(7)
        assert not apm_logging.ApmLoggingLevel.is_valid_level(9999)


class TestSetSwLog:
    def get_mock_logger_and_rfhandler(
        self,
        mocker,
        error=False,
    ):
        mock_apm_logger = mocker.patch(
            "solarwinds_apm.apm_logging.logger"
        )
        mock_warning = mocker.Mock()
        mock_error = mocker.Mock()
        mock_addhandler = mocker.Mock()
        mock_rmhandler = mocker.Mock()
        mock_apm_logger.configure_mock(
            **{
                "addHandler": mock_addhandler,
                "error": mock_error,
                "removeHandler": mock_rmhandler,
                "warning": mock_warning,
            }
        )
        if error:
            mock_rfhandler = mocker.patch(
                "solarwinds_apm.apm_logging.RotatingFileHandler",
                side_effect=FileNotFoundError("mock error")
            )
        else:
            mock_rfhandler = mocker.patch(
                "solarwinds_apm.apm_logging.RotatingFileHandler"
            )

        return mock_apm_logger, mock_rfhandler

    # def test_set_sw_log_type_invalid(self, mocker):
    #     mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(mocker)
    #
    #     apm_logging.set_sw_log_type(9999, "foo")
    #     mock_rfhandler.assert_not_called()
    #     mock_apm_logger.addHandler.assert_not_called()
    #     mock_apm_logger.removeHandler.assert_not_called()
    #     mock_apm_logger.error.assert_not_called()
    #     mock_apm_logger.warning.assert_called_once_with(
    #         "set_sw_log_type: Ignore attempt to set solarwinds_apm logger with invalid logging handler."
    #     )
    #
    # def test_set_sw_log_type_not_file(self, mocker):
    #     mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(mocker)
    #
    #     apm_logging.set_sw_log_type(0, "foo")
    #     mock_rfhandler.assert_not_called()
    #     mock_apm_logger.addHandler.assert_not_called()
    #     mock_apm_logger.removeHandler.assert_not_called()
    #     mock_apm_logger.error.assert_not_called()
    #     mock_apm_logger.warning.assert_not_called()
    #
    # def test_set_sw_log_type_no_log_filepath(self, mocker):
    #     mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(mocker)
    #
    #     apm_logging.set_sw_log_type(2, "")
    #     mock_rfhandler.assert_not_called()
    #     mock_apm_logger.addHandler.assert_not_called()
    #     mock_apm_logger.removeHandler.assert_not_called()
    #     mock_apm_logger.error.assert_not_called()
    #     mock_apm_logger.warning.assert_not_called()
    #
    # def test_set_sw_log_type_filenotfounderror(self, mocker):
    #     mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(
    #         mocker,
    #         error=True,
    #     )
    #
    #     apm_logging.set_sw_log_type(2, "foo")
    #     mock_rfhandler.assert_called_once_with(
    #         filename='foo', maxBytes=0, backupCount=0
    #     )
    #     mock_apm_logger.addHandler.assert_not_called()
    #     mock_apm_logger.removeHandler.assert_not_called()
    #     mock_apm_logger.error.assert_called_once_with(
    #         "Could not write logs to file; please check configured SW_APM_LOG_FILEPATH."
    #     )
    #     mock_apm_logger.warning.assert_not_called()

    # def test_set_sw_log_type_update_handlers(self, mocker):
    #     mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(mocker)
    #
    #     apm_logging.set_sw_log_type(2, "foo")
    #     mock_rfhandler.assert_called_once_with(
    #         filename='foo', maxBytes=0, backupCount=0
    #     )
    #     mock_apm_logger.addHandler.assert_called_once()
    #     mock_apm_logger.removeHandler.assert_called_once()
    #     mock_apm_logger.error.assert_not_called()
    #     mock_apm_logger.warning.assert_not_called()
