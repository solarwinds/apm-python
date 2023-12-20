# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import builtins
import sys

from solarwinds_apm import apm_config
import solarwinds_apm.apm_noop as NoopExtension
from solarwinds_apm.apm_noop import (
    Context as NoopContext,
    OboeAPI as NoopOboeApi,
)
from solarwinds_apm.extension import oboe as Extension
from solarwinds_apm.extension.oboe import (
    Context,
    OboeAPI,
)


# pylint: disable=unused-import
from .fixtures.env_vars import fixture_mock_env_vars


real_import = builtins.__import__

def monkeypatch_importerror(name, globals=None, locals=None, fromlist=(), level=0):
    if name in ('solarwinds_apm.extension.oboe', ):
        raise ImportError(f"Mocking ImportError of {name}")
    return real_import(name, globals=globals, locals=locals, fromlist=fromlist, level=level)


class TestApmConfigGetExtensionComponents:

    def test__get_extension_components_disabled(
        self,
        mock_env_vars,
    ):
        res1, res2, res3 = apm_config.SolarWindsApmConfig()._get_extension_components(False, False)
        assert res1 == NoopExtension
        assert res2 == NoopContext
        assert res3 == NoopOboeApi

    def test__get_extension_components_cannot_import(
        self,
        mock_env_vars,
        monkeypatch,
    ):
        monkeypatch.delitem(sys.modules, 'solarwinds_apm.extension.oboe', raising=False)
        monkeypatch.setattr(builtins, '__import__', monkeypatch_importerror)
        res1, res2, res3 = apm_config.SolarWindsApmConfig()._get_extension_components(True, False)
        assert res1 == NoopExtension
        assert res2 == NoopContext
        assert res3 == NoopOboeApi

    def test__get_extension_components_is_lambda_cannot_import(
        self,
        mock_env_vars,
        monkeypatch,
    ):
        monkeypatch.delitem(sys.modules, 'solarwinds_apm.extension.oboe', raising=False)
        monkeypatch.setattr(builtins, '__import__', monkeypatch_importerror)
        res1, res2, res3 = apm_config.SolarWindsApmConfig()._get_extension_components(True, True)
        assert res1 == NoopExtension
        assert res2 == NoopContext
        assert res3 == NoopOboeApi

    def test__get_extension_components_is_lambda(
        self,
        mock_env_vars,
    ):
        res1, res2, res3 = apm_config.SolarWindsApmConfig()._get_extension_components(True, True)
        assert res1 == NoopExtension
        assert res2 == NoopContext
        assert res3 == OboeAPI

    def test__get_extension_components_enabled(
        self,
        mock_env_vars,
    ):
        res1, res2, res3 = apm_config.SolarWindsApmConfig()._get_extension_components(True, False)
        assert res1 == Extension
        assert res2 == Context
        assert res3 == NoopOboeApi
