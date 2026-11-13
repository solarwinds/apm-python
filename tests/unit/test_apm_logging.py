# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

import logging

from solarwinds_apm import apm_logging


class TestApmLoggingLevel:
    def test_single_line_formatter_escapes_record_and_exception_newlines(self):
        try:
            raise ValueError("untrusted\r\nexception")
        except ValueError as error:
            exc_info = (type(error), error, error.__traceback__)

        record = logging.LogRecord(
            "solarwinds_apm",
            logging.ERROR,
            __file__,
            1,
            "untrusted\r\nmessage",
            (),
            exc_info,
        )
        formatter = apm_logging._SingleLineFormatter("%(message)s")

        formatted = formatter.format(record)

        assert "\r" not in formatted
        assert "\n" not in formatted
        assert r"untrusted\r\nmessage" in formatted
        assert r"untrusted\r\nexception" in formatted

    def test_stream_handler_uses_single_line_formatter(self):
        handler = apm_logging._create_stream_handler()

        assert isinstance(handler.formatter, apm_logging._SingleLineFormatter)

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
        mock_apm_logger = mocker.patch("solarwinds_apm.apm_logging.logger")
        mock_warning = mocker.Mock()
        mock_error = mocker.Mock()
        mock_addhandler = mocker.Mock()
        mock_rmhandler = mocker.Mock()
        mock_apm_logger.configure_mock(
            addHandler=mock_addhandler,
            error=mock_error,
            removeHandler=mock_rmhandler,
            warning=mock_warning,
        )
        if error:
            mock_rfhandler = mocker.patch(
                "solarwinds_apm.apm_logging.RotatingFileHandler",
                side_effect=FileNotFoundError("mock error"),
            )
        else:
            mock_rfhandler = mocker.patch(
                "solarwinds_apm.apm_logging.RotatingFileHandler"
            )

        return mock_apm_logger, mock_rfhandler

    def test_update_sw_log_handler_no_log_filepath(self, mocker):
        mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(
            mocker
        )

        apm_logging.update_sw_log_handler("")
        mock_rfhandler.assert_not_called()
        mock_apm_logger.addHandler.assert_not_called()
        mock_apm_logger.removeHandler.assert_not_called()
        mock_apm_logger.error.assert_not_called()
        mock_apm_logger.warning.assert_not_called()

    def test_update_sw_log_handler_filenotfounderror(self, mocker):
        mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(
            mocker,
            error=True,
        )

        apm_logging.update_sw_log_handler("foo")
        mock_rfhandler.assert_called_once_with(
            filename="foo", maxBytes=0, backupCount=0
        )
        mock_apm_logger.addHandler.assert_not_called()
        mock_apm_logger.removeHandler.assert_not_called()
        mock_apm_logger.error.assert_called_once_with(
            "Could not write logs to file; please check configured SW_APM_LOG_FILEPATH / logFilepath."
        )
        mock_apm_logger.warning.assert_not_called()

    def test_update_sw_log_handler_update_handlers(self, mocker):
        mock_apm_logger, mock_rfhandler = self.get_mock_logger_and_rfhandler(
            mocker
        )

        apm_logging.update_sw_log_handler("foo")
        mock_rfhandler.assert_called_once_with(
            filename="foo", maxBytes=0, backupCount=0
        )
        file_formatter = (
            mock_rfhandler.return_value.setFormatter.call_args.args[0]
        )
        assert isinstance(file_formatter, apm_logging._SingleLineFormatter)
        mock_apm_logger.addHandler.assert_called_once()
        mock_apm_logger.removeHandler.assert_called_once()
        mock_apm_logger.error.assert_not_called()
        mock_apm_logger.warning.assert_not_called()
