"""Tests for power_sdk.runtime.config: parse_sink_specs, validate_runtime_config."""

from __future__ import annotations

import pytest
from power_sdk.runtime.config import (
    parse_pipeline_specs,
    parse_sink_specs,
    validate_runtime_config,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_config(**overrides: object) -> dict:
    config: dict = {
        "version": 1,
        "pipelines": {
            "default_pipe": {
                "mode": "pull",
                "transport": "stub",
                "vendor": "acme",
                "protocol": "v1",
            },
        },
        "devices": [{"id": "dev1", "profile_id": "DEV1", "pipeline": "default_pipe"}],
    }
    config.update(overrides)
    return config


# ---------------------------------------------------------------------------
# parse_sink_specs
# ---------------------------------------------------------------------------


class TestParseSinkSpecs:
    def test_memory_defaults(self) -> None:
        spec = parse_sink_specs({"mem": {"type": "memory"}})["mem"]
        assert spec.type == "memory"
        assert spec.maxlen == 100

    def test_memory_custom_maxlen(self) -> None:
        spec = parse_sink_specs({"mem": {"type": "memory", "maxlen": 50}})["mem"]
        assert spec.maxlen == 50

    def test_memory_invalid_maxlen_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="maxlen"):
            parse_sink_specs({"mem": {"type": "memory", "maxlen": 0}})

    def test_memory_invalid_maxlen_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="maxlen"):
            parse_sink_specs({"mem": {"type": "memory", "maxlen": -5}})

    def test_jsonl_path_set(self) -> None:
        specs = parse_sink_specs({"log": {"type": "jsonl", "path": "/tmp/x.jsonl"}})
        assert specs["log"].path == "/tmp/x.jsonl"

    def test_jsonl_missing_path_raises(self) -> None:
        with pytest.raises(ValueError, match="path"):
            parse_sink_specs({"log": {"type": "jsonl"}})

    def test_jsonl_empty_path_raises(self) -> None:
        with pytest.raises(ValueError, match="path"):
            parse_sink_specs({"log": {"type": "jsonl", "path": "  "}})

    def test_composite_sub_sinks_stored(self) -> None:
        spec = parse_sink_specs({"c": {"type": "composite", "sinks": ["a", "b"]}})["c"]
        assert spec.sub_sinks == ["a", "b"]

    def test_composite_empty_sinks_raises(self) -> None:
        with pytest.raises(ValueError, match="sinks"):
            parse_sink_specs({"c": {"type": "composite", "sinks": []}})

    def test_composite_missing_sinks_key_raises(self) -> None:
        with pytest.raises(ValueError, match="sinks"):
            parse_sink_specs({"c": {"type": "composite"}})

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid"):
            parse_sink_specs({"bad": {"type": "kafka"}})

    def test_non_dict_raw_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_sink_specs({"bad": "just a string"})

    def test_non_dict_sinks_config_raises(self) -> None:
        with pytest.raises(ValueError, match="mapping"):
            parse_sink_specs("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# validate_runtime_config — version
# ---------------------------------------------------------------------------


class TestVersionValidation:
    def test_version_1_passes(self) -> None:
        validate_runtime_config(_base_config(version=1))

    def test_missing_version_defaults_to_1(self) -> None:
        config: dict = {
            "pipelines": {
                "p": {
                    "mode": "pull",
                    "transport": "stub",
                    "vendor": "acme",
                    "protocol": "v1",
                },
            },
            "devices": [{"id": "dev1", "profile_id": "DEV1", "pipeline": "p"}],
        }
        validate_runtime_config(config)  # should not raise

    def test_version_2_raises(self) -> None:
        with pytest.raises(ValueError, match="version"):
            validate_runtime_config(_base_config(version=2))

    def test_version_0_raises(self) -> None:
        with pytest.raises(ValueError, match="version"):
            validate_runtime_config(_base_config(version=0))


# ---------------------------------------------------------------------------
# validate_runtime_config — sinks section
# ---------------------------------------------------------------------------


class TestSinksValidation:
    def test_no_sinks_section_passes(self) -> None:
        validate_runtime_config(_base_config())

    def test_memory_sink_passes(self) -> None:
        validate_runtime_config(
            _base_config(sinks={"mem": {"type": "memory", "maxlen": 50}})
        )

    def test_jsonl_sink_passes(self) -> None:
        validate_runtime_config(
            _base_config(sinks={"log": {"type": "jsonl", "path": "/tmp/out.jsonl"}})
        )

    def test_composite_valid_passes(self) -> None:
        validate_runtime_config(
            _base_config(
                sinks={
                    "mem": {"type": "memory"},
                    "log": {"type": "jsonl", "path": "/tmp/out.jsonl"},
                    "combo": {"type": "composite", "sinks": ["mem", "log"]},
                }
            )
        )

    def test_composite_unknown_ref_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown sink"):
            validate_runtime_config(
                _base_config(
                    sinks={"combo": {"type": "composite", "sinks": ["nonexistent"]}}
                )
            )

    def test_composite_direct_cycle_raises(self) -> None:
        with pytest.raises(ValueError, match=r"[Cc]ycle"):
            validate_runtime_config(
                _base_config(
                    sinks={
                        "a": {"type": "composite", "sinks": ["b"]},
                        "b": {"type": "composite", "sinks": ["a"]},
                    }
                )
            )

    def test_composite_self_cycle_raises(self) -> None:
        with pytest.raises(ValueError, match=r"[Cc]ycle"):
            validate_runtime_config(
                _base_config(sinks={"a": {"type": "composite", "sinks": ["a"]}})
            )

    def test_composite_three_node_cycle_raises(self) -> None:
        with pytest.raises(ValueError, match=r"[Cc]ycle"):
            validate_runtime_config(
                _base_config(
                    sinks={
                        "a": {"type": "composite", "sinks": ["b"]},
                        "b": {"type": "composite", "sinks": ["c"]},
                        "c": {"type": "composite", "sinks": ["a"]},
                    }
                )
            )


# ---------------------------------------------------------------------------
# validate_runtime_config — defaults.sink
# ---------------------------------------------------------------------------


class TestDefaultsSinkValidation:
    def test_defaults_sink_with_valid_ref_passes(self) -> None:
        validate_runtime_config(
            _base_config(
                defaults={"sink": "mem"},
                sinks={"mem": {"type": "memory"}},
            )
        )

    def test_defaults_sink_no_sinks_section_raises(self) -> None:
        with pytest.raises(ValueError, match=r"defaults\.sink"):
            validate_runtime_config(_base_config(defaults={"sink": "mem"}))

    def test_defaults_sink_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match=r"defaults\.sink"):
            validate_runtime_config(
                _base_config(
                    defaults={"sink": "no_such"},
                    sinks={"mem": {"type": "memory"}},
                )
            )


