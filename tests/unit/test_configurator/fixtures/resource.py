# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest

def get_resource_mocks(mocker):
    mock_new_res = mocker.Mock()
    mock_new_res.configure_mock(
        **{
            "merge": {"foo-merged": "yay"}
        }
    )
    mock_res = mocker.patch(
        "solarwinds_apm.configurator.Resource",
    )
    mock_res.configure_mock(
        **{
            "create": mock_new_res
        }
    )
    return mock_res, mock_new_res
