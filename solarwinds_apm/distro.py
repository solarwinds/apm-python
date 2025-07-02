# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Module to configure OpenTelemetry to work with SolarWinds backend"""

import logging
import platform
import re
import sys
from os import environ

from opentelemetry.environment_variables import (
    OTEL_LOGS_EXPORTER,
    OTEL_METRICS_EXPORTER,
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER,
)
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.logging.environment_variables import (
    OTEL_PYTHON_LOG_FORMAT,
)
from opentelemetry.instrumentation.version import __version__ as inst_version
from opentelemetry.metrics import NoOpMeterProvider
from opentelemetry.sdk.environment_variables import (
    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS,
    OTEL_EXPORTER_OTLP_COMPRESSION,
    OTEL_EXPORTER_OTLP_ENDPOINT,
    OTEL_EXPORTER_OTLP_HEADERS,
    OTEL_EXPORTER_OTLP_METRICS_DEFAULT_HISTOGRAM_AGGREGATION,
    OTEL_EXPORTER_OTLP_PROTOCOL,
)
from opentelemetry.sdk.version import __version__ as sdk_version
from opentelemetry.util._importlib_metadata import EntryPoint

from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.apm_constants import (
    INTL_SWO_DEFAULT_OTLP_COLLECTOR,
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DEFAULT_RESOURCE_DETECTORS,
    INTL_SWO_DEFAULT_RESOURCE_DETECTORS_LAMBDA,
)
from solarwinds_apm.version import __version__ as apm_version

_SQLCOMMENTERS = [
    "django",
    "flask",
    "psycopg",
    "psycopg2",
    "sqlalchemy",
]

logger = logging.getLogger(__name__)


