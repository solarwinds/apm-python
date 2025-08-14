# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import re

logger = logging.getLogger(__name__)


class XTraceOptions:
    """Formats X-Trace-Options and signature for trigger tracing"""

    _XTRACEOPTIONS_CUSTOM = r"^custom-[^\s]*$"
    _XTRACEOPTIONS_CUSTOM_RE = re.compile(_XTRACEOPTIONS_CUSTOM)

    _XTRACEOPTIONS_HEADER_KEY_SW_KEYS = "sw-keys"
    _XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE = "trigger-trace"
    _XTRACEOPTIONS_HEADER_KEY_TS = "ts"

    # pylint: disable=too-many-branches,too-many-statements
    def __init__(
        self,
        xtraceoptions_header: str = "",
        signature_header: str = "",
    ):
        """
        Args:
          xtraceoptions_header: extracted request header value
          signature_header: extracted request header value
        """
        self.ignored = []
        self.options_header = ""
        self.signature = ""
        self.custom_kvs = {}
        self.sw_keys = ""
        self.trigger_trace = 0
        self.timestamp = 0
        self.include_response = False

        if xtraceoptions_header:
            self.options_header = xtraceoptions_header

        if signature_header:
            self.signature = signature_header

        if xtraceoptions_header:
            # If x-trace-options header given, set response header
            self.include_response = True

            traceoptions = re.split(r";+", xtraceoptions_header)
            for option in traceoptions:
                # KVs (e.g. sw-keys or custom-key1) are assigned by equals
                option_kv = option.split("=", 1)
                if not option_kv[0]:
                    continue

                option_key = option_kv[0].strip()
                if option_key == self._XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE:
                    if len(option_kv) > 1:
                        logger.debug(
                            "trigger-trace must be standalone flag. Ignoring."
                        )
                        self.ignored.append(
                            self._XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE
                        )
                    else:
                        self.trigger_trace = 1

                elif option_key == self._XTRACEOPTIONS_HEADER_KEY_SW_KEYS:
                    # sw-keys value is assigned with an equals sign (=)
                    # while value can contain more equals signs
                    if len(option_kv) > 1:
                        # use only the first sw-keys value if multiple in header
                        if not self.sw_keys:
                            self.sw_keys = option_kv[1].strip()
                    else:
                        logger.debug(
                            "sw-keys value needs to be assigned with an equals sign. Ignoring."
                        )
                        self.ignored.append(option_key)

                elif re.match(self._XTRACEOPTIONS_CUSTOM_RE, option_key):
                    # custom-* value is assigned with an equals sign (=)
                    # while value can contain more equals signs
                    if len(option_kv) > 1:
                        # use only the first custom-* value if multiple in header
                        if option_key not in self.custom_kvs:
                            self.custom_kvs[option_key] = option_kv[1].strip()
                    else:
                        logger.debug(
                            "Each custom-* value needs to be assigned with an equals sign. Ignoring."
                        )
                        self.ignored.append(option_key)

                elif option_key == self._XTRACEOPTIONS_HEADER_KEY_TS:
                    try:
                        if not self.timestamp:
                            self.timestamp = int(option_kv[1])
                    except ValueError:
                        logger.debug("ts must be base 10 int. Ignoring.")
                        self.ignored.append(self._XTRACEOPTIONS_HEADER_KEY_TS)

                else:
                    logger.debug(
                        "%s is not a recognized trace option. Ignoring",
                        option_key,
                    )
                    self.ignored.append(option_key)

                if self.ignored:
                    logger.debug(
                        "Some x-trace-options were ignored: %s",
                        ", ".join(self.ignored),
                    )
