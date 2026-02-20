"""Transport layer — pluggable transport contract and factory.

Provides the TransportProtocol contract and TransportFactory registry.
Concrete transport implementations are NOT imported eagerly here; they
are loaded on demand by TransportFactory builders so that optional
dependencies (e.g. paho-mqtt) are not required unless used.

To use MQTT explicitly::

    from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport

To register a custom transport::

    from power_sdk.transport import TransportFactory

    def _build_my_transport(**opts):
        from my_package import MyTransport, MyConfig
        return MyTransport(MyConfig(**opts))

    TransportFactory.register("my_key", _build_my_transport)
"""

from ..contracts.transport import TransportProtocol
from .factory import TransportFactory

__all__ = [
    "TransportFactory",
    "TransportProtocol",
]
