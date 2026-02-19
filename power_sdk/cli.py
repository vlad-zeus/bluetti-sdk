"""Power SDK CLI Tool — runtime multi-device mode.

The only supported entry point is:

    power-sdk runtime --config runtime.yaml [--dry-run | --once]
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from .runtime import DeviceSummary, RuntimeRegistry

logger = logging.getLogger(__name__)


def setup_logging(verbosity: int) -> None:
    """Configure logging level based on verbosity count."""
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


_DRY_RUN_HEADER = (
    "  {device_id:<18}  {vendor:<7}  {protocol:<8}  {profile:<9}  "
    "{transport:<9}  {poll:>13}  {cw:<9}  {stream:<9}"
)
_DRY_RUN_SEP = (
    "  {device_id:<18}  {vendor:<7}  {protocol:<8}  {profile:<9}  "
    "{transport:<9}  {poll:>13}  {cw:<9}  {stream:<9}"
)


def _format_dry_run_table(summaries: list[DeviceSummary]) -> str:
    """Render an ASCII table of device pipeline summaries without third-party deps."""
    lines: list[str] = ["Device Pipeline (dry-run):"]

    header = (
        "  {:<18}  {:<7}  {:<8}  {:<9}  {:<9}  {:>13}  {:<9}  {:<9}  {:<10}".format(
            "device_id",
            "vendor",
            "protocol",
            "profile",
            "transport",
            "poll_interval",
            "can_write",
            "streaming",
            "sink",
        )
    )
    sep = "  {:<18}  {:<7}  {:<8}  {:<9}  {:<9}  {:>13}  {:<9}  {:<9}  {:<10}".format(
        "-" * 18,
        "-" * 7,
        "-" * 8,
        "-" * 9,
        "-" * 9,
        "-" * 13,
        "-" * 9,
        "-" * 9,
        "-" * 10,
    )
    lines.append(header)
    lines.append(sep)

    for s in summaries:
        # Truncate device_id to 18 chars with ellipsis if needed
        dev_id = s.device_id if len(s.device_id) <= 18 else s.device_id[:15] + "..."
        fmt = "  {:<18}  {:<7}  {:<8}  {:<9}  {:<9}  {:>12}s  {:<9}  {:<9}  {:<10}"
        row = fmt.format(
            dev_id,
            s.vendor,
            s.protocol,
            s.profile_id,
            s.transport_key,
            int(s.poll_interval),
            "Yes" if s.can_write else "No",
            "Yes" if s.supports_streaming else "No",
            s.sink_name,
        )
        lines.append(row)

    n_write = sum(1 for s in summaries if s.can_write)
    lines.append("")
    lines.append(f"{len(summaries)} device(s) registered. {n_write} write-capable.")

    # Stage Resolution section — only shown when at least one device has a pipeline
    if any(s.pipeline_name != "direct" for s in summaries):
        lines.append("")
        lines.append("Stage Resolution:")
        sr_header = "  {:<18}  {:<14}  {:<4}  {:<12}  {:<12}  {:<5}".format(
            "device_id", "pipeline", "mode", "parser", "model", "write"
        )
        sr_sep = "  {:<18}  {:<14}  {:<4}  {:<12}  {:<12}  {:<5}".format(
            "-" * 18, "-" * 14, "-" * 4, "-" * 12, "-" * 12, "-" * 5
        )
        lines.append(sr_header)
        lines.append(sr_sep)
        for s in summaries:
            dev_id = s.device_id if len(s.device_id) <= 18 else s.device_id[:15] + "..."
            lines.append(
                f"  {dev_id:<18}  {s.pipeline_name[:14]:<14}"
                f"  {s.mode[:4]:<4}  {s.parser[:12]:<12}  {s.model[:12]:<12}"
                f"  {'Yes' if s.can_write else 'No':<5}"
            )

    return "\n".join(lines)


def main_runtime(args: argparse.Namespace) -> int:
    """Handle the 'runtime' subcommand. Sync-only — no asyncio."""
    if not args.dry_run and not args.once:
        print("Error: specify --dry-run or --once")
        return 2

    try:
        runtime_reg = RuntimeRegistry.from_config(args.config)
    except Exception as exc:
        print(f"Error: failed to load config {args.config!r}: {exc}")
        return 2

    if args.dry_run:
        summaries = runtime_reg.dry_run()
        print(_format_dry_run_table(summaries))
        return 0

    if args.once:
        from power_sdk.runtime import MemorySink

        fallback_sink = MemorySink()
        snapshots = runtime_reg.poll_all_once(
            connect=args.connect,
            disconnect=args.connect,
        )

        # Per-device: use configured sink if available, else shared fallback.
        # Use one event-loop run for the whole batch to avoid per-snapshot
        # loop creation overhead.
        async def _write_snapshots() -> None:
            for snapshot in snapshots:
                configured_sink = runtime_reg.get_sink(snapshot.device_id)
                await (configured_sink or fallback_sink).write(snapshot)

        asyncio.run(_write_snapshots())

        for s in snapshots:
            if s.ok:
                n_fields = len(s.state)
                print(
                    f"[{s.device_id}] OK — {s.blocks_read} blocks, "
                    f"state: {n_fields} fields, {s.duration_ms:.1f}ms"
                )
            else:
                print(f"[{s.device_id}] ERROR — {type(s.error).__name__}: {s.error}")

        # Show devices retained in the fallback MemorySink (no configured sink)
        stored = fallback_sink.all_last()
        if stored:
            print(f"(MemorySink: {len(stored)} device(s) state retained)")

        errors = [s for s in snapshots if not s.ok]
        return 1 if errors else 0

    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the runtime CLI."""
    parser = argparse.ArgumentParser(
        description="Power SDK CLI — runtime multi-device mode"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity")

    subparsers = parser.add_subparsers(dest="command", required=True)
    runtime_p = subparsers.add_parser("runtime", help="Run N devices from config file")
    runtime_p.add_argument("--config", required=True, help="Path to runtime.yaml")
    runtime_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show resolved pipeline, no I/O",
    )
    runtime_p.add_argument(
        "--once",
        action="store_true",
        help="Run one poll cycle (no transport connect)",
    )
    runtime_p.add_argument(
        "--connect",
        action="store_true",
        help="Connect/disconnect transport during --once",
    )

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    raise SystemExit(main_runtime(args))
