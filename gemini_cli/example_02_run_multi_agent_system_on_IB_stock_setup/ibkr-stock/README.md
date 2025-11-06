# IB Stock Trading Setup

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: QOL v1.1](https://img.shields.io/badge/license-QOL%20v1.1-blue.svg)](../LICENSE.md)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)
[![Security](https://img.shields.io/badge/security-policy-brightgreen.svg)](SECURITY.md)
[![Code of Conduct](https://img.shields.io/badge/code%20of-conduct-ff69b4.svg)](CODE_OF_CONDUCT.md)

> A Python framework for automated stock trading using the Interactive Brokers API.

## Overview

This framework provides a complete algorithmic trading solution for stock markets using the Interactive Brokers API. It includes risk management, real-time data processing, and machine learning-powered strategy development capabilities.

## Key Features

### Core Trading Engine
- **Interactive Brokers API Integration:** Connects to the Interactive Brokers API for market data and trade execution.
- **Order and Position Management:** Includes functionality for automated order placement and position tracking.
- **Error Handling:** Provides a foundation for error handling and recovery in a live trading environment.

### Customizable Strategy Framework
- **Example Machine Learning Strategy:** Provides a sample strategy using a Random Forest algorithm to demonstrate the setup's capabilities.
- **Flexible and Customizable:** You are meant to modify or replace the logic in `user_config/strategy.py`. The structure allows for integrating various technical indicators and analysis techniques.

### Data & Risk Management
- **Data Utilities:** Includes scripts for downloading historical data and handling real-time data streams.
- **Risk Management Tools:** The setup provides functions to manage risk, such as calculating position sizes and setting stop-loss/take-profit orders. The specific logic for how these are used is defined within your strategy file.
- **Performance Tracking:** The setup includes comprehensive logging and a structure for generating Excel-based reports for analysis.

## Architecture

```
ibkr-stock/
├── src/ibkr-stock/
│   ├── engine.py              # Main trading engine
│   ├── setup.py               # Core setup class
│   ├── ib_functions.py        # IB API integration
│   ├── trading_functions.py   # Trading logic
│   ├── setup_for_download_data.py  # Data management
│   ├── setup_functions.py    # Utility functions
│   └── create_database.py     # Data storage
├── user_config/
│   ├── main.py               # Main execution file
│   └── strategy.py           # Strategy configuration
└── doc/                      # Documentation
```

## Installation

### Prerequisites
- Python 3.12 or higher
- Interactive Brokers account
- TWS (Trader Workstation) or IB Gateway

### Setup

```bash
# Create virtual environment
conda create --name stock_trading python=3.12
conda activate stock_trading

# Install the trading setup
pip install dist/ibkr-stock-1.0.0-py3-none-any.whl

# Install Interactive Brokers API
# You should download it from IB and install in your environment
```

## Usage

To get started with the trading bot, follow these steps:

1.  **Install the package**: Make sure you have installed the package from the `.whl` file as described in the Installation section.
2.  **Configure Parameters**: Open `user_config/main.py` to set up your trading parameters. This is where you'll define your account details, the stock symbol to trade, data frequency, and other core settings.
3.  **Customize Your Strategy**: The trading logic is located in `user_config/strategy.py`. You can modify the existing strategy or implement your own from scratch in this file.
4.  **Run the Bot**: Once configured, you can start the trading bot by running the following command from the `ibkr-stock` directory:
    ```bash
    python user_config/main.py
    ```

You can further customize the setup by adjusting risk management settings and configuring email notifications within the configuration files.

## Documentation

| Documentation | Description |
|---------------|-------------|
| [Quick Start Guide](doc/Start_here_documentation.md) | How to get up and running in minutes |
| [Strategy Development](doc/Strategy_documentation.md) | How to build and customize trading strategies |
| [Technical Reference](doc/The_trading_setup_references.md) | Complete API documentation |
| [Developer Guide](doc/Developer_documentation.md) | Advanced customization and development |

## Contributing

We welcome contributions. You can see our [Contributing Guide](CONTRIBUTING.md) for details.

### Ways to Contribute
- You can report bugs and issues.
- You can suggest new features.
- You can improve documentation.
- You can submit code improvements.
- You can add tests and examples.

## Support

For questions and support:
- **Documentation**: You can check the documentation in the `doc/` folder.
- **Email**: You can contact your support manager (if you're a present EPAT student) or the alumni team (if you're a past EPAT student).

## Author and Maintainer

*   **Author:** [José Carlos Gonzáles Tanaka](https://www.linkedin.com/in/jose-carlos-gonzales-tanaka/)
*   **Maintainer:** EPAT Content Team

## Disclaimers

### Risk Warning
**Trading stocks involves substantial risk and may not be suitable for all investors. The value of investments can go down as well as up.**

### Educational Purpose
This trading setup is provided for **educational purposes only**. You should not consider it as investment advice. You should always:
- Test thoroughly in paper trading first.
- Understand the risks involved.
- Never risk more than you can afford to lose.
- Consult with financial professionals before live trading.
