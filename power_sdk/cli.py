"""Power SDK CLI Tool — Bluetti device utility.

Vendor-specific command-line tool for Bluetti device connectivity checks
and block reads.  Intentionally imports from power_sdk.contrib.bluetti;
this module is NOT part of the vendor-neutral core.

Also provides a vendor-neutral 'runtime' subcommand powered by RuntimeRegistry
for multi-device poll orchestration from a YAML config file.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import logging
import os
import sys
from pathlib import Path

from power_sdk.contrib.bluetti import build_bluetti_async_client, get_device_profile

from .client_async import AsyncClient
from .contracts.types import ParsedRecord
from .runtime import DeviceSummary, RuntimeRegistry
from .transport.factory import TransportFactory
from .utils.resilience import RetryPolicy

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


def _load_pfx_bytes(cert_path: str) -> bytes:
    """Load PFX certificate bytes from filesystem."""
    path = Path(cert_path)
    if not path.exists():
        raise FileNotFoundError(f"Certificate file not found: {path}")
    return path.read_bytes()


def _positive_float(value: str) -> float:
    """Validate that a float argument is positive."""
    try:
        fval = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid number: '{value}'") from exc
    if fval <= 0:
        raise argparse.ArgumentTypeError(f"Must be positive, got: {fval}")
    return fval


def _positive_int(value: str) -> int:
    """Validate that an int argument is positive."""
    try:
        ival = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid integer: '{value}'") from exc
    if ival <= 0:
        raise argparse.ArgumentTypeError(f"Must be positive, got: {ival}")
    return ival


def _nonnegative_int(value: str) -> int:
    """Validate that an int argument is non-negative (>= 0)."""
    try:
        ival = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid integer: '{value}'") from exc
    if ival < 0:
        raise argparse.ArgumentTypeError(f"Must be non-negative, got: {ival}")
    return ival


def _parse_blocks(blocks_arg: str) -> list[int]:
    """Parse comma-separated block IDs."""
    block_ids: list[int] = []
    for raw in blocks_arg.split(","):
        value = raw.strip()
        if not value:
            continue
        try:
            block_id = int(value)
        except ValueError as exc:
            msg = f"Invalid block ID (must be integer): '{value}'"
            raise ValueError(msg) from exc
        if block_id <= 0:
            raise ValueError(f"Block ID must be positive, got: {block_id}")
        block_ids.append(block_id)
    if not block_ids:
        raise ValueError("No valid block IDs provided")
    return block_ids


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Power SDK CLI")
    parser.add_argument("--sn", required=True, help="Device serial number")
    parser.add_argument("--cert", required=True, help="Path to PFX certificate")
    parser.add_argument(
        "--password",
        default=None,
        help="Certificate password (or use BLUETTI_CERT_PASSWORD env var)",
    )
    parser.add_argument("--model", default="EL100V2", help="Device model")
    parser.add_argument(
        "--transport",
        default="mqtt",
        help="Transport key (default: mqtt)",
    )
    parser.add_argument("--broker", default="iot.bluettipower.com", help="MQTT broker")
    parser.add_argument(
        "--port",
        type=_positive_int,
        default=18760,
        help="MQTT broker port (must be positive)",
    )
    parser.add_argument(
        "--keepalive",
        type=_positive_int,
        default=60,
        help="MQTT keepalive in seconds (must be positive)",
    )
    parser.add_argument(
        "--retries",
        type=_positive_int,
        default=3,
        help="Maximum retry attempts for transient errors (must be >= 1)",
    )
    parser.add_argument(
        "--retry-initial-delay",
        type=_positive_float,
        default=0.5,
        help="Initial retry delay in seconds (must be > 0)",
    )
    parser.add_argument(
        "--retry-max-delay",
        type=_positive_float,
        default=5.0,
        help="Maximum retry delay cap in seconds (must be > 0)",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity")

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Read a set of common blocks")
    scan.add_argument(
        "--blocks",
        default="100,1300",
        help="Comma-separated block IDs (default: 100,1300)",
    )

    raw = subparsers.add_parser("raw", help="Read one block and print raw payload")
    raw.add_argument(
        "--block",
        type=_positive_int,
        required=True,
        help="Block ID (must be positive)",
    )
    raw.add_argument(
        "--register-count",
        type=_positive_int,
        default=None,
        help="Optional Modbus register count override (must be positive)",
    )

    listen = subparsers.add_parser("listen", help="Continuously poll blocks")
    listen.add_argument(
        "--blocks",
        default="100,1300",
        help="Comma-separated block IDs (default: 100,1300)",
    )
    listen.add_argument(
        "--interval",
        type=_positive_float,
        default=5.0,
        help="Polling interval in seconds (must be positive)",
    )
    listen.add_argument(
        "--count",
        type=_nonnegative_int,
        default=0,
        help="Number of iterations (0 = infinite, must be non-negative)",
    )

    return parser


def _build_runtime_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the 'runtime' subcommand.

    Kept separate from _build_parser() so that --sn/--cert are not required
    for runtime operations and existing CLI tests remain unaffected.
    """
    parser = argparse.ArgumentParser(
        description="Power SDK CLI — runtime multi-device mode"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity")

    subparsers = parser.add_subparsers(dest="command", required=True)
    runtime_p = subparsers.add_parser(
        "runtime", help="Run N devices from config file"
    )
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


async def _run_scan(client: AsyncClient, blocks: list[int]) -> None:
    results = await asyncio.gather(
        *(client.read_block(block_id) for block_id in blocks),
        return_exceptions=True,
    )
    for block_id, result in zip(blocks, results):
        if isinstance(result, BaseException):
            print(f"[ERR] block={block_id}: {result}")
            continue
        if not isinstance(result, ParsedRecord):
            print(f"[ERR] block={block_id}: unexpected result type")
            continue
        print(f"\nBlock {result.block_id} ({result.name})")
        print(json.dumps(result.values, ensure_ascii=False, indent=2))


async def _run_raw(
    client: AsyncClient,
    block_id: int,
    register_count: int | None,
) -> None:
    parsed = await client.read_block(block_id, register_count=register_count)
    print(f"Block {parsed.block_id} ({parsed.name})")
    print(f"Length: {parsed.length} bytes")
    print(f"Raw: {parsed.raw.hex()}")
    print(json.dumps(parsed.values, ensure_ascii=False, indent=2))


async def _run_listen(
    client: AsyncClient,
    blocks: list[int],
    interval: float,
    count: int,
) -> None:
    iteration = 0
    while count == 0 or iteration < count:
        iteration += 1
        print(f"\n--- iteration {iteration} ---")
        await _run_scan(client, blocks)
        await asyncio.sleep(interval)


async def main_async(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)

    try:
        pfx_bytes = _load_pfx_bytes(args.cert)
        get_device_profile(args.model)  # early validation — fail before password prompt
    except Exception as exc:
        print(f"Error: {exc}")
        return 2

    # Validate retry parameters BEFORE user interaction (fail fast)
    if args.retry_max_delay < args.retry_initial_delay:
        print(
            f"Error: --retry-max-delay ({args.retry_max_delay}) must be >= "
            f"--retry-initial-delay ({args.retry_initial_delay})"
        )
        return 2

    # Resolve password from multiple sources (secure priority order)
    password = args.password or os.environ.get("BLUETTI_CERT_PASSWORD")
    if not password:
        try:
            password = getpass.getpass("Certificate password: ")
        except (EOFError, OSError):
            print(
                "Error: Certificate password not provided in non-interactive mode. "
                "Use --password or BLUETTI_CERT_PASSWORD."
            )
            return 2

    # Build retry policy from CLI arguments
    retry_policy = RetryPolicy(
        max_attempts=args.retries,
        initial_delay=args.retry_initial_delay,
        max_delay=args.retry_max_delay,
    )

    transport_opts = {
        "broker": args.broker,
        "port": args.port,
        "device_sn": args.sn,
        "pfx_cert": pfx_bytes,
        "cert_password": password,
        "keepalive": args.keepalive,
    }
    transport = TransportFactory.create(args.transport, **transport_opts)
    print(
        f"Connecting to {args.sn} ({args.model}) via "
        f"{args.transport}:{args.broker}:{args.port}..."
    )

    try:
        async with build_bluetti_async_client(
            args.model, transport, retry_policy=retry_policy
        ) as client:
            print("Connected.")
            if args.command == "scan":
                await _run_scan(client, _parse_blocks(args.blocks))
            elif args.command == "raw":
                await _run_raw(client, args.block, args.register_count)
            elif args.command == "listen":
                await _run_listen(
                    client,
                    _parse_blocks(args.blocks),
                    args.interval,
                    args.count,
                )
            else:
                print(f"Unknown command: {args.command}")
                return 2
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as exc:
        logger.exception("CLI execution failed")
        print(f"Error: {exc}")
        return 1

    print("\nDone.")
    return 0


# ---------------------------------------------------------------------------
# Runtime subcommand — sync-only, no asyncio
# ---------------------------------------------------------------------------

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
    sep = (
        "  {:<18}  {:<7}  {:<8}  {:<9}  {:<9}  {:>13}  {:<9}  {:<9}  {:<10}".format(
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
    )
    lines.append(header)
    lines.append(sep)

    for s in summaries:
        # Truncate device_id to 18 chars with ellipsis if needed
        dev_id = s.device_id if len(s.device_id) <= 18 else s.device_id[:15] + "..."
        fmt = (
            "  {:<18}  {:<7}  {:<8}  {:<9}  {:<9}"
            "  {:>12}s  {:<9}  {:<9}  {:<10}"
        )
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
        sr_header = (
            "  {:<18}  {:<14}  {:<4}  {:<12}  {:<12}".format(
                "device_id", "pipeline", "mode", "parser", "model"
            )
        )
        sr_sep = (
            "  {:<18}  {:<14}  {:<4}  {:<12}  {:<12}".format(
                "-" * 18, "-" * 14, "-" * 4, "-" * 12, "-" * 12
            )
        )
        lines.append(sr_header)
        lines.append(sr_sep)
        for s in summaries:
            dev_id = (
                s.device_id if len(s.device_id) <= 18 else s.device_id[:15] + "..."
            )
            lines.append(
                f"  {dev_id:<18}  {s.pipeline_name[:14]:<14}"
                f"  {s.mode[:4]:<4}  {s.parser[:12]:<12}  {s.model[:12]:<12}"
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
                print(
                    f"[{s.device_id}] ERROR — "
                    f"{type(s.error).__name__}: {s.error}"
                )

        # Show devices retained in the fallback MemorySink (no configured sink)
        stored = fallback_sink.all_last()
        if stored:
            print(f"(MemorySink: {len(stored)} device(s) state retained)")

        errors = [s for s in snapshots if not s.ok]
        return 1 if errors else 0

    return 0


def main() -> None:
    # Pre-dispatch: if the first positional arg is 'runtime', use the
    # runtime-specific parser (no --sn/--cert required).
    if len(sys.argv) > 1 and sys.argv[1] == "runtime":
        runtime_parser = _build_runtime_parser()
        args = runtime_parser.parse_args()
        raise SystemExit(main_runtime(args))

    parser = _build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))
