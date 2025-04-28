# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# pylint: disable=too-many-lines

import json
import logging
import os
import re
from functools import reduce
from typing import Any

from opentelemetry.environment_variables import OTEL_PROPAGATORS
from opentelemetry.sdk.resources import Resource

from solarwinds_apm import apm_logging
from solarwinds_apm.apm_constants import (
    INTL_SWO_BAGGAGE_PROPAGATOR,
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_PROPAGATOR,
    INTL_SWO_TRACECONTEXT_PROPAGATOR,
)
from solarwinds_apm.oboe.configuration import Configuration, TransactionSetting

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
        if tracing_mode == "enabled":
            return cls.OBOE_TRACE_ENABLED
        if tracing_mode == "disabled":
            return cls.OBOE_TRACE_DISABLED
        return cls.OBOE_SETTINGS_UNSET

    @classmethod
    def get_oboe_trigger_trace_mode(cls, trigger_trace_mode: str) -> int:
        if trigger_trace_mode == "enabled":
            return cls.OBOE_TRIGGER_ENABLED
        if trigger_trace_mode == "disabled":
            return cls.OBOE_TRIGGER_DISABLED
        return cls.OBOE_SETTINGS_UNSET


class SolarWindsApmConfig:
    """SolarWinds APM Configuration Class
    The precedence: in-code keyword arguments > Environment Variables > config file > default values.
    Note that oboe doesn't read configurations by itself. The Python agent needs to
    read environment variables and/or config files and pass them into oboe. This is
    done only once during the initialization and the properties cannot be refreshed.
    """

    _CONFIG_COLLECTOR_DEFAULT = "apm.collector.na-01.cloud.solarwinds.com"
    _CONFIG_FILE_DEFAULT = "./solarwinds-apm-config.json"
    _DELIMITER = "."
    _KEY_MASK = "{}...{}:{}"
    _KEY_MASK_BAD_FORMAT = "{}...<invalid_format>"
    _KEY_MASK_BAD_FORMAT_SHORT = "{}<invalid_format>"
    _SW_PREFIX = "sw_apm_"

    def __init__(
        self,
        otel_resource: "Resource" = Resource.create(),
        **kwargs: int,
    ) -> None:
        self.__config = {}
        # Update the config with default values
        self.__config = {
            "tracing_mode": OboeTracingMode.get_oboe_trace_mode("unset"),
            "trigger_trace": OboeTracingMode.get_oboe_trigger_trace_mode(
                "enabled"
            ),
            "collector": self._CONFIG_COLLECTOR_DEFAULT,
            "debug_level": apm_logging.ApmLoggingLevel.default_level(),
            "service_key": "",
            "transaction_filters": [],
            "transaction_name": None,
            "export_logs_enabled": False,
            "export_metrics_enabled": True,
            "log_filepath": "",
        }
        self.is_lambda = self.calculate_is_lambda()
        self.lambda_function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        self.agent_enabled = True
        self.update_with_cnf_file()
        self.update_with_env_var()
        # TODO Implement in-code config with kwargs after alpha
        # self.update_with_kwargs(kwargs)

        self.agent_enabled = self._calculate_agent_enabled()
        self.service_name = self._calculate_service_name(
            self.agent_enabled,
            otel_resource,
        )
        self.__config["service_key"] = self._update_service_key_name(
            self.agent_enabled,
            self.__config["service_key"],
            self.service_name,
        )

        # Update and apply logging settings to Python logger
        self._validate_log_filepath()
        apm_logging.update_sw_log_handler(
            self.__config["log_filepath"],
        )
        apm_logging.set_sw_log_level(self.__config["debug_level"])

        logger.debug("Set ApmConfig as: %s", self)

    @classmethod
    def calculate_is_lambda(cls) -> bool:
        """Checks if agent is running in an AWS Lambda environment."""
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") and os.environ.get(
            "LAMBDA_TASK_ROOT"
        ):
            return True
        return False

    @classmethod
    def calculate_collector(
        cls,
        cnf_dict: dict = None,
    ) -> str:
        """Special class method to return default/configured collector.
        Order of precedence: Environment Variable > config file > default.
        Default is SWO NA-01.
        Optional cnf_dict is presumably already from a config file, else a call
        to get_cnf_dict() is made for a fresh read."""
        collector = cls._CONFIG_COLLECTOR_DEFAULT
        if cnf_dict is None:
            cnf_dict = cls.get_cnf_dict()
        if cnf_dict:
            cnf_collector = cnf_dict.get("collector")
            collector = cnf_collector if cnf_collector else collector
        env_collector = os.environ.get("SW_APM_COLLECTOR")
        return env_collector if env_collector else collector

    @classmethod
    def calculate_metrics_enabled(
        cls,
        is_legacy: bool = False,
        cnf_dict: dict = None,
    ) -> bool:
        """Return if export of instrumentor metrics telemetry enabled.
        Invalid boolean values are ignored.
        Order of precedence: Environment Variable > config file > default.
        Default is True.
        Optional cnf_dict is presumably already from a config file, else a call
        to get_cnf_dict() is made for a fresh read."""
        metrics_enabled = True
        if cnf_dict is None:
            cnf_dict = cls.get_cnf_dict()
        if cnf_dict:
            cnf_enabled = cls.convert_to_bool(
                cnf_dict.get("export_metrics_enabled")
            )
            metrics_enabled = (
                cnf_enabled if cnf_enabled is not None else metrics_enabled
            )
        env_enabled = cls.convert_to_bool(
            os.environ.get("SW_APM_EXPORT_METRICS_ENABLED")
        )
        return env_enabled if env_enabled is not None else metrics_enabled

    def _calculate_agent_enabled_config_lambda(self) -> bool:
        """Checks if agent is enabled/disabled based on config in lambda environment:
        - SW_APM_AGENT_ENABLED (optional) (env var or cnf file)
        """
        if not self.agent_enabled:
            logger.info(
                "SolarWinds APM is disabled and will not report any traces because the environment variable "
                "SW_APM_AGENT_ENABLED or the config file agentEnabled field is set to 'false'! If this is not intended either unset the variable or set it to "
                "a value other than false. Note that SW_APM_AGENT_ENABLED/agentEnabled is case-insensitive."
            )
            return False
        return True

    # TODO: Account for in-code config with kwargs after alpha
    # pylint: disable=too-many-branches,too-many-return-statements
    def _calculate_agent_enabled_config(self) -> bool:
        """Checks if agent is enabled/disabled based on config:
        - SW_APM_SERVICE_KEY   (required) (env var or cnf file)
        - SW_APM_AGENT_ENABLED (optional) (env var or cnf file)
        - OTEL_PROPAGATORS     (optional) (env var only)
        """
        if self.is_lambda:
            return self._calculate_agent_enabled_config_lambda()

        # (1) SW_APM_SERVICE_KEY
        if not self.__config.get("service_key"):
            logger.error("Missing service key. Tracing disabled.")
            return False
        # Key must be at least one char + ":" + at least one other char
        key_parts = [
            p
            for p in self.__config.get("service_key", "").split(":")
            if len(p) > 0
        ]
        if len(key_parts) != 2:
            logger.error("Incorrect service key format. Tracing disabled.")
            return False

        # (2) SW_APM_AGENT_ENABLED
        # At this point it might be false after reading env var or cnf file
        if not self.agent_enabled:
            logger.info(
                "SolarWinds APM is disabled and will not report any traces because the environment variable "
                "SW_APM_AGENT_ENABLED or the config file agentEnabled field is set to 'false'! If this is not intended either unset the variable or set it to "
                "a value other than false. Note that SW_APM_AGENT_ENABLED/agentEnabled is case-insensitive."
            )
            return False

        # (3) OTEL_PROPAGATORS
        try:
            # SolarWindsDistro._configure does setdefault before this is called
            environ_propagators = os.environ.get(
                OTEL_PROPAGATORS,
                "",
            ).split(",")
            # If not using the default propagators,
            # can any arbitrary list BUT
            # (a) must include tracecontext and solarwinds_propagator
            # (b) tracecontext must be before solarwinds_propagator
            # (c) baggage, if configured, must be before solarwinds_propagator
            if environ_propagators != INTL_SWO_DEFAULT_PROPAGATORS:
                if (
                    INTL_SWO_TRACECONTEXT_PROPAGATOR not in environ_propagators
                    or INTL_SWO_PROPAGATOR not in environ_propagators
                ):
                    logger.error(
                        "Must include tracecontext and solarwinds_propagator in OTEL_PROPAGATORS to use SolarWinds APM. Tracing disabled."
                    )
                    return False

                if environ_propagators.index(
                    INTL_SWO_PROPAGATOR
                ) < environ_propagators.index(
                    INTL_SWO_TRACECONTEXT_PROPAGATOR
                ):
                    logger.error(
                        "tracecontext must be before solarwinds_propagator in OTEL_PROPAGATORS to use SolarWinds APM. Tracing disabled."
                    )
                    return False

                if INTL_SWO_BAGGAGE_PROPAGATOR in environ_propagators:
                    if environ_propagators.index(
                        INTL_SWO_PROPAGATOR
                    ) < environ_propagators.index(INTL_SWO_BAGGAGE_PROPAGATOR):
                        logger.error(
                            "baggage must be before solarwinds_propagator in OTEL_PROPAGATORS to use SolarWinds APM. Tracing disabled."
                        )
                        return False

        except ValueError:
            logger.error(
                "OTEL_PROPAGATORS must be a string of comma-separated propagator names. Tracing disabled."
            )
            return False

        return True

    # pylint: disable=too-many-branches,too-many-statements
    def _calculate_agent_enabled(self) -> bool:
        """Checks if agent is enabled/disabled based on platform and config"""
        agent_enabled = self._calculate_agent_enabled_config()
        logger.debug("agent_enabled: %s", agent_enabled)
        return agent_enabled

    def _calculate_service_name_lambda(
        self,
        otel_resource: "Resource",
    ) -> str:
        """Calculate `service.name` by priority system (decreasing):
        1. OTEL_SERVICE_NAME
        2. AWS_LAMBDA_FUNCTION_NAME

        Note: 1 is always set by the current lambda exec wrapper if used.
        The wrapper also sets service_name as the function_name, if
        former is not provided.

        If exec wrapper did not do the above, the passed in OTel Resource
        likely has a `service.name` already calculated by merging OTEL_SERVICE_NAME
        / OTEL_RESOURCE_ATTRIBUTES with defaults.

        We assume 2 is not none/empty because is_lambda check by caller should
        be True.
        """
        otel_service_name = otel_resource.attributes.get("service.name", None)

        if not otel_service_name:
            return self.lambda_function_name

        if otel_service_name == "unknown_service":
            # OTEL_SERVICE_NAME was not set
            # and exec wrapper did not wrap instrumentation
            return self.lambda_function_name

        return otel_service_name

    def _calculate_service_name_apm_proto(
        self,
        agent_enabled: bool,
        otel_resource: "Resource",
    ) -> str:
        """Calculate `service.name` by priority system (decreasing):
        1. OTEL_SERVICE_NAME
        2. service.name in OTEL_RESOURCE_ATTRIBUTES
        3. service name component of SW_APM_SERVICE_KEY
        4. empty string

        Note: 1-3 require that SW_APM_SERVICE_KEY exists and is in the correct
        format of "<api_token>:<service_name>". Otherwise agent_enabled: False
        and service.name is empty string.

        The passed in OTel Resource likely has a `service.name` already calculated
        by merging OTEL_SERVICE_NAME / OTEL_RESOURCE_ATTRIBUTES with defaults.
        Resource may also have other telemetry/arbitrary attributes that the
        user can overwrite/add.

        See also OTel SDK Resource.create and env vars:
        * https://github.com/open-telemetry/opentelemetry-python/blob/f5fb6b1353929cf8039b1d38f97450866357d901/opentelemetry-sdk/src/opentelemetry/sdk/resources/__init__.py#L156-L184
        * https://github.com/open-telemetry/opentelemetry-python/blob/8a0ce154ae27a699598cbf3ccc6396eb012902d6/opentelemetry-sdk/src/opentelemetry/sdk/environment_variables.py#L15-L39
        """
        service_name = ""
        if agent_enabled:
            # OTel SDK default service.name starts with "unknown_service" in-code:
            # https://github.com/open-telemetry/opentelemetry-python/blob/f5fb6b1353929cf8039b1d38f97450866357d901/opentelemetry-sdk/src/opentelemetry/sdk/resources/__init__.py#L175
            otel_service_name = otel_resource.attributes.get(
                "service.name", None
            )
            if otel_service_name and otel_service_name.startswith(
                "unknown_service"
            ):
                # When agent_enabled, assume service_key exists and is formatted correctly.
                service_name = self.__config.get("service_key", ":").split(
                    ":"
                )[1]
            else:
                service_name = otel_service_name
        return service_name

    def _calculate_service_name(
        self,
        agent_enabled: bool,
        otel_resource: "Resource",
    ) -> str:
        """Calculate service_name"""
        if self.is_lambda:
            return self._calculate_service_name_lambda(
                otel_resource,
            )

        return self._calculate_service_name_apm_proto(
            agent_enabled,
            otel_resource,
        )

    def _update_service_key_name(
        self,
        agent_enabled: bool,
        service_key: str,
        service_name: str,
    ) -> str:
        """Update service key with service name"""
        if agent_enabled and service_key and service_name:
            # Only update if service_name and service_key exist and non-empty,
            # and service_key in correct format.
            key_parts = service_key.split(":")
            if len(key_parts) < 2:
                logger.debug(
                    "Service key is not in the correct format to update its own service name. Skipping."
                )
                return service_key

            return ":".join([service_key.split(":")[0], service_name])

        # Else no need to update service_key when not reporting
        return service_key

    def mask_service_key(self) -> str:
        """Return masked service key except first 4 and last 4 chars"""
        service_key = self.__config.get("service_key")
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
        for cnf_k, cnf_v in self.__config.items():
            if cnf_k == "service_key":
                cnf_v = self.mask_service_key()
            config_masked[cnf_k] = cnf_v
        return config_masked

    def _validate_log_filepath(
        self,
    ) -> None:
        """Checks logFilepath validity else fileHandler will fail.
        If path up to file does not exist, creates directory.
        If that's not possible, switch to default empty logFilepath.
        """
        log_filepath = os.path.dirname(self.__config["log_filepath"])
        if log_filepath:
            if not os.path.exists(log_filepath):
                try:
                    os.makedirs(log_filepath)
                    logger.debug(
                        "Created directory path from provided SW_APM_LOG_FILEPATH / logFilepath."
                    )
                except FileNotFoundError:
                    logger.error(
                        "Could not create log file directory path from provided SW_APM_LOG_FILEPATH / logFilepath. Using default log settings."
                    )
                    self.__config["log_filepath"] = ""

    def __str__(self) -> str:
        """String representation of ApmConfig is config with masked service key,
        plus agent_enabled and context"""
        apm_config = {
            "__config": self._config_mask_service_key(),
            "agent_enabled": self.agent_enabled,
            "service_name": self.service_name,
        }
        return json.dumps(apm_config)

    def __setitem__(self, key: str, value: str) -> None:
        """Refresh the configurations in liboboe global struct while user changes settings."""
        if key == "tracing_mode":
            self._set_config_value(key, value)
        else:
            logger.warning(
                "Unsupported SolarWinds APM config key: %s",
                key,
            )

    def __getitem__(self, key: str) -> Any:
        return self.__config[key]

    def __delitem__(self, key: str) -> None:
        del self.__config[key]

    def get(self, key: str, default: Any = None):
        """Get the value of key. Nested keys separated by a dot are also accepted.
        Suggestion: Use mask_service_key() to safely get service_key value"""
        key = key.split(self._DELIMITER)
        value = reduce(
            lambda d, k: d.get(k, None) if isinstance(d, dict) else None,
            key,
            self.__config,
        )
        return value if value is not None else default

    @classmethod
    def get_cnf_dict(cls) -> Any:
        """Load Python dict from confg file (json), if any"""
        cnf_filepath = os.environ.get("SW_APM_CONFIG_FILE")
        cnf_dict = None

        if not cnf_filepath:
            cnf_filepath = cls._CONFIG_FILE_DEFAULT
            if not os.path.isfile(cnf_filepath):
                logger.debug("No config file at %s; skipping", cnf_filepath)
                return cnf_dict

        try:
            with open(cnf_filepath, encoding="utf-8") as cnf_file:
                try:
                    file_content = cnf_file.read()
                    cnf_dict = json.loads(file_content)
                except ValueError as ex:
                    logger.error(
                        "Invalid config file, must be valid json. Ignoring: %s",
                        ex,
                    )
        except FileNotFoundError as ex:
            logger.error("Invalid config file path. Ignoring: %s", ex)
        return cnf_dict

    def update_with_cnf_file(self) -> None:
        """Update the settings with the config file (json), if any."""

        def _snake_to_camel_case(key):
            key_parts = key.split("_")
            camel_head = key_parts[0]
            camel_body = "".join(part.title() for part in key_parts[1:])
            return f"{camel_head}{camel_body}"

        cnf_dict = self.get_cnf_dict()
        if not cnf_dict:
            return

        # agent_enabled is special
        cnf_agent_enabled = self.convert_to_bool(
            cnf_dict.get(_snake_to_camel_case("agent_enabled"))
        )
        if cnf_agent_enabled is not None:
            self.agent_enabled = cnf_agent_enabled

        available_cnf = set(self.__config.keys())
        for key in available_cnf:
            # Use internal snake_case config keys to check JSON config file camelCase keys
            val = cnf_dict.get(_snake_to_camel_case(key))
            if val is not None:
                self._set_config_value(key, val)

        self.update_transaction_filters(cnf_dict)

    def update_transaction_filters(self, cnf_dict: dict) -> None:
        """Update configured transaction_filters using config dict"""
        txn_settings = cnf_dict.get("transactionSettings")
        if not txn_settings:
            logger.debug("No transaction filters provided by config.")
            return
        if not isinstance(txn_settings, list):
            logger.warning(
                "Transaction filters must be a list of filters. Ignoring."
            )
            return
        for filter in txn_settings:
            if set(filter) != set(["regex", "tracing"]) or filter[
                "tracing"
            ] not in ["enabled", "disabled"]:
                logger.warning(
                    "Invalid transaction filter rule. Ignoring: %s", filter
                )
                continue

            txn_filter = {}
            txn_filter["tracing_mode"] = OboeTracingMode.get_oboe_trace_mode(
                filter["tracing"]
            )

            if not isinstance(filter["regex"], str):
                logger.warning(
                    "Transaction filter regex must be string or regex. Ignoring: %s",
                    filter,
                )
                continue

            if not len(filter["regex"]) > 0:
                logger.warning(
                    "Transaction filter regex must not be empty. Ignoring: %s",
                    filter,
                )
                continue

            txn_filter_re = None
            try:
                txn_filter_re = re.compile(filter["regex"])
            except re.error:
                logger.warning(
                    "Transaction filter regex invalid. Ignoring: %s",
                    filter,
                )
                continue

            # only the first filter for given `regex` will be used
            if txn_filter_re not in [
                cfilter["regex"]
                for cfilter in self.__config["transaction_filters"]
            ]:
                txn_filter["regex"] = txn_filter_re
                self.__config["transaction_filters"].append(txn_filter)

        logger.debug(
            "Set up transaction filters: %s",
            self.__config["transaction_filters"],
        )

    def update_with_env_var(self) -> None:
        """Update the settings with environment variables."""
        # agent_enabled is special
        env_agent_enabled = self.convert_to_bool(
            os.environ.get("SW_APM_AGENT_ENABLED")
        )
        if env_agent_enabled is not None:
            self.agent_enabled = env_agent_enabled

        available_envvs = set(self.__config.keys())
        for key in available_envvs:
            if key == "transaction":
                # we do not allow complex config options to be set via environment variables
                continue
            env = (self._SW_PREFIX + key).upper()
            val = os.environ.get(env)
            if val is not None:
                self._set_config_value(key, val)

    def update_with_kwargs(self, kwargs):
        """Update the configuration settings with (in-code) keyword arguments"""
        # TODO Implement in-code config with kwargs after alpha

    @classmethod
    def convert_to_bool(cls, val):
        """Converts given value to boolean value if bool or str representation, else None"""
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            if val.lower() == "true":
                return True
            if val.lower() == "false":
                return False
        logger.debug("Received config %s instead of true/false", val)
        return None

    # pylint: disable=too-many-branches,too-many-statements
    def _set_config_value(self, keys_str: str, val: Any) -> Any:
        """Sets the value of the config option indexed by 'keys' to 'val', where 'keys' is a nested key (separated by
        self.delimiter, i.e., the position of the element to be changed in the nested dictionary)
        """
        # _config is a nested dict, thus find most deeply nested sub dict according to the provided keys
        # by defaulting to None in d.get(), we do not allow the creation of any new (key, value) pair, even
        # when we are handling a defaultdict (i.e., with this we do not allow e.g. the creation of new instrumentations
        # through the config)
        keys = keys_str.split(self._DELIMITER)
        sub_dict = reduce(
            lambda d, key: d.get(key, None) if isinstance(d, dict) else None,
            keys[:-1],
            self.__config,
        )
        key = keys[-1]
        try:
            if keys == ["tracing_mode"]:
                if not isinstance(val, str):
                    raise ValueError
                val = val.lower()
                if val in {"always", "never"}:
                    val = "enabled" if val == "always" else "disabled"
                if val not in ["enabled", "disabled"]:
                    raise ValueError
                oboe_trace_mode = OboeTracingMode.get_oboe_trace_mode(val)
                self.__config[key] = oboe_trace_mode
            elif keys == ["trigger_trace"]:
                if not isinstance(val, str):
                    raise ValueError
                val = val.lower()
                if val in {"always", "never"}:
                    val = "enabled" if val == "always" else "disabled"
                if val not in ["enabled", "disabled"]:
                    raise ValueError
                oboe_trigger_trace = (
                    OboeTracingMode.get_oboe_trigger_trace_mode(val)
                )
                self.__config[key] = oboe_trigger_trace
            elif keys == ["debug_level"]:
                val = int(val)
                if not apm_logging.ApmLoggingLevel.is_valid_level(val):
                    raise ValueError
                self.__config[key] = val
            elif keys == ["transaction_name"]:
                self.__config[key] = val
            elif keys in [["export_logs_enabled"], ["export_metrics_enabled"]]:
                val = self.convert_to_bool(val)
                if val not in (True, False):
                    raise ValueError
                self.__config[key] = val
            elif isinstance(sub_dict, dict) and keys[-1] in sub_dict:
                if isinstance(sub_dict[keys[-1]], bool):
                    val = self.convert_to_bool(val)
                else:
                    val = type(sub_dict[keys[-1]])(val)
                sub_dict[keys[-1]] = val
            else:
                logger.warning(
                    "Ignore invalid configuration key: %s",
                    ".".join(keys),
                )
        except (ValueError, TypeError):
            logger.warning(
                "Ignore config option with invalid (non-convertible or out-of-range) type: %s",
                ".".join(keys if keys[0] != "transaction" else keys[1:]),
            )

    @classmethod
    def to_configuration(cls, apm_config) -> Configuration:
        """Converts apm_config to Configuration"""
        token = (
            apm_config.get("service_key").split(":")[0]
            if len(apm_config.get("service_key").split(":")) > 0
            else ""
        )
        filters = apm_config.get("transaction_filters")
        transaction_settings = []
        for transaction_filter in filters:
            if isinstance(transaction_filter, dict):
                transaction_setting = TransactionSetting(
                    tracing=transaction_filter.get("tracing_mode") == 1,
                    matcher=lambda s, regex=transaction_filter.get(
                        "regex"
                    ): regex.match(s),
                )
                transaction_settings.append(transaction_setting)
        return Configuration(
            enabled=apm_config.agent_enabled,
            service=apm_config.service_name,
            collector=apm_config.get("collector"),
            headers={"Authorization": f"Bearer {token}"},
            tracing_mode=apm_config.get("tracing_mode") != 0,
            trigger_trace_enabled=apm_config.get("trigger_trace") == 1,
            transaction_name=apm_config.get("transaction_name"),
            transaction_settings=transaction_settings,
        )
