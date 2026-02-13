"""Basic SDK usage example.

Demonstrates simple grid monitoring with Block 1300.

Key features:
- Auto-registration of schemas from SchemaRegistry
- No manual schema registration needed
- Simple MQTT transport setup
"""

import getpass
import logging

# Import auth from old code temporarily
import sys

from bluetti_sdk import BluettiClient, MQTTConfig, MQTTTransport
from bluetti_sdk.models.profiles import get_device_profile

sys.path.insert(0, "../")
from bluetti_mqtt_client import BluettiAuth


def main():
    """Main example."""

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

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
        device_sn=device_sn, pfx_cert=pfx_data, cert_password=cert_password
    )

    transport = MQTTTransport(config)

    # Get device profile
    profile = get_device_profile("EL100V2")  # or "EL30V2", "Elite 200 V2"

    # Create client
    # Note: Schemas are auto-registered from device profile
    # No need for manual schema registration!
    client = BluettiClient(transport=transport, profile=profile, device_address=1)

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
