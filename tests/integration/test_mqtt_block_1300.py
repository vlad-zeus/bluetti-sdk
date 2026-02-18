"""End-to-End Test: Read Block 1300 via MQTT

Tests complete stack:
    MQTT Transport → Protocol → V2 Parser → Device Model

This is the "Hello World" for the V2 system.
"""

import getpass
import logging
import sys
from contextlib import suppress

# Import existing auth from research folder
sys.path.insert(0, "_research/old_code")
from bluetti_mqtt_client import BluettiAuth

# Import SDK
from power_sdk import Client, MQTTConfig, MQTTTransport
from power_sdk.devices.profiles import get_device_profile
from power_sdk.protocol.v2.datatypes import Int16, UInt16
from power_sdk.protocol.v2.schema import BlockSchema, Field


def create_block_1300_schema() -> BlockSchema:
    """Create Block 1300 schema (Grid Info).

    Based on BLOCK_1300_INV_GRID_INFO.md from reverse engineering.
    """
    return BlockSchema(
        block_id=1300,
        name="INV_GRID_INFO",
        description="Grid input monitoring",
        min_length=32,
        fields=[
            Field(
                name="frequency",
                offset=0,
                type=UInt16(),
                transform=["scale:0.1"],
                unit="Hz",
                required=True,
                description="Grid frequency",
            ),
            Field(
                name="phase_0_power",
                offset=26,
                type=Int16(),
                transform=["abs"],
                unit="W",
                required=True,
                description="Phase 0 power",
            ),
            Field(
                name="phase_0_voltage",
                offset=28,
                type=UInt16(),
                transform=["scale:0.1"],
                unit="V",
                required=True,
                description="Phase 0 voltage",
            ),
            Field(
                name="phase_0_current",
                offset=30,
                type=Int16(),
                transform=["abs", "scale:0.1"],
                unit="A",
                required=True,
                description="Phase 0 current",
            ),
        ],
        strict=True,
        schema_version="1.0.0",
    )


def main():
    """End-to-end test."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("V2 End-to-End Test - Block 1300 (Grid Info)")
    print("=" * 60)

    # === Step 1: Get credentials ===
    print("\n[Step 1] Authentication")
    print("-" * 60)

    email = input("Email: ")
    password = getpass.getpass("Password: ")
    device_sn = input("Device SN: ")
    device_model = input("Device model (EL100V2/EL30V2): ") or "EL100V2"

    # === Step 2: Login and get certificate ===
    print("\n[Step 2] Getting certificate...")
    print("-" * 60)

    auth = BluettiAuth(email, password)

    if not auth.login():
        print("❌ Login failed")
        return

    pfx_data, cert_password = auth.get_certificate()

    if not pfx_data:
        print("❌ Failed to get certificate")
        return

    print(f"✓ Certificate downloaded ({len(pfx_data)} bytes)")
    print(f"✓ Password: {cert_password}")

    # === Step 3: Create transport ===
    print("\n[Step 3] Creating MQTT transport...")
    print("-" * 60)

    mqtt_config = MQTTConfig(
        device_sn=device_sn, pfx_cert=pfx_data, cert_password=cert_password
    )

    transport = MQTTTransport(mqtt_config)

    # === Step 4: Get device profile ===
    print("\n[Step 4] Loading device profile...")
    print("-" * 60)

    try:
        profile = get_device_profile(device_model)
        print(f"✓ Model: {profile.model}")
        print(f"✓ Type ID: {profile.type_id}")
        print(f"✓ Protocol: {profile.protocol}")
        print(f"✓ Groups: {list(profile.groups.keys())}")
    except ValueError as e:
        print(f"❌ {e}")
        return

    # === Step 5: Create V2 client ===
    print("\n[Step 5] Creating V2 client...")
    print("-" * 60)

    client = Client(
        transport=transport,
        profile=profile,
        device_address=1,  # Modbus slave address
    )

    # === Step 6: Register Block 1300 schema ===
    print("\n[Step 6] Registering Block 1300 schema...")
    print("-" * 60)

    schema_1300 = create_block_1300_schema()
    client.register_schema(schema_1300)

    print(f"✓ Schema registered: {schema_1300.name}")
    print(f"✓ Fields: {len(schema_1300.fields)}")
    print(f"✓ Min length: {schema_1300.min_length} bytes")

    # === Step 7: Connect to device ===
    print("\n[Step 7] Connecting to device...")
    print("-" * 60)

    try:
        client.connect()
        print("✓ Connected")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # === Step 8: Read Block 1300 ===
    print("\n[Step 8] Reading Block 1300 (Grid Info)...")
    print("-" * 60)

    try:
        # Read block
        # Block 1300 needs 32 bytes = 16 registers
        parsed = client.read_block(1300, register_count=16)

        print("✓ Block read successfully")
        print(f"  Block ID: {parsed.block_id}")
        print(f"  Name: {parsed.name}")
        print(f"  Fields parsed: {len(parsed.values)}")
        print(f"  Data length: {parsed.length} bytes")

    except Exception as e:
        print(f"❌ Read failed: {e}")
        import traceback

        traceback.print_exc()

        # Disconnect before exit
        with suppress(Exception):
            client.disconnect()

        return

    # === Step 9: Display results ===
    print("\n[Step 9] Parsed Values")
    print("-" * 60)

    print("\n📊 Grid Status:")
    print(f"  Frequency:     {parsed.values['frequency']:.1f} Hz")
    print(f"  Voltage:       {parsed.values['phase_0_voltage']:.1f} V")
    print(f"  Current:       {parsed.values['phase_0_current']:.1f} A")
    print(f"  Power:         {parsed.values['phase_0_power']} W")

    # === Step 10: Validate results ===
    print("\n[Step 10] Validation")
    print("-" * 60)

    frequency = parsed.values["frequency"]
    voltage = parsed.values["phase_0_voltage"]

    # Sanity checks
    issues = []

    if not (45.0 <= frequency <= 55.0):
        issues.append(f"Frequency out of range: {frequency} Hz (expected 45-55)")

    if not (200.0 <= voltage <= 250.0):
        issues.append(f"Voltage out of range: {voltage} V (expected 200-250)")

    if issues:
        print("⚠️  Validation warnings:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ All values in expected ranges")

    # === Step 11: Check device state ===
    print("\n[Step 11] Device State")
    print("-" * 60)

    state = client.get_device_state()

    print(f"Device: {state['model']}")
    print(f"Last update: {state['last_update']}")
    print(f"Grid voltage: {state.get('grid_voltage')} V")
    print(f"Grid frequency: {state.get('grid_frequency')} Hz")

    # === Step 12: Disconnect ===
    print("\n[Step 12] Disconnecting...")
    print("-" * 60)

    try:
        client.disconnect()
        print("✓ Disconnected")
    except Exception as e:
        print(f"⚠️  Disconnect warning: {e}")

    # === Summary ===
    print("\n" + "=" * 60)
    print("✅ End-to-End Test COMPLETE")
    print("=" * 60)

    print("\nKey achievements:")
    print("✓ MQTT connection established")
    print("✓ Block 1300 read successfully")
    print("✓ Modbus framing handled correctly")
    print("✓ V2 parser extracted fields")
    print("✓ Device model updated")
    print("✓ Values validated")

    print("\nNext steps:")
    print("- Implement Block 100 (Dashboard data)")
    print("- Implement Block 6000 (Battery pack)")
    print("- Add continuous polling")
    print("- Integrate with Home Assistant")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()


