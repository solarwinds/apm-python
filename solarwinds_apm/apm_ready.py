# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import Any

from solarwinds_apm.apm_oboe_codes import OboeReadyCode

logger = logging.getLogger(__name__)


def solarwinds_ready(
    wait_milliseconds: int = 3000,
    integer_response: bool = False,
) -> Any:
    """
    solarwinds_apm.apm_ready.solarwinds_ready is deprecated and will no
    longer be available in a near-future version.

    Please instead use:
     from solarwinds_apm.api import solarwinds_ready
     if not solarwinds_ready(wait_milliseconds=10000, integer_response=True):
        Logger.info("SolarWinds not ready after 10 seconds, no metrics will be sent")
    """
    logger.warning(
        "solarwinds_apm.apm_ready.solarwinds_ready is deprecated and will no "
        "longer be available in a near-future version. Please instead use: \n"
        "from solarwinds_apm.api import solarwinds_ready"
    )
    return (
        OboeReadyCode.OBOE_SERVER_RESPONSE_UNKNOWN
        if integer_response
        else False
    )
