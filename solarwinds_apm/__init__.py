COMMA = ","
COMMA_W3C_SANITIZED = "...."
EQUALS = "="
EQUALS_W3C_SANITIZED = "####"
SW_TRACESTATE_KEY = "sw"
OTEL_CONTEXT_SW_OPTIONS_KEY = "sw_xtraceoptions"
OTEL_CONTEXT_SW_SIGNATURE_KEY = "sw_signature"
DEFAULT_SW_TRACES_EXPORTER = "solarwinds_exporter"
TRACECONTEXT_PROPAGATOR = "tracecontext"
SW_PROPAGATOR = "solarwinds_propagator"
DEFAULT_SW_PROPAGATORS = [
    TRACECONTEXT_PROPAGATOR,
    "baggage",
    SW_PROPAGATOR,
]
# TODO: Update support doc urls and email alias for SWO
DOC_SUPPORTED_PLATFORMS = 'https://docs.appoptics.com/kb/apm_tracing/supported_platforms/'
DOC_TRACING_PYTHON = 'https://docs.appoptics.com/kb/apm_tracing/python/'
SUPPORT_EMAIL = 'support@appoptics.com'