""" This module provides a SolarWinds-specific sampler.

The custom sampler will fetch sampling configurations for the SolarWinds backend.
"""

import logging
from types import MappingProxyType
from typing import Optional, Sequence, Dict, TYPE_CHECKING

from opentelemetry.context.context import Context as OtelContext
from opentelemetry.sdk.trace.sampling import (ALWAYS_ON, Decision, ParentBased, Sampler,
                                              SamplingResult)
from opentelemetry.trace import Link, SpanKind, get_current_span
from opentelemetry.trace.span import SpanContext, TraceState
from opentelemetry.util.types import Attributes

from solarwinds_apm.apm_constants import (
    INTL_SWO_COMMA_W3C_SANITIZED,
    INTL_SWO_EQUALS_W3C_SANITIZED,
    INTL_SWO_TRACESTATE_KEY
)
from solarwinds_apm.apm_config import OboeTracingMode
from solarwinds_apm.traceoptions import XTraceOptions
from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.extension.oboe import Context

logger = logging.getLogger(__name__)

class ParentBasedSwSampler(ParentBased):
    """ALWAYS_ON"""
    def __init__(self, apm_config: "SolarWindsApmConfig"):
        super().__init__(
            root=ALWAYS_ON
        )

    def should_sample(
        self,
        parent_context: Optional["Context"],
        trace_id: int,
        name: str,
        kind: SpanKind = None,
        attributes: Attributes = None,
        links: Sequence["Link"] = None,
        trace_state: "TraceState" = None
    ) -> "SamplingResult":
        sampler = self._root
        return sampler.should_sample(
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state
        )
