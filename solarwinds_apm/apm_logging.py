""" SolarWinds APM agent-internal logging module.

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


class ApmLoggingLevel:
    """Abstract mapping class providing a conversion between solarwinds_apm agent logging level and Python logging module
    logging levels.
    The solarwinds_apm package has seven different log levels, which are defined in the debug_levels dictionary."""

    # maps string representation of solarwinds_apm.sw_logging levels to their integer counterpart
    debug_levels = {
        'OBOE_DEBUG_DISABLE': -1,
        'OBOE_DEBUG_FATAL': 0,
        'OBOE_DEBUG_ERROR': 1,
        'OBOE_DEBUG_WARNING': 2,
        'OBOE_DEBUG_INFO': 3,
        'OBOE_DEBUG_LOW': 4,
        'OBOE_DEBUG_MEDIUM': 5,
        'OBOE_DEBUG_HIGH': 6,
    }

    # maps solarwinds_apm log levels to python logging module log levels
    logging_map = {
        debug_levels['OBOE_DEBUG_DISABLE']: logging.CRITICAL,
        debug_levels['OBOE_DEBUG_FATAL']: logging.CRITICAL,
        debug_levels['OBOE_DEBUG_ERROR']: logging.ERROR,
        debug_levels['OBOE_DEBUG_WARNING']: logging.WARNING,
        debug_levels['OBOE_DEBUG_INFO']: logging.INFO,
        debug_levels['OBOE_DEBUG_LOW']: logging.DEBUG,
        debug_levels['OBOE_DEBUG_MEDIUM']: logging.DEBUG,
        debug_levels['OBOE_DEBUG_HIGH']: logging.DEBUG,
    }

    @classmethod
    def default_level(cls):
        """Returns integer representation of default debugging level"""
        return cls.debug_levels['OBOE_DEBUG_WARNING']

    @classmethod
    def is_valid_level(cls, level):
        """Returns True if the provided level is a valid interger representation of a solarwinds_apm.sw_logging level,
        False otherwise."""
        try:
            level = int(level)
            return bool(level in list(cls.debug_levels.values()))
        except (ValueError, TypeError):
            return False
