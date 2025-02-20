import time

from solarwinds_apm.oboe.settings import Flags, LocalSettings, merge, SampleSource, Settings, TracingMode


def test_merge_override_unset():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LocalDefault,
        flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS | Flags.TRIGGERED_TRACE,
        buckets={},
        timestamp=int(time.time()),
        ttl=60
    )
    local = LocalSettings(
        tracing_mode=TracingMode.NEVER,
        trigger_mode=False
    )

    merged = merge(remote, local)
    assert merged.flags == 0x0


def test_merge_override_unset_always_trigger_enabled():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LocalDefault,
        flags=0x0,
        buckets={},
        timestamp=int(time.time()),
        ttl=60
    )
    local = LocalSettings(
        tracing_mode=TracingMode.ALWAYS,
        trigger_mode=True
    )

    merged = merge(remote, local)
    assert merged.flags == (Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS | Flags.TRIGGERED_TRACE)


def test_merge_override_unset_defaults_to_remote():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LocalDefault,
        flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS | Flags.TRIGGERED_TRACE,
        buckets={},
        timestamp=int(time.time()),
        ttl=60
    )
    local = LocalSettings(
        trigger_mode=True
    )

    merged = merge(remote, local)
    assert merged == remote


def test_merge_override_set_never_trigger_disabled():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LocalDefault,
        flags=Flags.OVERRIDE | Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS | Flags.TRIGGERED_TRACE,
        buckets={},
        timestamp=int(time.time()),
        ttl=60
    )
    local = LocalSettings(
        tracing_mode=TracingMode.NEVER,
        trigger_mode=False
    )

    merged = merge(remote, local)
    assert merged.flags == Flags.OVERRIDE


def test_merge_override_set_always_trigger_enabled():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LocalDefault,
        flags=Flags.OVERRIDE,
        buckets={},
        timestamp=int(time.time()),
        ttl=60
    )
    local = LocalSettings(
        tracing_mode=TracingMode.ALWAYS,
        trigger_mode=True
    )

    merged = merge(remote, local)
    assert merged == remote


def test_merge_override_set_defaults_to_remote():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LocalDefault,
        flags=Flags.OVERRIDE,
        buckets={},
        timestamp=int(time.time()),
        ttl=60
    )
    local = LocalSettings(
        trigger_mode=False
    )

    merged = merge(remote, local)
    assert merged == remote
