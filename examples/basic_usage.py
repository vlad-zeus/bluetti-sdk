"""Basic SDK usage example.

Demonstrates simple grid monitoring with Block 1300.
"""

import logging
import getpass
from bluetti_sdk import BluettiClient, MQTTTransport, MQTTConfig
from bluetti_sdk.protocol.v2 import BlockSchema, Field, UInt16, Int16

# Import auth from old code temporarily
import sys
sys.path.insert(0, '../')
from bluetti_mqtt_client import BluettiAuth


def create_block_1300_schema() -> BlockSchema:
    """Create Block 1300 schema (Grid Info)."""
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
                description="Grid frequency"
            ),
            Field(
                name="phase_0_power",
                offset=26,
                type=Int16(),
                transform=["abs"],
                unit="W",
                required=True,
                description="Phase 0 power"
            ),
            Field(
                name="phase_0_voltage",
                offset=28,
                type=UInt16(),
                transform=["scale:0.1"],
                unit="V",
                required=True,
                description="Phase 0 voltage"
            ),
            Field(
                name="phase_0_current",
                offset=30,
                type=Int16(),
                transform=["abs", "scale:0.1"],
                unit="A",
                required=True,
                description="Phase 0 current"
            ),
        ],
        strict=True,
        schema_version="1.0.0"
    )


def main():
    """Main example."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    print("=== Bluetti SDK - Basic Usage Example ===\n")

    # Get credentials
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    device_sn = input("Device SN: ")

    # Authenticate and get certificate
    logger.info("Authenticating with Bluetti API...")
    auth = BluettiAuth(email, password)

    if not auth.login():
        logger.error("Login failed")
        return

    pfx_data, cert_password = auth.get_certificate()

    if not pfx_data:
        logger.error("Failed to get certificate")
        return

    logger.info(f"Certificate downloaded ({len(pfx_data)} bytes)")

    # Create MQTT transport
    config = MQTTConfig(
        device_sn=device_sn,
        pfx_cert=pfx_data,
        cert_password=cert_password
    )

    transport = MQTTTransport(config)

    # Create client
    client = BluettiClient(
        transport=transport,
        model="EL100V2",  # or "EL30V2"
        device_address=1
    )

    # Register Block 1300 schema
    schema = create_block_1300_schema()
    client.register_schema(schema)

    # Connect
    logger.info("Connecting to device...")
    client.connect()

    # Read Block 1300
    logger.info("Reading grid information...")
    grid_data = client.read_block(1300, register_count=16)

    # Display results
    print("\n📊 Grid Status:")
    print(f"  Frequency:  {grid_data.values['frequency']:.1f} Hz")
    print(f"  Voltage:    {grid_data.values['phase_0_voltage']:.1f} V")
    print(f"  Current:    {grid_data.values['phase_0_current']:.1f} A")
    print(f"  Power:      {grid_data.values['phase_0_power']} W")

    # Disconnect
    client.disconnect()

    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
