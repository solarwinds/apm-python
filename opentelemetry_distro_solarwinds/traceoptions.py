import logging
import re
import typing

from opentelemetry.context.context import Context

logger = logging.getLogger(__file__)

class TraceOptions():
    """Formats X-Trace-Options for trigger tracing"""

    _TRACEOPTIONS_CUSTOM = ("^custom-[^\s]*$")
    _TRACEOPTIONS_CUSTOM_RE = re.compile(_TRACEOPTIONS_CUSTOM)

    def __init__(self,
        options: str,
        context: typing.Optional[Context] = None
    ):
        """
        Args:
          options: A string of x-trace-options
          context: OTel context that may contain x-trace-options
        
        Examples of options:
          "trigger-trace"
          "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo"
          "trigger-trace;custom-key1=value1"
        """
        self.custom_kvs = {}
        self.sw_keys = {}
        self.trigger_trace = False
        self.ts = 0
        self.ignored = []

        # TODO: What if OTel context already has traceoptions

        # each of options delimited by semicolon
        traceoptions = re.split(r";+", options)
        for option in traceoptions:
            # KVs (e.g. sw-keys or custom-key1) are assigned by equals
            option_kv = option.split("=", 2)
            if not option_kv[0]:
                continue

            option_key = option_kv[0].strip()
            if option_key == "trigger-trace":
                if len(option_kv) > 1:
                    logger.warning("trigger-trace must be standalone flag. Ignoring.")
                    self.ignored.append("trigger-trace")
                else:
                    self.trigger_trace = True
        
            elif option_key == "sw-keys":
                # each of sw-keys KVs delimited by comma
                sw_kvs = re.split(r",+", option_kv[1])
                for assignment in sw_kvs:
                    # each of sw-keys values assigned by colon
                    sw_kv = assignment.split(":", 2)
                    if not sw_kv[0]:
                        logger.warning(
                            "Could not parse sw-key assignment {0}. Ignoring.".format(
                                assignment
                            ))
                        self.ignore.append(assignment)
                        continue
                    self.sw_keys.update({
                        sw_kv[0]: sw_kv[1]
                    })

            elif re.match(self._TRACEOPTIONS_CUSTOM_RE, option_key):
                self.custom_kvs[option_key] = option_kv[1].strip()

            elif option_key == "ts":
                try:
                    self.ts = int(option_kv[1])
                except ValueError as e:
                    logger.warning("ts must be base 10 int. Ignoring.")
                    self.ignore.append("ts")
            
            else:
                logger.warning(
                    "{0} is not a recognized trace option. Ignoring".format(
                        option_key
                    ))
                self.ignored.append(option_key)

            if self.ignored:
                logger.warning(
                    "Some x-trace-options were ignored: {0}".format(
                        ", ".join(self.ignored)
                    ))
