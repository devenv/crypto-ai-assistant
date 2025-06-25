import unittest.mock
from unittest.mock import patch

import pytest
import toml

from core import config
from core.config import AppConfig


@pytest.fixture(autouse=True)
def clear_config_cache() -> None:
    """Fixture to clear the cached config before each test."""
    config._config = None


def test_get_config_success() -> None:
    """Test that get_config successfully loads and returns a mock config."""
    mock_toml_content: AppConfig = {
        "cli": {"account_min_value": 10.0, "history_limit": 20},
        "analysis": {
            "ema_periods": [10, 20],
            "ema_short_period": 12,
            "ema_long_period": 26,
            "ema_signal_period": 9,
            "rsi_period": 14,
            "min_data_points": 35,
        },
    }

    # Patch the resource loading mechanism
    with patch("importlib.resources.files") as mock_files:
        mock_file_handle = unittest.mock.mock_open(read_data=toml.dumps(mock_toml_content))
        # The 'open' method of the object returned by 'joinpath' should return our mock file handle
        mock_files.return_value.joinpath.return_value.open = mock_file_handle
        cfg = config.get_config()
        assert cfg["cli"]["history_limit"] == 20
        assert cfg["analysis"]["rsi_period"] == 14


def test_get_config_caching() -> None:
    """Test that the configuration is cached after the first call."""
    mock_toml_content: AppConfig = {
        "cli": {"account_min_value": 10.0, "history_limit": 20},
        "analysis": {
            "ema_periods": [10, 20],
            "ema_short_period": 12,
            "ema_long_period": 26,
            "ema_signal_period": 9,
            "rsi_period": 14,
            "min_data_points": 35,
        },
    }

    # Patch the internal _load_config to control when it's called
    with patch("core.config._load_config", return_value=mock_toml_content) as mock_load:
        # First call should load the config
        cfg1 = config.get_config()
        assert cfg1 == mock_toml_content
        mock_load.assert_called_once()

        # Second call should use the cache
        cfg2 = config.get_config()
        assert cfg2 == mock_toml_content
        mock_load.assert_called_once()  # Not called again


def test_load_config_file_not_found() -> None:
    """Test that FileNotFoundError is raised if the config file is missing."""
    # Patch the new resource loading mechanism
    with patch("importlib.resources.files") as mock_files:
        # Configure the mock chain to raise FileNotFoundError when 'open' is called
        mock_files.return_value.joinpath.return_value.open.side_effect = FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            config._load_config()


def test_load_config_decode_error() -> None:
    """Test that ValueError is raised on a TOML decoding error."""
    # Patch the resource loading mechanism
    with patch("importlib.resources.files") as mock_files:
        # mock_open provides a file-like object with the desired content for toml.load to fail on
        mock_file_handle = unittest.mock.mock_open(read_data="invalid toml")
        mock_files.return_value.joinpath.return_value.open = mock_file_handle
        # Patch toml.load to raise the error we want to test
        with patch("toml.load", side_effect=toml.TomlDecodeError("Test error", "doc", 0)):
            with pytest.raises(ValueError, match="Error decoding"):
                # The function that raises the error must be called inside the context manager
                config._load_config()
