# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0


def get_resource_mocks(mocker):
    mock_new_res = mocker.Mock()
    mock_new_res.configure_mock(merge={"foo-merged": "yay"})
    mock_res = mocker.patch(
        "solarwinds_apm.configurator.Resource",
    )
    mock_res.configure_mock(create=mock_new_res)
    return mock_res
