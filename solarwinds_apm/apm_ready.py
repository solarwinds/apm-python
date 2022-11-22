"""
Example usage:

from solarwinds_apm.apm_ready import solarwinds_ready
solarwinds_ready(wait_milliseconds=10000, integer_response=True)
"""

import logging
from typing import Any

from solarwinds_apm.apm_oboe_codes import OboeReadyCode
from solarwinds_apm.extension.oboe import Context

logger = logging.getLogger(__name__)


def solarwinds_ready(
    wait_milliseconds: int = 3000,
    integer_response: bool = False,
) -> Any:
    """
    Wait for SolarWinds to be ready to send traces.

    This may be useful in short lived background processes when it is important to capture
    information during the whole time the process is running. Usually SolarWinds doesn't block an
    application while it is starting up.

    :param wait_milliseconds:int default 3000, the maximum time to wait in milliseconds
    :param integer_response:bool default False to return boolean value, otherwise True to
    return integer for detailed information

    :return:
    if integer_response:int code 1 for ready; 0,2,3,4,5 for not ready
    else:bool True for ready, False not ready,

    :Example:

     if not solarwinds_ready(10000):
        Logger.info("SolarWinds not ready after 10 seconds, no metrics will be sent")
    """
    rc = Context.isReady(wait_milliseconds)
    if not isinstance(rc, int) or rc not in OboeReadyCode.code_values():
        logger.warning("Unrecognized return code: %s", rc)
        return (
            OboeReadyCode.OBOE_SERVER_RESPONSE_UNKNOWN
            if integer_response
            else False
        )
    if rc != OboeReadyCode.OBOE_SERVER_RESPONSE_OK[0]:
        logger.warning(OboeReadyCode.code_values()[rc])

    return (
        rc
        if integer_response
        else rc == OboeReadyCode.OBOE_SERVER_RESPONSE_OK[0]
    )
