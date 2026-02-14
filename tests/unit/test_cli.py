"""Test CLI module functions."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from bluetti_sdk.cli import (
    _build_parser,
    _load_pfx_bytes,
    _nonnegative_int,
    _parse_blocks,
    _positive_float,
    _positive_int,
    setup_logging,
)


def test_parse_blocks_single() -> None:
    """Test parsing a single block ID."""
    result = _parse_blocks("100")
    assert result == [100]


def test_parse_blocks_multiple() -> None:
    """Test parsing multiple block IDs."""
    result = _parse_blocks("100,1300,6000")
    assert result == [100, 1300, 6000]


def test_parse_blocks_with_spaces() -> None:
    """Test parsing block IDs with whitespace."""
    result = _parse_blocks(" 100 , 1300 , 6000 ")
    assert result == [100, 1300, 6000]


def test_parse_blocks_empty_string() -> None:
    """Test parsing empty string raises ValueError."""
    with pytest.raises(ValueError, match="No valid block IDs provided"):
        _parse_blocks("")


def test_parse_blocks_only_commas() -> None:
    """Test parsing only commas raises ValueError."""
    with pytest.raises(ValueError, match="No valid block IDs provided"):
        _parse_blocks(",,,")


def test_parse_blocks_invalid_number() -> None:
    """Test parsing invalid number raises ValueError."""
    with pytest.raises(ValueError):
        _parse_blocks("100,invalid,6000")


def test_parse_blocks_with_empty_elements() -> None:
    """Test parsing with empty elements between commas."""
    result = _parse_blocks("100,,1300")
    assert result == [100, 1300]


def test_load_pfx_bytes_success(tmp_path: Path) -> None:
    """Test loading PFX bytes from valid file."""
    cert_file = tmp_path / "cert.pfx"
    cert_data = b"fake certificate data"
    cert_file.write_bytes(cert_data)

    result = _load_pfx_bytes(str(cert_file))
    assert result == cert_data


def test_load_pfx_bytes_not_found() -> None:
    """Test loading PFX from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Certificate file not found"):
        _load_pfx_bytes("/nonexistent/cert.pfx")


def test_setup_logging_default() -> None:
    """Test setup_logging with default verbosity (WARNING)."""
    with patch("bluetti_sdk.cli.logging.basicConfig") as mock_config:
        setup_logging(0)
        mock_config.assert_called_once()
        assert mock_config.call_args.kwargs["level"] == 30  # WARNING


def test_setup_logging_info() -> None:
    """Test setup_logging with info verbosity (-v)."""
    import logging

    with patch("bluetti_sdk.cli.logging.basicConfig") as mock_config:
        setup_logging(1)
        mock_config.assert_called_once()
        assert mock_config.call_args.kwargs["level"] == logging.INFO


def test_setup_logging_debug() -> None:
    """Test setup_logging with debug verbosity (-vv)."""
    import logging

    with patch("bluetti_sdk.cli.logging.basicConfig") as mock_config:
        setup_logging(2)
        mock_config.assert_called_once()
        assert mock_config.call_args.kwargs["level"] == logging.DEBUG


def test_build_parser_creates_parser() -> None:
    """Test that _build_parser creates valid ArgumentParser."""
    parser = _build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_required_arguments() -> None:
    """Test that parser has required arguments."""
    parser = _build_parser()

    # Missing required arguments should fail
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_scan_command() -> None:
    """Test parser with scan command."""
    parser = _build_parser()
    args = parser.parse_args([
        "--sn", "TEST123",
        "--cert", "/path/to/cert.pfx",
        "scan",
    ])

    assert args.sn == "TEST123"
    assert args.cert == "/path/to/cert.pfx"
    assert args.command == "scan"
    assert args.blocks == "100,1300"  # default
    assert args.password is None  # optional now


def test_build_parser_raw_command() -> None:
    """Test parser with raw command."""
    parser = _build_parser()
    args = parser.parse_args([
        "--sn", "TEST123",
        "--cert", "/path/to/cert.pfx",
        "--password", "secret",
        "raw",
        "--block", "6000",
    ])

    assert args.command == "raw"
    assert args.block == 6000
    assert args.register_count is None
    assert args.password == "secret"


def test_build_parser_listen_command() -> None:
    """Test parser with listen command."""
    parser = _build_parser()
    args = parser.parse_args([
        "--sn", "TEST123",
        "--cert", "/path/to/cert.pfx",
        "listen",
        "--interval", "10.5",
        "--count", "5",
    ])

    assert args.command == "listen"
    assert args.interval == 10.5
    assert args.count == 5


def test_build_parser_custom_broker() -> None:
    """Test parser with custom broker settings."""
    parser = _build_parser()
    args = parser.parse_args([
        "--sn", "TEST123",
        "--cert", "/path/to/cert.pfx",
        "--broker", "custom.broker.com",
        "--port", "8883",
        "scan",
    ])

    assert args.broker == "custom.broker.com"
    assert args.port == 8883


def test_build_parser_verbose_flag() -> None:
    """Test parser with verbose flags."""
    parser = _build_parser()

    args = parser.parse_args(["--sn", "TEST", "--cert", "cert.pfx", "scan"])
    assert args.verbose == 0

    args = parser.parse_args(["--sn", "TEST", "--cert", "cert.pfx", "-v", "scan"])
    assert args.verbose == 1

    args = parser.parse_args(["--sn", "TEST", "--cert", "cert.pfx", "-vv", "scan"])
    assert args.verbose == 2


