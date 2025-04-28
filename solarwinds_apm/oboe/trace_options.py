# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from __future__ import annotations

import hashlib
import hmac
import logging
import re
import time
from enum import Enum

TRIGGER_TRACE_KEY = "trigger-trace"
TIMESTAMP_KEY = "ts"
SW_KEYS_KEY = "sw-keys"

CUSTOM_KEY_REGEX = r"^custom-[^\s]+$"

logger = logging.getLogger(__name__)


class TraceOptions:
    def __init__(
        self,
        trigger_trace: bool | None,
        timestamp: int | None,
        sw_keys: str | None,
        custom: dict[str, str],
        ignored: list[tuple[str, str | None]],
    ):
        self._trigger_trace = trigger_trace
        self._timestamp = timestamp
        self._sw_keys = sw_keys
        self._custom = custom
        self._ignored = ignored

    @property
    def trigger_trace(self):
        return self._trigger_trace

    @trigger_trace.setter
    def trigger_trace(self, new_trigger_trace):
        self._trigger_trace = new_trigger_trace

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, new_timestamp):
        self._timestamp = new_timestamp

    @property
    def sw_keys(self):
        return self._sw_keys

    @sw_keys.setter
    def sw_keys(self, new_sw_keys):
        self._sw_keys = new_sw_keys

    @property
    def custom(self):
        return self._custom

    @custom.setter
    def custom(self, new_custom):
        self._custom = new_custom

    @property
    def ignored(self):
        return self._ignored

    @ignored.setter
    def ignored(self, new_ignored):
        self._ignored = new_ignored

    def __eq__(self, other):
        if not isinstance(other, TraceOptions):
            return NotImplemented
        return (
            self._trigger_trace == other._trigger_trace
            and self._timestamp == other._timestamp
            and self._sw_keys == other._sw_keys
            and self._custom == other._custom
            and self._ignored == other._ignored
        )

    def __str__(self):
        return f"trigger_trace={self._trigger_trace}, timestamp={self._timestamp}, sw_keys={self._sw_keys}, custom={self._custom}, ignored={self._ignored}"


class Auth(Enum):
    OK = "ok"
    BAD_TIMESTAMP = "bad-timestamp"
    BAD_SIGNATURE = "bad-signature"
    NO_SIGNATURE_KEY = "no-signature-key"


class TriggerTrace(Enum):
    OK = "ok"
    NOT_REQUESTED = "not-requested"
    IGNORED = "ignored"
    TRACING_DISABLED = "tracing-disabled"
    TRIGGER_TRACING_DISABLED = "trigger-tracing-disabled"
    RATE_EXCEEDED = "rate-exceeded"
    SETTINGS_NOT_AVAILABLE = "settings-not-available"


class TraceOptionsResponse:
    def __init__(
        self,
        auth: Auth | None = None,
        trigger_trace: TriggerTrace | None = None,
        ignored: list[str] | None = None,
    ):
        self._auth = auth
        self._trigger_trace = trigger_trace
        self._ignored = ignored

    @property
    def auth(self):
        return self._auth

    @auth.setter
    def auth(self, new_auth):
        self._auth = new_auth

    @property
    def trigger_trace(self):
        return self._trigger_trace

    @trigger_trace.setter
    def trigger_trace(self, new_trigger_trace):
        self._trigger_trace = new_trigger_trace

    @property
    def ignored(self):
        return self._ignored

    @ignored.setter
    def ignored(self, new_ignored):
        self._ignored = new_ignored

    def __eq__(self, other):
        if not isinstance(other, TraceOptionsResponse):
            return NotImplemented
        return (
            self._auth == other._auth
            and self._trigger_trace == other._trigger_trace
            and self._ignored == other._ignored
        )

    def __str__(self):
        return f"auth={self._auth}, trigger_trace={self._trigger_trace}, ignored={self._ignored}"


class TraceOptionsWithResponse(TraceOptions):
    def __init__(
        self,
        trigger_trace: bool | None,
        timestamp: int | None,
        sw_keys: str | None,
        custom: dict[str, str],
        ignored: list[tuple[str, str | None]],
        response: TraceOptionsResponse,
    ):
        super().__init__(trigger_trace, timestamp, sw_keys, custom, ignored)
        self._response = response

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, new_response):
        self._response = new_response

    def __eq__(self, other):
        if not isinstance(other, TraceOptionsWithResponse):
            return NotImplemented
        return super().__eq__(self) and self._response == other._response

    def __str__(self):
        return f"{super().__str__()}, response={self._response}"


