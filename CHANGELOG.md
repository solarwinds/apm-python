# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/solarwinds/apm-python/compare/rel-1.1.1...HEAD)


## [1.1.1](https://github.com/solarwinds/apm-python/releases/tag/rel-1.1.1) - 2024-01-18

### Changed
- Updated lambda layer workflow ([#278](https://github.com/solarwinds/apm-python/pull/278))
- Fixed release PR action ([#282](https://github.com/solarwinds/apm-python/pull/282))
- SolarWinds c-lib 14.0.2 ([#288](https://github.com/solarwinds/apm-python/pull/288))
- Added environment logging ([#291](https://github.com/solarwinds/apm-python/pull/291))
- Linting ([#292](https://github.com/solarwinds/apm-python/pull/292))

### Removed
- Removed `sw.nonce` metrics attribute ([#284](https://github.com/solarwinds/apm-python/pull/284))
- Removed todos ([#285](https://github.com/solarwinds/apm-python/pull/285))

## [1.1.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.1.0) - 2024-01-18

### Added
- Added configuration of transaction name in response_time metrics by lambda environment ([#257](https://github.com/solarwinds/apm-python/pull/257))
- Added Dependabot config ([#261](https://github.com/solarwinds/apm-python/pull/261), [#270](https://github.com/solarwinds/apm-python/pull/270))
- Added support for `SW_APM_LOG_FILEPATH` ([#275](https://github.com/solarwinds/apm-python/pull/275))

### Changed
- Fixed unit tests ([#249](https://github.com/solarwinds/apm-python/pull/249))
- Refactored span processors ([#251](https://github.com/solarwinds/apm-python/pull/251), [#252](https://github.com/solarwinds/apm-python/pull/252), [#253](https://github.com/solarwinds/apm-python/pull/253), [#254](https://github.com/solarwinds/apm-python/pull/254), [#255](https://github.com/solarwinds/apm-python/pull/255))
- Add API unit tests ([#256](https://github.com/solarwinds/apm-python/pull/256))
- Refactor c-lib init ([#258](https://github.com/solarwinds/apm-python/pull/258))
- SolarWinds c-lib 14.0.0 ([#259](https://github.com/solarwinds/apm-python/pull/259))
- Upgraded workflow dependencies ([#262](https://github.com/solarwinds/apm-python/pull/262),[#263](https://github.com/solarwinds/apm-python/pull/263), [#264](https://github.com/solarwinds/apm-python/pull/264), [#265](https://github.com/solarwinds/apm-python/pull/265), [#266](https://github.com/solarwinds/apm-python/pull/266), [#271](https://github.com/solarwinds/apm-python/pull/271))
- Move build configuration to pyproject.toml ([#273](https://github.com/solarwinds/apm-python/pull/273))
- SolarWinds c-lib 14.0.1 ([#280](https://github.com/solarwinds/apm-python/pull/280))

### Removed
- Removed unused mend/whitesource config ([#260](https://github.com/solarwinds/apm-python/pull/260))

## [1.0.2](https://github.com/solarwinds/apm-python/releases/tag/rel-1.0.2) - 2023-12-04

### Changed
- Update setup.cfg metadata ([#232](https://github.com/solarwinds/apm-python/pull/232))
- Increased unit test coverage ([#225](https://github.com/solarwinds/apm-python/pull/225), [#231](https://github.com/solarwinds/apm-python/pull/231), [#233](https://github.com/solarwinds/apm-python/pull/233), [#234](https://github.com/solarwinds/apm-python/pull/234), [#235](https://github.com/solarwinds/apm-python/pull/235), [#236](https://github.com/solarwinds/apm-python/pull/236), [#237](https://github.com/solarwinds/apm-python/pull/237), [#238](https://github.com/solarwinds/apm-python/pull/238), [#239](https://github.com/solarwinds/apm-python/pull/239), [#240](https://github.com/solarwinds/apm-python/pull/240), [#241](https://github.com/solarwinds/apm-python/pull/241), [#242](https://github.com/solarwinds/apm-python/pull/242), [#243](https://github.com/solarwinds/apm-python/pull/243), [#244](https://github.com/solarwinds/apm-python/pull/244))
- SimpleSpanProcessor when lambda ([#245](https://github.com/solarwinds/apm-python/pull/245))

## [1.0.1](https://github.com/solarwinds/apm-python/releases/tag/rel-1.0.1) - 2023-11-21

### Added
- Added lambda build workflows ([#221](https://github.com/solarwinds/apm-python/pull/221))
- Integrated OboeAPI ([#223](https://github.com/solarwinds/apm-python/pull/223))

### Changed
- Updated layer extension build target ([#215](https://github.com/solarwinds/apm-python/pull/215))
- Updated experimental exporter defaults ([#217](https://github.com/solarwinds/apm-python/pull/217))
- Optimized layer builds ([#214](https://github.com/solarwinds/apm-python/pull/214))
- Updated setup.py and OboeAPI usage ([#224](https://github.com/solarwinds/apm-python/pull/224))
- Fixed release workflows ([#226](https://github.com/solarwinds/apm-python/pull/226))

## [1.0.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.0.0) - 2023-11-14

### Changed
- Change c-lib usage and `agent_enabled` calculation if `is_lambda` ([#211](https://github.com/solarwinds/apm-python/pull/211))
- Updated Makefile for APM Python lambda builds ([#212](https://github.com/solarwinds/apm-python/pull/212))
- Move organization and repo ([#218](https://github.com/solarwinds/apm-python/pull/218))

## [0.18.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.18.0) - 2023-10-31

### Added
- Add experimental configuration of OpenTelemetry metrics ([#200](https://github.com/solarwinds/apm-python/pull/200))
- Add generation and OTLP export of `trace.service.response_time` metrics ([#201](https://github.com/solarwinds/apm-python/pull/201))
- Add support for `SW_APM_TRANSACTION_NAME` ([#206](https://github.com/solarwinds/apm-python/pull/206))

### Changed
- Fixed test dependency for support of Flask < 3 ([#202](https://github.com/solarwinds/apm-python/pull/202))
- Fixed EC2 runner publish actions ([#203](https://github.com/solarwinds/apm-python/pull/203))
- Updated install test coverage for Debian 11 ([#204](https://github.com/solarwinds/apm-python/pull/204))
- Updated Codeowners ([#205](https://github.com/solarwinds/apm-python/pull/205))

## [0.17.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.17.0) - 2023-09-20

### Changed
- OpenTelemetry API/SDK and instrumentation 1.20.0/0.41b0 ([#195](https://github.com/solarwinds/apm-python/pull/195))
- Update CODEOWNERS ([#196](https://github.com/solarwinds/apm-python/pull/196))

## [0.16.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.16.0) - 2023-08-24

### Changed
- Updated to liboboe version 13.0.0 (skipped 12.4.1) ([#192](https://github.com/solarwinds/apm-python/pull/192))

## [0.15.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.15.0) - 2023-08-17

### Added
- Add context-in-logs configuration with `OTEL_SQLCOMMENTER_OPTIONS` ([#182](https://github.com/solarwinds/apm-python/pull/182))
- Add CODEOWNERS file ([#189](https://github.com/solarwinds/apm-python/pull/189))

### Changed
- Remove unused baggage from propagator injection ([#184](https://github.com/solarwinds/apm-python/pull/184))
- Simplify internal baggage setting for custom naming ([#186](https://github.com/solarwinds/apm-python/pull/186))
- Fix custom name storage clearing when not sampled ([#187](https://github.com/solarwinds/apm-python/pull/187))

### Removed
- Remove old print statements in exporter ([#183](https://github.com/solarwinds/apm-python/pull/183))
- Remove unneeded `Spec` key from error events ([#188](https://github.com/solarwinds/apm-python/pull/188))

## [0.14.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.14.0) - 2023-07-20
### Changed
- Refactored propagator and sampler ([#175](https://github.com/solarwinds/apm-python/pull/175))
- Renamed CI secrets ([#176](https://github.com/solarwinds/apm-python/pull/176))
- Updated to liboboe version 12.4.0 ([#177](https://github.com/solarwinds/apm-python/pull/177))
- OpenTelemetry API/SDK and instrumentation 1.19.0/0.40b0 ([#178](https://github.com/solarwinds/apm-python/pull/178))

### Removed
- Removed PackageCloud build workflows ([#179](https://github.com/solarwinds/apm-python/pull/179))

## [0.13.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.13.0) - 2023-07-11
### Added
- Add OTEL_SQLCOMMENTER_ENABLED for some instrumentation libraries ([#169](https://github.com/solarwinds/apm-python/pull/169))

### Changed
- aarch64 builds run on EC2 ([#170](https://github.com/solarwinds/apm-python/pull/170))
- Metric format is `ResponseTime` instead of both for non-AO backend ([#172](https://github.com/solarwinds/apm-python/pull/172))

## [0.12.1](https://github.com/solarwinds/apm-python/releases/tag/rel-0.12.1) - 2023-06-13
### Added
- Add log warning when `set_transaction_name` with empty name ([#162](https://github.com/solarwinds/apm-python/pull/162))

### Changed
- Fix accepted config boolean values ([#166](https://github.com/solarwinds/apm-python/pull/166))

### Removed
- Removed unused log_trace_id config storage ([#163](https://github.com/solarwinds/apm-python/pull/163))
- Removed unused enable_sanitize_sql config storage ([#164](https://github.com/solarwinds/apm-python/pull/164))
- Removed unused is_grpc_clean_hack_enabled config storage ([#165](https://github.com/solarwinds/apm-python/pull/165))

## [0.12.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.12.0) - 2023-06-01
### Changed
- Bugfix: APM tracing disabled when platform not supported ([#153](https://github.com/solarwinds/apm-python/pull/153))
- Updated to liboboe version 12.3.1 ([#155](https://github.com/solarwinds/apm-python/pull/155))
- Verify Installation tests run on EC2 ([#156](https://github.com/solarwinds/apm-python/pull/156), [#160](https://github.com/solarwinds/apm-python/pull/160))
- Installation tests include Ubuntu 22 ([#158](https://github.com/solarwinds/apm-python/pull/158))

## [0.11.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.11.0) - 2023-05-25
### Added
- Added trace context to logging ([#146](https://github.com/solarwinds/apm-python/pull/146))

### Changed
- Adjusted config file logging ([#147](https://github.com/solarwinds/apm-python/pull/147))
- OpenTelemetry API/SDK 1.18.0 ([#150](https://github.com/solarwinds/apm-python/pull/150))
- Added Amazon 2023 install tests; removed Amazon 2018 and Amazon 2 install tests ([#151](https://github.com/solarwinds/apm-python/pull/151))


## [0.10.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.10.0) - 2023-05-01
### Added
- Add custom transaction filtering support ([#136](https://github.com/solarwinds/apm-python/pull/136), [#137](https://github.com/solarwinds/apm-python/pull/137), [#138](https://github.com/solarwinds/apm-python/pull/138), [#139](https://github.com/solarwinds/apm-python/pull/139), [#141](https://github.com/solarwinds/apm-python/pull/141))
- Add span attribute `sw.span_name` at export ([#143](https://github.com/solarwinds/apm-python/pull/143))

### Removed
- Removed unused prepend_domain_name config storage ([#140](https://github.com/solarwinds/apm-python/pull/140))

## [0.9.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.9.0) - 2023-04-20
### Changed
- OpenTelemetry API/SDK 1.17.0 ([#131](https://github.com/solarwinds/apm-python/pull/131))
- SolarWinds c-lib 12.2.0, to fix memory leak in extension ([#132](https://github.com/solarwinds/apm-python/pull/132))
- Adds support for `SW_APM_CONFIG_FILE` ([#133](https://github.com/solarwinds/apm-python/pull/133))
- Updates Span Layer to be `<KIND>:<NAME>` ([#134](https://github.com/solarwinds/apm-python/pull/134))

## [0.8.3](https://github.com/solarwinds/apm-python/releases/tag/rel-0.8.3) - 2023-03-21
### Changed
- Bugfix: fixed errors at API `set_transaction_name` calls when APM library tracing disabled ([#126](https://github.com/solarwinds/apm-python/pull/126))
- SolarWinds c-lib 12.1.0, for enhanced metadata retrieval, skipping metrics HTTP status if unavailable, fixed threading locking issue ([#127](https://github.com/solarwinds/apm-python/pull/127))

## [0.8.2](https://github.com/solarwinds/apm-python/releases/tag/rel-0.8.2) - 2023-03-13
### Changed
- Bugfix: fixed noisy trace state KV deletion attempts when key not present ([#121](https://github.com/solarwinds/apm-python/pull/121))
- Bugfix: fixed version lookup failures for instrumented aiohttp library ([#122](https://github.com/solarwinds/apm-python/pull/122))

## [0.8.1](https://github.com/solarwinds/apm-python/releases/tag/rel-0.8.1) - 2023-03-08
### Changed
- Fixed installation from source distribution ([#119](https://github.com/solarwinds/apm-python/pull/119))

## [0.8.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.8.0) - 2023-02-28

### Added
- Add `set_transaction_name` API method ([#115](https://github.com/solarwinds/apm-python/pull/115))

### Changed
- Deprecated `solarwinds_apm.apm_ready.solarwinds_ready`. Instead, use `solarwinds_apm.api.solarwinds_ready`. ([#115](https://github.com/solarwinds/apm-python/pull/115))
- OpenTelemetry API/SDK 1.16.0 ([#116](https://github.com/solarwinds/apm-python/pull/116))
- OpenTelemetry Instrumentation 0.37b0 ([#116](https://github.com/solarwinds/apm-python/pull/116))

## [0.7.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.7.0) - 2023-02-22

### Added
- Add ARM support ([#111](https://github.com/solarwinds/apm-python/pull/111))

### Changed
- Updated CodeQL scans ([#112](https://github.com/solarwinds/apm-python/pull/112))

## [0.6.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.6.0) - 2023-02-08
### Changed
- SolarWinds c-lib 12.0.0, for gRPC upgrade ([#107](https://github.com/solarwinds/apm-python/pull/107))
- Bugfix: fix version lookup failures for instrumented ASGI libraries ([#108](https://github.com/solarwinds/apm-python/pull/108))

### Removed
- Drop centos7 support ([#107](https://github.com/solarwinds/apm-python/pull/107))
- Drop Debian 9 support ([#107](https://github.com/solarwinds/apm-python/pull/107))
- Drop Amazon Linux 2018.03 support ([#107](https://github.com/solarwinds/apm-python/pull/107))

## [0.5.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.5.0) - 2023-01-18
### Added
- Add support for OTEL_SERVICE_NAME, OTEL_RESOURCE_ATTRIBUTES environment variables ([#90](https://github.com/solarwinds/apm-python/pull/90))
- Add prioritization of OTEL_SERVICE_NAME, OTEL_RESOURCE_ATTRIBUTES, SW_APM_SERVICE_KEY for setting service.name ([#103](https://github.com/solarwinds/apm-python/pull/103))

### Changed
- Update Init message with HostID ([#90](https://github.com/solarwinds/apm-python/pull/90))
- Update Init message with Python framework versions ([#94](https://github.com/solarwinds/apm-python/pull/94), [#100](https://github.com/solarwinds/apm-python/pull/100))
- SolarWinds c-lib 11.1.0, for Init message updates ([#90](https://github.com/solarwinds/apm-python/pull/90))
- Updated exported spans with Python framework versions ([#92](https://github.com/solarwinds/apm-python/pull/92))
- Bugfix: existing attributes without parent context now write to spans ([#102](https://github.com/solarwinds/apm-python/pull/102))
- Bugfix: setting sw.tracestate_parent_id is based on existence of remote parent span ([#102](https://github.com/solarwinds/apm-python/pull/102))
- Fix install tests on Ubuntu with Python 3.10/3.11 using older setuptools version ([#104](https://github.com/solarwinds/apm-python/pull/104))

## [0.4.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.4.0) - 2023-01-03
### Added
- Add security policy ([#95](https://github.com/solarwinds/apm-python/pull/95))
- Add issue templates ([#96](https://github.com/solarwinds/apm-python/pull/96/files))

### Changed
- OpenTelemetry API/SDK 1.15.0 ([#91](https://github.com/solarwinds/apm-python/pull/91))
- OpenTelemetry Instrumentation 0.36b0 ([#91](https://github.com/solarwinds/apm-python/pull/91))
- x-trace-options header `custom-*` KVs written to entry span attributes ([#85](https://github.com/solarwinds/apm-python/pull/85))
- Fix `x-trace-options-signature` extraction ([#85](https://github.com/solarwinds/apm-python/pull/85))
- Fix validation of `x-trace-options` header ([#87](https://github.com/solarwinds/apm-python/pull/87))
- Fix calculation of `x-trace-options-response` header ([#88](https://github.com/solarwinds/apm-python/pull/88))
- Update GH organization ([#96](https://github.com/solarwinds/apm-python/pull/96/files))

## [0.3.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.3.0) - 2022-11-24
### Changed
- Fix flake8 and installation tests ([#83](https://github.com/solarwinds/apm-python/pull/83))

## [0.2.2](https://github.com/solarwinds/apm-python/releases/tag/rel-0.2.2) - 2022-11-24
### Added
- Added integration tests ([#67](https://github.com/solarwinds/apm-python/pull/67))
- Added sdist and wheel extension file checks as part of library packaging ([#75](https://github.com/solarwinds/apm-python/pull/75))
- Added linting and code formatting ([#80](https://github.com/solarwinds/apm-python/pull/80), [#82](https://github.com/solarwinds/apm-python/pull/82))

### Changed
- OpenTelemetry API/SDK 1.14.0 ([#76](https://github.com/solarwinds/apm-python/pull/76))
- OpenTelemetry Instrumentation 0.35b0 ([#76](https://github.com/solarwinds/apm-python/pull/76))
- Reformatted code based on linting rules ([#81](https://github.com/solarwinds/apm-python/pull/81))
- Fixed changelog links ([#78](https://github.com/solarwinds/apm-python/pull/78))

## [0.2.1](https://github.com/solarwinds/apm-python/releases/tag/rel-0.2.1) - 2022-11-08
### Changed
- Version bump for rebuild of 0.2.0 ([#73](https://github.com/solarwinds/apm-python/pull/73))

## [0.2.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.2.0) - 2022-11-07
### Added
- Added `solarwinds_ready` method ([#64](https://github.com/solarwinds/apm-python/pull/64))
- Added startup `__Init` with SWO ([#64](https://github.com/solarwinds/apm-python/pull/64))
- Added more unit tests ([#68](https://github.com/solarwinds/apm-python/pull/68))

### Changed
- SolarWinds c-lib 11.0.0, for AppOptics certificate compatibility ([#70](https://github.com/solarwinds/apm-python/pull/70))
- Fixed logging vulnerabilities ([#63](https://github.com/solarwinds/apm-python/pull/63))
- Update packaging and install tests ([#71](https://github.com/solarwinds/apm-python/pull/71))

## [0.1.0](https://github.com/solarwinds/apm-python/releases/tag/rel-0.1.0) - 2022-10-13
### Added
- Initial release for GA (alpha)
- OpenTelemetry API/SDK 1.13.0, for trace generation
- OpenTelemetry Instrumentation 0.34b0, for (auto-)instrumentation of common Python frameworks
- SolarWinds c-lib 10.6.1, for unified inbound metrics generation, trace sample decision, and export to SWO
- W3C trace context propagation
- OTel, APM instrumentation startup, and trigger trace configurable with environment variables
