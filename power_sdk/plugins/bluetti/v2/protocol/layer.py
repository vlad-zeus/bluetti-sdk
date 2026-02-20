"""Protocol layer implementations.

Core protocol logic is transport-agnostic:
- Build wire request from logical read operation
- Validate/decode raw transport response
- Return normalized payload for schema parser
"""

from __future__ import annotations

import logging

from power_sdk.contracts.protocol import NormalizedPayload, ProtocolLayerInterface
from power_sdk.contracts.transport import TransportProtocol
from power_sdk.errors import ProtocolError

from .modbus import (
    build_modbus_request,
    normalize_modbus_response,
    parse_modbus_frame,
    validate_crc,
)

logger = logging.getLogger(__name__)


class ModbusProtocolLayer(ProtocolLayerInterface):
    """Default Modbus protocol layer implementation for V2 blocks."""

    def read_block(
        self,
        transport: TransportProtocol,
        device_address: int,
        block_id: int,
        register_count: int,
    ) -> NormalizedPayload:
        """Read and normalize one block payload via transport."""
        request = build_modbus_request(
            device_address=device_address,
            block_address=block_id,
            register_count=register_count,
        )
        logger.debug(f"Protocol request block={block_id}: {request.hex()}")

        response_frame = transport.send_frame(request, timeout=5.0)
        logger.debug(f"Protocol response block={block_id}: {response_frame.hex()}")

        if not validate_crc(response_frame):
            raise ProtocolError("CRC validation failed")

        modbus_response = parse_modbus_frame(response_frame)
        normalized_data = normalize_modbus_response(modbus_response)

        return NormalizedPayload(
            block_id=block_id,
            data=normalized_data,
            device_address=device_address,
            protocol_version=2000,
        )
