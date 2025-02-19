import hashlib
import hmac
import logging
import re
import time
from typing import Optional, Dict, List, Tuple

TRIGGER_TRACE_KEY = "trigger-trace"
TIMESTAMP_KEY = "ts"
SW_KEYS_KEY = "sw-keys"

CUSTOM_KEY_REGEX = r'^custom-[^\s]+$'


class Auth:
    OK = "ok"
    BAD_TIMESTAMP = "bad-timestamp"
    BAD_SIGNATURE = "bad-signature"
    NO_SIGNATURE_KEY = "no-signature-key"


class TriggerTrace:
    OK = "ok"
    NOT_REQUESTED = "not-requested"
    IGNORED = "ignored"
    TRACING_DISABLED = "tracing-disabled"
    TRIGGER_TRACING_DISABLED = "trigger-tracing-disabled"
    RATE_EXCEEDED = "rate-exceeded"
    SETTINGS_NOT_AVAILABLE = "settings-not-available"


class TraceOptions:
    def __init__(self,
                 trigger_trace: Optional[bool] = None,
                 timestamp: Optional[int] = None,
                 sw_keys: Optional[str] = None,
                 custom: Optional[Dict[str, str]] = None,
                 ignored: Optional[List[Tuple[str, Optional[str]]]] = None):
        self.trigger_trace = trigger_trace
        self.timestamp = timestamp
        self.sw_keys = sw_keys
        self.custom = custom if custom is not None else {}
        self.ignored = ignored if ignored is not None else []

    def __eq__(self, other):
        if not isinstance(other, TraceOptions):
            return NotImplemented
        return self.trigger_trace == other.trigger_trace and self.timestamp == other.timestamp and self.sw_keys == other.sw_keys and self.custom == other.custom and self.ignored == other.ignored


def parse_trace_options(header, logger=logging.getLogger(__name__)):
    trace_options = TraceOptions()
    kvs = []
    for pair in header.split(";"):
        kv = pair.split("=", 1)
        if len(kv) == 2:
            kvs.append((kv[0].strip(), kv[1].strip()))
        elif len(kv) == 1 and len(kv[0].strip()) > 0:
            kvs.append((kv[0].strip(), None))

    for [k, v] in kvs:
        if k == TRIGGER_TRACE_KEY:
            if v is not None or trace_options.trigger_trace is not None:
                logger.debug(
                    "invalid trace option for trigger trace, should not have a value and only be provided once")
                trace_options.ignored.append((k, v))
                continue
            trace_options.trigger_trace = True
        elif k == TIMESTAMP_KEY:
            if v is None or trace_options.timestamp is not None:
                logger.debug("invalid trace option for timestamp, should have a value and only be provided once")
                trace_options.ignored.append((k, v))
                continue
            try:
                ts = float(v)
                if not ts.is_integer():
                    raise ValueError
                trace_options.timestamp = int(ts)
            except ValueError:
                logger.debug("invalid trace option for timestamp, should be an integer")
                trace_options.ignored.append((k, v))
        elif k == SW_KEYS_KEY:
            if v is None or trace_options.sw_keys is not None:
                logger.debug("invalid trace option for sw keys, should have a value and only be provided once")
                trace_options.ignored.append((k, v))
                continue
            trace_options.sw_keys = v
        elif re.match(CUSTOM_KEY_REGEX, k):
            if v is None or k in trace_options.custom:
                logger.debug(f"invalid trace option for custom key {k}, should have a value and only be provided once")
                trace_options.ignored.append((k, v))
                continue
            trace_options.custom[k] = v
        else:
            trace_options.ignored.append((k, v)) if len(k) > 0 else None
    return trace_options


def stringify_trace_options_response(trace_options_response):
    kvs = {
        'auth': trace_options_response.get('auth') if trace_options_response.get('auth') is not None else None,
        'trigger-trace': trace_options_response.get('trigger-trace') if trace_options_response.get(
            'trigger-trace') is not None else None,
        'ignored': ','.join(trace_options_response.get('ignored')) if trace_options_response.get(
            'ignored') is not None else None,
    }
    return ';'.join(f"{k}={v}" for k, v in kvs.items() if v is not None)


def validate_signature(header, signature, key, timestamp):
    if key is None:
        return Auth.NO_SIGNATURE_KEY
    if timestamp is None or abs(int(time.time()) - timestamp) > 5 * 60:
        return Auth.BAD_TIMESTAMP
    digest = hmac.new(key, header.encode(), hashlib.sha1).hexdigest()
    if signature == digest:
        return Auth.OK
    else:
        return Auth.BAD_SIGNATURE