class RequestHeaders:
    def __init__(
        self,
        x_trace_options: str | None,
        x_trace_options_signature: str | None,
    ):
        self._x_trace_options = x_trace_options
        self._x_trace_options_signature = x_trace_options_signature

    @property
    def x_trace_options(self):
        return self._x_trace_options

    @x_trace_options.setter
    def x_trace_options(self, new_x_trace_options):
        self._x_trace_options = new_x_trace_options

    @property
    def x_trace_options_signature(self):
        return self._x_trace_options_signature

    @x_trace_options_signature.setter
    def x_trace_options_signature(self, new_x_trace_options_signature):
        self._x_trace_options_signature = new_x_trace_options_signature

    def __eq__(self, other):
        if not isinstance(other, RequestHeaders):
            return NotImplemented
        return (
            self._x_trace_options == other._x_trace_options
            and self._x_trace_options_signature
            == other._x_trace_options_signature
        )

    def __str__(self):
        return f"x_trace_options={self._x_trace_options}, x_trace_options_signature={self._x_trace_options_signature}"


class ResponseHeaders:
    def __init__(self, x_trace_options_response: str | None):
        self._x_trace_options_response = x_trace_options_response

    @property
    def x_trace_options_response(self):
        return self._x_trace_options_response

    @x_trace_options_response.setter
    def x_trace_options_response(self, new_x_trace_options_response):
        self._x_trace_options_response = new_x_trace_options_response

    def __eq__(self, other):
        if not isinstance(other, ResponseHeaders):
            return NotImplemented
        return (
            self._x_trace_options_response == other._x_trace_options_response
        )

    def __str__(self):
        return f"x_trace_options_response={self._x_trace_options_response}"


def parse_trace_options(header):
    trace_options = TraceOptions(
        trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[]
    )
    kvs = parse_key_value_pairs(header)
    for key, value in kvs:
        if key == TRIGGER_TRACE_KEY:
            parse_trigger_trace(trace_options, key, value)
        elif key == TIMESTAMP_KEY:
            parse_timestamp(trace_options, key, value)
        elif key == SW_KEYS_KEY:
            parse_sw_keys(trace_options, key, value)
        elif re.match(CUSTOM_KEY_REGEX, key):
            parse_custom_key(trace_options, key, value)
        elif len(key) > 0:
            trace_options.ignored.append((key, value))
    return trace_options


def parse_key_value_pairs(header):
    """
    Parse the key value pairs from the trace options header.
    """
    kvs = []
    for pair in header.split(";"):
        kv = pair.split("=", 1)
        if len(kv) == 2:
            kvs.append((kv[0].strip(), kv[1].strip()))
        elif len(kv) == 1 and len(kv[0].strip()) > 0:
            kvs.append((kv[0].strip(), None))
    return kvs


def parse_trigger_trace(trace_options, key, value):
    """
    Parse the trigger trace option.
    """
    if value is not None or trace_options.trigger_trace is not None:
        logger.debug(
            "invalid trace option for trigger trace, should not have a value and only be provided once"
        )
        trace_options.ignored.append((key, value))
    else:
        trace_options.trigger_trace = True


def parse_timestamp(trace_options, key, value):
    """
    Parse the timestamp from trace option.
    """
    if value is None or trace_options.timestamp is not None:
        logger.debug(
            "invalid trace option for timestamp, should have a value and only be provided once"
        )
        trace_options.ignored.append((key, value))
    else:
        try:
            ts = float(value)
            if not ts.is_integer():
                raise ValueError
            trace_options.timestamp = int(ts)
        except ValueError:
            logger.debug(
                "invalid trace option for timestamp, should be an integer"
            )
            trace_options.ignored.append((key, value))


def parse_sw_keys(trace_options, key, value):
    """
    Parse the sw keys from trace option.
    """
    if value is None or trace_options.sw_keys is not None:
        logger.debug(
            "invalid trace option for sw keys, should have a value and only be provided once"
        )
        trace_options.ignored.append((key, value))
    else:
        trace_options.sw_keys = value


def parse_custom_key(trace_options, key, value):
    """
    Parse the custom key from trace option.
    """
    if value is None or key in trace_options.custom:
        logger.debug(
            "invalid trace option for custom key %s, should have a value and only be provided once",
            key,
        )
        trace_options.ignored.append((key, value))
    else:
        trace_options.custom[key] = value


def stringify_trace_options_response(
    trace_options_response: TraceOptionsResponse,
):
    """
    Stringify the trace options response.
    """
    kvs = {
        "auth": (
            trace_options_response.auth.value
            if trace_options_response.auth
            else None
        ),
        "trigger-trace": (
            trace_options_response.trigger_trace.value
            if trace_options_response.trigger_trace
            else None
        ),
        "ignored": (
            ",".join(trace_options_response.ignored)
            if trace_options_response.ignored
            else None
        ),
    }
    return ";".join(f"{k}={v}" for k, v in kvs.items() if v is not None)


def validate_signature(header, signature, key, timestamp):
    """
    Validate the signature of the trace options header using sha1 algorithm.
    """
    if key is None:
        return Auth.NO_SIGNATURE_KEY
    if timestamp is None or abs(int(time.time()) - timestamp) > 5 * 60:
        return Auth.BAD_TIMESTAMP
    digest = hmac.new(
        str.encode(key), str.encode(header), hashlib.sha1
    ).hexdigest()
    if signature == digest:
        return Auth.OK
    return Auth.BAD_SIGNATURE
