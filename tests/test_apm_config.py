

class TestSolarWindsApmConfig:
    def test_foo(self):
        pass

    # TODO Test these cases after moving from test_distro
    # def test_configure_env_without_sw_propagator_fails(self, mocker):
    #     mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "tracecontext,baggage"})
    #     with pytest.raises(ValueError):
    #         SolarWindsDistro()._configure()

    # def test_configure_env_without_tracecontext_propagator_fails(self, mocker):
    #     mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "solarwinds_propagator"})
    #     with pytest.raises(ValueError):
    #         SolarWindsDistro()._configure()

    # def test_configure_env_sw_before_tracecontext_propagator_fails(self, mocker):
    #     mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "solarwinds_propagator,tracecontext"})
    #     with pytest.raises(ValueError):
    #         SolarWindsDistro()._configure()