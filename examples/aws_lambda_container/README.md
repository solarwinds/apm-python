# Example: AWS Lambda container image publishing with APM Python auto-instrumentation

This directory contains an example container image setup for an AWS Lambda Python function with SolarWinds APM Python auto-instrumentation, with instructions for configuration and deployment to AWS ECR and AWS Lambda.

## Contents

```
apm-python/
├── examples/
│   ├── aws_lambda_container/        # this directory
│   │   ├── README.md                # this file
│   │   ├── download-layer.sh        # APM instrumentation layer download script
│   │   ├── lambda_function.py       # sample AWS Lambda function in Python
│   │   └── Dockerfile               # container image build definition
```

## Prerequisites

### For APM layer download (once per APM install/upgrade)
- AWS CLI installed
- AWS authentication configured (credentials file, SSO, environment variables, etc.)
- permission to call `lambda:GetLayerVersionByArn`

### For container build
- Docker installed with BuildKit enabled (Docker 18.09+)
- downloaded layer zip: `solarwinds_apm_lambda.zip`, i.e. from `download-layer.sh`

### For Deployment
- an existing AWS ECR, e.g. `my-cool-repo`
- an existing AWS Lambda, e.g. `my-cool-lambda`
- an existing AWS Lambda function or IAM role with Lambda execution permissions
- SolarWinds Observability SaaS account with API token

## Instructions

### (1) Download APM instrumentation layer (once per APM install/upgrade)

This downloads `solarwinds_apm_lambda.zip` which can be committed or stored in your artifact registry. APM Python library version `>=6.1.1` is required.

```bash
cd <path_to>/apm-python/examples/aws_lambda_container

# Ensure you are authenticated with your AWS account
# with permission to call lambda:GetLayerVersionByArn
# Verify your authentication:
aws sts get-caller-identity

./download-layer.sh
```

To upgrade APM to a newer version later:
```bash
LAYER_VERSION=7_0_1 LAYER_VERSION_NUMBER=1 ./download-layer.sh
```

Check contents of `./download-layer.sh` for more options.

### (2) Build container image with instrumentation

This builds a Docker container image for `my-cool-repo` with:
- SolarWinds OpenTelemetry Collector extension
- APM Python auto-instrumentation
- the function defined in `lambda_function.py`

```bash
# Example build command for ARM64 architecture
DOCKER_BUILDKIT=1 docker build --platform linux/arm64 --provenance=false \
  -t my-cool-repo:latest .
```

**Note:** Check the Dockerfile and use only the commands suitable for your container's platform, e.g. x86_64 or arm64 for extension installation.

### (3) Set/Update AWS Lambda environment variables for instrumentation

This configures environment variables for an existing AWS Lambda function, `my-cool-lambda`. For more information, see [SWO AWS Lambda Instrumentation](https://documentation.solarwinds.com/en/success_center/observability/content/intro/services/aws-lambda-overview.htm).

```bash
# a valid SolarWinds Observability SaaS API token
export SW_APM_API_TOKEN=<valid_swo_api_token>
# the AWS region of your choice
export AWS_REGION=us-east-1

# Option 1: only the required and highly recommended variables
aws lambda update-function-configuration \
    --function-name my-cool-lambda \
    --environment '{"Variables":{"SW_APM_API_TOKEN":"'"${SW_APM_API_TOKEN}"'","OTEL_SERVICE_NAME":"my-cool-lambda"}}' \
    --region ${AWS_REGION}

# Option 2: additional options
aws lambda update-function-configuration \
    --function-name my-cool-lambda \
    --environment '{"Variables":{"SW_APM_API_TOKEN":"'"${SW_APM_API_TOKEN}"'","OTEL_SERVICE_NAME":"my-cool-lambda","SW_APM_DATA_CENTER":"na-02","SW_APM_TELEMETRY_API_SUBSCRIPTION":"platform,function","OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION":"true","SW_APM_DEBUG_LEVEL":"6"}}' \
    --region ${AWS_REGION}
```

### (4) Push to AWS ECR and deploy AWS Lambda

This pushes your built image to an existing AWS ECR repository named `my-cool-repo` then updates `my-cool-lambda` to use it.

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

docker tag my-cool-repo:latest \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/my-cool-repo:latest

docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/my-cool-repo:latest

aws lambda update-function-code \
    --function-name my-cool-lambda \
    --image-uri ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/my-cool-repo:latest \
    --region ${AWS_REGION}

# Wait for the update to complete before you invoke
aws lambda wait function-updated \
    --function-name my-cool-lambda \
    --region ${AWS_REGION}
```
