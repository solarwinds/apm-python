---
applyTo: "**/*.py"
description: 'Python coding conventions and guidelines'
---

## Python Coding Conventions

### Codebase Patterns to Follow

When scanning the codebase for patterns:

- **Naming conventions**: Use snake_case for variables/functions, PascalCase for classes
- **Import organization**: Group as standard library, third-party, local imports (separated by blank lines)
- **Error handling**: Use try/except blocks with specific exception types
- **Logging**: Use Python's logging module with module-level loggers
- **OpenTelemetry SDK**: Follow established patterns for SDK component integration

### Python Instructions

- Follow docstring conventions per PEP 257 at class and function level.
- Use the `typing` module for type annotations (e.g., `List[str]`, `Dict[str, int]`)
  if compatible with all supported Python versions and OpenTelemetry dependencies.
- Add type checks for all function parameters and return values.

### General Instructions

- Always prioritize readability and clarity.
- Write code with good maintainability practices, including comments on why certain
  design decisions were made.
- Handle edge cases and write clear exception handling.
- Use consistent naming conventions and follow language-specific best practices.

### Code Style and Formatting

- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation) and follow PEP 8 rules.
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Follow import organization as described in "Codebase Patterns to Follow" above.
- Order metrics and other code elements alphabetically within their respective groups.
- Use double quotes for all string literals and docstrings.
- Use blank lines to separate functions, classes, and code blocks where appropriate.
- Remove all trailing whitespaces.

### Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and 
  large datasets.
- Include comments for edge cases and the expected behavior in those cases.

### Example of Proper Documentation

```python
import math

def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.
    
    Parameters:
    radius (float): The radius of the circle.
    
    Returns:
    float: The area of the circle, calculated as π * radius**2.
    """
    return math.pi * radius ** 2
```
