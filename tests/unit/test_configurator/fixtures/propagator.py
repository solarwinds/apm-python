# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest


@pytest.fixture(name="mock_set_global_textmap")
def mock_set_global_textmap(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.set_global_textmap",
    )

@pytest.fixture(name="mock_set_global_response_propagator")
def mock_set_global_response_propagator(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.set_global_response_propagator",
    )

@pytest.fixture(name="mock_composite_propagator")
def mock_composite_propagator(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.CompositePropagator",
    )