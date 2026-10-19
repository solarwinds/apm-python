# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

from opentelemetry.sdk.trace.sampling import StaticSampler

from solarwinds_apm.oboe.http_sampler import HttpSampler
from solarwinds_apm.oboe.json_sampler import JsonSampler
from solarwinds_apm.sampler import ParentBasedSwSampler


class TestParentBasedSwSampler:
    def test_init(self, mocker):
        mock_apm_config = mocker.Mock()
        mock_apm_config.get = mocker.Mock(return_value="foo")
        mock_apm_config.is_lambda = False
        sampler = ParentBasedSwSampler(mock_apm_config)
        assert isinstance(sampler._root, HttpSampler)
        assert isinstance(sampler._remote_parent_sampled, HttpSampler)
        assert isinstance(sampler._remote_parent_not_sampled, HttpSampler)
        assert isinstance(sampler._local_parent_sampled, StaticSampler)
        assert isinstance(sampler._local_parent_not_sampled, StaticSampler)

    def test_init_is_lambda(self, mocker):
        mock_apm_config = mocker.Mock()
        mock_apm_config.get = mocker.Mock(return_value="foo")
        mock_apm_config.is_lambda = True
        sampler = ParentBasedSwSampler(mock_apm_config)
        assert isinstance(sampler._root, JsonSampler)
        assert isinstance(sampler._remote_parent_sampled, JsonSampler)
        assert isinstance(sampler._remote_parent_not_sampled, JsonSampler)
        assert isinstance(sampler._local_parent_sampled, StaticSampler)
        assert isinstance(sampler._local_parent_not_sampled, StaticSampler)
