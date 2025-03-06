# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from typing import Optional, Dict, Callable


class Otlp:
    def __init__(self, traces: str, metrics: str, logs: str):
        self._traces = traces
        self._metrics = metrics
        self._logs = logs

    @property
    def traces(self) -> str:
        return self._traces

    @traces.setter
    def traces(self, value: str):
        self._traces = value

    @property
    def metrics(self) -> str:
        return self._metrics

    @metrics.setter
    def metrics(self, value: str):
        self._metrics = value

    @property
    def logs(self) -> str:
        return self._logs

    @logs.setter
    def logs(self, value: str):
        self._logs = value


class TransactionSetting:
    def __init__(self, tracing: bool, matcher: Callable[[str], bool]):
        self._tracing = tracing
        self._matcher = matcher

    @property
    def tracing(self) -> bool:
        return self._tracing

    @tracing.setter
    def tracing(self, value: bool):
        self._tracing = value

    @property
    def matcher(self) -> Callable[[str], bool]:
        return self._matcher

    @matcher.setter
    def matcher(self, value: Callable[[str], bool]):
        self._matcher = value


class Configuration:
    def __init__(self,
                 enabled: bool,
                 service: str,
                 token: Optional[str],
                 collector: str,
                 headers: Dict[str, str],
                 otlp: Otlp,
                 log_level: int,
                 tracing_mode: Optional[bool],
                 trigger_trace_enabled: bool,
                 export_logs_enabled: bool,
                 transaction_name: Optional[Callable[[], str]],
                 transaction_settings: list[TransactionSetting]):
        self._enabled = enabled
        self._service = service
        self._token = token
        self._collector = collector
        self._headers = headers
        self._otlp = otlp
        self._log_level = log_level
        self._tracing_mode = tracing_mode
        self._trigger_trace_enabled = trigger_trace_enabled
        self._export_logs_enabled = export_logs_enabled
        self._transaction_name = transaction_name
        self._transaction_settings = transaction_settings

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def service(self) -> str:
        return self._service

    @service.setter
    def service(self, value: str):
        self._service = value

    @property
    def token(self) -> Optional[str]:
        return self._token

    @token.setter
    def token(self, value: Optional[str]):
        self._token = value

    @property
    def collector(self) -> str:
        return self._collector

    @collector.setter
    def collector(self, value: str):
        self._collector = value

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers

    @headers.setter
    def headers(self, value: Dict[str, str]):
        self._headers = value

    @property
    def otlp(self) -> Otlp:
        return self._otlp

    @otlp.setter
    def otlp(self, value: Otlp):
        self._otlp = value

    @property
    def log_level(self) -> int:
        return self._log_level

    @log_level.setter
    def log_level(self, value: int):
        self._log_level = value

    @property
    def tracing_mode(self) -> Optional[bool]:
        return self._tracing_mode

    @tracing_mode.setter
    def tracing_mode(self, value: Optional[bool]):
        self._tracing_mode = value

    @property
    def trigger_trace_enabled(self) -> bool:
        return self._trigger_trace_enabled

    @trigger_trace_enabled.setter
    def trigger_trace_enabled(self, value: bool):
        self._trigger_trace_enabled = value

    @property
    def export_logs_enabled(self) -> bool:
        return self._export_logs_enabled

    @export_logs_enabled.setter
    def export_logs_enabled(self, value: bool):
        self._export_logs_enabled = value

    @property
    def transaction_name(self) -> Optional[Callable[[], str]]:
        return self._transaction_name

    @transaction_name.setter
    def transaction_name(self, value: Optional[Callable[[], str]]):
        self._transaction_name = value

    @property
    def transaction_settings(self) -> list[TransactionSetting]:
        return self._transaction_settings

    @transaction_settings.setter
    def transaction_settings(self, value: list[TransactionSetting]):
        self._transaction_settings = value
