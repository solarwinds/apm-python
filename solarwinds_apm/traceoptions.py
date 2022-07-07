import logging
import re
import typing

from opentelemetry.context.context import Context

from solarwinds_apm.apm_constants import (
    INTL_SWO_X_OPTIONS_KEY,
    INTL_SWO_SIGNATURE_KEY
)

logger = logging.getLogger(__name__)

class XTraceOptions():
    """Formats X-Trace-Options and signature for trigger tracing"""

    _SW_XTRACEOPTIONS_RESPONSE_KEY = "xtrace_options_response"
    _XTRACEOPTIONS_CUSTOM = (r"^custom-[^\s]*$")
    _XTRACEOPTIONS_CUSTOM_RE = re.compile(_XTRACEOPTIONS_CUSTOM)

    _XTRACEOPTIONS_HEADER_KEY_SW_KEYS = "sw-keys"
    _XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE = "trigger-trace"
    _XTRACEOPTIONS_HEADER_KEY_TS = "ts"

    def __init__(self,
        context: typing.Optional[Context] = None,
    ):
        """
        Args:
          context: OTel context that may contain OTEL_CONTEXT_SW_OPTIONS_KEY,OTEL_CONTEXT_SW_SIGNATURE_KEY
        """
        self.ignored = []
        self.options_header = ""
        self.signature = None
        self.sw_keys = ""
        self.trigger_trace = 0
        self.ts = 0
        
        if not context:
            return
        options_header = context.get(INTL_SWO_X_OPTIONS_KEY, None)
        if not options_header:
            return

        # store original header for sample decision later
        self.options_header = options_header

        traceoptions = re.split(r";+", options_header)
        for option in traceoptions:
            # KVs (e.g. sw-keys or custom-key1) are assigned by equals
            option_kv = option.split("=", 2)
            if not option_kv[0]:
                continue

            option_key = option_kv[0].strip()
            if option_key == self._XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE:
                if len(option_kv) > 1:
                    logger.debug("trigger-trace must be standalone flag. Ignoring.")
                    self.ignored.append(
                        self._XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE
                    )
                else:
                    self.trigger_trace = 1
        
            elif option_key == self._XTRACEOPTIONS_HEADER_KEY_SW_KEYS:
                self.sw_keys = option_kv[1].strip()                    

            elif re.match(self._XTRACEOPTIONS_CUSTOM_RE, option_key):
                # custom keys are valid but do not need parsing
                pass

            elif option_key == self._XTRACEOPTIONS_HEADER_KEY_TS:
                try:
                    self.ts = int(option_kv[1])
                except ValueError as e:
                    logger.debug("ts must be base 10 int. Ignoring.")
                    self.ignore.append(self._XTRACEOPTIONS_HEADER_KEY_TS)
            
            else:
                logger.debug(
                    "{} is not a recognized trace option. Ignoring".format(
                        option_key
                    ))
                self.ignored.append(option_key)

            if self.ignored:
                logger.debug(
                    "Some x-trace-options were ignored: {}".format(
                        ", ".join(self.ignored)
                    ))
        
        options_signature = context.get(INTL_SWO_SIGNATURE_KEY, None)
        if options_signature:
            self.signature = options_signature

    @classmethod
    def get_sw_xtraceoptions_response_key(cls) -> str:
        return cls._SW_XTRACEOPTIONS_RESPONSE_KEY
