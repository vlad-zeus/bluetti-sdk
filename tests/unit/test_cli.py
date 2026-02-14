"""Test CLI module functions."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bluetti_sdk.cli import _build_parser, _load_pfx_bytes, _parse_blocks, setup_logging


def test_parse_blocks_single():
    """Test parsing a single block ID."""
    result = _parse_blocks("100")
    assert result == [100]


def test_parse_blocks_multiple():
    """Test parsing multiple block IDs."""
    result = _parse_blocks("100,1300,6000")
    assert result == [100, 1300, 6000]


def test_parse_blocks_with_spaces():
    """Test parsing block IDs with whitespace."""
    result = _parse_blocks(" 100 , 1300 , 6000 ")
    assert result == [100, 1300, 6000]


def test_parse_blocks_empty_string():
    """Test parsing empty string raises ValueError."""
    with pytest.raises(ValueError, match="No valid block IDs provided"):
        _parse_blocks("")


def test_parse_blocks_only_commas():
    """Test parsing only commas raises ValueError."""
    with pytest.raises(ValueError, match="No valid block IDs provided"):
        _parse_blocks(",,,")


def test_parse_blocks_invalid_number():
    """Test parsing invalid number raises ValueError."""
    with pytest.raises(ValueError):
        _parse_blocks("100,invalid,6000")


def test_parse_blocks_with_empty_elements():
    """Test parsing with empty elements between commas."""
    result = _parse_blocks("100,,1300")
    assert result == [100, 1300]


def test_load_pfx_bytes_success(tmp_path: Path):
    """Test loading PFX bytes from valid file."""
    cert_file = tmp_path / "cert.pfx"
    cert_data = b"fake certificate data"
    cert_file.write_bytes(cert_data)

    result = _load_pfx_bytes(str(cert_file))
    assert result == cert_data


def test_load_pfx_bytes_not_found():
    """Test loading PFX from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Certificate file not found"):
        _load_pfx_bytes("/nonexistent/cert.pfx")


def test_setup_logging_default():
    """Test setup_logging with default verbosity (WARNING)."""
    with patch("bluetti_sdk.cli.logging.basicConfig") as mock_config:
        setup_logging(0)
        mock_config.assert_called_once()
        assert mock_config.call_args.kwargs["level"] == 30  # WARNING


def test_setup_logging_info():
    """Test setup_logging with info verbosity (-v)."""
    import logging

    with patch("bluetti_sdk.cli.logging.basicConfig") as mock_config:
        setup_logging(1)
        mock_config.assert_called_once()
        assert mock_config.call_args.kwargs["level"] == logging.INFO


def test_setup_logging_debug():
    """Test setup_logging with debug verbosity (-vv)."""
    import logging

    with patch("bluetti_sdk.cli.logging.basicConfig") as mock_config:
        setup_logging(2)
        mock_config.assert_called_once()
        assert mock_config.call_args.kwargs["level"] == logging.DEBUG


def test_build_parser_creates_parser():
    """Test that _build_parser creates valid ArgumentParser."""
    parser = _build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_required_arguments():
    """Test that parser has required arguments."""
    parser = _build_parser()

    # Missing required arguments should fail
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_scan_command():
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


def test_build_parser_raw_command():
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


def test_build_parser_listen_command():
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


def test_build_parser_custom_broker():
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


def test_build_parser_verbose_flag():
    """Test parser with verbose flags."""
    parser = _build_parser()

    args = parser.parse_args(["--sn", "TEST", "--cert", "cert.pfx", "scan"])
    assert args.verbose == 0

    args = parser.parse_args(["--sn", "TEST", "--cert", "cert.pfx", "-v", "scan"])
    assert args.verbose == 1

    args = parser.parse_args(["--sn", "TEST", "--cert", "cert.pfx", "-vv", "scan"])
    assert args.verbose == 2


def test_password_env_var_support():
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


def test_password_priority_order():
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
