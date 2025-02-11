# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm.extension.oboe import (
    Reporter,
)
from solarwinds_apm.apm_noop import (
    OboeAPI as NoOpOboeAPI,
)

from ..test_base_sw import TestBaseSw


class TestBaseSwLegacy(TestBaseSw):
    """
    Class for testing SolarWinds custom distro header propagation
    and span attributes calculation from decision and headers,
    in legacy mode.
    """

    def _setup_env_vars(self):
        super()._setup_env_vars()
        os.environ["SW_APM_LEGACY"] = "true"

    def _assert_defaults(self):
        super()._assert_defaults()
        # In legacy, traces exporter default is APM-proto
        assert os.environ["OTEL_TRACES_EXPORTER"] == "solarwinds_exporter"

    def _assert_reporter(self, reporter):
        assert isinstance(reporter, Reporter)

    def _setup_test_traces_export(
        self,
        apm_config,
        configurator,
        reporter,
        oboe_api = None,
    ):
        oboe_api = NoOpOboeAPI()
        super()._setup_test_traces_export(
            apm_config,
            configurator,
            reporter,
            oboe_api,
        )

    def setUp(self):
        super().setUp()
        # Finish setup by running Flask app instrumented with APM Python
        self._setup_instrumented_app()