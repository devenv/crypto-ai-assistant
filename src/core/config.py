import importlib.resources
from typing import List, TypedDict, cast

import toml


# --- Type Definitions for Config ---
class AnalysisConfig(TypedDict):
    ema_periods: List[int]
    ema_short_period: int
    ema_long_period: int
    ema_signal_period: int
    rsi_period: int
    min_data_points: int


class CLIConfig(TypedDict):
    account_min_value: float
    history_limit: int


class AppConfig(TypedDict):
    analysis: AnalysisConfig
    cli: CLIConfig


# --- Constants ---
# The config file is now treated as a package resource within the 'core' package.
CONFIG_PATH_DESCRIPTION = "src/core/config.toml"

# --- Cached Configuration ---
_config: AppConfig | None = None


def _load_config() -> AppConfig:
    """
    Loads the TOML configuration file using importlib.resources.
    This approach is robust for finding package data, whether the project
    is run from source or installed as a package.
    """
    try:
        # Use importlib.resources to get a reader for the package
        files = importlib.resources.files("core")
        with files.joinpath("config.toml").open("r") as f:
            # Cast the loaded TOML data to our structured AppConfig type
            return cast(AppConfig, toml.load(f))
    except FileNotFoundError:
        # Provide a helpful error message if the config is missing.
        raise FileNotFoundError("Configuration file not found. Ensure 'config.toml' exists in the 'src/core/' directory.") from None
    except toml.TomlDecodeError as e:
        # Catch parsing errors.
        raise ValueError(f"Error decoding config file: {e}") from e


def get_config() -> AppConfig:
    """
    Retrieves the application configuration.
    The configuration is loaded once and cached for subsequent calls.
    """
    global _config
    if _config is None:
        _config = _load_config()
    return _config
