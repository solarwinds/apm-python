# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from __future__ import annotations

from collections.abc import Callable


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

    def __str__(self):
        return f"TransactionSetting(tracing={self._tracing}, matcher={self._matcher})"


class Configuration:
    def __init__(
        self,
        enabled: bool,
        service: str,
        collector: str,
        headers: dict[str, str],
        tracing_mode: bool | None,
        trigger_trace_enabled: bool,
        transaction_name: Callable[[], str] | None,
        transaction_settings: list[TransactionSetting],
    ):
        self._enabled = enabled
        self._service = service
        self._collector = collector
        self._headers = headers
        self._tracing_mode = tracing_mode
        self._trigger_trace_enabled = trigger_trace_enabled
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
    def collector(self) -> str:
        return self._collector

    @collector.setter
    def collector(self, value: str):
        self._collector = value

    @property
    def headers(self) -> dict[str, str]:
        return self._headers

    @headers.setter
    def headers(self, value: dict[str, str]):
        self._headers = value

    @property
    def tracing_mode(self) -> bool | None:
        return self._tracing_mode

    @tracing_mode.setter
    def tracing_mode(self, value: bool | None):
        self._tracing_mode = value

    @property
    def trigger_trace_enabled(self) -> bool:
        return self._trigger_trace_enabled

    @trigger_trace_enabled.setter
    def trigger_trace_enabled(self, value: bool):
        self._trigger_trace_enabled = value

    @property
    def transaction_name(self) -> Callable[[], str] | None:
        return self._transaction_name

    @transaction_name.setter
    def transaction_name(self, value: Callable[[], str] | None):
        self._transaction_name = value

    @property
    def transaction_settings(self) -> list[TransactionSetting]:
        return self._transaction_settings

    @transaction_settings.setter
    def transaction_settings(self, value: list[TransactionSetting]):
        self._transaction_settings = value

    def __str__(self):
        return f"Configuration(enabled={self._enabled}, service={self._service}, collector={self._collector}, headers={self._headers}, tracing_mode={self._tracing_mode}, trigger_trace_enabled={self._trigger_trace_enabled}, transaction_name={self._transaction_name}, transaction_settings={self._transaction_settings})"