# ---------------------------------------------------------------------------
# validate_runtime_config — poll_interval
# ---------------------------------------------------------------------------


class TestPollIntervalValidation:
    def test_valid_float_passes(self) -> None:
        validate_runtime_config(
            _base_config(
                devices=[
                    {
                        "id": "dev1",
                        "profile_id": "DEV1",
                        "pipeline": "default_pipe",
                        "poll_interval": 0.5,
                    }
                ]
            )
        )

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="poll_interval"):
            validate_runtime_config(
                _base_config(
                    devices=[{"id": "dev1", "profile_id": "DEV1", "poll_interval": 0}]
                )
            )

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="poll_interval"):
            validate_runtime_config(
                _base_config(
                    devices=[{"id": "dev1", "profile_id": "DEV1", "poll_interval": -1}]
                )
            )

    def test_non_number_raises(self) -> None:
        with pytest.raises(ValueError, match="poll_interval"):
            validate_runtime_config(
                _base_config(
                    devices=[
                        {"id": "dev1", "profile_id": "DEV1", "poll_interval": "fast"}
                    ]
                )
            )

    def test_defaults_poll_interval_applied(self) -> None:
        # devices entry without poll_interval inherits from defaults
        config = {
            "version": 1,
            "defaults": {"poll_interval": 60},
            "pipelines": {
                "p": {
                    "mode": "pull",
                    "transport": "stub",
                    "vendor": "acme",
                    "protocol": "v1",
                },
            },
            "devices": [{"id": "dev1", "profile_id": "DEV1", "pipeline": "p"}],
        }
        validate_runtime_config(config)


# ---------------------------------------------------------------------------
# validate_runtime_config — per-device sink ref
# ---------------------------------------------------------------------------


class TestDeviceSinkRefValidation:
    def test_device_sink_valid_passes(self) -> None:
        validate_runtime_config(
            _base_config(
                sinks={"mem": {"type": "memory"}},
                devices=[
                    {
                        "id": "dev1",
                        "profile_id": "DEV1",
                        "pipeline": "default_pipe",
                        "sink": "mem",
                    }
                ],
            )
        )

    def test_device_sink_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match=r"devices\[0\]\.sink"):
            validate_runtime_config(
                _base_config(
                    sinks={"mem": {"type": "memory"}},
                    devices=[
                        {
                            "id": "dev1",
                            "profile_id": "DEV1",
                            "pipeline": "default_pipe",
                            "sink": "no_such",
                        }
                    ],
                )
            )

    def test_device_sink_no_sinks_section_raises(self) -> None:
        with pytest.raises(ValueError, match=r"devices\[0\]\.sink"):
            validate_runtime_config(
                _base_config(
                    devices=[
                        {
                            "id": "dev1",
                            "profile_id": "DEV1",
                            "pipeline": "default_pipe",
                            "sink": "mem",
                        }
                    ]
                )
            )


# ---------------------------------------------------------------------------
# parse_pipeline_specs
# ---------------------------------------------------------------------------


