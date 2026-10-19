# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

import json


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from Lambda!"}),
    }
