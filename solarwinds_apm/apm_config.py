
from collections import defaultdict
from functools import reduce
import logging
import os

from solarwinds_apm import apm_logging
from solarwinds_apm.extension.oboe import Context
from solarwinds_apm.apm_logging import ApmLoggingLevel

logger = logging.getLogger(__name__)


# TODO agent_enabled logic


class OboeTracingMode:
    """Provides an interface to translate the string representation of tracing_mode to the C-extension equivalent."""
    OBOE_SETTINGS_UNSET = -1
    OBOE_TRACE_DISABLED = 0
    OBOE_TRACE_ENABLED = 1
    OBOE_TRIGGER_DISABLED = 0
    OBOE_TRIGGER_ENABLED = 1

    @classmethod
    def get_oboe_trace_mode(cls, tracing_mode):
        if tracing_mode == 'enabled':
            return cls.OBOE_TRACE_ENABLED
        if tracing_mode == 'disabled':
            return cls.OBOE_TRACE_DISABLED
        return cls.OBOE_SETTINGS_UNSET

    @classmethod
    def get_oboe_trigger_trace_mode(cls, trigger_trace_mode):
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

    delimiter = '.'

    def __init__(self, **kwargs):
        self._config = dict()
        # Update the config with default values
        self._config = {
            # 'sample_rate' and 'tracing_mode' do not have any default values (i.e. they are unset by default)
            'sample_rate': None,
            'tracing_mode': None,
            # 'trigger_trace' is enabled by default
            'trigger_trace': 'enabled',
            'collector': '',  # the collector address in host:port format.
            'reporter': '',  # the reporter mode, either 'udp' or 'ssl'.
            'debug_level': ApmLoggingLevel.default_level(),
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

        cnf_file = os.environ.get('SOLARWINDS_APM_CONFIG_PYTHON', os.environ.get('SOLARWINDS_PYCONF', None))
        if cnf_file:
            self.update_with_cnf_file(cnf_file)

        self.update_with_env_var()
        self.update_with_kwargs(kwargs)

    def __setitem__(self, key, value):
        """Refresh the configurations in liboboe global struct while user changes settings.
        """
        if key == 'tracing_mode':
            self._set_config_value(key, value)

        elif key == 'sample_rate':
            self._set_config_value(key, value)

        # TODO set up using OTel logging instrumentation
        elif key == 'log_trace_id':
            self._set_config_value(key, value)

        elif key in ('enable_sanitize_sql', 'warn_deprecated'):
            self._set_config_value(key, value)
        else:
            logger.warning('Unsupported SolarWinds APM config key: {key}'.format(key=key))

    def __getitem__(self, key):
        return self._config[key]

    def __delitem__(self, key):
        del self._config[key]

    def get(self, key, default=None):
        """Get the value of key. Nested keys separated by a dot are also accepted."""
        key = key.split(self.delimiter)
        value = reduce(lambda d, k: d.get(k, None) if isinstance(d, dict) else None, key, self._config)
        return value if value is not None else default

    def update_with_cnf_file(self, cnf_path):
        """Update the settings with the config file, if any."""
        # TODO
        pass

    def update_with_env_var(self):
        """Update the settings with environment variables."""
        val = os.environ.get('SOLARWINDS_APM_PREPEND_DOMAIN_NAME', None)
        if val is not None:
            self._set_config_value('transaction.prepend_domain_name', val)
        available_envvs = set(self._config.keys())
        # TODO after alpha: is_lambda
        for key in available_envvs:
            if key in ('inst_enabled', 'transaction', 'inst'):
                # we do not allow complex config options to be set via environment variables
                continue
            env = 'SOLARWINDS_' + key.upper()
            val = os.environ.get(env)
            if val is not None:
                self._set_config_value(key, val)

    def update_with_kwargs(self, kwargs):
        """Update the configuration settings with (in-code) keyword arguments"""
        # TODO
        pass

    def _set_config_value(self, keys, val):
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
        keys = keys.split(self.delimiter)
        sub_dict = reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys[:-1], self._config)
        key = keys[-1]
        try:
            if keys == ['sample_rate']:
                sample_rate = float(val)
                if not 0 <= sample_rate <= 1:
                    raise ValueError
                self._config[key] = sample_rate
                Context.setDefaultSampleRate(int(sample_rate * 1e6))
            elif keys == ['ec2_metadata_timeout']:
                timeout = int(val)
                if timeout not in range(0, 3001):
                    raise ValueError
                self._config[key] = timeout
            elif keys == ['token_bucket_capacity']:
                bucket_cap = float(val)
                if not 0 <= bucket_cap <= 8.0:
                    raise ValueError
                self._config[key] = bucket_cap
            elif keys == ['token_bucket_rate']:
                bucket_rate = float(val)
                if not 0 <= bucket_rate <= 4.0:
                    raise ValueError
                self._config[key] = bucket_rate
            elif keys == ['proxy']:
                if not isinstance(val, str) or not val.startswith('http://'):
                    raise ValueError
                self._config[key] = val
            elif keys == ['tracing_mode']:
                if not isinstance(val, str):
                    raise ValueError
                val = val.lower()
                if val in ['always', 'never']:
                    val = 'enabled' if val == 'always' else 'disabled'
                if val not in ['enabled', 'disabled']:
                    raise ValueError
                self._config[key] = val
                Context.setTracingMode(OboeTracingMode.get_oboe_trace_mode(val))
            elif keys == ['trigger_trace']:
                if not isinstance(val, str):
                    raise ValueError
                val = val.lower()
                if val in ['always', 'never']:
                    val = 'enabled' if val == 'always' else 'disabled'
                if val not in ['enabled', 'disabled']:
                    raise ValueError
                self._config[key] = val
                # TODO oboe_settings_trigger_set, not setTracingMode
                # Context.setTracingMode(OboeTracingMode.get_oboe_trigger_trace_mode(val))
            elif keys == ['reporter']:
                if not isinstance(val, str) or val.lower() not in ('udp', 'ssl', 'null', 'file', 'lambda'):
                    raise ValueError
                self._config[key] = val.lower()
            elif keys == ['debug_level']:
                val = int(val)
                if not ApmLoggingLevel.is_valid_level(val):
                    raise ValueError
                self._config[key] = val
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
                self._config[key] = val.lower()
            elif keys == ['is_grpc_clean_hack_enabled']:
                self._config[key] = _convert_to_bool(val)
            elif (keys[0] == 'inst' and keys[1] in self.supported_instrumentations and keys[2] == 'collect_backtraces'):
                self._config[keys[0]][keys[1]][keys[2]] = _convert_to_bool(val)
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
