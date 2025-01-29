# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Helpers to handle trace from upstream instrumentors conforming to new or old semantic conventions"""

from typing import Any

from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.util.types import Attributes


def get_url_attrs(
    attributes: Attributes = None,
) -> (Any, Any, Any, Any):
    """Returns URL scheme, host, target, port from span attributes. Order of precedence is new semconv > old semconv > none"""
    # Upstream OTel instrumentation libraries are individually updating
    # to implement support of HTTP semconv opt-in, so APM Python checks both
    # https://github.com/open-telemetry/opentelemetry-python-contrib/issues/936

    scheme = attributes.get(SpanAttributes.URL_SCHEME)
    if not scheme:
        scheme = attributes.get(SpanAttributes.HTTP_SCHEME)

    host = attributes.get(SpanAttributes.SERVER_ADDRESS)
    if not host:
        host = attributes.get(SpanAttributes.NET_HOST_NAME)

    port = attributes.get(SpanAttributes.SERVER_PORT)
    if not port:
        port = attributes.get(SpanAttributes.NET_HOST_PORT)

    # If new, it could be either URL_PATH or URL_QUERY
    target = attributes.get(SpanAttributes.URL_PATH)
    if not target:
        target = attributes.get(SpanAttributes.URL_QUERY)
    if not target:
        target = attributes.get(SpanAttributes.HTTP_TARGET)

    return scheme, host, port, target
