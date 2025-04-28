# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""SolarWinds APM agent-internal logging module.

The solarwinds_apm internal logging is making use of the built-in Python logging module. The solarwinds_apm package
creates a logging handler reporting to stderr where all log messages are reported to. All logging from solarwinds_apm
can be stopped completely by invoking the disable_logger() method.

A log message has the following format:
    '<date> <time> [ <logger_name> <logging_level> p#<process_id>.<thread_id>] <log_message>'

The logging level of the solarwinds_apm logger can be configured with an integer in the range of -1 to 6, representing
the following severities:
    -1: logging disabled
     0: fatal messages
     1: errors
     2: warnings
     3: info
     4: debug low
     5: debug medium
     6: debug high

The log level should not be modified manually from outside the solarwinds_apm package.

For package-internal purposes, the logging level can be configured by providing one of the above levels to the
`set_sw_log_level`. The setLevel method should not be used to modify logging levels of individual module logger
instances.

The name of the main logger is `solarwinds_apm`. Each module should create its own child logger by simply calling
logging.getLogger(__name__) which will return a child logger of the `solarwinds_apm` logger.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


class ApmLoggingLevel:
    """Mapping class providing a conversion between solarwinds_apm library logging level and Python logging module
    logging levels.
    The solarwinds_apm package has six main log levels, which are defined in the debug_levels dictionary.
    There is also a special 7th OBOE_DEBUG_DISABLE for disabling logging, as there is no "disabled" level in Python logging nor agent logging.
    """

    # maps string representation of solarwinds_apm.sw_logging levels to their integer counterpart
    debug_levels = {
        "OBOE_DEBUG_DISABLE": -1,
        "OBOE_DEBUG_FATAL": 0,
        "OBOE_DEBUG_ERROR": 1,
        "OBOE_DEBUG_WARNING": 2,
        "OBOE_DEBUG_INFO": 3,
        "OBOE_DEBUG_LOW": 4,
        "OBOE_DEBUG_MEDIUM": 5,
        "OBOE_DEBUG_HIGH": 6,
    }

    # maps solarwinds_apm log levels to python logging module log levels
    logging_map = {
        debug_levels["OBOE_DEBUG_DISABLE"]: logging.CRITICAL,
        debug_levels["OBOE_DEBUG_FATAL"]: logging.CRITICAL,
        debug_levels["OBOE_DEBUG_ERROR"]: logging.ERROR,
        debug_levels["OBOE_DEBUG_WARNING"]: logging.WARNING,
        debug_levels["OBOE_DEBUG_INFO"]: logging.INFO,
        debug_levels["OBOE_DEBUG_LOW"]: logging.DEBUG,
        debug_levels["OBOE_DEBUG_MEDIUM"]: logging.DEBUG,
        debug_levels["OBOE_DEBUG_HIGH"]: logging.DEBUG,
    }

    @classmethod
    def default_level(cls):
        """Returns integer representation of default debugging level"""
        return cls.debug_levels["OBOE_DEBUG_WARNING"]

    @classmethod
    def is_valid_level(cls, level):
        """Returns True if the provided level is a valid integer representation of a solarwinds_apm.sw_logging level,
        False otherwise."""
        try:
            level = int(level)
            return bool(level in list(cls.debug_levels.values()))
        except (ValueError, TypeError):
            return False


def _create_stream_handler():
    """Creates stream handler reporting to stderr."""
    sh = logging.StreamHandler()  # get stream handler to custom logging prefix
    fm = logging.Formatter(
        "%(asctime)s [ %(name)s %(levelname)-8s p#%(process)d.%(thread)d] %(message)s"
    )
    sh.setFormatter(fm)
    return sh


_stream_handler = _create_stream_handler()


def _get_logger():
    """Creates the logger for agent-internal logging.
    By default, the logging level of the created logger will be set to ApmLoggingLevel.default_level().
    If the logging level of the agent-internal logger needs to be changed, this should happen through one of the
    following options only:
    (1) Through environment variable SW_APM_DEBUG_LEVEL
        - When _get_logger is invoked, SW_APM_DEBUG_LEVEL is checked and the logging level will be set to the
          value provided by the variable. If an invalid value has been provided, the logging level will not be changed.
    (2) By invoking set_sw_log_level
    """

    # create base logger for solarwinds_apm package
    _logger = logging.getLogger("solarwinds_apm")

    # configure logging level of solarwinds_apm logger
    log_level = ApmLoggingLevel.default_level()
    # check if SW_APM_DEBUG_LEVEL has been set and configure newly created logger accordingly
    envv_val = os.getenv("SW_APM_DEBUG_LEVEL", None)
    if envv_val is not None:
        if not ApmLoggingLevel.is_valid_level(envv_val):
            _logger.warning(
                "Misconfigured SW_APM_DEBUG_LEVEL ignored. Defaulted to debug_level %s",
                log_level,
            )
            _logger.warning("")
        else:
            log_level = int(envv_val)

    _logger.setLevel(ApmLoggingLevel.logging_map[log_level])

    _logger.propagate = False
    if log_level != ApmLoggingLevel.debug_levels["OBOE_DEBUG_DISABLE"]:
        _logger.addHandler(_stream_handler)
    else:
        _logger.addHandler(logging.NullHandler())

    return _logger


logger = _get_logger()


def disable_logger(disable=True):
    """Disables all logging messages from the `solarwinds_apm` package when disable is True.
    To restoring logging, set disable as False.
    """
    if disable:
        logger.addHandler(logging.NullHandler())
        logger.removeHandler(_stream_handler)
        logger.propagate = False
    else:
        logger.addHandler(_stream_handler)
        logger.removeHandler(logging.NullHandler())
        logger.propagate = True


def update_sw_log_handler(log_filepath):
    """If log_filepath is provided, APM-internal logger's stream handler
    is swapped with a rotating file handler.
    """
    if log_filepath:
        try:
            file_handler = RotatingFileHandler(
                filename=log_filepath,
                maxBytes=0,
                backupCount=0,
            )
            file_formatter = logging.Formatter(
                "%(asctime)s [ %(name)s %(levelname)-8s p#%(process)d.%(thread)d] %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.propagate = False
            logger.addHandler(file_handler)
            # stop logging to stream
            logger.removeHandler(_stream_handler)
        except FileNotFoundError:
            # path should be checked first by ApmConfig._validate_log_filepath
            logger.error(
                "Could not write logs to file; please check configured SW_APM_LOG_FILEPATH / logFilepath."
            )


def set_sw_log_level(level):
    """Set the logging level of the agent-internal logger to the provided level. This function expects the level
    to be one of the integer representations of the levels defined in ApmLoggingLevel.debug_levels.
    If an invalid level has been provided, the logging level will not be changed but a warning message will be emitted.

    This function should not be used from outside the solarwinds_apm package to modify agent logging behaviour.
    """
    if ApmLoggingLevel.is_valid_level(level):
        logger.setLevel(ApmLoggingLevel.logging_map[level])
        if level == ApmLoggingLevel.debug_levels["OBOE_DEBUG_DISABLE"]:
            disable_logger()
    else:
        logger.warning(
            "set_sw_log_level: Ignore attempt to set solarwinds_apm logger to invalid logging level."
        )
