"""Tests for power_sdk.runtime.sink_factory.build_sinks_from_config."""
from __future__ import annotations

from pathlib import Path

import pytest
from power_sdk.runtime.sink import CompositeSink, JsonlSink, MemorySink
from power_sdk.runtime.sink_factory import build_sinks_from_config


class TestBuildSinksFromConfig:
    def test_empty_dict_returns_empty(self) -> None:
        assert build_sinks_from_config({}) == {}

    def test_none_returns_empty(self) -> None:
        assert build_sinks_from_config(None) == {}  # type: ignore[arg-type]

    def test_memory_sink_created(self) -> None:
        result = build_sinks_from_config({"mem": {"type": "memory", "maxlen": 50}})
        assert "mem" in result
        assert isinstance(result["mem"], MemorySink)

    def test_memory_sink_default_maxlen(self) -> None:
        result = build_sinks_from_config({"mem": {"type": "memory"}})
        assert isinstance(result["mem"], MemorySink)

    def test_jsonl_sink_created(self, tmp_path: Path) -> None:
        path = str(tmp_path / "out.jsonl")
        result = build_sinks_from_config({"log": {"type": "jsonl", "path": path}})
        assert "log" in result
        assert isinstance(result["log"], JsonlSink)

    def test_composite_sink_created(self, tmp_path: Path) -> None:
        path = str(tmp_path / "out.jsonl")
        config = {
            "mem": {"type": "memory"},
            "log": {"type": "jsonl", "path": path},
            "combo": {"type": "composite", "sinks": ["mem", "log"]},
        }
        result = build_sinks_from_config(config)
        assert "combo" in result
        assert isinstance(result["combo"], CompositeSink)

    def test_composite_sub_sinks_are_memoised(self) -> None:
        """The sub-sink inside composite is the same object as the top-level sink."""
        config = {
            "mem": {"type": "memory"},
            "combo": {"type": "composite", "sinks": ["mem"]},
        }
        result = build_sinks_from_config(config)
        assert result["mem"] is result["combo"]._sinks[0]

    def test_all_named_sinks_returned(self) -> None:
        config = {
            "mem": {"type": "memory"},
            "log": {"type": "jsonl", "path": "/tmp/x.jsonl"},
        }
        result = build_sinks_from_config(config)
        assert set(result.keys()) == {"mem", "log"}

    def test_unknown_sink_type_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid"):
            build_sinks_from_config({"bad": {"type": "kafka"}})

    def test_composite_built_in_any_order(self) -> None:
        """composite defined before its sub-sinks — still builds correctly."""
        config = {
            "combo": {"type": "composite", "sinks": ["mem"]},
            "mem": {"type": "memory"},
        }
        result = build_sinks_from_config(config)
        assert isinstance(result["combo"], CompositeSink)
        assert isinstance(result["mem"], MemorySink)
