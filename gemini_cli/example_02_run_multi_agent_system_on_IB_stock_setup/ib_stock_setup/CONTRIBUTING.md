# Contributing to IB Stock Trading Setup

Thank you for your interest in contributing to the IB Stock Trading Setup! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Pull Request Process](#pull-request-process)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Reporting Issues](#reporting-issues)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

- Use the GitHub issue tracker to report bugs
- Include detailed steps to reproduce the bug
- Provide your operating system and Python version
- Include any error messages or logs

### Suggesting Enhancements

- Use the GitHub issue tracker to suggest new features
- Describe the enhancement and its potential benefits
- Consider the impact on existing functionality

### Pull Requests

- Fork the repository
- Create a feature branch (`git checkout -b feature/amazing-feature`)
- Make your changes
- Add tests if applicable
- Update documentation
- Commit your changes (`git commit -m 'Add amazing feature'`)
- Push to the branch (`git push origin feature/amazing-feature`)
- Open a Pull Request

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/QuantInsti/Trading-setups.git
   cd Trading-setups/ib_stock_setup
   ```

2. **Create a virtual environment**
   ```bash
   conda create --name ib_stock_dev python=3.12
   conda activate ib_stock_dev
   ```

3. **Install development dependencies**
   ```bash
   # For development (editable install)
   pip install -e .
   
   # For regular users (wheel install)
   pip install dist/ib_stock_setup-1.0.0-py3-none-any.whl
   
   # Install testing tools
   pip install pytest black flake8 mypy
   ```

4. **Install Interactive Brokers API**
   - Download the IB API from Interactive Brokers
   - Install it in your development environment

## Pull Request Process

1. **Update the README.md** with details of changes if applicable
2. **Update the CHANGELOG.md** with a brief description of your changes
3. **Ensure the code follows the style guidelines**
4. **Add tests for new functionality**
5. **Update documentation** if you've changed any public APIs
6. **The PR will be merged once you have the sign-off** of at least one maintainer

## Code Style Guidelines

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and reasonably sized
- Use type hints where appropriate

### Example Code Style

```python
def calculate_position_size(
    account_value: float, 
    risk_percentage: float, 
    stop_loss_percentage: float
) -> int:
    """
    Calculate the position size based on account value and risk parameters.
    
    Args:
        account_value: Total account value in base currency
        risk_percentage: Percentage of account to risk (0.0 to 1.0)
        stop_loss_percentage: Stop loss as percentage of stock price
        
    Returns:
        Position size in shares
        
    Raises:
        ValueError: If risk_percentage is not between 0 and 1
    """
    if not 0 <= risk_percentage <= 1:
        raise ValueError("Risk percentage must be between 0 and 1")
    
    risk_amount = account_value * risk_percentage
    # Additional calculation logic here
    return position_size
```

### File Organization

- Keep related functionality in the same module
- Use clear, descriptive file names
- Organize imports: standard library, third-party, local imports
- Separate imports with blank lines

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/ib_stock_setup

# Run specific test file
pytest tests/test_trading_functions.py
```

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies (like IB API calls)
- Ensure tests are independent and repeatable

### Example Test

```python
import pytest
from src.ib_stock_setup.trading_functions import calculate_position_size

def test_calculate_position_size_valid_inputs():
    """Test position size calculation with valid inputs."""
    result = calculate_position_size(10000, 0.02, 0.02)
    assert result > 0
    assert isinstance(result, int)

def test_calculate_position_size_invalid_risk():
    """Test position size calculation with invalid risk percentage."""
    with pytest.raises(ValueError, match="Risk percentage must be between 0 and 1"):
        calculate_position_size(10000, 1.5, 0.02)
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google or NumPy docstring format
- Include examples for complex functions
- Document exceptions that may be raised

### User Documentation

- Update README.md for user-facing changes
- Update doc/ files for significant changes
- Include screenshots for UI changes
- Provide clear installation and usage instructions

## Reporting Issues

When reporting issues, please include:

1. **Environment Information**
   - Operating system and version
   - Python version
   - Interactive Brokers API version
   - Package versions (from `pip freeze`)

2. **Issue Description**
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs

3. **Additional Context**
   - Screenshots if applicable
   - Stock symbols being traded
   - Market conditions at the time
   - Any recent changes to configuration 