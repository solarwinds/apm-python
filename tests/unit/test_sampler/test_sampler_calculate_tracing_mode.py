# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from opentelemetry.trace import SpanKind

# pylint: disable=unused-import
from .fixtures.sampler import (
    fixture_swsampler,
    fixture_swsampler_txnfilters,
)

# The Tests =========================================================

class Test_SwSampler_construct_url():
    def test_construct_url_attrs_none(
        self,
        fixture_swsampler,
    ):
        assert fixture_swsampler.construct_url() == ""

    def test_construct_url_no_http(
        self,
        fixture_swsampler,
    ):
        assert fixture_swsampler.construct_url({"foo": "bar"}) == ""

    def test_construct_url_one_only(
        self,
        fixture_swsampler,
    ):
        assert fixture_swsampler.construct_url({"http.scheme": "bar"}) == ""
        assert fixture_swsampler.construct_url({"net.host.name": "bar"}) == ""
        assert fixture_swsampler.construct_url({"net.host.port": "bar"}) == ""
        assert fixture_swsampler.construct_url({"http.target": "bar"}) == ""

    def test_construct_url_all_attrs(
        self,
        fixture_swsampler,
    ):
        assert fixture_swsampler.construct_url(
            {
                "http.scheme": "foo",
                "net.host.name": "bar",
                "net.host.port": "baz",
                "http.target": "/qux"
            }
        ) == "foo://bar:baz/qux"

    def test_construct_url_all_attrs_except_port(
        self,
        fixture_swsampler,
    ):
        assert fixture_swsampler.construct_url(
            {
                "http.scheme": "foo",
                "net.host.name": "bar",
                "http.target": "/qux"
            }
        ) == "foo://bar/qux"


class Test_SwSampler_calculate_tracing_mode():
    def test_calculate_tracing_mode_no_filters(
        self,
        fixture_swsampler,
    ):
        # this fixture has global tracing_mode -1 (unset)
        assert fixture_swsampler.calculate_tracing_mode("foo", None) == -1

    def test_calculate_tracing_mode_filters_url_no_match(
        self,
        fixture_swsampler_txnfilters,
    ):
        # this fixture has global tracing_mode -1 (unset)
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "foo",
            None,
            {
                "http.scheme": "foo",
                "net.host.name": "bar",
                "net.host.port": "baz",
                "http.target": "/qux"   
            }
        ) == -1

    def test_calculate_tracing_mode_filters_url_one_match_exact(
        self,
        fixture_swsampler_txnfilters,
    ):
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "foo",
            None,
            {
                "http.scheme": "http",
                "net.host.name": "foo",
                "http.target": "/bar"   
            }
        ) == 1

    def test_calculate_tracing_mode_filters_url_one_match(
        self,
        fixture_swsampler_txnfilters,
    ):
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "foo",
            None,
            {
                "http.scheme": "http",
                "net.host.name": "foo",
                "http.target": "/abcdef/bar"   
            }
        ) == 1

    def test_calculate_tracing_mode_filters_url_multiple_match(
        self,
        fixture_swsampler_txnfilters,
    ):
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "foo",
            None,
            {
                "http.scheme": "http",
                "net.host.name": "foo",
                "http.target": "/bar-baz"   
            }
        ) == 1

    def test_calculate_tracing_mode_filters_no_url_no_match(
        self,
        fixture_swsampler_txnfilters,
    ):
        # the sampler fixture has global tracing_mode -1 (unset)
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "no-foo",
            SpanKind.CLIENT,
        ) == -1

    def test_calculate_tracing_mode_filters_no_url_one_match_exact(
        self,
        fixture_swsampler_txnfilters,
    ):
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "foo",
            SpanKind.CLIENT,
        ) == 1

    def test_calculate_tracing_mode_filters_no_url_one_match(
        self,
        fixture_swsampler_txnfilters,
    ):
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "fooooooo",
            SpanKind.CLIENT,
        ) == 1

    def test_calculate_tracing_mode_filters_no_url_multiple_match(
        self,
        fixture_swsampler_txnfilters,
    ):
        assert fixture_swsampler_txnfilters.calculate_tracing_mode(
            "foo_bar",
            SpanKind.CLIENT,
        ) == 1
