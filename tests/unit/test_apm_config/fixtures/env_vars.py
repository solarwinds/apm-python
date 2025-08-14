import os
import pytest

from solarwinds_apm.apm_constants import INTL_SWO_DEFAULT_PROPAGATORS


@pytest.fixture(name="mock_env_vars")
def fixture_mock_env_vars(mocker):
    mocker.patch.dict(
        os.environ,
        {
            "OTEL_PROPAGATORS": ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
            "SW_APM_SERVICE_KEY": "valid:key",
        },
    )
