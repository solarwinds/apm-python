# Dockerfile for AWS Lambda container image build with SolarWinds APM Python,
# OpenTelemetry Collector extension, and function definition.
# Download the layer first: ./download-layer.sh

FROM public.ecr.aws/lambda/python:3.12-arm64

# Download and extract the latest SolarWinds OTel Lambda extension for ARM64
ARG SOLARWINDS_OTEL_VERSION=0.0.13
ARG LAYER_ZIP=solarwinds_apm_lambda.zip
ADD https://github.com/solarwinds/opentelemetry-lambda/releases/download/layer-collector/${SOLARWINDS_OTEL_VERSION}/opentelemetry-collector-layer-arm64.zip /tmp/swo-otel-extension.zip
RUN python -m zipfile -e /tmp/swo-otel-extension.zip /opt && rm /tmp/swo-otel-extension.zip
RUN mv /opt/extensions/collector /opt/extensions/otel-extension && chmod +x /opt/extensions/otel-extension
ENV OPENTELEMETRY_COLLECTOR_CONFIG_URI=file:///opt/collector-config/config.yaml

# Extract the pre-downloaded APM Python Lambda Layer
COPY ${LAYER_ZIP} /tmp/apm-python-layer.zip
RUN python -m zipfile -e /tmp/apm-python-layer.zip /opt && rm /tmp/apm-python-layer.zip
RUN chmod +x /opt/python/bin/opentelemetry-instrument
RUN chmod +x /opt/solarwinds-apm/wrapper
RUN mv /opt/python/otel_wrapper.py ${LAMBDA_TASK_ROOT}/otel_wrapper.py

# Required configuration for OpenTelemetry auto-instrumentation
ENV AWS_LAMBDA_EXEC_WRAPPER=/opt/solarwinds-apm/wrapper
ENV ORIG_HANDLER=lambda_function.lambda_handler \
    _HANDLER=otel_wrapper.lambda_handler
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

# Run auto-instrumented AWS Lambda function
CMD ["otel_wrapper.lambda_handler"]
