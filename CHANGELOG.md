# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/solarwinds/apm-python/compare/rel-4.3.0...HEAD)

## [4.3.0](https://github.com/solarwinds/apm-python/releases/tag/rel-4.3.0) - 2025-08-07

### Changed
- Updated configurator Resource creation with `service.instance.id` ([#666](https://github.com/solarwinds/apm-python/pull/666))
- Updated Lambda layer tags and testing for Python 3.13 ([#667](https://github.com/solarwinds/apm-python/pull/667))
- Upgraded to OTel Python 1.35.0/0.56b0 ([#668](https://github.com/solarwinds/apm-python/pull/668))
- Cleaned up constants ([#669](https://github.com/solarwinds/apm-python/pull/669))
- Upgraded to OTel Python 1.36.0/0.57b0 ([#672](https://github.com/solarwinds/apm-python/pull/672))

## [4.2.0](https://github.com/solarwinds/apm-python/releases/tag/rel-4.2.0) - 2025-07-15

### Changed
- Updated default histogram aggregation to exponential ([#650](https://github.com/solarwinds/apm-python/pull/650))
- Upgraded to OTel Python 1.34.1/0.55b1 ([#657](https://github.com/solarwinds/apm-python/pull/657))
- Removed unnecessary try-except when auto-instrumentation handles all exceptions ([#660](https://github.com/solarwinds/apm-python/pull/660))
- Updated pylint max-positional-arguments ([#661](https://github.com/solarwinds/apm-python/pull/661))

## [4.1.0](https://github.com/solarwinds/apm-python/releases/tag/rel-4.1.0) - 2025-05-21

### Added
- Added local installation option to Verify Install CI/CD ([#635](https://github.com/solarwinds/apm-python/pull/635))
- Added Windows coverage to Verify Install CI/CD ([#636](https://github.com/solarwinds/apm-python/pull/636))
- Added macOS coverage to Verify Install CI/CD ([#637](https://github.com/solarwinds/apm-python/pull/637))
- Added `psutil` dependency ([#629](https://github.com/solarwinds/apm-python/pull/629))

### Changed
- Simplify Lambda builds ([#630](https://github.com/solarwinds/apm-python/pull/630))
- Simplify Verify Install CI/CD ([#633](https://github.com/solarwinds/apm-python/pull/633))
- Fixed function signature ([#634](https://github.com/solarwinds/apm-python/pull/634))
- Fixed sampling/response time metrics descriptions ([#639](https://github.com/solarwinds/apm-python/pull/639), [#640](https://github.com/solarwinds/apm-python/pull/640))
- Updated Verify Install CI/CD, requirements for system-metrics ([#629](https://github.com/solarwinds/apm-python/pull/629), [#638](https://github.com/solarwinds/apm-python/pull/638), [#641](https://github.com/solarwinds/apm-python/pull/641))
- Upgraded to OpenTelemetry 1.33.1/0.54b1 ([#644](https://github.com/solarwinds/apm-python/pull/644))
- Changed `psutil` dependency ([#638](https://github.com/solarwinds/apm-python/pull/638))

### Removed
- Removed system-metrics default instrumentation in k8s ([#642](https://github.com/solarwinds/apm-python/pull/642))
- Removed `psutil` dependency ([#641](https://github.com/solarwinds/apm-python/pull/641))

## [4.0.0](https://github.com/solarwinds/apm-python/releases/tag/rel-4.0.0) - 2025-04-29

### Breaking changes

- Breaking: APM Python is now pure Python ([#556](https://github.com/solarwinds/apm-python/pull/556))
- Breaking: Removed c-lib extension and legacy components ([#549](https://github.com/solarwinds/apm-python/pull/549), [#612](https://github.com/solarwinds/apm-python/pull/612), [#614](https://github.com/solarwinds/apm-python/pull/614))
- Breaking: Removed discontinued OboeAPI ([#565](https://github.com/solarwinds/apm-python/pull/565))
- Breaking: Changed SolarWindsSpanExporter to no-op for future removal ([#572](https://github.com/solarwinds/apm-python/pull/572))
- Breaking: Changed default export protocol to OTLP HTTP for all signals ([#580](https://github.com/solarwinds/apm-python/pull/580))
- Breaking: Removed legacy configuration logic ([#570](https://github.com/solarwinds/apm-python/pull/570), [#571](https://github.com/solarwinds/apm-python/pull/571), [#583](https://github.com/solarwinds/apm-python/pull/583))
- Breaking: AWS Lambda builds without architecture in layer name ([#594](https://github.com/solarwinds/apm-python/pull/594))
- Breaking: Removed discontinued grpcio-using dependencies from Lambda builds ([#591](https://github.com/solarwinds/apm-python/pull/591))
- Breaking: Updated local development setup for pure Python ([#603](https://github.com/solarwinds/apm-python/pull/603))

### Added

- Added ApmConfig mapping for pure Python sampler ([#552](https://github.com/solarwinds/apm-python/pull/552), [#589](https://github.com/solarwinds/apm-python/pull/589))
- Added pure Python transaction name pool ([#559](https://github.com/solarwinds/apm-python/pull/559))
- Added suppression of tracing when HTTP getSettings ([#560](https://github.com/solarwinds/apm-python/pull/560))
- Added resource detection for AWS, Azure, Kubernetes, UAMS written to resource attributes ([#577](https://github.com/solarwinds/apm-python/pull/577), [#596](https://github.com/solarwinds/apm-python/pull/596))
- Added internal deduction of export endpoint from SW_APM_COLLECTOR ([#590](https://github.com/solarwinds/apm-python/pull/590), [#602](https://github.com/solarwinds/apm-python/pull/602))

### Changed

- Updated custom transaction naming as pure Python ([#558](https://github.com/solarwinds/apm-python/pull/558))
- Simplified spankind check ([#561](https://github.com/solarwinds/apm-python/pull/561))
- Updated `http.route` assignment based on semconv ([#562](https://github.com/solarwinds/apm-python/pull/562))
- Updated to register NoOp provider if not exporting ([#566](https://github.com/solarwinds/apm-python/pull/566))
- Fixed counter metrics init ([#564](https://github.com/solarwinds/apm-python/pull/564))
- Refactored ResponseTime metrics and request counters ([#563](https://github.com/solarwinds/apm-python/pull/563), [#567](https://github.com/solarwinds/apm-python/pull/567), [#568](https://github.com/solarwinds/apm-python/pull/568))
- Fixed transaction name environment config support ([#569](https://github.com/solarwinds/apm-python/pull/569))
- Redesigned custom Configurator ([#578](https://github.com/solarwinds/apm-python/pull/578), [#581](https://github.com/solarwinds/apm-python/pull/581))
- Updated `solarwinds_ready` API function for pure Python ([#582](https://github.com/solarwinds/apm-python/pull/582), [#584](https://github.com/solarwinds/apm-python/pull/584), [#599](https://github.com/solarwinds/apm-python/pull/599))
- Updated Lambda dependencies and builds for resource detection ([#593](https://github.com/solarwinds/apm-python/pull/593))
- Fixed Configurator exporter loading to prevent ImportError ([#592](https://github.com/solarwinds/apm-python/pull/592))
- Updated smoke tests / verify_install for pure Python ([#595](https://github.com/solarwinds/apm-python/pull/595))
- Updated PyPI sdist, wheel publishes in pure Python ([#597](https://github.com/solarwinds/apm-python/pull/597))
- Update autoinstrumentation-python image builds for pure Python, beta testing ([#598](https://github.com/solarwinds/apm-python/pull/598))
- Updated default OTel export header assignment for SWO vs other ([#601](https://github.com/solarwinds/apm-python/pull/601))
- Fixed HttpSampler warning message ([#604](https://github.com/solarwinds/apm-python/pull/604))
- Fixed `sw.w3c.tracestate` attribute assignment ([#606](https://github.com/solarwinds/apm-python/pull/606))
- Updated integration tests ([#605](https://github.com/solarwinds/apm-python/pull/605))
- Updated units, descriptions of APM counters ([#608](https://github.com/solarwinds/apm-python/pull/608))
- Updated sampler init ([#609](https://github.com/solarwinds/apm-python/pull/609))
- Updated `SW_APM_LOG_FILEPATH` support for Pure Python ([#613](https://github.com/solarwinds/apm-python/pull/613))
- Fixed tracestate KV deletion ([#617](https://github.com/solarwinds/apm-python/pull/617))

### Removed

- Removed warning log for Lambda mode ([#600](https://github.com/solarwinds/apm-python/pull/600))
- Removed unnecessary tests ([#611](https://github.com/solarwinds/apm-python/pull/611), [#610](https://github.com/solarwinds/apm-python/pull/610), [#615](https://github.com/solarwinds/apm-python/pull/615))
- Removed setup.py usage for builds ([#616](https://github.com/solarwinds/apm-python/pull/616))

## [3.6.0](https://github.com/solarwinds/apm-python/releases/tag/rel-3.6.0) - 2025-04-07

### Breaking changes
- Breaking: SWO metrics is now enabled by default if configured for OTLP; `SW_APM_EXPORT_METRICS_ENABLED` limits instrumentor metrics only ([#551](https://github.com/solarwinds/apm-python/pull/551))

### Added
- Added baseline components for custom pure Python sampling ([#534](https://github.com/solarwinds/apm-python/pull/534))

### Changed
- Fixed OTLP logging component init ([#550](https://github.com/solarwinds/apm-python/pull/550))
- Upgraded Otel Python 1.31.1/0.52b1 ([#553](https://github.com/solarwinds/apm-python/pull/553))
- Fixed dependabot CI/CD ([#554](https://github.com/solarwinds/apm-python/pull/554))
- Updated OTLP exporter compression to be gzip by default ([#573](https://github.com/solarwinds/apm-python/pull/573))
- Updated all meters preferred aggregation temporality to be Delta ([#574](https://github.com/solarwinds/apm-python/pull/574))
- Fixed image CI/CD ([#575](https://github.com/solarwinds/apm-python/pull/575))

## [3.5.0](https://github.com/solarwinds/apm-python/releases/tag/rel-3.5.0) - 2025-03-14

### Changed
- Updated image builds and scans ([#529](https://github.com/solarwinds/apm-python/pull/529), [#531](https://github.com/solarwinds/apm-python/pull/531), [#535](https://github.com/solarwinds/apm-python/pull/535), [#537](https://github.com/solarwinds/apm-python/pull/537))
- Fixed warning message at boto3 lookup during APM export ([#539](https://github.com/solarwinds/apm-python/pull/539))
- Fixed custom propagator to support boto3, botocore instrumentation injection ([#540]https://github.com/solarwinds/apm-python/pull/540)

## [3.4.0](https://github.com/solarwinds/apm-python/releases/tag/rel-3.4.0) - 2025-02-18

### Added
- Added autoinstrumentation image publishing ([#481](https://github.com/solarwinds/apm-python/pull/481), [#490](https://github.com/solarwinds/apm-python/pull/490), [#520](https://github.com/solarwinds/apm-python/pull/520), [#523](https://github.com/solarwinds/apm-python/pull/523))
- Added support for `SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE` ([#524](https://github.com/solarwinds/apm-python/pull/524))

### Changed
- Fixed PyPI publishing ([#488](https://github.com/solarwinds/apm-python/pull/488))
- Fixed version lookup logs ([#489](https://github.com/solarwinds/apm-python/pull/489))
- Changed exporter header defaults ([#494](https://github.com/solarwinds/apm-python/pull/494))
- Make service_key updates more general ([#496](https://github.com/solarwinds/apm-python/pull/496))
- Fixed AttributeError if Propagators None ([#501](https://github.com/solarwinds/apm-python/pull/501))
- Fixed test mocks ([#502](https://github.com/solarwinds/apm-python/pull/502))
- Upgraded to OpenTelemetry Python 1.30.0/0.51b0 ([#521](https://github.com/solarwinds/apm-python/pull/521))

### Removed
- Removed support of deprecated `OTEL_SQLCOMMENTER_ENABLED` and `OTEL_SQLCOMMENTER_OPTIONS` ([#522](https://github.com/solarwinds/apm-python/pull/522))

## [3.3.2](https://github.com/solarwinds/apm-python/releases/tag/rel-3.3.2) - 2025-01-06

### Changed
- Updated error reporting to SWO ([#470](https://github.com/solarwinds/apm-python/pull/470))

## [3.3.1](https://github.com/solarwinds/apm-python/releases/tag/rel-3.3.1) - 2024-11-21

### Changed
- Upgraded OpenTelemetry API/SDK and instrumentation 1.28.2/0.49b2 ([#459](https://github.com/solarwinds/apm-python/pull/459))

## [3.3.0](https://github.com/solarwinds/apm-python/releases/tag/rel-3.3.0) - 2024-11-14

### Changed
- Fixed CodeQL warnings ([#445](https://github.com/solarwinds/apm-python/pull/445), [#446](https://github.com/solarwinds/apm-python/pull/446))
- Upgraded OpenTelemetry API/SDK and instrumentation 1.28.1/0.49b1, remove `pkg_resources` usage ([#450](https://github.com/solarwinds/apm-python/pull/450))

## [3.2.0](https://github.com/solarwinds/apm-python/releases/tag/rel-3.2.0) - 2024-10-08

### Added
- Added support for `SW_APM_EXPORT_METRICS_ENABLED` ([#439](https://github.com/solarwinds/apm-python/pull/439))

## [3.1.0](https://github.com/solarwinds/apm-python/releases/tag/rel-3.1.0) - 2024-10-01

### Added
- Added linting for all supported Python versions ([#428](https://github.com/solarwinds/apm-python/pull/428))
- Added support for `SW_APM_ENABLED_SQLCOMMENT`, `SW_APM_OPTIONS_SQLCOMMENT`([#434](https://github.com/solarwinds/apm-python/pull/434), [#437](https://github.com/solarwinds/apm-python/pull/437))

### Changed
- Fixed AwsLambdaInstrumentor loading in Lambda environment ([#430](https://github.com/solarwinds/apm-python/pull/430))
- Fixed code style ([#433](https://github.com/solarwinds/apm-python/pull/433))
- Deprecated `OTEL_SQLCOMMENTER_ENABLED`, `OTEL_SQLCOMMENTER_OPTIONS` ([#434](https://github.com/solarwinds/apm-python/pull/434))

## [3.0.0](https://github.com/solarwinds/apm-python/releases/tag/rel-3.0.0) - 2024-09-04

### Added
- Added Python 3.12 support ([#422](https://github.com/solarwinds/apm-python/pull/422))
- Added ReversingLabs scan before publishes ([#420](https://github.com/solarwinds/apm-python/pull/420))

### Changed
- Upgraded OpenTelemetry API/SDK and instrumentation 1.27.0/0.48b0 ([#422](https://github.com/solarwinds/apm-python/pull/422))
- Skip logs_headers setdefault in lambda ([#425](https://github.com/solarwinds/apm-python/pull/425))

### Reverted
- Reverted distro doing setdefault to disable AwsLambdaInstrumentor if outside Lambda, because of update in Otel 1.27.0/0.48b0 ([#422](https://github.com/solarwinds/apm-python/pull/422))

## [2.2.0](https://github.com/solarwinds/apm-python/releases/tag/rel-2.2.0) - 2024-08-12

### Added
- Added OTLP logs export support ([#393](https://github.com/solarwinds/apm-python/pull/393), [#394](https://github.com/solarwinds/apm-python/pull/394), [#400](https://github.com/solarwinds/apm-python/pull/400))
- Added Python 3.12 support ([#401](https://github.com/solarwinds/apm-python/pull/401), [#406](https://github.com/solarwinds/apm-python/pull/406))

### Changed
- Upgraded OpenTelemetry API/SDK and instrumentation 1.26.0/0.47b0 ([#398](https://github.com/solarwinds/apm-python/pull/398), [#406](https://github.com/solarwinds/apm-python/pull/406))
- Distro does setdefault to disable AwsLambdaInstrumentor if outside Lambda ([#405](https://github.com/solarwinds/apm-python/pull/405))

### Reverted
- Reverted upgrade OpenTelemetry API/SDK and instrumentation 1.26.0/0.47b0 because of FastAPI instrumentation bug it introduces ([#406](https://github.com/solarwinds/apm-python/pull/406))
- Reverted add of Python 3.12 support because of revert of API/SDK upgrade ([#406](https://github.com/solarwinds/apm-python/pull/406))

## [2.1.0](https://github.com/solarwinds/apm-python/releases/tag/rel-2.1.0) - 2024-07-17

### Changed
- Move builds and tests to gh `apm-arm-runner` ([#385](https://github.com/solarwinds/apm-python/pull/385))
- Don't inject baggage header if empty ([#386](https://github.com/solarwinds/apm-python/pull/386))
- Always unset local token bucket capacity/rate ([#388](https://github.com/solarwinds/apm-python/pull/388))

## [2.0.0](https://github.com/solarwinds/apm-python/releases/tag/rel-2.0.0) - 2024-06-18

### Changed
- Upgraded OpenTelemetry API/SDK and instrumentation 1.25.0/0.46b0 ([#364](https://github.com/solarwinds/apm-python/pull/364), [#375](https://github.com/solarwinds/apm-python/pull/375/files), [#376](https://github.com/solarwinds/apm-python/pull/376), [#377](https://github.com/solarwinds/apm-python/pull/377), [#380](https://github.com/solarwinds/apm-python/pull/380))
- Fixed version lookups at APM startup ([#378](https://github.com/solarwinds/apm-python/pull/378))
- Upgraded c-lib 15.0.1 ([#379](https://github.com/solarwinds/apm-python/pull/379))

### Removed
- Removed docker-compose version keys ([#381](https://github.com/solarwinds/apm-python/pull/381))

## [1.7.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.7.0) - 2024-05-16

### Changed
- Fixed log duplication ([#357](https://github.com/solarwinds/apm-python/pull/357))
- Refactored sampler ([#359](https://github.com/solarwinds/apm-python/pull/359))
- Removed debug line ([#360](https://github.com/solarwinds/apm-python/pull/360))
- Sampler inits with APM-proto exporter ([#366](https://github.com/solarwinds/apm-python/pull/366))
- Fixed APM-proto export for non-scalar attribute types ([#367](https://github.com/solarwinds/apm-python/pull/367))

## [1.6.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.6.0) - 2024-04-02

### Added
- Added layer production workflow ([#341](https://github.com/solarwinds/apm-python/pull/341))
- Added `check_lambda_modules` before publish ([#346](https://github.com/solarwinds/apm-python/pull/346))

### Changed
- Upgraded layer asgiref 3.8 ([#343](https://github.com/solarwinds/apm-python/pull/343))
- Fixed init event logging ([#345](https://github.com/solarwinds/apm-python/pull/345))
- Upgraded layer grpcio 1.62.1 ([#351](https://github.com/solarwinds/apm-python/pull/351))
- Upgraded c-lib 14.1.0 ([#352](https://github.com/solarwinds/apm-python/pull/352))

## [1.5.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.5.0) - 2024-03-18

### Added
- Added more `sw` resource attributes to metrics ([#327](https://github.com/solarwinds/apm-python/pull/327))
- Added default disabling of AWS context propagation ([#333](https://github.com/solarwinds/apm-python/pull/333))

### Changed
- Fixed grpcio ImportError if outside Python 3.8 ([#326](https://github.com/solarwinds/apm-python/pull/326))
- Improve `load_instrumentor` error logging ([#332](https://github.com/solarwinds/apm-python/pull/332))
- Fixed APM-proto reporter status logging ([#336](https://github.com/solarwinds/apm-python/pull/336))

## [1.4.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.4.0) - 2024-03-04

### Changed
- SolarWinds c-lib 14.0.3 ([#316](https://github.com/solarwinds/apm-python/pull/316))
- Update layer exec wrapper ([#317](https://github.com/solarwinds/apm-python/pull/317))
- Non-empty `http.*` attributes on metrics ([#319](https://github.com/solarwinds/apm-python/pull/319))
- Add formatter to RotatingFileHander ([#320](https://github.com/solarwinds/apm-python/pull/320))
- Fixed `sw.is_error` attribute type ([#321](https://github.com/solarwinds/apm-python/pull/321))
- Update CI role ([#324](https://github.com/solarwinds/apm-python/pull/324))

### Removed
- Remove ForceFlushSpanProcessor ([#312](https://github.com/solarwinds/apm-python/pull/312))

## [1.3.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.3.0) - 2024-02-20

### Changed
- Fixed release_pr script ([#302](https://github.com/solarwinds/apm-python/pull/302))
- OTLP traces, metrics `sw.transaction` attribute with environment customization ([#307](https://github.com/solarwinds/apm-python/pull/307))
- Fixed service key, service name usage ([#309](https://github.com/solarwinds/apm-python/pull/309))
- Fixed exporter defaults based on protocol ([#310](https://github.com/solarwinds/apm-python/pull/310))
- Updated workflow dependency ([#304](https://github.com/solarwinds/apm-python/pull/304))

### Removed
- Removed `experimental` config support ([#308](https://github.com/solarwinds/apm-python/pull/308))

## [1.2.0](https://github.com/solarwinds/apm-python/releases/tag/rel-1.2.0) - 2024-02-05

### Changed
- Updated OTLP metrics components initialization ([#289](https://github.com/solarwinds/apm-python/pull/289))
- Fixed no-op function signature ([#295](https://github.com/solarwinds/apm-python/pull/295))
- Set histogram preferred temporality to delta ([#296](https://github.com/solarwinds/apm-python/pull/296))
- Set Periodic metric reading interval infinity ([#297](https://github.com/solarwinds/apm-python/pull/297))
- Fixed response_time metrics for milliseconds ([#298](https://github.com/solarwinds/apm-python/pull/298))
- Renamed local variables ([#300](https://github.com/solarwinds/apm-python/pull/300))

### Removed
- Removed meters for sample_rate, sample_source ([#299](https://github.com/solarwinds/apm-python/pull/299))

## [1.1.1](https://github.com/solarwinds/apm-python/releases/tag/rel-1.1.1) - 2024-01-31

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
