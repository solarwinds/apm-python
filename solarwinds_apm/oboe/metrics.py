from opentelemetry.sdk.metrics import MeterProvider


class Counters:
    def __init__(self, meter_provider: MeterProvider):
        self._meter = meter_provider.get_meter("sw.apm.sampling.metrics")
        self._request_count = self._meter.create_counter(name="trace.service.request_count")
        self._sample_count = self._meter.create_counter(name="trace.service.samplecount")
        self._trace_count = self._meter.create_counter(name="trace.service.tracecount")
        self._through_trace_count = self._meter.create_counter(name="trace.service.through_trace_count")
        self._triggered_trace_count = self._meter.create_counter(name="trace.service.triggered_trace_count")
        self._token_bucket_exhaustion_count = self._meter.create_counter(
            name="trace.service.tokenbucket_exhaustion_count")

    @property
    def request_count(self):
        return self._request_count

    @property
    def sample_count(self):
        return self._sample_count

    @property
    def trace_count(self):
        return self._trace_count

    @property
    def through_trace_count(self):
        return self._through_trace_count

    @property
    def triggered_trace_count(self):
        return self._triggered_trace_count

    @property
    def token_bucket_exhaustion_count(self):
        return self._token_bucket_exhaustion_count
