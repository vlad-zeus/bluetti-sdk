"""Bluetti SDK CLI Tool.

Command-line utility for connectivity checks and block reads.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import logging
import os
from pathlib import Path

from .client_async import AsyncV2Client
from .devices.profiles import get_device_profile
from .protocol.v2.types import ParsedBlock
from .transport.mqtt import MQTTConfig, MQTTTransport

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


def _parse_blocks(blocks_arg: str) -> list[int]:
    """Parse comma-separated block IDs."""
    block_ids: list[int] = []
    for raw in blocks_arg.split(","):
        value = raw.strip()
        if not value:
            continue
        block_ids.append(int(value))
    if not block_ids:
        raise ValueError("No valid block IDs provided")
    return block_ids


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bluetti SDK CLI")
    parser.add_argument("--sn", required=True, help="Device serial number")
    parser.add_argument("--cert", required=True, help="Path to PFX certificate")
    parser.add_argument(
        "--password",
        default=None,
        help="Certificate password (or use BLUETTI_CERT_PASSWORD env var)",
    )
    parser.add_argument("--model", default="EL100V2", help="Device model")
    parser.add_argument("--broker", default="iot.bluettipower.com", help="MQTT broker")
    parser.add_argument("--port", type=int, default=18760, help="MQTT broker port")
    parser.add_argument("--keepalive", type=int, default=60, help="MQTT keepalive")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity")

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Read a set of common blocks")
    scan.add_argument(
        "--blocks",
        default="100,1300",
        help="Comma-separated block IDs (default: 100,1300)",
    )

    raw = subparsers.add_parser("raw", help="Read one block and print raw payload")
    raw.add_argument("--block", type=int, required=True, help="Block ID")
    raw.add_argument(
        "--register-count",
        type=int,
        default=None,
        help="Optional Modbus register count override",
    )

    listen = subparsers.add_parser("listen", help="Continuously poll blocks")
    listen.add_argument(
        "--blocks",
        default="100,1300",
        help="Comma-separated block IDs (default: 100,1300)",
    )
    listen.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Polling interval in seconds",
    )
    listen.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of iterations (0 = infinite)",
    )

    return parser


async def _run_scan(client: AsyncV2Client, blocks: list[int]) -> None:
    results = await asyncio.gather(
        *(client.read_block(block_id) for block_id in blocks),
        return_exceptions=True,
    )
    for block_id, result in zip(blocks, results):
        if isinstance(result, BaseException):
            print(f"[ERR] block={block_id}: {result}")
            continue
        if not isinstance(result, ParsedBlock):
            print(f"[ERR] block={block_id}: unexpected result type")
            continue
        print(f"\nBlock {result.block_id} ({result.name})")
        print(json.dumps(result.values, ensure_ascii=False, indent=2))


async def _run_raw(
    client: AsyncV2Client,
    block_id: int,
    register_count: int | None,
) -> None:
    parsed = await client.read_block(block_id, register_count=register_count)
    print(f"Block {parsed.block_id} ({parsed.name})")
    print(f"Length: {parsed.length} bytes")
    print(f"Raw: {parsed.raw.hex()}")
    print(json.dumps(parsed.values, ensure_ascii=False, indent=2))


async def _run_listen(
    client: AsyncV2Client,
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
        profile = get_device_profile(args.model)
    except Exception as exc:
        print(f"Error: {exc}")
        return 2

    # Resolve password from multiple sources (secure priority order)
    password = args.password or os.environ.get("BLUETTI_CERT_PASSWORD")
    if not password:
        password = getpass.getpass("Certificate password: ")

    config = MQTTConfig(
        broker=args.broker,
        port=args.port,
        device_sn=args.sn,
        pfx_cert=pfx_bytes,
        cert_password=password,
        keepalive=args.keepalive,
    )

    transport = MQTTTransport(config)
    print(f"Connecting to {args.sn} ({args.model}) via {args.broker}:{args.port}...")

    try:
        async with AsyncV2Client(transport, profile) as client:
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


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))
