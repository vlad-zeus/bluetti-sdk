"""Runtime-first quick example.

This example uses only the public runtime API and a YAML config file.
No legacy auth helpers and no imports from `_research/old_code`.
"""

from __future__ import annotations

from pathlib import Path

from power_sdk.runtime import RuntimeRegistry


def main() -> int:
    config_path = Path("examples/runtime.yaml")
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        return 2

    registry = RuntimeRegistry.from_config(config_path)
    snapshots = registry.poll_all_once(connect=False, disconnect=False)
    ok_count = sum(1 for s in snapshots if s.ok)

    print(f"Devices polled: {len(snapshots)}")
    print(f"Successful snapshots: {ok_count}")
    for snap in snapshots:
        status = "ok" if snap.ok else f"error: {snap.error}"
        print(f"- {snap.device_id}: {status}, blocks={snap.blocks_read}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


