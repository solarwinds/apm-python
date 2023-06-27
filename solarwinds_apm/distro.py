# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Module to configure OpenTelemetry to work with SolarWinds backend"""

from os import environ

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER,
)
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.logging.environment_variables import (
    OTEL_PYTHON_LOG_FORMAT,
)
from pkg_resources import EntryPoint

from solarwinds_apm.apm_constants import (
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DEFAULT_TRACES_EXPORTER,
)


class SolarWindsDistro(BaseDistro):
    """OpenTelemetry Distro for SolarWinds reporting environment"""

    def _configure(self, **kwargs):
        """Configure default OTel exporter and propagators"""
        environ.setdefault(
            OTEL_TRACES_EXPORTER, INTL_SWO_DEFAULT_TRACES_EXPORTER
        )
        environ.setdefault(
            OTEL_PROPAGATORS, ",".join(INTL_SWO_DEFAULT_PROPAGATORS)
        )
        environ.setdefault(
            OTEL_PYTHON_LOG_FORMAT,
            "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s trace_flags=%(otelTraceSampled)02d resource.service.name=%(otelServiceName)s] - %(message)s",
        )

    def load_instrumentor(self, entry_point: EntryPoint, **kwargs):
        """Takes a collection of instrumentation entry points
        and activates them by instantiating and calling instrument()
        on each one. This is a method override to pass additional
        arguments to each entry point.
        """
        # Set enable for sqlcommenter. Assumes kwargs ignored if not
        # implemented for current instrumentation library
        if self.enable_commenter(entry_point, **kwargs):
            # instrumentation for Flask ORM, sqlalchemy, psycopg2
            kwargs["enable_commenter"] = True
            # instrumentation for Django ORM
            kwargs["is_sql_commentor_enabled"] = True
        instrumentor: BaseInstrumentor = entry_point.load()
        instrumentor().instrument(**kwargs)

    def enable_commenter(self, entry_point: EntryPoint, **kwargs) -> bool:
        """Enable sqlcommenter feature, if implemented"""
        # TODO: Update if changed in OTel spec:
        # https://github.com/open-telemetry/opentelemetry-specification/issues/3560
        enable_commenter = environ.get("OTEL_SQLCOMMENTER_ENABLED", "")
        if enable_commenter.lower() == "true":
            return True
        return False
