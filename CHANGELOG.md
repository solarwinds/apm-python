# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/solarwindscloud/solarwinds-apm-python/compare/rel-0.3.0...HEAD)

## [0.4.0.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.4.0) - 2022-12-15
### Changed
- OpenTelemetry API/SDK 1.15.0 ([#91](https://github.com/solarwindscloud/solarwinds-apm-python/pull/91))
- OpenTelemetry Instrumentation 0.36b0 ([#91](https://github.com/solarwindscloud/solarwinds-apm-python/pull/91))
- x-trace-options header `custom-*` KVs written to entry span attributes ([#85](https://github.com/solarwindscloud/solarwinds-apm-python/pull/85))
- Fix `x-trace-options-signature` extraction ([#85](https://github.com/solarwindscloud/solarwinds-apm-python/pull/85))
- Fix validation of `x-trace-options` header ([#87](https://github.com/solarwindscloud/solarwinds-apm-python/pull/87))
- Fix calculation of `x-trace-options-response` header ([#88](https://github.com/solarwindscloud/solarwinds-apm-python/pull/88))

## [0.3.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.3.0) - 2022-11-24
### Changed
- Fix flake8 and installation tests ([#83](https://github.com/solarwindscloud/solarwinds-apm-python/pull/83))

## [0.2.2](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.2.2) - 2022-11-24
### Added
- Added integration tests ([#67](https://github.com/solarwindscloud/solarwinds-apm-python/pull/67))
- Added sdist and wheel extension file checks as part of library packaging ([#75](https://github.com/solarwindscloud/solarwinds-apm-python/pull/75))
- Added linting and code formatting ([#80](https://github.com/solarwindscloud/solarwinds-apm-python/pull/80), [#82](https://github.com/solarwindscloud/solarwinds-apm-python/pull/82))

### Changed
- OpenTelemetry API/SDK 1.14.0 ([#76](https://github.com/solarwindscloud/solarwinds-apm-python/pull/76))
- OpenTelemetry Instrumentation 0.35b0 ([#76](https://github.com/solarwindscloud/solarwinds-apm-python/pull/76))
- Reformatted code based on linting rules ([#81](https://github.com/solarwindscloud/solarwinds-apm-python/pull/81))
- Fixed changelog links ([#78](https://github.com/solarwindscloud/solarwinds-apm-python/pull/78))

## [0.2.1](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.2.1) - 2022-11-08
### Changed
- Version bump for rebuild of 0.2.0 ([#73](https://github.com/solarwindscloud/solarwinds-apm-python/pull/73))

## [0.2.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.2.0) - 2022-11-07
### Added
- Added `solarwinds_ready` method ([#64](https://github.com/solarwindscloud/solarwinds-apm-python/pull/64))
- Added startup `__Init` with SWO ([#64](https://github.com/solarwindscloud/solarwinds-apm-python/pull/64))
- Added more unit tests ([#68](https://github.com/solarwindscloud/solarwinds-apm-python/pull/68))

### Changed
- SolarWinds c-lib 11.0.0, for AppOptics certificate compatibility ([#70](https://github.com/solarwindscloud/solarwinds-apm-python/pull/70))
- Fixed logging vulnerabilities ([#63](https://github.com/solarwindscloud/solarwinds-apm-python/pull/63))
- Update packaging and install tests ([#71](https://github.com/solarwindscloud/solarwinds-apm-python/pull/71))

## [0.1.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.1.0) - 2022-10-13
### Added
- Initial release for GA (alpha)
- OpenTelemetry API/SDK 1.13.0, for trace generation
- OpenTelemetry Instrumentation 0.34b0, for (auto-)instrumentation of common Python frameworks
- SolarWinds c-lib 10.6.1, for unified inbound metrics generation, trace sample decision, and export to SWO
- W3C trace context propagation
- OTel, APM instrumentation startup, and trigger trace configurable with environment variables