class TestParsePipelineSpecs:
    def test_pull_mode_defaults(self) -> None:
        specs = parse_pipeline_specs({"p": {"mode": "pull", "transport": "mqtt"}})
        assert specs["p"].mode == "pull"
        assert specs["p"].transport == "mqtt"

    def test_push_mode_accepted(self) -> None:
        specs = parse_pipeline_specs({"p": {"mode": "push", "transport": "mqtt"}})
        assert specs["p"].mode == "push"

    def test_mode_defaults_to_pull(self) -> None:
        specs = parse_pipeline_specs({"p": {"transport": "mqtt"}})
        assert specs["p"].mode == "pull"

    def test_invalid_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="mode="):
            parse_pipeline_specs({"p": {"mode": "stream"}})

    def test_non_dict_entry_raises(self) -> None:
        with pytest.raises(ValueError, match="mapping"):
            parse_pipeline_specs({"p": "invalid"})

    def test_non_dict_input_raises(self) -> None:
        with pytest.raises(ValueError, match="mapping"):
            parse_pipeline_specs("not a dict")  # type: ignore[arg-type]

    def test_non_string_transport_raises(self) -> None:
        with pytest.raises(ValueError, match="transport"):
            parse_pipeline_specs({"p": {"transport": 123}})

    def test_non_string_vendor_raises(self) -> None:
        with pytest.raises(ValueError, match="vendor"):
            parse_pipeline_specs({"p": {"vendor": 99}})

    def test_vendor_protocol_stored(self) -> None:
        specs = parse_pipeline_specs({"p": {"vendor": "bluetti", "protocol": "v2"}})
        assert specs["p"].vendor == "bluetti"
        assert specs["p"].protocol == "v2"

    def test_multiple_pipelines_parsed(self) -> None:
        specs = parse_pipeline_specs(
            {
                "pull": {"mode": "pull", "transport": "mqtt"},
                "push": {"mode": "push", "transport": "mqtt"},
            }
        )
        assert set(specs) == {"pull", "push"}


# ---------------------------------------------------------------------------
# validate_runtime_config — pipelines section + per-device ref
# ---------------------------------------------------------------------------


class TestPipelineRefValidation:
    def test_valid_pipeline_ref_passes(self) -> None:
        config = {
            "version": 1,
            "pipelines": {"my_pipeline": {"mode": "pull", "transport": "mqtt"}},
            "devices": [
                {
                    "id": "dev1",
                    "profile_id": "DEV1",
                    "pipeline": "my_pipeline",
                }
            ],
        }
        validate_runtime_config(config)  # should not raise

    def test_device_without_pipeline_raises(self) -> None:
        """Device that does not reference a pipeline is rejected."""
        config = {
            "version": 1,
            "pipelines": {"unused": {"mode": "pull"}},
            "devices": [{"id": "dev1", "profile_id": "DEV1"}],
        }
        with pytest.raises(ValueError, match=r"'pipeline' is required"):
            validate_runtime_config(config)

    def test_device_unknown_pipeline_ref_raises(self) -> None:
        config = {
            "version": 1,
            "pipelines": {"real_pipeline": {"mode": "pull"}},
            "devices": [
                {
                    "id": "dev1",
                    "profile_id": "DEV1",
                    "pipeline": "ghost_pipeline",
                }
            ],
        }
        with pytest.raises(ValueError, match=r"pipeline="):
            validate_runtime_config(config)

    def test_device_pipeline_no_pipelines_section_raises(self) -> None:
        """Config without 'pipelines:' section is rejected."""
        config = {
            "version": 1,
            "devices": [
                {"id": "dev1", "profile_id": "DEV1", "pipeline": "some_pipeline"}
            ],
        }
        with pytest.raises(ValueError, match=r"'pipelines' section is required"):
            validate_runtime_config(config)

    def test_pipeline_invalid_mode_in_section_raises(self) -> None:
        config = {
            "version": 1,
            "pipelines": {"bad": {"mode": "unknown_mode"}},
            "devices": [{"id": "dev1", "profile_id": "DEV1"}],
        }
        with pytest.raises(ValueError, match="mode="):
            validate_runtime_config(config)

    def test_validate_rejects_missing_pipelines_section(self) -> None:
        """Config with no 'pipelines:' key raises with the required message."""
        config = {
            "version": 1,
            "devices": [{"id": "dev1", "profile_id": "DEV1"}],
        }
        with pytest.raises(ValueError, match=r"'pipelines' section is required"):
            validate_runtime_config(config)

    def test_validate_rejects_device_without_pipeline_field(self) -> None:
        """Device missing the 'pipeline:' field raises with path in message."""
        config = {
            "version": 1,
            "pipelines": {
                "default_pipe": {
                    "mode": "pull",
                    "transport": "stub",
                    "vendor": "acme",
                    "protocol": "v1",
                },
            },
            "devices": [{"id": "dev1", "profile_id": "DEV1"}],
        }
        with pytest.raises(ValueError, match=r"devices\[0\]: 'pipeline' is required"):
            validate_runtime_config(config)
