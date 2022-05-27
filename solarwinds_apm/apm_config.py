
from collections import defaultdict
import os

from solarwinds_apm import DEFAULT_SW_DEBUG_LEVEL

class SolarWindsApmConfig:
    """SolarWinds APM Configuration Class
    The precedence: in-code keyword arguments > Environment Variables > config file > default values.
    Note that oboe doesn't read configurations by itself. The Python agent needs to
    read environment variables and/or config files and pass them into oboe. This is
    done only once during the initialization and the properties cannot be refreshed.
    """

    def __init__(self, **kwargs):
        self._config = dict()
        # Update the config with default values
        self._config = {
            #'sample_rate' and 'tracing_mode' do not have any default values (i.e. they are unset by default)
            'sample_rate': None,
            'tracing_mode': None,
            'trigger_trace': None,
            'collector': '',  # the collector address in host:port format.
            'reporter': '',  # the reporter mode, either 'udp' or 'ssl'.
            'debug_level': DEFAULT_SW_DEBUG_LEVEL,
            'warn_deprecated': True,
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

        cnf_file = os.environ.get('APPOPTICS_APM_CONFIG_PYTHON', os.environ.get('APPOPTICS_PYCONF', None))
        if cnf_file:
            self.update_with_cnf_file(cnf_file)

        self.update_with_env_var()
        self.update_with_kwargs(kwargs)

    def __setitem__(self, key, value):
        # TODO
        pass

    def __getitem__(self, key):
        return self._config[key]

    def __delitem__(self, key):
        del self._config[key]

    def update_with_cnf_file(self, cnf_path):
        """Update the settings with the config file, if any."""
        # TODO
        pass

    def update_with_env_var(self):
        """Update the settings with environment variables."""
        # TODO
        # log_level = os.environ.get('SOLARWINDS_DEBUG_LEVEL', 3)
        # try:
        #     log_level = int(log_level)
        # except ValueError:
        #     log_level = 3
        pass

    def update_with_kwargs(self, kwargs):
        """Update the configuration settings with (in-code) keyword arguments"""
        # TODO
        pass
