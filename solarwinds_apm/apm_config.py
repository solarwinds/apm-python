
from collections import defaultdict
from functools import reduce
import logging
import os
from pkg_resources import iter_entry_points
import sys
from typing import Any

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER,
)

from solarwinds_apm import apm_logging
from solarwinds_apm.apm_constants import (
    INTL_SWO_AO_COLLECTOR,
    INTL_SWO_AO_STG_COLLECTOR,
    INTL_SWO_DEFAULT_TRACES_EXPORTER,
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DOC_SUPPORTED_PLATFORMS,
    INTL_SWO_DOC_TRACING_PYTHON,
    INTL_SWO_SUPPORT_EMAIL,
    INTL_SWO_PROPAGATOR,
    INTL_SWO_TRACECONTEXT_PROPAGATOR,
)

logger = logging.getLogger(__name__)

class OboeTracingMode:
    """Provides an interface to translate the string representation of tracing_mode to the C-extension equivalent."""
    OBOE_SETTINGS_UNSET = -1
    OBOE_TRACE_DISABLED = 0
    OBOE_TRACE_ENABLED = 1
    OBOE_TRIGGER_DISABLED = 0
    OBOE_TRIGGER_ENABLED = 1

    @classmethod
    def get_oboe_trace_mode(cls, tracing_mode: str) -> int:
        if tracing_mode == 'enabled':
            return cls.OBOE_TRACE_ENABLED
        if tracing_mode == 'disabled':
            return cls.OBOE_TRACE_DISABLED
        return cls.OBOE_SETTINGS_UNSET

    @classmethod
    def get_oboe_trigger_trace_mode(cls, trigger_trace_mode: str) -> int:
        if trigger_trace_mode == 'enabled':
            return cls.OBOE_TRIGGER_ENABLED
        if trigger_trace_mode == 'disabled':
            return cls.OBOE_TRIGGER_DISABLED
        return cls.OBOE_SETTINGS_UNSET


