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
