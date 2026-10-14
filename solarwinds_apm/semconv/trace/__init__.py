# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

"""Helpers to handle trace from upstream instrumentors conforming to new or old semantic conventions."""

from __future__ import annotations

from typing import Any

from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.util.types import Attributes


def get_url_attrs(
    attributes: Attributes | None = None,
) -> tuple[Any, Any, Any, Any]:
    """
    Extract URL components from span attributes with fallback to old semantic conventions.

    Returns URL scheme, host, target, and port from span attributes.
    Order of precedence is new semconv > old semconv > none.

    Parameters:
    attributes (Attributes | None): The span attributes to extract URL components from.

    Returns:
    tuple[Any, Any, Any, Any]: A tuple containing (scheme, host, port, target).
    """
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
