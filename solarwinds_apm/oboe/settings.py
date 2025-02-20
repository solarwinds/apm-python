from typing import Optional, Dict


class SampleSource:
    LocalDefault = 2
    Remote = 6


class Flags:
    OK = 0x0
    INVALID = 0x1
    OVERRIDE = 0x2
    SAMPLE_START = 0x4
    SAMPLE_THROUGH_ALWAYS = 0x10
    TRIGGERED_TRACE = 0x20


class TracingMode:
    ALWAYS = Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS
    NEVER = 0x0


class BucketType:
    DEFAULT = ""
    TRIGGER_RELAXED = "TriggerRelaxed"
    TRIGGER_STRICT = "TriggerStrict"


class BucketSettings:
    def __init__(self, capacity: int, rate: int):
        self.capacity = capacity
        self.rate = rate


class Settings:
    def __init__(self, sample_rate: int, sample_source: SampleSource, flags: int,
                 timestamp: int, ttl: int,
                 buckets: Optional[Dict[BucketType, BucketSettings]] = None,
                 signature_key: Optional[str] = None):
        self.sample_rate = sample_rate
        self.sample_source = sample_source
        self.flags = flags
        self.buckets = buckets if buckets is not None else {}
        self.signature_key = signature_key
        self.timestamp = timestamp
        self.ttl = ttl

    def __eq__(self, other):
        if not isinstance(other, Settings):
            return NotImplemented
        return self.sample_rate == other.sample_rate and self.sample_source == other.sample_source and self.flags == other.flags and self.buckets == other.buckets and self.signature_key == other.signature_key and self.timestamp == other.timestamp and self.ttl == other.ttl


class LocalSettings:
    def __init__(self, trigger_mode: bool, tracing_mode: Optional[TracingMode] = None):
        self.tracing_mode = tracing_mode
        self.trigger_mode = trigger_mode

    def __eq__(self, other):
        if not isinstance(other, LocalSettings):
            return NotImplemented
        return self.tracing_mode == other.tracing_mode and self.trigger_mode == other.trigger_mode


def merge(remote: Settings, local: LocalSettings) -> Settings:
    flags = local.tracing_mode if local.tracing_mode is not None else remote.flags

    if local.trigger_mode:
        flags |= Flags.TRIGGERED_TRACE
    else:
        flags &= ~Flags.TRIGGERED_TRACE

    if remote.flags & Flags.OVERRIDE:
        flags &= remote.flags
        flags |= Flags.OVERRIDE

    return Settings(
        sample_rate=remote.sample_rate,
        sample_source=remote.sample_source,
        flags=flags,
        buckets=remote.buckets,
        signature_key=remote.signature_key,
        timestamp=remote.timestamp,
        ttl=remote.ttl
    )
