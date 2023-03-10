# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Module to configure OpenTelemetry to work with SolarWinds backend"""

import logging
from os import environ
from pkg_resources import EntryPoint
from types import MappingProxyType

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER,
)
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

from solarwinds_apm.apm_constants import (
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DEFAULT_TRACES_EXPORTER,
)


logger = logging.getLogger(__name__)

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

    def load_instrumentor(  # pylint: disable=no-self-use
        self, entry_point: EntryPoint, **kwargs
    ):
        """
        Override of BaseDistro method that loads and instrument() of all installed OTel instrumentation libraries.   
        """
        def request_hook(span, request):
            """
            request_hook for instrumentation libraries that use them.
            Edits attributes of spans created from receiving requests.

            See also Django usage
            https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/opentelemetry-instrumentation-django/src/opentelemetry/instrumentation/django/__init__.py#L124-L141
            """
            logger.debug("request_hook received span:")
            logger.debug("type %s", type(span))
            logger.debug("name %s", span.name)
            logger.debug("kind %s", span.kind)
            logger.debug("attributes %s", span.attributes)
            logger.debug("resource %s", span.resource)
            logger.debug("request_hook received Django request:")
            logger.debug("path %s", request.path)
            logger.debug("headers %s", request.headers)

            new_attributes = {"request-hook-foo": "some-bar-value"}
            for attr_k, attr_v in span.attributes.items():
                new_attributes[attr_k] = attr_v
            span.set_attributes(MappingProxyType(new_attributes))
            logger.debug("Updated span attributes is %s", span.attributes)

        kwargs.update({"request_hook": request_hook})
        instrumentor: BaseInstrumentor = entry_point.load()
        instrumentor().instrument(**kwargs)
