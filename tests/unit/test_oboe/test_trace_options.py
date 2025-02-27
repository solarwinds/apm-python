import time

import pytest

from solarwinds_apm.oboe.trace_options import (
    Auth,
    parse_trace_options,
    stringify_trace_options_response,
    TriggerTrace,
    validate_signature, TraceOptions, TraceOptionsResponse,
)


@pytest.mark.parametrize("header, expected", [
    ("=", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[])),
    ("=value", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[])),
    ("trigger-trace", TraceOptions(trigger_trace=True, timestamp=None, sw_keys=None, custom={}, ignored=[])),
    ("trigger-trace=value", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("trigger-trace", "value")])),
    ("trigger-trace;trigger-trace", TraceOptions(trigger_trace=True, timestamp=None, sw_keys=None, custom={}, ignored=[("trigger-trace", None)])),
    ("ts", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("ts", None)])),
    ("ts=1234;ts=5678", TraceOptions(trigger_trace=None, timestamp=1234, sw_keys=None, custom={}, ignored=[("ts", "5678")])),
    ("ts=value", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("ts", "value")])),
    ("ts=12.34", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("ts", "12.34")])),
    ("ts = 1234567890 ", TraceOptions(trigger_trace=None, timestamp=1234567890, sw_keys=None, custom={}, ignored=[])),
    ("sw-keys", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("sw-keys", None)])),
    ("sw-keys=keys1;sw-keys=keys2", TraceOptions(trigger_trace=None, timestamp=None, sw_keys="keys1", custom={}, ignored=[("sw-keys", "keys2")])),
    ("sw-keys= name:value ", TraceOptions(trigger_trace=None, timestamp=None, sw_keys="name:value", custom={}, ignored=[])),
    ("sw-keys=check-id:check-1013,website-id;booking-demo", TraceOptions(trigger_trace=None, timestamp=None, sw_keys="check-id:check-1013,website-id", custom={}, ignored=[("booking-demo", None)])),
    ("custom-key= value ", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={"custom-key": "value"}, ignored=[])),
    ("custom-key", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("custom-key", None)])),
    ("custom-key=value1;custom-key=value2", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={"custom-key": "value1"}, ignored=[("custom-key", "value2")])),
    ("custom-key=name=value", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={"custom-key": "name=value"}, ignored=[])),
    ("custom- key=value;custom-ke y=value", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("custom- key", "value"), ("custom-ke y", "value")])),
    ("key=value", TraceOptions(trigger_trace=None, timestamp=None, sw_keys=None, custom={}, ignored=[("key", "value")])),
    ("trigger-trace ; custom-something=value; custom-OtherThing = other val ; sw-keys = 029734wr70:9wqj21,0d9j1 ; ts = 12345 ; foo = bar", TraceOptions(trigger_trace=True, timestamp=12345, sw_keys="029734wr70:9wqj21,0d9j1", custom={"custom-something": "value", "custom-OtherThing": "other val"}, ignored=[("foo", "bar")])),
    (";foo=bar;;;custom-something=value_thing;;sw-keys=02973r70:1b2a3;;;;custom-key=val;ts=12345;;;;;;;trigger-trace;;;", TraceOptions(trigger_trace=True, timestamp=12345, sw_keys="02973r70:1b2a3", custom={"custom-something": "value_thing", "custom-key": "val"}, ignored=[("foo", "bar")])),
    ("trigger-trace;custom-foo='bar;bar';custom-bar=foo", TraceOptions(trigger_trace=True, timestamp=None, sw_keys=None, custom={"custom-foo": "'bar", "custom-bar": "foo"}, ignored=[("bar'", None)])),
    (";trigger-trace;custom-something=value_thing;sw-keys=02973r70:9wqj21,0d9j1;1;2;3;4;5;=custom-key=val?;=", TraceOptions(trigger_trace=True, timestamp=None, sw_keys="02973r70:9wqj21,0d9j1", custom={"custom-something": "value_thing"},ignored=[("1", None), ("2", None), ("3", None), ("4", None), ("5", None)])),
])
def test_parse_trace_options(header, expected):
    result = parse_trace_options(header)
    assert result == expected


def test_stringify_trace_options_response():
    result = stringify_trace_options_response(TraceOptionsResponse(
        auth=Auth.OK,
        trigger_trace=TriggerTrace.OK,
        ignored=None,
    ))
    assert result == "auth=ok;trigger-trace=ok"

    result = stringify_trace_options_response(TraceOptionsResponse(
        auth=Auth.OK,
        trigger_trace=TriggerTrace.TRIGGER_TRACING_DISABLED,
        ignored=["invalid-key1", "invalid_key2"],
    ))
    assert result == "auth=ok;trigger-trace=trigger-tracing-disabled;ignored=invalid-key1,invalid_key2"


@pytest.mark.parametrize("header, signature, key, timestamp, expected", [
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     "8mZ98ZnZhhggcsUmdMbS", int(time.time()) - 60, Auth.OK),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59d",
     "8mZ98ZnZhhggcsUmdMbS", int(time.time()) - 60, Auth.BAD_SIGNATURE),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c", None,
     int(time.time()) - 60, Auth.NO_SIGNATURE_KEY),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     "8mZ98ZnZhhggcsUmdMbS", int(time.time()) - 10 * 60, Auth.BAD_TIMESTAMP),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     "8mZ98ZnZhhggcsUmdMbS", int(time.time()) + 10 * 60, Auth.BAD_TIMESTAMP),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     "8mZ98ZnZhhggcsUmdMbS", None, Auth.BAD_TIMESTAMP),
])
def test_validate_signature(header, signature, key, timestamp, expected):
    result = validate_signature(header, signature, key, timestamp)
    assert result == expected
