# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/appoptics/solarwinds-apm-python/compare/v0.1.0...HEAD)
## [0.2.1](https://github.com/appoptics/solarwinds-apm-python/releases/tag/v0.2.1) - 2022-11-08
Version bump for rebuild of 0.2.0.

## [0.2.0](https://github.com/appoptics/solarwinds-apm-python/releases/tag/v0.2.0) - 2022-11-07
### Added
- Added `solarwinds_ready` method ([#64](https://github.com/appoptics/solarwinds-apm-python/pull/64))
- Added startup `__Init` with SWO ([#64](https://github.com/appoptics/solarwinds-apm-python/pull/64))
- Added more unit tests ([#68](https://github.com/appoptics/solarwinds-apm-python/pull/68))

### Changed
- SolarWinds c-lib 11.0.0, for AppOptics certificate compatibility ([#70](https://github.com/appoptics/solarwinds-apm-python/pull/70))
- Fixed logging vulnerabilities ([#63](https://github.com/appoptics/solarwinds-apm-python/pull/63))
- Update packaging and install tests ([#71](https://github.com/appoptics/solarwinds-apm-python/pull/71))

## [0.1.0](https://github.com/appoptics/solarwinds-apm-python/releases/tag/v0.1.0) - 2022-10-13
### Added
- Initial release for GA (alpha)
- OpenTelemetry API/SDK 1.13.0, for trace generation
- OpenTelemetry Instrumentation 0.34b, for (auto-)instrumentation of common Python frameworks
- SolarWinds c-lib 10.6.1, for unified inbound metrics generation, trace sample decision, and export to SWO
- W3C trace context propagation
- OTel, APM instrumentation startup, and trigger trace configurable with environment variables
