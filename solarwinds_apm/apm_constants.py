# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

INTL_SWO_DEFAULT_OTLP_COLLECTOR = (
    "https://otel.collector.na-01.cloud.solarwinds.com:443"
)
INTL_SWO_COMMA = ","
INTL_SWO_COMMA_W3C_SANITIZED = "...."
INTL_SWO_EQUALS = "="
INTL_SWO_EQUALS_W3C_SANITIZED = "####"
INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN = "sw-current-trace-entry-span"
INTL_SWO_TRACESTATE_KEY = "sw"
INTL_SWO_TRANSACTION_ATTR_KEY = "sw.transaction"
INTL_SWO_TRANSACTION_ATTR_MAX = 255
INTL_SWO_TRANSACTION_NAME_ATTR = "TransactionName"
INTL_SWO_X_OPTIONS_KEY = "sw_xtraceoptions"
INTL_SWO_X_OPTIONS_RESPONSE_KEY = "xtrace_options_response"
INTL_SWO_TRACECONTEXT_PROPAGATOR = "tracecontext"
INTL_SWO_BAGGAGE_PROPAGATOR = "baggage"
INTL_SWO_PROPAGATOR = "solarwinds_propagator"
INTL_SWO_DEFAULT_PROPAGATORS = [
    INTL_SWO_TRACECONTEXT_PROPAGATOR,
    INTL_SWO_BAGGAGE_PROPAGATOR,
    INTL_SWO_PROPAGATOR,
]
INTL_SWO_DEFAULT_RESOURCE_DETECTORS = [
    "process",
    "os",
    "host",
    "aws_ec2",
    "aws_ecs",
    "aws_eks",
    "azure_app_service",
    "azure_functions",
    "azure_vm",
    "k8s",
    "uams",
]
INTL_SWO_DEFAULT_RESOURCE_DETECTORS_LAMBDA = [
    "process",
    "os",
    "host",
    "aws_lambda",
]
INTL_SWO_DOC_SUPPORTED_PLATFORMS = "https://documentation.solarwinds.com/en/success_center/observability/content/system_requirements/apm_requirements.htm#link3"
INTL_SWO_DOC_TRACING_PYTHON = "https://documentation.solarwinds.com/en/success_center/observability/default.htm#cshid=app-add-python-agent"
INTL_SWO_SUPPORT_EMAIL = "SWO-support@solarwinds.com"