class SolarWindsApmConfig:
    """SolarWinds APM Configuration Class
    The precedence: in-code keyword arguments > Environment Variables > config file > default values.
    Note that oboe doesn't read configurations by itself. The Python agent needs to
    read environment variables and/or config files and pass them into oboe. This is
    done only once during the initialization and the properties cannot be refreshed.
    """
    _DELIMITER = '.'
    _KEY_MASK = '{}...{}:{}'
    _KEY_MASK_BAD_FORMAT = '{}...<invalid_format>'
    _KEY_MASK_BAD_FORMAT_SHORT = '{}<invalid_format>'

    def __init__(self, **kwargs: int) -> None:
        self.__config = dict()
        # Update the config with default values
        self.__config = {
            # 'tracing_mode' is unset by default and not supported in NH Python
            'tracing_mode': None,
            # 'trigger_trace' is enabled by default
            'trigger_trace': 'enabled',
            'collector': '',  # the collector address in host:port format.
            'reporter': '',  # the reporter mode, either 'udp' or 'ssl'.
            'debug_level': apm_logging.ApmLoggingLevel.default_level(),
            'service_key': '',
            'hostname_alias': '',
            'trustedpath': '',
            'events_flush_interval': -1,
            'max_request_size_bytes': -1,
            'ec2_metadata_timeout': 1000,
            'max_flush_wait_time': -1,
            'max_transactions': -1,
            'logname': '',
            'trace_metrics': -1,
            'token_bucket_capacity': -1,
            'token_bucket_rate': -1,
            'bufsize': -1,
            'histogram_precision': -1,
            'reporter_file_single': 0,
            'enable_sanitize_sql': True,
            'inst_enabled': defaultdict(lambda: True),
            'log_trace_id': 'never',
            'proxy': '',
            'transaction': defaultdict(lambda: True),
            'inst': defaultdict(lambda: True),
            'is_grpc_clean_hack_enabled': False,
        }
        self.agent_enabled = self._calculate_agent_enabled()

        if self.agent_enabled:
            from solarwinds_apm.extension.oboe import Context
            self.context = Context
        else:
            from solarwinds_apm.apm_noop import Context
            self.context = Context

        # TODO Implement config with cnf_file after alpha
        # cnf_file = os.environ.get('SW_APM_APM_CONFIG_PYTHON', os.environ.get('SW_APM_PYCONF', None))
        # if cnf_file:
        #     self.update_with_cnf_file(cnf_file)

        self.update_with_env_var()

        self.metric_format = self._calculate_metric_format()

        # TODO Implement in-code config with kwargs after alpha
        # self.update_with_kwargs(kwargs)

        logger.debug("Set ApmConfig as: {}".format(self))

    def _is_lambda(self) -> bool:
        """Checks if agent is running in an AWS Lambda environment."""
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') and os.environ.get("LAMBDA_TASK_ROOT"):
            logger.warning("AWS Lambda is not yet supported by Python SolarWinds APM.")
            return True
        return False

    def _calculate_agent_enabled(self) -> bool:
        """Checks if agent is enabled/disabled based on config:
        - SW_APM_SERVICE_KEY   (required)
        - OTEL_PROPAGATORS     (optional)
        - OTEL_TRACES_EXPORTER (optional)
        - SW_APM_AGENT_ENABLED (optional)
        """
        agent_enabled = True

        try:
            # SolarWindsDistro._configure does setdefault so this shouldn't
            # be None, but safer and more explicit this way
            environ_propagators = os.environ.get(
                OTEL_PROPAGATORS,
                ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
            ).split(",")
            # If not using the default propagators,
            # can any arbitrary list BUT
            # (1) must include tracecontext and solarwinds_propagator
            # (2) tracecontext must be before solarwinds_propagator
            if environ_propagators != INTL_SWO_DEFAULT_PROPAGATORS:
                if not INTL_SWO_TRACECONTEXT_PROPAGATOR in environ_propagators or \
                    not INTL_SWO_PROPAGATOR in environ_propagators:
                    logger.error("Must include tracecontext and solarwinds_propagator in OTEL_PROPAGATORS to use SolarWinds APM. Tracing disabled.")
                    raise ValueError

                if environ_propagators.index(INTL_SWO_PROPAGATOR) \
                    < environ_propagators.index(INTL_SWO_TRACECONTEXT_PROPAGATOR):
                    logger.error("tracecontext must be before solarwinds_propagator in OTEL_PROPAGATORS to use SolarWinds APM. Tracing disabled.")
                    raise ValueError
        except ValueError:
            agent_enabled = False

        try:
            # SolarWindsDistro._configure does setdefault so this shouldn't
            # be None, but safer and more explicit this way
            environ_exporters = os.environ.get(
                OTEL_TRACES_EXPORTER,
                INTL_SWO_DEFAULT_TRACES_EXPORTER,
            ).split(",")
            # If not using the default propagators,
            # can any arbitrary list BUT
            # (1) must include solarwinds_exporter
            # (2) other exporters must be loadable by OTel
            if INTL_SWO_DEFAULT_TRACES_EXPORTER not in environ_exporters:
                logger.error("Must include solarwinds_exporter in OTEL_TRACES_EXPORTER to use Solarwinds APM. Tracing disabled.")
                raise ValueError
            for environ_exporter_name in environ_exporters:
                try:
                    if environ_exporter_name != INTL_SWO_DEFAULT_TRACES_EXPORTER:
                        next(
                            iter_entry_points(
                                "opentelemetry_traces_exporter",
                                environ_exporter_name
                            )
                        )
                except StopIteration:
                    logger.error(
                        "Failed to load configured OTEL_TRACES_EXPORTER {}. "
                        "Tracing disabled".format(
                            environ_exporter_name
                        )
                    )
                    agent_enabled = False
        except ValueError:
            agent_enabled = False

        try:
            if os.environ.get('SW_APM_AGENT_ENABLED', 'true').lower() == 'false':
                agent_enabled = False
                logger.info(
                    "SolarWinds APM is disabled and will not report any traces because the environment variable "
                    "SW_APM_AGENT_ENABLED is set to 'false'! If this is not intended either unset the variable or set it to "
                    "a value other than false. Note that the value of SW_APM_AGENT_ENABLED is case-insensitive.")
                raise ImportError

            if not os.environ.get('SW_APM_SERVICE_KEY', None) and not self._is_lambda():
                logger.error("Missing service key. Tracing disabled.")
                agent_enabled = False
                raise ImportError

            else:
                # Key must be at least one char + ":" + at least one other char
                key_parts = [p for p in os.environ.get('SW_APM_SERVICE_KEY', "").split(":") if len(p) > 0]
                if len(key_parts) != 2:
                    logger.error("Incorrect service key format. Tracing disabled.")
                    agent_enabled = False
                    raise ImportError

        except ImportError as e:
            try:
                if agent_enabled:
                    # only log the following messages if agent wasn't explicitly disabled
                    # via SW_APM_AGENT_ENABLED or due to missing service key
                    if sys.platform.startswith('linux'):
                        logger.warning(
                            """Missing extension library.
                            Tracing is disabled and will go into no-op mode.
                            Contact {} if this is unexpected.
                            Error: {}
                            See: {}""".format(
                                INTL_SWO_SUPPORT_EMAIL,
                                e,
                                INTL_SWO_DOC_TRACING_PYTHON,
                            ))
                    else:
                        logger.warning(
                            """Platform {} not yet supported.
                            See: {}
                            Tracing is disabled and will go into no-op mode.
                            Contact {} if this is unexpected.""".format(
                                sys.platform,
                                INTL_SWO_DOC_SUPPORTED_PLATFORMS,
                                INTL_SWO_SUPPORT_EMAIL,
                            ))
            except ImportError as err:
                logger.error(
                    """Unexpected error: {}.
                    Please reinstall or contact {}.""".format(
                        err,
                        INTL_SWO_SUPPORT_EMAIL,
                    ))
            finally:
                # regardless of how we got into this (outer) exception block, the agent will not be able to trace (and thus be
                # disabled)
                agent_enabled = False
        
        logger.debug("agent_enabled: {}".format(agent_enabled))
        return agent_enabled

    def _calculate_metric_format(self) -> int:
        """Return one of 0 (both) or 1 (TransactionResponseTime only). Future: return 2 (ResponseTime only) instead of 0. Based on collector URL which may have a port e.g. foo-collector.com:443"""
        metric_format = 0
        host = self.get("collector")
        if host:
            if len(host.split(":")) > 1:
                host = host.split(":")[0]
            if host in [INTL_SWO_AO_COLLECTOR, INTL_SWO_AO_STG_COLLECTOR]:
                logger.warning("AO collector detected. Only exporting TransactionResponseTime metrics")
                metric_format = 1
        return metric_format

    def mask_service_key(self) -> str:
        """Return masked service key except first 4 and last 4 chars"""
        service_key = self.__config.get('service_key')
        if not service_key:
            return ""
        if service_key.strip() == "":
            return service_key

        key_parts = service_key.split(":")
        if len(key_parts) < 2:
            bad_format_key = key_parts[0]
            if len(bad_format_key) < 5:
                return self._KEY_MASK_BAD_FORMAT_SHORT.format(bad_format_key)
            return self._KEY_MASK_BAD_FORMAT.format(
                bad_format_key[0:4],
            )

        api_token = key_parts[0]
        if len(api_token) < 9:
            return service_key
        return self._KEY_MASK.format(
            api_token[0:4],
            api_token[-4:],
            key_parts[1],
        )

    def _config_mask_service_key(self) -> dict:
        """Return new config with service key masked"""
        config_masked = {}
        for k, v in self.__config.items():
            if k == "service_key":
                v = self.mask_service_key()
            config_masked[k] = v
        return config_masked

    def __str__(self) -> str:
        """String representation of ApmConfig is config with masked service key,
        plus agent_enabled and context"""
        apm_config = {
            "__config": self._config_mask_service_key(),
            "agent_enabled": self.agent_enabled,
            "context": self.context,
        }
        return "{}".format(apm_config)

    def __setitem__(self, key: str, value: str) -> None:
        """Refresh the configurations in liboboe global struct while user changes settings.
        """
        if key == 'tracing_mode':
            self._set_config_value(key, value)

        # TODO set up using OTel logging instrumentation
        elif key == 'log_trace_id':
            self._set_config_value(key, value)

        elif key in ('enable_sanitize_sql', 'warn_deprecated'):
            self._set_config_value(key, value)
        else:
            logger.warning('Unsupported SolarWinds APM config key: {key}'.format(key=key))

    def __getitem__(self, key: str) -> Any:
        return self.__config[key]

    def __delitem__(self, key: str) -> None:
        del self.__config[key]

    def get(self, key: str, default: Any = None):
        """Get the value of key. Nested keys separated by a dot are also accepted.
        Suggestion: Use mask_service_key() to safely get service_key value"""
        key = key.split(self._DELIMITER)
        value = reduce(lambda d, k: d.get(k, None) if isinstance(d, dict) else None, key, self.__config)
        return value if value is not None else default

    def update_with_cnf_file(self, cnf_path: str) -> None:
        """Update the settings with the config file, if any."""
        # TODO Implement config with cnf_file after alpha
        pass

    def update_with_env_var(self) -> None:
        """Update the settings with environment variables."""
        val = os.environ.get('SW_APM_PREPEND_DOMAIN_NAME', None)
        if val is not None:
            self._set_config_value('transaction.prepend_domain_name', val)
        available_envvs = set(self.__config.keys())
        # TODO after alpha: is_lambda
        for key in available_envvs:
            if key in ('inst_enabled', 'transaction', 'inst'):
                # we do not allow complex config options to be set via environment variables
                continue
            env = 'SW_APM_' + key.upper()
            val = os.environ.get(env)
            if val is not None:
                self._set_config_value(key, val)

    def update_with_kwargs(self, kwargs):
        """Update the configuration settings with (in-code) keyword arguments"""
        # TODO Implement in-code config with kwargs after alpha
        pass

    def _set_config_value(self, keys: str, val: Any) -> Any:
        """Sets the value of the config option indexed by 'keys' to 'val', where 'keys' is a nested key (separated by
        self.delimiter, i.e., the position of the element to be changed in the nested dictionary)"""
        def _convert_to_bool(val):
            """Converts given value to boolean value"""
            val = val.lower() if isinstance(val, str) else val
            return val == 'true' if isinstance(val, str) and val in ('true', 'false') else bool(int(val))

        # _config is a nested dict, thus find most deeply nested sub dict according to the provided keys
        # by defaulting to None in d.get(), we do not allow the creation of any new (key, value) pair, even
        # when we are handling a defaultdict (i.e., with this we do not allow e.g. the creation of new instrumentations
        # through the config)
        keys = keys.split(self._DELIMITER)
        sub_dict = reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys[:-1], self.__config)
        key = keys[-1]
        try:
            if keys == ['ec2_metadata_timeout']:
                timeout = int(val)
                if timeout not in range(0, 3001):
                    raise ValueError
                self.__config[key] = timeout
            elif keys == ['token_bucket_capacity']:
                bucket_cap = float(val)
                if not 0 <= bucket_cap <= 8.0:
                    raise ValueError
                self.__config[key] = bucket_cap
            elif keys == ['token_bucket_rate']:
                bucket_rate = float(val)
                if not 0 <= bucket_rate <= 4.0:
                    raise ValueError
                self.__config[key] = bucket_rate
            elif keys == ['proxy']:
                if not isinstance(val, str) or not val.startswith('http://'):
                    raise ValueError
                self.__config[key] = val
            elif keys == ['tracing_mode']:
                if not isinstance(val, str):
                    raise ValueError
                val = val.lower()
                if val in ['always', 'never']:
                    val = 'enabled' if val == 'always' else 'disabled'
                if val not in ['enabled', 'disabled']:
                    raise ValueError
                self.__config[key] = val
                self.context.setTracingMode(OboeTracingMode.get_oboe_trace_mode(val))
            elif keys == ['trigger_trace']:
                if not isinstance(val, str):
                    raise ValueError
                val = val.lower()
                if val in ['always', 'never']:
                    val = 'enabled' if val == 'always' else 'disabled'
                if val not in ['enabled', 'disabled']:
                    raise ValueError
                self.__config[key] = val
                self.context.setTriggerMode(OboeTracingMode.get_oboe_trigger_trace_mode(val))
            elif keys == ['reporter']:
                # TODO: support 'lambda'
                if not isinstance(val, str) or val.lower() not in ('udp', 'ssl', 'null', 'file'):
                    raise ValueError
                self.__config[key] = val.lower()
            elif keys == ['debug_level']:
                val = int(val)
                if not apm_logging.ApmLoggingLevel.is_valid_level(val):
                    raise ValueError
                self.__config[key] = val
                # update logging level of agent logger
                apm_logging.set_sw_log_level(val)
            elif keys == ['log_trace_id']:
                if not isinstance(val, str) or val.lower() not in [
                        'never',
                        'sampled',
                        'traced',
                        'always',
                ]:
                    raise ValueError
                self.__config[key] = val.lower()
            elif keys == ['is_grpc_clean_hack_enabled']:
                self.__config[key] = _convert_to_bool(val)
            elif isinstance(sub_dict, dict) and keys[-1] in sub_dict:
                if isinstance(sub_dict[keys[-1]], bool):
                    val = _convert_to_bool(val)
                else:
                    val = type(sub_dict[keys[-1]])(val)
                sub_dict[keys[-1]] = val
            else:
                logger.warning("Ignore invalid configuration key: {}".format('.'.join(keys)))
        except (ValueError, TypeError):
            logger.warning(
                'Ignore config option with invalid (non-convertible or out-of-range) type: ' +
                '.'.join(keys if keys[0] not in ['inst', 'transaction'] else keys[1:]))
