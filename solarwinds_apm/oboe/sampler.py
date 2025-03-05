import asyncio
import logging
import threading
from logging import Logger
from typing import Dict, Any, Optional, Sequence

from opentelemetry.context import Context
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Attributes
from opentelemetry.semconv._incubating.attributes.http_attributes import HTTP_METHOD, HTTP_STATUS_CODE, HTTP_SCHEME, \
    HTTP_TARGET
from opentelemetry.semconv._incubating.attributes.net_attributes import NET_HOST_NAME
from opentelemetry.semconv.attributes.http_attributes import HTTP_REQUEST_METHOD, HTTP_RESPONSE_STATUS_CODE
from opentelemetry.semconv.attributes.server_attributes import SERVER_ADDRESS
from opentelemetry.semconv.attributes.url_attributes import URL_SCHEME, URL_PATH
from opentelemetry.trace import SpanKind, Link, TraceState
from typing_extensions import override

from solarwinds_apm.apm_constants import INTL_SWO_X_OPTIONS_KEY, INTL_SWO_X_OPTIONS_RESPONSE_KEY
from solarwinds_apm.oboe.configuration import Configuration
from solarwinds_apm.oboe.oboe_sampler import OboeSampler
from solarwinds_apm.oboe.settings import Settings, Flags, BucketType, SampleSource, BucketSettings, TracingMode, \
    LocalSettings
from solarwinds_apm.oboe.trace_options import RequestHeaders, ResponseHeaders
from solarwinds_apm.traceoptions import XTraceOptions


def http_span_metadata(kind: SpanKind, attributes: Attributes):
    if kind != SpanKind.SERVER or not (HTTP_REQUEST_METHOD in attributes or HTTP_METHOD in attributes):
        return {"http": False}
    method = str(attributes.get(HTTP_METHOD, attributes.get(HTTP_REQUEST_METHOD, "")))
    status = int(attributes.get(HTTP_RESPONSE_STATUS_CODE, attributes.get(HTTP_STATUS_CODE, 0)))
    scheme = str(attributes.get(URL_SCHEME, attributes.get(HTTP_SCHEME, "http")))
    hostname = str(attributes.get(SERVER_ADDRESS, attributes.get(NET_HOST_NAME, "localhost")))
    path = str(attributes.get(URL_PATH, attributes.get(HTTP_TARGET, "")))
    url = f"{scheme}://{hostname}{path}"
    return {
        "http": True,
        "method": method,
        "status": status,
        "scheme": scheme,
        "hostname": hostname,
        "path": path,
        "url": url,
    }

def parse_settings(unparsed: Any) -> Optional[tuple[Settings, Optional[str]]]:
    if unparsed is None or not isinstance(unparsed, dict):
        return None
    try:
        sample_rate = int(unparsed["value"])
        timestamp = int(unparsed["timestamp"])
        ttl = int(unparsed["ttl"])
    except (KeyError, ValueError):
        return None
    flags = Flags.OK
    if "flags" in unparsed and isinstance(unparsed["flags"], str):
        for f in unparsed["flags"].split(","):
            flag = {
                "OVERRIDE": Flags.OVERRIDE,
                "SAMPLE_START": Flags.SAMPLE_START,
                "SAMPLE_THROUGH_ALWAYS": Flags.SAMPLE_THROUGH_ALWAYS,
                "TRIGGER_TRACE": Flags.TRIGGERED_TRACE,
            }.get(f)
            if flag:
                flags |= flag
    buckets : Dict[BucketType, BucketSettings] = {}
    signature_key = None
    if "arguments" in unparsed:
        args = unparsed["arguments"]
        if "BucketCapacity" in args and "BucketRate" in args:
            buckets[BucketType.DEFAULT] = BucketSettings(
                capacity=args["BucketCapacity"],
                rate=args["BucketRate"],
            )
        if "TriggerRelaxedBucketCapacity" in args and "TriggerRelaxedBucketRate" in args:
            buckets[BucketType.TRIGGER_RELAXED] = BucketSettings(
                capacity=args["TriggerRelaxedBucketCapacity"],
                rate=args["TriggerRelaxedBucketRate"],
            )
        if "TriggerStrictBucketCapacity" in args and "TriggerStrictBucketRate" in args:
            buckets[BucketType.TRIGGER_STRICT] = BucketSettings(
                capacity=args["TriggerStrictBucketCapacity"],
                rate=args["TriggerStrictBucketRate"],
            )
        if "SignatureKey" in args:
            signature_key = args["SignatureKey"]
    warning = unparsed.get("warning")
    return Settings(
        sample_source=SampleSource.Remote,
        sample_rate=sample_rate,
        flags=flags,
        timestamp=timestamp,
        ttl=ttl,
        buckets=buckets,
        signature_key=signature_key
    ), warning


