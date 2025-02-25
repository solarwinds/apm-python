from typing import Optional, Dict
from enum import Enum, IntEnum


class SampleSource(IntEnum):
    LocalDefault = 2
    Remote = 6


class Flags(IntEnum):
    OK = 0x0
    INVALID = 0x1
    OVERRIDE = 0x2
    SAMPLE_START = 0x4
    SAMPLE_THROUGH_ALWAYS = 0x10
    TRIGGERED_TRACE = 0x20


class TracingMode(IntEnum):
    ALWAYS = Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS
    NEVER = 0x0


class BucketType(Enum):
    DEFAULT = ""
    TRIGGER_RELAXED = "TriggerRelaxed"
    TRIGGER_STRICT = "TriggerStrict"


class BucketSettings:
    def __init__(self, capacity: int, rate: int):
        self._capacity = capacity
        self._rate = rate

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, new_capacity):
        self._capacity = new_capacity

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, new_rate):
        self._rate = new_rate


class Settings:
    def __init__(self, sample_rate: int, sample_source: SampleSource, flags: int,
                 timestamp: int, ttl: int,
                 buckets: Optional[Dict[BucketType, BucketSettings]] = None,
                 signature_key: Optional[str] = None):
        self._sample_rate = sample_rate
        self._sample_source = sample_source
        self._flags = flags
        self._buckets = buckets if buckets is not None else {}
        self._signature_key = signature_key
        self._timestamp = timestamp
        self._ttl = ttl

    @property
    def sample_rate(self):
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, new_sample_rate):
        self._sample_rate = new_sample_rate

    @property
    def sample_source(self):
        return self._sample_source

    @sample_source.setter
    def sample_source(self, new_sample_source):
        self._sample_source = new_sample_source

    @property
    def flags(self):
        return self._flags

    @flags.setter
    def flags(self, new_flags):
        self._flags = new_flags

    @property
    def buckets(self):
        return self._buckets

    @buckets.setter
    def buckets(self, new_buckets):
        self._buckets = new_buckets

    @property
    def signature_key(self):
        return self._signature_key

    @signature_key.setter
    def signature_key(self, new_signature_key):
        self._signature_key = new_signature_key

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, new_timestamp):
        self._timestamp = new_timestamp

    @property
    def ttl(self):
        return self._ttl

    @ttl.setter
    def ttl(self, new_ttl):
        self._ttl = new_ttl

    def __eq__(self, other):
        if not isinstance(other, Settings):
            return NotImplemented
        return self._sample_rate == other._sample_rate and self._sample_source == other._sample_source and self._flags == other._flags and self._buckets == other._buckets and self._signature_key == other._signature_key and self._timestamp == other._timestamp and self._ttl == other._ttl

    def __str__(self):
        return f"Settings(sample_rate={self._sample_rate}, sample_source={self._sample_source}, flags={self._flags}, buckets={self._buckets}, timestamp={self._timestamp}, ttl={self._ttl})"

class LocalSettings:
    def __init__(self, trigger_mode: bool, tracing_mode: Optional[TracingMode] = None):
        self._tracing_mode = tracing_mode
        self._trigger_mode = trigger_mode

    @property
    def tracing_mode(self):
        return self._tracing_mode

    @tracing_mode.setter
    def tracing_mode(self, new_tracing_mode):
        self._tracing_mode = new_tracing_mode

    @property
    def trigger_mode(self):
        return self._trigger_mode

    @trigger_mode.setter
    def trigger_mode(self, new_trigger_mode):
        self._trigger_mode = new_trigger_mode

    def __eq__(self, other):
        if not isinstance(other, LocalSettings):
            return NotImplemented
        return self._tracing_mode == other._tracing_mode and self._trigger_mode == other._trigger_mode

    def __str__(self):
        return f"LocalSettings(tracing_mode={self._tracing_mode}, trigger_mode={self._trigger_mode})"


def merge(remote: Optional[Settings] = None, local: Optional[LocalSettings] = None) -> Optional[Settings]:
    if remote is None and local is None:
        return None
    elif remote is None:
        return local
    elif local is None:
        return remote
    else:
        return _merge(remote, local)

def _merge(remote: Settings, local: LocalSettings) -> Settings:
    flags = local.tracing_mode if local.tracing_mode is not None or False else remote.flags

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
