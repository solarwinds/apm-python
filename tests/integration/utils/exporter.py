# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=protected-access,no-self-use

from typing import Sequence
from opentelemetry.sdk.metrics.export import (
    Metric,
    MetricExporter,
    MetricExportResult,
)

# Copied from Opentelemetry SDK test
class InMemoryMetricExporter(MetricExporter):
    def __init__(self):
        super().__init__()
        self.metrics = {}
        self._counter = 0

    def export(
        self,
        metrics_data: Sequence[Metric],
        timeout_millis: float = 10_000,
        **kwargs,
    ) -> MetricExportResult:
        self.metrics[self._counter] = metrics_data
        self._counter += 1
        return MetricExportResult.SUCCESS

    def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
        pass

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        return True
