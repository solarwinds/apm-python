# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from opentelemetry.sdk.trace.sampling import StaticSampler

from solarwinds_apm.oboe.http_sampler import HttpSampler
from solarwinds_apm.oboe.json_sampler import JsonSampler
from solarwinds_apm.sampler import ParentBasedSwSampler


class TestParentBasedSwSampler():
    def test_init(self, mocker):
        mock_apm_config = mocker.Mock()
        mock_apm_config.get = mocker.Mock(return_value="foo")
        mock_apm_config.is_lambda = False
        sampler = ParentBasedSwSampler(mock_apm_config)
        assert type(sampler._root) == HttpSampler
        assert type(sampler._remote_parent_sampled) == HttpSampler
        assert type(sampler._remote_parent_not_sampled) == HttpSampler
        assert type(sampler._local_parent_sampled) == StaticSampler
        assert type(sampler._local_parent_not_sampled) == StaticSampler

    def test_init_is_lambda(self, mocker):
        mock_apm_config = mocker.Mock()
        mock_apm_config.get = mocker.Mock(return_value="foo")
        mock_apm_config.is_lambda = True
        sampler = ParentBasedSwSampler(mock_apm_config)
        assert type(sampler._root) == JsonSampler
        assert type(sampler._remote_parent_sampled) == JsonSampler
        assert type(sampler._remote_parent_not_sampled) == JsonSampler
        assert type(sampler._local_parent_sampled) == StaticSampler
        assert type(sampler._local_parent_not_sampled) == StaticSampler