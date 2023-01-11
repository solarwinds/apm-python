# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


class OboeReadyCode:
    OBOE_SERVER_RESPONSE_UNKNOWN = (0, "Oboe server : unknown error")
    OBOE_SERVER_RESPONSE_OK = (1, "Oboe server : is ready")
    OBOE_SERVER_RESPONSE_TRY_LATER = (
        2,
        "Oboe server : not ready yet, try later",
    )
    OBOE_SERVER_RESPONSE_LIMIT_EXCEEDED = (3, "Oboe server : limit exceeded")
    OBOE_SERVER_RESPONSE_INVALID_API_KEY = (4, "Oboe server : invalid API key")
    OBOE_SERVER_RESPONSE_CONNECT_ERROR = (5, "Oboe server : connection error")

    @classmethod
    def code_values(cls):
        code_pairs = [
            v for k, v in cls.__dict__.items() if not k.startswith("__")
        ]
        return {p[0]: p[1] for p in code_pairs if isinstance(p, tuple)}


class OboeReporterCode:
    """Return values of Oboe Reporter"""

    OBOE_INIT_ALREADY_INIT = -1
    OBOE_INIT_OK = 0
    OBOE_INIT_WRONG_VERSION = 1
    OBOE_INIT_INVALID_PROTOCOL = 2
    OBOE_INIT_NULL_REPORTER = 3
    OBOE_INIT_DESC_ALLOC = 4
    OBOE_INIT_FILE_OPEN_LOG = 5
    OBOE_INIT_UDP_NO_SUPPORT = 6
    OBOE_INIT_UDP_OPEN = 7
    OBOE_INIT_SSL_CONFIG_AUTH = 8
    OBOE_INIT_SSL_LOAD_CERT = 9
    OBOE_INIT_SSL_REPORTER_CREATE = 10
    OBOE_INIT_SSL_MISSING_KEY = 11

    @classmethod
    def get_text_code(cls, num):
        """Returns the textual representation of the numerical status code."""
        for init_status, init_code in cls.__dict__.items():
            if init_code == num:
                return init_status
        return None
