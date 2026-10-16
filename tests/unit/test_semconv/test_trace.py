# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

from solarwinds_apm.semconv.trace import get_url_attrs


class TestSemconvTrace:
    def test_get_url_attrs__new_path(self):
        attributes = {
            "url.scheme": "foo",
            "server.address": "bar",
            "server.port": "baz",
            "url.path": "/qux",
        }
        scheme, host, port, target = get_url_attrs(attributes)
        assert scheme == "foo"
        assert host == "bar"
        assert port == "baz"
        assert target == "/qux"

    def test_get_url_attrs__new_query(self):
        attributes = {
            "url.scheme": "foo",
            "server.address": "bar",
            "server.port": "baz",
            "url.query": "/qux",
        }
        scheme, host, port, target = get_url_attrs(attributes)
        assert scheme == "foo"
        assert host == "bar"
        assert port == "baz"
        assert target == "/qux"

    def test_get_url_attrs__old(self):
        attributes = {
            "http.scheme": "foo",
            "net.host.name": "bar",
            "net.host.port": "baz",
            "http.target": "/qux",
        }
        scheme, host, port, target = get_url_attrs(attributes)
        assert scheme == "foo"
        assert host == "bar"
        assert port == "baz"
        assert target == "/qux"

    def test_get_url_attrs__neither(self):
        attributes = {}
        scheme, host, port, target = get_url_attrs(attributes)
        assert scheme is None
        assert host is None
        assert port is None
        assert target is None

    def test_get_url_attrs__prefer_new(self):
        attributes = {
            "url.scheme": "foo",
            "server.address": "bar",
            "server.port": "baz",
            "url.path": "/qux",
            "http.scheme": "OLD",
            "net.host.name": "OLD",
            "net.host.port": "OLD",
            "http.target": "/OLD",
        }
        scheme, host, port, target = get_url_attrs(attributes)
        assert scheme == "foo"
        assert host == "bar"
        assert port == "baz"
        assert target == "/qux"
