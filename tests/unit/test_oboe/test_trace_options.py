import time

import pytest

from solarwinds_apm.oboe.trace_options import (
    Auth,
    parse_trace_options,
    stringify_trace_options_response,
    TriggerTrace,
    validate_signature, TraceOptions,
)


@pytest.mark.parametrize("header, expected", [
    ("=", TraceOptions()),
    ("=value", TraceOptions()),
    ("trigger-trace", TraceOptions(True)),
    ("trigger-trace=value", TraceOptions(None, None, None, {}, [("trigger-trace", "value")])),
    ("trigger-trace;trigger-trace", TraceOptions(True, None, None, {}, [("trigger-trace", None)])),
    ("ts", TraceOptions(None, None, None, {}, [("ts", None)])),
    ("ts=1234;ts=5678", TraceOptions(None, 1234, None, {}, [("ts", "5678")])),
    # ("ts=value", TraceOptions(None, None, None, {}, [("ts", "value")])),
    ("ts=12.34", TraceOptions(None, None, None, {}, [("ts", "12.34")])),
    ("ts = 1234567890 ", TraceOptions(None, 1234567890, None, {}, [])),
    ("sw-keys", TraceOptions(None, None, None, {}, [("sw-keys", None)])),
    ("sw-keys=keys1;sw-keys=keys2", TraceOptions(None, None, "keys1", {}, [("sw-keys", "keys2")])),
    ("sw-keys= name:value ", TraceOptions(None, None, "name:value", {}, [])),
    ("sw-keys=check-id:check-1013,website-id;booking-demo",
     TraceOptions(None, None, "check-id:check-1013,website-id", {}, [("booking-demo", None)])),
    ("custom-key= value ", TraceOptions(None, None, None, {"custom-key": "value"}, [])),
    ("custom-key", TraceOptions(None, None, None, {}, [("custom-key", None)])),
    ("custom-key=value1;custom-key=value2",
     TraceOptions(None, None, None, {"custom-key": "value1"}, [("custom-key", "value2")])),
    ("custom-key=name=value", TraceOptions(None, None, None, {"custom-key": "name=value"}, [])),
    ("custom- key=value;custom-ke y=value",
     TraceOptions(None, None, None, {}, [("custom- key", "value"), ("custom-ke y", "value")])),
    ("key=value", TraceOptions(None, None, None, {}, [("key", "value")])),
    (
            "trigger-trace ; custom-something=value; custom-OtherThing = other val ; sw-keys = 029734wr70:9wqj21,0d9j1 ; ts = 12345 ; foo = bar",
            TraceOptions(True, 12345, "029734wr70:9wqj21,0d9j1",
                         {"custom-something": "value", "custom-OtherThing": "other val"}, [("foo", "bar")])),
    (
            ";foo=bar;;;custom-something=value_thing;;sw-keys=02973r70:1b2a3;;;;custom-key=val;ts=12345;;;;;;;trigger-trace;;;",
            TraceOptions(True, 12345, "02973r70:1b2a3", {"custom-something": "value_thing", "custom-key": "val"},
                         [("foo", "bar")])),
    ("trigger-trace;custom-foo='bar;bar';custom-bar=foo",
     TraceOptions(True, None, None, {"custom-foo": "'bar", "custom-bar": "foo"}, [("bar'", None)])),
    (";trigger-trace;custom-something=value_thing;sw-keys=02973r70:9wqj21,0d9j1;1;2;3;4;5;=custom-key=val?;=",
     TraceOptions(True, None, "02973r70:9wqj21,0d9j1", {"custom-something": "value_thing"},
                  [("1", None), ("2", None), ("3", None), ("4", None), ("5", None)])),
])
def test_parse_trace_options(header, expected):
    result = parse_trace_options(header)
    assert result == expected


def test_stringify_trace_options_response():
    result = stringify_trace_options_response({
        "auth": Auth.OK.value,
        "trigger-trace": TriggerTrace.OK.value,
    })
    assert result == "auth=ok;trigger-trace=ok"

    result = stringify_trace_options_response({
        "auth": Auth.OK.value,
        "trigger-trace": TriggerTrace.TRIGGER_TRACING_DISABLED.value,
        "ignored": ["invalid-key1", "invalid_key2"],
    })
    assert result == "auth=ok;trigger-trace=trigger-tracing-disabled;ignored=invalid-key1,invalid_key2"


@pytest.mark.parametrize("header, signature, key, timestamp, expected", [
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     b"8mZ98ZnZhhggcsUmdMbS", int(time.time()) - 60, Auth.OK),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59d",
     b"8mZ98ZnZhhggcsUmdMbS", int(time.time()) - 60, Auth.BAD_SIGNATURE),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c", None,
     int(time.time()) - 60, Auth.NO_SIGNATURE_KEY),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     b"8mZ98ZnZhhggcsUmdMbS", int(time.time()) - 10 * 60, Auth.BAD_TIMESTAMP),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     b"8mZ98ZnZhhggcsUmdMbS", int(time.time()) + 10 * 60, Auth.BAD_TIMESTAMP),
    ("trigger-trace;pd-keys=lo:se,check-id:123;ts=1564597681", "2c1c398c3e6be898f47f74bf74f035903b48b59c",
     b"8mZ98ZnZhhggcsUmdMbS", None, Auth.BAD_TIMESTAMP),
])
def test_validate_signature(header, signature, key, timestamp, expected):
    result = validate_signature(header, signature, key, timestamp)
    assert result == expected
