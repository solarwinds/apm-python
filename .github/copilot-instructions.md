## GitHub Copilot Instructions

### Priority Guidelines

When generating code for this repository:

1. **Context Files**: Follow `.github/instructions/python.instructions.md` for all Python files (*.py)
2. **Codebase Patterns**: Scan existing code for established patterns when context files don't provide guidance
3. **Architectural Consistency**: Maintain OpenTelemetry distribution architecture and SDK component patterns
4. **Code Quality**: Prioritize maintainability, performance, security, and testability

### Technology Stack

- **Python Versions**: 3.9-3.13 (use 3.9-compatible features for maximum compatibility)
- **Core Dependencies**: OpenTelemetry API, SDK, and instrumentation packages (see pyproject.toml)
- **Purpose**: Custom OpenTelemetry distribution for SolarWinds APM backend

### Project Structure

This is the **solarwinds-apm** Python distribution package:
- Main package: `solarwinds_apm/` (distro, configurator, sampler, propagator, tracer_provider, apm_config)
- Entry points in pyproject.toml: SolarWindsDistro, SolarWindsConfigurator, SolarWindsPropagator, ParentBasedSwSampler, resource detectors (uams, k8s)
- Lambda code: `lambda/` directory
- Tests: `tests/unit/` and `tests/integration/`

### OpenTelemetry Distribution Patterns

**Critical**: This extends the upstream OpenTelemetry SDK. Follow established patterns:

```python
# Distro: configures environment variables
class SolarWindsDistro(BaseDistro):
    def _configure(self, **kwargs):
        # Set OTEL environment variables, configure propagators/exporters/resource detectors

# Configurator: initializes SDK components
class SolarWindsConfigurator(_OTelSDKConfigurator):
    def _configure(self, **kwargs):
        # Initialize tracer provider, sampler, processors, exporters, metrics, logging
```

### Key Components

**Configuration**:
- `SolarWindsApmConfig`: Central configuration class
- Environment variables: `SW_APM_*` (SolarWinds-specific) and `OTEL_*` (standard)
- See [Configuration Documentation](https://documentation.solarwinds.com/en/success_center/observability/content/configure/services/python/configure.htm)

**Custom SDK Components**:
- `ParentBasedSwSampler`: Integrates with SolarWinds backend
- `ServiceEntrySpanProcessor`, `ResponseTimeProcessor`: Span processors
- `SolarWindsPropagator`, `SolarWindsTraceResponsePropagator`: Propagators

**Error Handling**:
- Validate configuration before SDK initialization
- Gracefully handle missing/invalid configuration
- Log warnings for config issues, errors for critical failures
- Use try/except for external service communication

**Testing**:
- Unit tests: `tests/unit/` (pytest with mocker, mock liboboe/HTTP clients)
- Integration tests: `tests/integration/` (InMemorySpanExporter, end-to-end validation)
- Lambda tests: `lambda/tests/`

**Development**:
- Docker containers: PyPA manylinux images (x86_64/aarch64)
- Volume mounting: `./:/code`

### Code Quality Standards

**Performance**: Minimize SDK overhead, use efficient data structures, avoid blocking in hot paths
**Security**: Validate inputs, never log sensitive data, use HTTPS defaults, follow OWASP guidelines

### Deployment

Published to PyPI as `solarwinds-apm` package. Maintains backward compatibility and semantic versioning.
