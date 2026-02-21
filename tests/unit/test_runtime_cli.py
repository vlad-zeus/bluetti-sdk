"""Tests for CLI runtime subcommand."""

from __future__ import annotations

import argparse
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from power_sdk.cli import main_runtime
from power_sdk.runtime import DeviceSnapshot
from power_sdk.runtime.registry import DeviceSummary


def _make_summary(**kwargs: object) -> DeviceSummary:
    defaults: dict[str, object] = dict(
        device_id="dev1",
        vendor="acme",
        protocol="v1",
        profile_id="ACME_DEV1",
        transport_key="stub",
        poll_interval=30.0,
        can_write=False,
        supports_streaming=True,
    )
    defaults.update(kwargs)
    return DeviceSummary(**defaults)  # type: ignore[arg-type]


def _make_args(**kwargs: object) -> argparse.Namespace:
    defaults: dict[str, object] = dict(
        config="runtime.yaml", dry_run=False, once=False, connect=False
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_runtime_no_mode_falls_through_to_0() -> None:
    """With no mode flag (dry_run=False, once=False), main_runtime falls through to 0.

    In real CLI usage this path is unreachable — argparse enforces the
    required mutually-exclusive mode group.  The fallthrough return 0 is the
    correct no-op sentinel for callers that construct Namespace by hand.
    """
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(),
    ):
        args = _make_args()
        rc = main_runtime(args)
    assert rc == 0


def test_runtime_dry_run_prints_table(capsys: pytest.CaptureFixture[str]) -> None:
    summaries = [_make_summary(device_id=f"dev{i}") for i in range(3)]
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(dry_run=lambda **kw: summaries),
    ):
        args = _make_args(dry_run=True)
        rc = main_runtime(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "dev0" in out
    assert "dev1" in out
    assert "dev2" in out
    assert "3 device(s)" in out
    # sink column present in header and rows
    assert "sink" in out
    assert "memory" in out  # default sink_name for _make_summary()


def test_runtime_dry_run_exits_0() -> None:
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(dry_run=lambda **kw: []),
    ):
        rc = main_runtime(_make_args(dry_run=True))
    assert rc == 0


def test_runtime_config_not_found_exits_2() -> None:
    args = _make_args(dry_run=True, config="/no/such/file.yaml")
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        side_effect=FileNotFoundError("not found"),
    ):
        rc = main_runtime(args)
    assert rc == 2


def test_runtime_once_returns_0_on_all_ok() -> None:
    snaps = [
        DeviceSnapshot(
            device_id="dev1", model="M", timestamp=0.0, state={}, blocks_read=0
        ),
    ]
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(
            poll_all_once=lambda **kw: snaps,
            get_sink=lambda device_id: None,
        ),
    ):
        rc = main_runtime(_make_args(once=True))
    assert rc == 0


def test_runtime_once_returns_1_if_any_error() -> None:
    from power_sdk.errors import TransportError

    snaps = [
        DeviceSnapshot(
            device_id="dev1", model="M", timestamp=0.0, state={}, blocks_read=0
        ),
        DeviceSnapshot(
            device_id="dev2",
            model="M",
            timestamp=0.0,
            state={},
            blocks_read=0,
            error=TransportError("x"),
        ),
    ]
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(
            poll_all_once=lambda **kw: snaps,
            get_sink=lambda device_id: None,
        ),
    ):
        rc = main_runtime(_make_args(once=True))
    assert rc == 1


def test_runtime_dry_run_stage_resolution_section() -> None:
    """Stage Resolution table is printed when pipeline_name != 'direct'."""
    summaries = [
        _make_summary(
            device_id="dev1",
            pipeline_name="my_pipe",
            mode="pull",
            parser="bluetti/v2",
            model="bluetti/v2",
            can_write=True,
        ),
    ]
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(dry_run=lambda **kw: summaries),
    ):
        args = _make_args(dry_run=True)
        rc = main_runtime(args)
    assert rc == 0


def test_runtime_dry_run_stage_resolution_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Stage Resolution rows include parser, model, pipeline, mode columns."""
    summaries = [
        _make_summary(
            device_id="dev1",
            pipeline_name="my_pipe",
            mode="pull",
            parser="bluetti/v2",
            model="bluetti/v2",
        ),
    ]
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(dry_run=lambda **kw: summaries),
    ):
        rc = main_runtime(_make_args(dry_run=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "Stage Resolution" in out
    assert "my_pipe" in out
    assert "pull" in out
    assert "bluetti/v2" in out


def test_runtime_dry_run_no_stage_resolution_when_direct_pipeline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Stage Resolution section is omitted when all pipelines are 'direct'."""
    summaries = [_make_summary(device_id="dev1")]  # pipeline_name="direct" by default
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(dry_run=lambda **kw: summaries),
    ):
        rc = main_runtime(_make_args(dry_run=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "Stage Resolution" not in out


def test_runtime_once_uses_single_asyncio_run_for_sink_batch() -> None:
    snaps = [
        DeviceSnapshot(
            device_id="dev1", model="M", timestamp=0.0, state={}, blocks_read=0
        ),
        DeviceSnapshot(
            device_id="dev2", model="M", timestamp=0.0, state={}, blocks_read=0
        ),
    ]
    orig_run = asyncio.run
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(
            poll_all_once=lambda **kw: snaps,
            get_sink=lambda device_id: None,
        ),
    ), patch(
        "power_sdk.cli.asyncio.run",
        side_effect=lambda coro: orig_run(coro),
    ) as run_mock:
        rc = main_runtime(_make_args(once=True))
    assert rc == 0
    # One run for write batch + one run for fallback sink close.
    assert run_mock.call_count == 2


def test_runtime_once_closes_configured_sink() -> None:
    snaps = [
        DeviceSnapshot(
            device_id="dev1", model="M", timestamp=0.0, state={}, blocks_read=0
        ),
    ]
    calls: list[str] = []

    class StubSink:
        async def write(self, snapshot: DeviceSnapshot) -> None:
            calls.append("write")

        async def close(self) -> None:
            calls.append("close")

    sink = StubSink()
    with patch(
        "power_sdk.cli.RuntimeRegistry.from_config",
        return_value=MagicMock(
            poll_all_once=lambda **kw: snaps,
            get_sink=lambda device_id: sink,
        ),
    ):
        rc = main_runtime(_make_args(once=True))
    assert rc == 0
    assert calls == ["write", "close"]
