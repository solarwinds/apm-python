#!/bin/bash

# © 2026 SolarWinds Worldwide, LLC. All rights reserved.
#
# Helper script to download APM Python Lambda layer from AWS.
# Requires AWS CLI and valid AWS_PROFILE for login.

set -e

# Configurable values
AWS_REGION="${AWS_REGION:-us-east-1}"
LAYER_VERSION="${LAYER_VERSION:-6_1_1}"
LAYER_VERSION_NUMBER="${LAYER_VERSION_NUMBER:-1}"
OUTPUT_FILE="${OUTPUT_FILE:-solarwinds_apm_lambda.zip}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}SolarWinds APM Python Lambda Layer Downloader${NC}"
echo "=================================================="
echo ""
echo "Configuration:"
echo "  AWS Profile: $AWS_PROFILE"
echo "  AWS Region: $AWS_REGION"
echo "  Layer Version: $LAYER_VERSION"
echo "  Layer Version Number: $LAYER_VERSION_NUMBER"
echo "  Output File: $OUTPUT_FILE"
echo ""

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed${NC}"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    echo -e "${RED}ERROR: AWS credentials not valid${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials valid${NC}"
echo ""

LAYER_NAME="solarwinds-apm-python-${LAYER_VERSION}"
LAYER_ARN="arn:aws:lambda:${AWS_REGION}:851060098468:layer:${LAYER_NAME}:${LAYER_VERSION_NUMBER}"
echo "Downloading layer from AWS Lambda..."
echo "  ARN: $LAYER_ARN"
echo ""
echo "Getting layer download URL..."
LAYER_URL=$(aws lambda get-layer-version-by-arn \
    --arn "$LAYER_ARN" \
    --query 'Content.Location' \
    --output text \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --no-cli-pager \
    --no-cli-auto-prompt)
if [ -z "$LAYER_URL" ]; then
    echo -e "${RED}ERROR: Failed to get layer download URL${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Got download URL${NC}"
echo ""

echo "Downloading layer zip (this may take a moment)..."
if curl -L "$LAYER_URL" -o "$OUTPUT_FILE"; then
    echo -e "${GREEN}✓ Download complete${NC}"
else
    echo -e "${RED}ERROR: Download failed${NC}"
    exit 1
fi
if [ ! -f "$OUTPUT_FILE" ]; then
    echo -e "${RED}ERROR: Output file not found${NC}"
    exit 1
fi

FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo ""
echo "=================================================="
echo -e "${GREEN}Success!${NC}"
echo ""
echo "Downloaded: $OUTPUT_FILE"
echo "Size: $FILE_SIZE"
echo ""
echo "The layer zip is ready to use with Dockerfile."
echo "=================================================="
