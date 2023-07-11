# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/solarwindscloud/solarwinds-apm-python/compare/rel-0.13.0...HEAD)

## [0.13.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.13.0) - 2023-07-11
### Added
- Add OTEL_SQLCOMMENTER_ENABLED for some instrumentation libraries ([#169](https://github.com/solarwindscloud/solarwinds-apm-python/pull/169))

### Changed
- aarch64 builds run on EC2 ([#170](https://github.com/solarwindscloud/solarwinds-apm-python/pull/170))
- Metric format is `ResponseTime` instead of both for non-AO backend ([#172](https://github.com/solarwindscloud/solarwinds-apm-python/pull/172))

## [0.12.1](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.12.1) - 2023-06-13
### Added
- Add log warning when `set_transaction_name` with empty name ([#162](https://github.com/solarwindscloud/solarwinds-apm-python/pull/162))

### Changed
- Fix accepted config boolean values ([#166](https://github.com/solarwindscloud/solarwinds-apm-python/pull/166))

### Removed
- Removed unused log_trace_id config storage ([#163](https://github.com/solarwindscloud/solarwinds-apm-python/pull/163))
- Removed unused enable_sanitize_sql config storage ([#164](https://github.com/solarwindscloud/solarwinds-apm-python/pull/164))
- Removed unused is_grpc_clean_hack_enabled config storage ([#165](https://github.com/solarwindscloud/solarwinds-apm-python/pull/165))

## [0.12.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.12.0) - 2023-06-01
### Changed
- Bugfix: APM tracing disabled when platform not supported ([#153](https://github.com/solarwindscloud/solarwinds-apm-python/pull/153))
- Updated to liboboe version 12.3.1 ([#155](https://github.com/solarwindscloud/solarwinds-apm-python/pull/155))
- Verify Installation tests run on EC2 ([#156](https://github.com/solarwindscloud/solarwinds-apm-python/pull/156), [#160](https://github.com/solarwindscloud/solarwinds-apm-python/pull/160))
- Installation tests include Ubuntu 22 ([#158](https://github.com/solarwindscloud/solarwinds-apm-python/pull/158))

## [0.11.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.11.0) - 2023-05-25
### Added
- Added trace context to logging ([#146](https://github.com/solarwindscloud/solarwinds-apm-python/pull/146))

### Changed
- Adjusted config file logging ([#147](https://github.com/solarwindscloud/solarwinds-apm-python/pull/147))
- OpenTelemetry API/SDK 1.18.0 ([#150](https://github.com/solarwindscloud/solarwinds-apm-python/pull/150))
- Added Amazon 2023 install tests; removed Amazon 2018 and Amazon 2 install tests ([#151](https://github.com/solarwindscloud/solarwinds-apm-python/pull/151))


## [0.10.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.10.0) - 2023-05-01
### Added
- Add custom transaction filtering support ([#136](https://github.com/solarwindscloud/solarwinds-apm-python/pull/136), [#137](https://github.com/solarwindscloud/solarwinds-apm-python/pull/137), [#138](https://github.com/solarwindscloud/solarwinds-apm-python/pull/138), [#139](https://github.com/solarwindscloud/solarwinds-apm-python/pull/139), [#141](https://github.com/solarwindscloud/solarwinds-apm-python/pull/141))
- Add span attribute `sw.span_name` at export ([#143](https://github.com/solarwindscloud/solarwinds-apm-python/pull/143))

### Removed
- Removed unused prepend_domain_name config storage ([#140](https://github.com/solarwindscloud/solarwinds-apm-python/pull/140))

## [0.9.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.9.0) - 2023-04-20
### Changed
- OpenTelemetry API/SDK 1.17.0 ([#131](https://github.com/solarwindscloud/solarwinds-apm-python/pull/131))
- SolarWinds c-lib 12.2.0, to fix memory leak in extension ([#132](https://github.com/solarwindscloud/solarwinds-apm-python/pull/132))
- Adds support for `SW_APM_CONFIG_FILE` ([#133](https://github.com/solarwindscloud/solarwinds-apm-python/pull/133))
- Updates Span Layer to be `<KIND>:<NAME>` ([#134](https://github.com/solarwindscloud/solarwinds-apm-python/pull/134))

## [0.8.3](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.8.3) - 2023-03-21
### Changed
- Bugfix: fixed errors at API `set_transaction_name` calls when APM library tracing disabled ([#126](https://github.com/solarwindscloud/solarwinds-apm-python/pull/126))
- SolarWinds c-lib 12.1.0, for enhanced metadata retrieval, skipping metrics HTTP status if unavailable, fixed threading locking issue ([#127](https://github.com/solarwindscloud/solarwinds-apm-python/pull/127))

## [0.8.2](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.8.2) - 2023-03-13
### Changed
- Bugfix: fixed noisy trace state KV deletion attempts when key not present ([#121](https://github.com/solarwindscloud/solarwinds-apm-python/pull/121))
- Bugfix: fixed version lookup failures for instrumented aiohttp library ([#122](https://github.com/solarwindscloud/solarwinds-apm-python/pull/122))

## [0.8.1](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.8.1) - 2023-03-08
### Changed
- Fixed installation from source distribution ([#119](https://github.com/solarwindscloud/solarwinds-apm-python/pull/119))

## [0.8.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.8.0) - 2023-02-28

### Added
- Add `set_transaction_name` API method ([#115](https://github.com/solarwindscloud/solarwinds-apm-python/pull/115))

### Changed
- Deprecated `solarwinds_apm.apm_ready.solarwinds_ready`. Instead, use `solarwinds_apm.api.solarwinds_ready`. ([#115](https://github.com/solarwindscloud/solarwinds-apm-python/pull/115))
- OpenTelemetry API/SDK 1.16.0 ([#116](https://github.com/solarwindscloud/solarwinds-apm-python/pull/116))
- OpenTelemetry Instrumentation 0.37b0 ([#116](https://github.com/solarwindscloud/solarwinds-apm-python/pull/116))

## [0.7.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.7.0) - 2023-02-22

### Added
- Add ARM support ([#111](https://github.com/solarwindscloud/solarwinds-apm-python/pull/111))

### Changed
- Updated CodeQL scans ([#112](https://github.com/solarwindscloud/solarwinds-apm-python/pull/112))

## [0.6.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.6.0) - 2023-02-08
### Changed
- SolarWinds c-lib 12.0.0, for gRPC upgrade ([#107](https://github.com/solarwindscloud/solarwinds-apm-python/pull/107))
- Bugfix: fix version lookup failures for instrumented ASGI libraries ([#108](https://github.com/solarwindscloud/solarwinds-apm-python/pull/108))

### Removed
- Drop centos7 support ([#107](https://github.com/solarwindscloud/solarwinds-apm-python/pull/107))
- Drop Debian 9 support ([#107](https://github.com/solarwindscloud/solarwinds-apm-python/pull/107))
- Drop Amazon Linux 2018.03 support ([#107](https://github.com/solarwindscloud/solarwinds-apm-python/pull/107))

## [0.5.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.5.0) - 2023-01-18
### Added
- Add support for OTEL_SERVICE_NAME, OTEL_RESOURCE_ATTRIBUTES environment variables ([#90](https://github.com/solarwindscloud/solarwinds-apm-python/pull/90))
- Add prioritization of OTEL_SERVICE_NAME, OTEL_RESOURCE_ATTRIBUTES, SW_APM_SERVICE_KEY for setting service.name ([#103](https://github.com/solarwindscloud/solarwinds-apm-python/pull/103))

### Changed
- Update Init message with HostID ([#90](https://github.com/solarwindscloud/solarwinds-apm-python/pull/90))
- Update Init message with Python framework versions ([#94](https://github.com/solarwindscloud/solarwinds-apm-python/pull/94), [#100](https://github.com/solarwindscloud/solarwinds-apm-python/pull/100))
- SolarWinds c-lib 11.1.0, for Init message updates ([#90](https://github.com/solarwindscloud/solarwinds-apm-python/pull/90))
- Updated exported spans with Python framework versions ([#92](https://github.com/solarwindscloud/solarwinds-apm-python/pull/92))
- Bugfix: existing attributes without parent context now write to spans ([#102](https://github.com/solarwindscloud/solarwinds-apm-python/pull/102))
- Bugfix: setting sw.tracestate_parent_id is based on existence of remote parent span ([#102](https://github.com/solarwindscloud/solarwinds-apm-python/pull/102))
- Fix install tests on Ubuntu with Python 3.10/3.11 using older setuptools version ([#104](https://github.com/solarwindscloud/solarwinds-apm-python/pull/104))

## [0.4.0](https://github.com/solarwindscloud/solarwinds-apm-python/releases/tag/rel-0.4.0) - 2023-01-03
### Added
- Add security policy ([#95](https://github.com/solarwindscloud/solarwinds-apm-python/pull/95))
- Add issue templates ([#96](https://github.com/solarwindscloud/solarwinds-apm-python/pull/96/files))

### Changed
- OpenTelemetry API/SDK 1.15.0 ([#91](https://github.com/solarwindscloud/solarwinds-apm-python/pull/91))
- OpenTelemetry Instrumentation 0.36b0 ([#91](https://github.com/solarwindscloud/solarwinds-apm-python/pull/91))
- x-trace-options header `custom-*` KVs written to entry span attributes ([#85](https://github.com/solarwindscloud/solarwinds-apm-python/pull/85))
- Fix `x-trace-options-signature` extraction ([#85](https://github.com/solarwindscloud/solarwinds-apm-python/pull/85))
- Fix validation of `x-trace-options` header ([#87](https://github.com/solarwindscloud/solarwinds-apm-python/pull/87))
- Fix calculation of `x-trace-options-response` header ([#88](https://github.com/solarwindscloud/solarwinds-apm-python/pull/88))
- Update GH organization ([#96](https://github.com/solarwindscloud/solarwinds-apm-python/pull/96/files))

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
