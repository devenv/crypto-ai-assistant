"""Technical indicators module for cryptocurrency market analysis.

This module provides comprehensive technical analysis capabilities including
RSI, EMA, MACD calculations, support/resistance detection, and rich console display.

The module is organized into focused components:
- service: Main IndicatorService orchestration
- calculations: Mathematical indicator calculations
- data_processor: K-line data fetching and processing
- display: Rich console output and formatting
- support_resistance: Swing low/high detection
"""

# Main service class for backward compatibility
# Individual components for advanced usage
from .calculations import IndicatorCalculations
from .data_processor import DataProcessor, safe_float
from .display import IndicatorDisplay
from .service import IndicatorService
from .support_resistance import SupportResistanceDetector

# Main exports for backward compatibility
__all__ = [
    # Main service (primary export)
    "IndicatorService",
    # Component classes (for advanced usage)
    "IndicatorCalculations",
    "DataProcessor",
    "IndicatorDisplay",
    "SupportResistanceDetector",
    # Utility functions
    "safe_float",
]
