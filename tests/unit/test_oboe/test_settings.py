# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import time

from solarwinds_apm.oboe.settings import (
    Flags,
    LocalSettings,
    merge,
    SampleSource,
    Settings,
    TracingMode,
)


def test_merge_override_unset():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LOCAL_DEFAULT,
        flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS | Flags.TRIGGERED_TRACE,
        buckets={},
        signature_key=None,
        timestamp=int(time.time()),
        ttl=60,
    )
    local = LocalSettings(tracing_mode=TracingMode.NEVER, trigger_mode=False)

    merged = merge(remote, local)
    assert merged.flags == Flags.OK


def test_merge_override_unset_always_trigger_enabled():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LOCAL_DEFAULT,
        flags=Flags.OK,
        buckets={},
        signature_key=None,
        timestamp=int(time.time()),
        ttl=60,
    )
    local = LocalSettings(tracing_mode=TracingMode.ALWAYS, trigger_mode=True)

    merged = merge(remote, local)
    assert merged.flags == (
        Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS | Flags.TRIGGERED_TRACE
    )


def test_merge_override_unset_defaults_to_remote():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LOCAL_DEFAULT,
        flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS | Flags.TRIGGERED_TRACE,
        buckets={},
        signature_key=None,
        timestamp=int(time.time()),
        ttl=60,
    )
    local = LocalSettings(trigger_mode=True, tracing_mode=None)

    merged = merge(remote, local)
    assert merged == remote


def test_merge_override_set_never_trigger_disabled():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LOCAL_DEFAULT,
        flags=Flags.OVERRIDE
        | Flags.SAMPLE_START
        | Flags.SAMPLE_THROUGH_ALWAYS
        | Flags.TRIGGERED_TRACE,
        buckets={},
        signature_key=None,
        timestamp=int(time.time()),
        ttl=60,
    )
    local = LocalSettings(tracing_mode=TracingMode.NEVER, trigger_mode=False)

    merged = merge(remote, local)
    assert merged.flags == Flags.OVERRIDE


def test_merge_override_set_always_trigger_enabled():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LOCAL_DEFAULT,
        flags=Flags.OVERRIDE,
        buckets={},
        signature_key=None,
        timestamp=int(time.time()),
        ttl=60,
    )
    local = LocalSettings(tracing_mode=TracingMode.ALWAYS, trigger_mode=True)

    merged = merge(remote, local)
    assert merged == remote


def test_merge_override_set_defaults_to_remote():
    remote = Settings(
        sample_rate=1,
        sample_source=SampleSource.LOCAL_DEFAULT,
        flags=Flags.OVERRIDE,
        buckets={},
        signature_key=None,
        timestamp=int(time.time()),
        ttl=60,
    )
    local = LocalSettings(trigger_mode=False, tracing_mode=None)

    merged = merge(remote, local)
    assert merged == remote
