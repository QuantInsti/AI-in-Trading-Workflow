# Contributing to IB Stock Trading Setup

Thank you for your interest in contributing to the IB Stock Trading Setup! This document provides guidelines and information for you.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can You Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Pull Request Process](#pull-request-process)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Reporting Issues](#reporting-issues)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can You Contribute?

### Reporting Bugs

- You can use the GitHub issue tracker to report bugs.
- You should include detailed steps to reproduce the bug.
- You should provide your operating system and Python version.
- You should include any error messages or logs.

### Suggesting Enhancements

- You can use the GitHub issue tracker to suggest new features.
- You should describe the enhancement and its potential benefits.
- You should consider the impact on existing functionality.

### Pull Requests

- You should fork the repository.
- You should create a feature branch (`git checkout -b feature/amazing-feature`).
- You should make your changes.
- You should add tests if applicable.
- You should update documentation.
- You should commit your changes (`git commit -m 'Add amazing feature'`).
- You should push to the branch (`git push origin feature/amazing-feature`).
- You should open a Pull Request.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/QuantInsti/QuantInsti-Live-Algo-Trading-Setups.git
   cd Trading-setups/ibkr-stock
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
   
   # For regular usage (wheel install)
   pip install dist/ibkr-stock-1.0.0-py3-none-any.whl
   
   # Install testing tools
   pip install pytest black flake8 mypy
   ```

4. **Install Interactive Brokers API**
   - You should download the IB API from Interactive Brokers.
   - You should install it in your development environment.

## Pull Request Process

1. **You should update the README.md** with details of changes if applicable.
2. **You should ensure the code follows the style guidelines.**
3. **You should add tests for new functionality.**
4. **You should update documentation** if you've changed any public APIs.
5. **The PR will be merged once you have the sign-off** of at least one maintainer.

## Code Style Guidelines

### Python Code Style

- You should follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines.
- You should use meaningful variable and function names.
- You should add docstrings to all public functions and classes.
- You should keep functions focused and reasonably sized.
- You should use type hints where appropriate.

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

- You should keep related functionality in the same module.
- You should use clear, descriptive file names.
- You should organize imports: standard library, third-party, local imports.
- You should separate imports with blank lines.

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/ibkr-stock

# Run specific test file
pytest tests/test_trading_functions.py
```

### Writing Tests

- You should write tests for all new functionality.
- You should use descriptive test names.
- You should test both success and failure cases.
- You should mock external dependencies (like IB API calls).
- You should ensure tests are independent and repeatable.

### Example Test

```python
import pytest
from src.ibkr-stock.trading_functions import calculate_position_size

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

- You should add docstrings to all public functions and classes.
- You should use Google or NumPy docstring format.
- You should include examples for complex functions.
- You should document exceptions that may be raised.

### User Documentation

- You should update README.md for user-facing changes.
- You should update doc/ files for significant changes.
- You should include screenshots for UI changes.
- You should provide clear installation and usage instructions.

## Reporting Issues

When you report issues, please include:

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
   - Sample data or configuration
   - Any workarounds you've tried

## Security

- **You should not include sensitive information** in issues or pull requests.
- **You should not commit API keys, passwords, or account credentials.**
- You should report security vulnerabilities privately to the maintainers.

## Questions?

If you have questions about contributing, you should:

1. Check the existing documentation.
2. Search existing issues and pull requests.
3. Create a new issue with the "question" label.

Thank you for contributing to the IB Stock Trading Setup!