class Sampler(OboeSampler):
    def __init__(self, meter_provider: MeterProvider, config: Configuration, logger: Logger, initial: Any):
        super().__init__(meter_provider=meter_provider ,logger=logger)
        if config.tracing_mode is not None:
            self._tracing_mode = TracingMode.ALWAYS if config.tracing_mode else TracingMode.NEVER
        else:
            self._tracing_mode = None
        self._trigger_mode = config.trigger_trace_enabled
        self._transaction_settings = config.transaction_settings
        self._ready = threading.Event()
        if initial:
            self.update_settings(initial)

    def __str__(self) -> str:
        return f"Sampler{self._tracing_mode}({self._trigger_mode}) {super.__str__(self)}"

    @property
    def tracing_mode(self):
        return self._tracing_mode

    @property
    def trigger_mode(self):
        return self._trigger_mode

    @property
    def transaction_settings(self):
        return self._transaction_settings

    def wait_until_ready(self, timeout: int) -> bool:
        return self._ready.wait(timeout)

    @override
    def local_settings(self,
                       parent_context: Optional["Context"],
                       trace_id: int,
                       name: str,
                       kind: Optional[SpanKind] = None,
                       attributes: Attributes = None,
                       links: Optional[Sequence["Link"]] = None,
                       trace_state: Optional["TraceState"] = None) -> LocalSettings:
        settings = LocalSettings(tracing_mode=self.tracing_mode, trigger_mode=self.trigger_mode)
        if self.transaction_settings is None or len(self.transaction_settings) == 0:
            return settings
        meta = http_span_metadata(kind, attributes)
        identifier = meta["url"] if meta["http"] else f"{SpanKind(kind).name}:{name}"
        for t in self.transaction_settings:
            if t.matcher and t.matcher(identifier):
                settings.tracing_mode = TracingMode.ALWAYS if t.tracing else TracingMode.NEVER
                break
        return settings

    @override
    def request_headers(self,
                        parent_context: Optional["Context"],
                        trace_id: int,
                        name: str,
                        kind: Optional[SpanKind] = None,
                        attributes: Attributes = None,
                        links: Optional[Sequence["Link"]] = None,
                        trace_state: Optional["TraceState"] = None
                        ) -> RequestHeaders:
        if parent_context:
            options = parent_context.get(INTL_SWO_X_OPTIONS_KEY)
            if options and isinstance(options, XTraceOptions):
                RequestHeaders(x_trace_options=options.options_header, x_trace_options_signature=options.signature)
        return RequestHeaders(x_trace_options=None, x_trace_options_signature=None)

    @override
    def set_response_headers(self,
                             headers: ResponseHeaders,
                             parent_context: Optional["Context"],
                             trace_id: int,
                             name: str,
                             kind: Optional[SpanKind] = None,
                             attributes: Attributes = None,
                             links: Optional[Sequence["Link"]] = None,
                             trace_state: Optional["TraceState"] = None
                             ) -> Optional["TraceState"]:
        if parent_context:
            options = parent_context.get(INTL_SWO_X_OPTIONS_KEY)
            if options and isinstance(options, XTraceOptions):
                if options.include_response and headers.x_trace_options_response:
                    return trace_state.add(INTL_SWO_X_OPTIONS_RESPONSE_KEY, headers.x_trace_options_response)
        return None

    def update_settings(self, settings: Any) -> Optional[Settings]:
        parsed = parse_settings(settings)
        if parsed:
            parsed_settings, parsed_warning = parsed
            self.logger.debug("valid settings", parsed_settings, settings)
            super().update_settings(parsed_settings)
            self._ready.set()
            if parsed_warning:
                self.logger.warning(parsed_warning)
            return parsed_settings
        else:
            self.logger.debug("invalid settings", settings)
            return None
