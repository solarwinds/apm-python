import logging
import re
import typing

from opentelemetry.context.context import Context

logger = logging.getLogger(__file__)

class XTraceOptions():
    """Formats X-Trace-Options for trigger tracing"""

    _SW_XTRACEOPTIONS_RESPONSE_KEY = "xtrace_options_response"
    _XTRACEOPTIONS_CUSTOM = ("^custom-[^\s]*$")
    _XTRACEOPTIONS_CUSTOM_RE = re.compile(_XTRACEOPTIONS_CUSTOM)

    _XTRACEOPTIONS_HEADER_KEY_SW_KEYS = "sw-keys"
    _XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE = "trigger-trace"
    _XTRACEOPTIONS_HEADER_KEY_TS = "ts"

    _OPTION_KEYS = [
        "custom_kvs",
        "signature",
        "sw_keys",
        "trigger_trace",
        "ts",
        "ignored"
    ]

    def __init__(self,
        context: typing.Optional[Context] = None,
        options_header: str = None,
        signature_header: str = None
    ):
        """
        Args:
          context: OTel context that may contain x-trace-options
          options_header: A string of x-trace-options
          signature_header: A string required for signed trigger trace
        
        Examples of options_header:
          "trigger-trace"
          "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo"
          "trigger-trace;custom-key1=value1"
        """
        self.custom_kvs = {}
        self.signature = None
        self.sw_keys = {}
        self.trigger_trace = False
        self.ts = 0
        self.ignored = []

        if not options_header:
            self.from_context(context)
            return

        # each of options delimited by semicolon
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
                    self.trigger_trace = True
        
            elif option_key == self._XTRACEOPTIONS_HEADER_KEY_SW_KEYS:
                # each of sw-keys KVs delimited by comma
                sw_kvs = re.split(r",+", option_kv[1])
                for assignment in sw_kvs:
                    # each of sw-keys values assigned by colon
                    sw_kv = assignment.split(":", 2)
                    if not sw_kv[0]:
                        logger.debug(
                            "Could not parse sw-key assignment {}. Ignoring.".format(
                                assignment
                            ))
                        self.ignore.append(assignment)
                    else:
                        self.sw_keys.update({sw_kv[0]: sw_kv[1]})

            elif re.match(self._XTRACEOPTIONS_CUSTOM_RE, option_key):
                self.custom_kvs[option_key] = option_kv[1].strip()

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
        
        if signature_header:
            self.signature = signature_header

    def __iter__(self) -> typing.Iterator:
        """Iterable representation of XTraceOptions"""
        yield from self.__dict__.items()

    def to_options_header(self) -> str:
        """String representation of XTraceOptions, without signature."""
        options = []

        if self.trigger_trace:
            options.append(self._XTRACEOPTIONS_HEADER_KEY_TRIGGER_TRACE)

        if len(self.sw_keys) > 0:
            sw_keys = []
            for _, (k, v) in enumerate(self.sw_keys.items()):
                sw_keys.append(":".join([k, v])) 
            options.append(
                "=".join([
                    self._XTRACEOPTIONS_HEADER_KEY_SW_KEYS,
                    ",".join(sw_keys)
                ])
            )

        if len(self.custom_kvs) > 0:
            for _, (k, v) in enumerate(self.custom_kvs.items()):
                options.append("=".join([k, v]))

        if self.ts > 0:
            options.append(
                "=".join([
                    self._XTRACEOPTIONS_HEADER_KEY_TS, str(self.ts)
                ])
            )

        return ";".join(options)

    def from_context(
        self,
        context: typing.Optional[Context]
    ) -> None:
        """
        Args:
          context: OTel context that may contain x-trace-options
        """
        logger.debug("Setting XTraceOptions from_context with {}".format(context))
        if not context:
            return
        for option_key in self._OPTION_KEYS:
            if context.get(option_key, None):
                setattr(self, option_key, context[option_key])

    @classmethod
    def get_sw_xtraceoptions_response_key(cls) -> str:
        return cls._SW_XTRACEOPTIONS_RESPONSE_KEY
