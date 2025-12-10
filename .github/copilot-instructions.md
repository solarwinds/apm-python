## GitHub Copilot Instructions

### Priority Guidelines

When generating code for this repository:

1. **Context Files**: Prioritize patterns and standards defined in the 
   .github/instructions directory
   - For all Python files at *.py, follow 
     .github/instructions/python.instructions.md.
2. **Codebase Patterns**: When context files don't provide specific guidance, 
   scan the codebase for established patterns
3. **Architectural Consistency**: Maintain our OpenTelemetry distribution 
   architecture and established SDK component patterns
4. **Code Quality**: Prioritize maintainability, performance, security, and 
   testability in all generated code

### Technology Version Detection

Before generating code, scan the codebase to identify:

1. **Python Versions**: This project supports Python 3.9-3.13
   - Use Python 3.9 compatible features for maximum compatibility

2. **Key Dependencies**: Note the exact versions of libraries
   - OpenTelemetry API, SDK, and instrumentation packages (see pyproject.toml)
   - This is a custom OpenTelemetry distribution for SolarWinds APM

### Context Files

Always use the following files in .github/instructions directory:

- **python.instructions.md**: Python-specific coding standards and 
  conventions, for all Python files at *.py

### Codebase Scanning Instructions

Only if context files don't provide specific guidance:

1. Identify similar files to the one being modified or created
2. Analyze patterns in existing code for consistency
3. When conflicting patterns exist, prioritize style preferences in this order 
   of precedence: context files, patterns in newer files.

### Project-Specific Patterns

#### Application Structure
This is the **solarwinds-apm** Python distribution package:
- Main package resides in `solarwinds_apm/` directory
- Core modules include: distro, configurator, sampler, propagator, 
  tracer_provider, apm_config
- Entry points defined in pyproject.toml for OpenTelemetry integration:
  - `opentelemetry_distro`: SolarWindsDistro
  - `opentelemetry_configurator`: SolarWindsConfigurator
  - `opentelemetry_propagator`: SolarWindsPropagator
  - `opentelemetry_traces_sampler`: ParentBasedSwSampler
  - `opentelemetry_resource_detector`: uams, k8s
- Lambda-specific code in `lambda/` directory
- Tests organized in `tests/unit/` and `tests/integration/`

#### OpenTelemetry Distribution Architecture
**Critical**: This is an OpenTelemetry distribution that extends the upstream 
SDK. Follow established patterns:

```python
# Distro pattern - configures environment variables
class SolarWindsDistro(BaseDistro):
    def _configure(self, **kwargs):
        # Set default OTEL environment variables
        # Configure propagators, exporters, resource detectors
        pass

# Configurator pattern - initializes SDK components
class SolarWindsConfigurator(_OTelSDKConfigurator):
    def _configure(self, **kwargs):
        # Initialize tracer provider with custom components
        # Configure sampler, processors, exporters
        # Initialize metrics and logging
        pass
```

#### Configuration Management
- Central configuration in `SolarWindsApmConfig` class
- Reads environment variables with `SW_APM_` prefix
- Supports both SolarWinds-specific and standard OTEL_ variables

#### Custom SDK Components

**Sampler Integration**:
- `ParentBasedSwSampler`: Custom sampler that integrates with SolarWinds backend

**Span Processors**:
- `ServiceEntrySpanProcessor`: Identifies service entry spans
- `ResponseTimeProcessor`: Calculates response times

**Propagators**:
- `SolarWindsPropagator`: Custom trace context propagation
- `SolarWindsTraceResponsePropagator`: Response header propagation

#### Error Handling Patterns
- Always validate configuration before SDK initialization
- Gracefully handle missing or invalid configuration
- Log warnings for configuration issues, errors for critical failures
- Use try/except for external service communication

```python
try:
    # SDK initialization or backend communication
    pass
except Exception as e:
    logger.error("Failed to initialize: %s", str(e))
    # Provide fallback behavior
```

#### Environment Variables
The agent supports both SolarWinds-specific (`SW_APM_*`) and standard OpenTelemetry 
(`OTEL_*`) environment variables for configuration. For a complete list of supported 
environment variables and their descriptions, see the 
[SolarWinds APM Python Configuration Documentation](https://documentation.solarwinds.com/en/success_center/observability/content/configure/services/python/configure.htm).

#### Testing Approach

**Unit Testing**:
- Located in `tests/unit/` organized by module
- Use pytest with mocker for mocking dependencies
- Test configuration, SDK components, and utility functions
- Mock external dependencies (liboboe, HTTP clients)

```python
class TestSolarWindsConfigurator:
    def test_configure_tracer_provider(self, mocker):
        # Mock dependencies
        mock_provider = mocker.Mock()
        # Test configurator behavior
        configurator = SolarWindsConfigurator()
        configurator._configure()
        # Assert expected behavior
```

**Integration Testing**:
- Located in `tests/integration/`
- Test end-to-end SDK initialization and trace generation
- Use InMemorySpanExporter for trace verification
- Test propagation and sampling behavior

#### Docker Integration
- Development container defined in docker-compose.yml
- Based on PyPA manylinux images (x86_64 and aarch64)
- Volume mounting for development: `./:/code`
- Testing in containerized environment

### Code Quality Standards

#### Performance
- Minimize overhead in SDK initialization and trace processing
- Use efficient data structures for context propagation
- Avoid blocking operations in hot paths
- Follow OpenTelemetry SDK performance best practices

#### Security
- Validate and sanitize configuration inputs
- Handle service keys securely, never log sensitive data
- Use secure defaults for collector communication (HTTPS)
- Follow OWASP guidelines for external service communication

### Project-Specific Guidance

- **Primary Purpose**: OpenTelemetry distribution for SolarWinds APM backend
- **Architecture**: Custom distro extending OTel SDK with SolarWinds-specific 
  components
- **Core Technology**: OpenTelemetry SDK with custom sampler, propagators, and 
  processors
- **Backend Integration**: Communicates with SolarWinds APM backend for 
  sampling and configuration
- **Testing**: Comprehensive unit and integration tests using pytest
- **Deployment**: Published to PyPI as `solarwinds-apm` package

### File-Type Specific Instructions

For detailed file-type specific guidance, refer to:
- `.github/instructions/python.instructions.md` for Python code standards, 
  for all Python files at *.py

These files provide comprehensive language-specific guidelines that should be 
followed in addition to the repository-specific patterns documented above.
