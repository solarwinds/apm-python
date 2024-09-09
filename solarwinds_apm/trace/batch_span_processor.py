# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer_provider


class SolarWindsBatchSpanProcessor(BatchSpanProcessor):
    """Subclasses Otel Python BatchSpanProcessor to force_flush at shutdown"""

    def shutdown(self) -> None:
        # Force flush spans that have not yet been processed
        logger.warning("Performing TracerProvider force_flush of traces")
        get_tracer_provider().force_flush()
        super().shutdown()