def test_password_env_var_support() -> None:
    """Test that password can be provided via environment variable."""
    parser = _build_parser()
    args = parser.parse_args([
        "--sn", "TEST123",
        "--cert", "/path/to/cert.pfx",
        "scan",
    ])

    # Simulate password resolution logic from main_async
    password = args.password or os.environ.get("BLUETTI_CERT_PASSWORD")

    # Without env var, should be None
    if "BLUETTI_CERT_PASSWORD" not in os.environ:
        assert password is None

    # With env var
    with patch.dict(os.environ, {"BLUETTI_CERT_PASSWORD": "env_secret"}):
        password = args.password or os.environ.get("BLUETTI_CERT_PASSWORD")
        assert password == "env_secret"


def test_password_priority_order() -> None:
    """Test password resolution priority: CLI > env var > prompt."""
    parser = _build_parser()

    # Test CLI argument takes priority over env var
    with patch.dict(os.environ, {"BLUETTI_CERT_PASSWORD": "env_secret"}):
        args = parser.parse_args([
            "--sn", "TEST",
            "--cert", "cert.pfx",
            "--password", "cli_secret",
            "scan",
        ])
        password = args.password or os.environ.get("BLUETTI_CERT_PASSWORD")
        assert password == "cli_secret"

    # Test env var used when CLI not provided
    with patch.dict(os.environ, {"BLUETTI_CERT_PASSWORD": "env_secret"}):
        args = parser.parse_args([
            "--sn", "TEST",
            "--cert", "cert.pfx",
            "scan",
        ])
        password = args.password or os.environ.get("BLUETTI_CERT_PASSWORD")
        assert password == "env_secret"


# === Validation Function Tests ===


def test_positive_float_valid() -> None:
    """Test _positive_float with valid positive values."""
    assert _positive_float("1.5") == 1.5
    assert _positive_float("100.0") == 100.0
    assert _positive_float("0.001") == 0.001


def test_positive_float_zero() -> None:
    """Test _positive_float rejects zero."""
    with pytest.raises(argparse.ArgumentTypeError, match="Must be positive"):
        _positive_float("0")


def test_positive_float_negative() -> None:
    """Test _positive_float rejects negative values."""
    with pytest.raises(argparse.ArgumentTypeError, match="Must be positive"):
        _positive_float("-1.5")


def test_positive_float_invalid() -> None:
    """Test _positive_float rejects invalid input."""
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid number"):
        _positive_float("abc")


def test_positive_int_valid() -> None:
    """Test _positive_int with valid positive values."""
    assert _positive_int("1") == 1
    assert _positive_int("100") == 100
    assert _positive_int("9999") == 9999


def test_positive_int_zero() -> None:
    """Test _positive_int rejects zero."""
    with pytest.raises(argparse.ArgumentTypeError, match="Must be positive"):
        _positive_int("0")


def test_positive_int_negative() -> None:
    """Test _positive_int rejects negative values."""
    with pytest.raises(argparse.ArgumentTypeError, match="Must be positive"):
        _positive_int("-1")


def test_positive_int_invalid() -> None:
    """Test _positive_int rejects invalid input."""
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer"):
        _positive_int("abc")


def test_nonnegative_int_valid() -> None:
    """Test _nonnegative_int with valid non-negative values."""
    assert _nonnegative_int("0") == 0
    assert _nonnegative_int("1") == 1
    assert _nonnegative_int("100") == 100


def test_nonnegative_int_negative() -> None:
    """Test _nonnegative_int rejects negative values."""
    with pytest.raises(argparse.ArgumentTypeError, match="Must be non-negative"):
        _nonnegative_int("-1")


def test_nonnegative_int_invalid() -> None:
    """Test _nonnegative_int rejects invalid input."""
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer"):
        _nonnegative_int("abc")


def test_parse_blocks_negative() -> None:
    """Test _parse_blocks rejects negative block IDs."""
    with pytest.raises(ValueError, match="Block ID must be positive"):
        _parse_blocks("-100")


def test_parse_blocks_zero() -> None:
    """Test _parse_blocks rejects zero block ID."""
    with pytest.raises(ValueError, match="Block ID must be positive"):
        _parse_blocks("0")


def test_parse_blocks_better_error_message() -> None:
    """Test _parse_blocks provides clear error for invalid input."""
    with pytest.raises(ValueError, match=r"Invalid block ID.*'xyz'"):
        _parse_blocks("100,xyz,6000")


def test_argument_validation_negative_interval() -> None:
    """Test parser rejects negative interval."""
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--sn", "TEST",
            "--cert", "cert.pfx",
            "listen",
            "--interval", "-5",
        ])


def test_argument_validation_zero_interval() -> None:
    """Test parser rejects zero interval."""
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--sn", "TEST",
            "--cert", "cert.pfx",
            "listen",
            "--interval", "0",
        ])


def test_argument_validation_negative_count() -> None:
    """Test parser rejects negative count."""
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--sn", "TEST",
            "--cert", "cert.pfx",
            "listen",
            "--count", "-1",
        ])


def test_argument_validation_negative_port() -> None:
    """Test parser rejects negative port."""
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--sn", "TEST",
            "--cert", "cert.pfx",
            "--port", "-1",
            "scan",
        ])
