# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup for stock trading with Interactive Brokers API
- Machine learning-based trading strategy using Random Forest algorithm
- Risk management features with stop-loss and take-profit orders
- Email notification system for trading alerts
- Historical data download and management
- Real-time market data integration
- Position sizing and leverage management
- Multi-timeframe support (1min, 5min, 15min, 1h, 1D)
- Excel-based reporting and data storage
- Timezone handling for global trading

### Changed
- Converted from forex trading setup to stock trading setup
- Updated all documentation to reflect stock trading focus
- Modified risk parameters for stock market characteristics
- Adjusted trading hours and market session handling

### Fixed
- Package naming consistency across all files
- Documentation file references and paths
- License and copyright information

## [1.0.0] - 2025-01-XX

### Added
- Core trading engine with Interactive Brokers API integration
- Machine learning strategy implementation
- Risk management system
- Data management and storage
- Reporting and analytics
- Email notification system
- Comprehensive documentation

### Technical Features
- **Trading Engine**: Automated execution of buy/sell orders
- **ML Strategy**: Random Forest-based signal generation
- **Risk Management**: Configurable stop-loss and take-profit
- **Data Management**: Historical data download and storage
- **Reporting**: Excel-based trade and performance reports
- **Notifications**: Email alerts for trading events

### Documentation
- Start Here Guide for quick setup
- Strategy Documentation for customization
- Trading Setup References for technical details
- Comprehensive README with installation instructions

### Dependencies
- pandas >= 2.0.0
- numpy >= 1.24.0
- scikit-learn >= 1.3.0
- ibapi >= 10.19.0
- openpyxl >= 3.1.0
- pytz >= 2023.3
- matplotlib >= 3.7.0
- seaborn >= 0.12.0

---

## Version History

### Version 1.0.0
- Initial release of the stock trading setup
- Complete trading system with ML strategy
- Full documentation and examples
- Ready for paper trading and live trading (with proper testing)

---

## Release Notes

### Version 1.0.0 Release Notes

**What's New:**
- Complete algorithmic trading system for stocks
- Machine learning-based strategy using Random Forest
- Interactive Brokers API integration
- Risk management and position sizing
- Real-time market data and order execution

**Key Features:**
- Automated trading with customizable strategies
- Risk management with stop-loss and take-profit
- Historical data management and analysis
- Performance tracking and reporting
- Email notifications for trading events

**System Requirements:**
- Python 3.8 or higher
- Interactive Brokers account (paper or live)
- TWS or IB Gateway platform
- Internet connection for market data

**Installation:**
```bash
pip install dist/ib_stock_setup-1.0.0-py3-none-any.whl
```

**Quick Start:**
1. Install the package
2. Configure your IB account settings
3. Modify main.py with your trading parameters
4. Run the trading system

**Documentation:**
- See doc/Start_here_documentation.md for setup instructions
- See doc/Strategy_documentation.md for strategy customization
- See doc/The_trading_setup_references.md for technical details

**Support:**
- For issues and questions, contact support@quantinsti.com
- Check the documentation in the doc/ folder
- Review the README.md for installation and setup

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.txt](LICENSE.txt) file for details. 