class SolarWindsDistro(BaseDistro):
    """OpenTelemetry Distro for SolarWinds reporting environment"""

    _cnf_dict = None
    _collector = None
    _instrumentor_metrics_enabled = None

    _DEFAULT_OTLP_EXPORTER = "otlp"
    _DEFAULT_OTLP_PROTOCOL = "http/protobuf"

    def __new__(cls, *args, **kwargs):
        # Maintain singleton pattern and cache SW APM user config
        # for Distro lifecycle at auto-instrumentation
        cls._cnf_dict = SolarWindsApmConfig.get_cnf_dict()
        cls._collector = SolarWindsApmConfig.calculate_collector(cls._cnf_dict)
        cls._instrumentor_metrics_enabled = (
            SolarWindsApmConfig.calculate_metrics_enabled(cls._cnf_dict)
        )
        cls._meter_provider = None
        if cls._instrumentor_metrics_enabled is False:
            cls._meter_provider = NoOpMeterProvider()
        return super().__new__(cls, *args, **kwargs)

    def _log_python_runtime(self):
        """Logs Python runtime info, with any warnings"""
        python_vers = platform.python_version()
        logger.info("Python %s", python_vers)

        # https://devguide.python.org/versions/
        if sys.version_info.major == 3 and sys.version_info.minor < 8:
            logger.error(
                "Obsolete: Python %s is at end-of-life and support "
                "by APM Python and OpenTelemetry has been dropped. Please upgrade.",
                python_vers,
            )

    def _log_runtime(self):
        """Logs APM Python runtime info (high debug level)"""
        logger.info("SolarWinds APM Python %s", apm_version)
        self._log_python_runtime()
        logger.info("OpenTelemetry %s/%s", sdk_version, inst_version)

    def _get_token_from_service_key(self):
        """Return token portion of service_key if set, else None"""
        service_key = environ.get("SW_APM_SERVICE_KEY")
        if not service_key:
            logger.debug("Missing service key")
            return None
        # Key must be at least one char + ":" + at least one other char
        key_parts = [p for p in service_key.split(":") if len(p) > 0]
        if len(key_parts) != 2:
            logger.debug("Incorrect service key format")
            return None
        return key_parts[0]

    def _configure(self, **kwargs):
        """Configure default OTel exporters and propagators"""
        self._log_runtime()

        # Default OTLP protocol and exporters as HTTP
        environ.setdefault(OTEL_TRACES_EXPORTER, self._DEFAULT_OTLP_EXPORTER)
        environ.setdefault(OTEL_METRICS_EXPORTER, self._DEFAULT_OTLP_EXPORTER)
        environ.setdefault(OTEL_LOGS_EXPORTER, self._DEFAULT_OTLP_EXPORTER)
        environ.setdefault(
            OTEL_EXPORTER_OTLP_PROTOCOL, self._DEFAULT_OTLP_PROTOCOL
        )

        # Default histogram aggregation as exponential
        environ.setdefault(
            OTEL_EXPORTER_OTLP_METRICS_DEFAULT_HISTOGRAM_AGGREGATION,
            "base2_exponential_bucket_histogram",
        )

        # Default collector OTLP endpoint, which HTTP exporters map to signal-specific routes
        collector = self._collector
        if collector is not None and collector.startswith("apm.collector"):
            # Collector endpoint is set, try it
            match = re.search(
                r"\b[a-z]{2}-\d{2}(?:\.\w+(?:-\w+)*)?\b", collector
            )
            if match:
                # Set the OTLP endpoint to the collector endpoint with the correct region
                resolved = (
                    "https://otel.collector."
                    + match.group()
                    + ".solarwinds.com:443"
                )
                logger.debug(
                    "Using exporter otlp collector endpoint %s", resolved
                )
                environ.setdefault(OTEL_EXPORTER_OTLP_ENDPOINT, resolved)
            else:
                environ.setdefault(
                    OTEL_EXPORTER_OTLP_ENDPOINT,
                    INTL_SWO_DEFAULT_OTLP_COLLECTOR,
                )
        else:
            environ.setdefault(
                OTEL_EXPORTER_OTLP_ENDPOINT,
                INTL_SWO_DEFAULT_OTLP_COLLECTOR,
            )

        # Set default headers if export endpoint is a SWO one
        # (default or configured and resolved by above)
        endpoint = environ.get(OTEL_EXPORTER_OTLP_ENDPOINT)
        if endpoint is not None:
            match = re.search(
                r"https://otel.collector.\b[a-z]{2}-\d{2}(?:\.\w+(?:-\w+)*)?\b.solarwinds.com",
                endpoint,
            )
            if match:
                header_token = self._get_token_from_service_key()
                if not header_token:
                    logger.debug(
                        "Setting OTLP export defaults without SWO token"
                    )
                environ.setdefault(
                    OTEL_EXPORTER_OTLP_HEADERS,
                    f"authorization=Bearer%20{header_token}",
                )

        environ.setdefault(
            OTEL_PROPAGATORS, ",".join(INTL_SWO_DEFAULT_PROPAGATORS)
        )
        # Default for LoggingInstrumentor
        environ.setdefault(
            OTEL_PYTHON_LOG_FORMAT,
            "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s trace_flags=%(otelTraceSampled)02d resource.service.name=%(otelServiceName)s] - %(message)s",
        )
        # Default for ResourceDetector
        if SolarWindsApmConfig.calculate_is_lambda():
            environ.setdefault(
                OTEL_EXPERIMENTAL_RESOURCE_DETECTORS,
                ",".join(INTL_SWO_DEFAULT_RESOURCE_DETECTORS_LAMBDA),
            )
        else:
            environ.setdefault(
                OTEL_EXPERIMENTAL_RESOURCE_DETECTORS,
                ",".join(INTL_SWO_DEFAULT_RESOURCE_DETECTORS),
            )

        # TODO: Support other signal types when available
        # Always opt into new semconv for all instrumentors (if supported)
        environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = self.get_semconv_opt_in()

        environ.setdefault(OTEL_EXPORTER_OTLP_COMPRESSION, "gzip")

    def load_instrumentor(self, entry_point: EntryPoint, **kwargs):
        """Takes a collection of instrumentation entry points
        and activates them by instantiating and calling instrument()
        on each one. This is a method override to pass additional
        arguments to each entry point. This function is called for every
        individual instrumentor by upstream sitecustomize.

        For enabling sqlcommenting, SW_APM_ENABLED_SQLCOMMENT enables
        individual instrumentors if in _SQLCOMMENTERS (each is false by default).
        APM Python also sets enable_attribute_commenter=True by default;
        can be opted out for each instrumentor with SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE.
        """
        # If we're in Lambda environment, then we skip loading
        # AwsLambdaInstrumentor because we assume the wrapper
        # has done it for us already
        if entry_point.name == "aws-lambda":
            if SolarWindsApmConfig.calculate_is_lambda():
                return

        if entry_point.name in _SQLCOMMENTERS:
            entry_point_setting = self.get_enable_commenter_env_map().get(
                entry_point.name
            )
            if entry_point_setting.get("enable_commenter") is True:
                if entry_point.name == "django":
                    kwargs["is_sql_commentor_enabled"] = True
                else:
                    kwargs["enable_commenter"] = True
                    # Assumes this value can be empty
                    # Note: Django ORM reads options in settings.py instead
                    # https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/django/django.html
                    kwargs["commenter_options"] = (
                        self.detect_commenter_options()
                    )
            if entry_point_setting.get("enable_attribute_commenter") is True:
                kwargs["enable_attribute_commenter"] = True

            logger.debug(
                "Enabling sqlcommenter for %s with %s",
                entry_point.name,
                kwargs,
            )

        # If SW_APM_EXPORT_METRICS_ENABLED is set to false,
        # then we load the instrumentors with NoOp provider to disable
        # Otel instrumentor-based metrics export if supported.
        # Assumes kwargs are ignored if not implemented
        # for the current instrumentation library.
        if self._instrumentor_metrics_enabled is False:
            kwargs["meter_provider"] = self._meter_provider

        instrumentor: BaseInstrumentor = entry_point.load()
        instrumentor().instrument(**kwargs)

    def get_enable_commenter_env_map(self) -> dict:
        """Return a map of which instrumentors will have sqlcomment and attribute
        -in-attribute enabled, if implemented.
        Reads env SW_APM_ENABLED_SQLCOMMENT and SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE
        each as a comma-separated string of KVs paired by equals signs,
        e.g. 'django=true,sqlalchemy=false'.

        Partial example returned map:
        {
            "django": {
                "enable_commenter": True,
                "enable_attribute_commenter", False,
            }
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter", True,
            }
            ...
        }

        Default for sqlcomment is False for each instrumentor in _SQLCOMMENTERS.
        Default for adding sqlcomment to attribute is True. This has no effect
        upstream if sqlcomment is False."""
        env_commenter_map = {
            instr: {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            }
            for instr in _SQLCOMMENTERS
        }

        def parse_env_items(env_var, key_name):
            env_items = environ.get(env_var, "")
            if env_items:
                for item in env_items.split(","):
                    try:
                        key, value = item.split("=", maxsplit=1)
                    except ValueError as exc:
                        logger.warning(
                            "Invalid sqlcommenter key value at pair %s: %s",
                            item,
                            exc,
                        )
                        continue

                    instrumentor_name = key.strip().lower()
                    if instrumentor_name in _SQLCOMMENTERS:
                        env_v_bool = SolarWindsApmConfig.convert_to_bool(
                            value.strip()
                        )
                        if env_v_bool is not None:
                            env_commenter_map[instrumentor_name][
                                key_name
                            ] = env_v_bool

        parse_env_items("SW_APM_ENABLED_SQLCOMMENT", "enable_commenter")
        parse_env_items(
            "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE", "enable_attribute_commenter"
        )
        return env_commenter_map

    def detect_commenter_options(self):
        """Returns commenter options dict parsed from environment, if any"""
        commenter_opts = {}
        commenter_opts_env = environ.get("SW_APM_OPTIONS_SQLCOMMENT")

        opt_items = []
        if commenter_opts_env:
            opt_items = commenter_opts_env.split(",")
        else:
            return commenter_opts

        for opt_item in opt_items:
            opt_k = ""
            opt_v = ""
            try:
                opt_k, opt_v = opt_item.split("=", maxsplit=1)
            except ValueError as exc:
                logger.warning(
                    "Invalid key-value pair for sqlcommenter option %s: %s",
                    opt_item,
                    exc,
                )
            opt_v_bool = SolarWindsApmConfig.convert_to_bool(opt_v.strip())
            if opt_v_bool is not None:
                commenter_opts[opt_k.strip()] = opt_v_bool

        return commenter_opts

    def get_semconv_opt_in(self):
        """
        Always returns semconv config as opt-into new, stable HTTP only

        See also:
        https://github.com/open-telemetry/opentelemetry-python-contrib/blob/0a231e57f9722e6101194c6b38695addf23ab950/opentelemetry-instrumentation/src/opentelemetry/instrumentation/_semconv.py#L93-L99
        """
        # TODO: Support other signal types when available
        # return environ.get("OTEL_SEMCONV_STABILITY_OPT_IN")

        return "http"
