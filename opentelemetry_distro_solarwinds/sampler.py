""" This module provides a SolarWinds-specific sampler.

The custom sampler will fetch sampling configurations for the SolarWinds backend.
"""

import logging
from typing import Optional, Sequence

from opentelemetry.sdk.trace.sampling import (Decision, ParentBased, Sampler,
                                              SamplingResult)
from opentelemetry.trace import SpanKind
from opentelemetry.util.types import Attributes

from opentelemetry_distro_solarwinds.extension.oboe import Context

logger = logging.getLogger(__name__)


class _AoSampler(Sampler):
    """AppOptics Custom sampler which obeys configuration options provided by the AO Backend."""
    def get_description(self) -> str:
        return "AppOptics custom sampler"

    def should_sample(
        self,
        parent_context: Optional["Context"],
        trace_id: int,
        name: str,
        kind: SpanKind = None,
        attributes: Attributes = None,
        links: Sequence["Link"] = None,
        trace_state: "TraceState" = None,
    ) -> "SamplingResult":

        do_metrics, do_sample, _, _, _, _, _, _, _, _, _ = Context.getDecisions(
            None)
        decision = Decision.DROP
        if do_metrics:
            # TODO: need to eck what record only actually means and how metrics work in OTel
            decision = Decision.RECORD_ONLY
        if do_sample:
            decision = Decision.RECORD_AND_SAMPLE
        return SamplingResult(
            decision,
            attributes if decision != Decision.DROP else None,
            trace_state,
        )


class ParentBasedAoSampler(ParentBased):
    """
    Sampler that respects its parent span's sampling decision, but otherwise
    samples according to the configurations from the AO backend.
    """
    def __init__(self):
        super().__init__(root=_AoSampler())
