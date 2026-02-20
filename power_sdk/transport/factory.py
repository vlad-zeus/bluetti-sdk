"""Transport layer factory and registry."""

from __future__ import annotations

from typing import Any, Callable, ClassVar

from ..contracts.transport import TransportProtocol
from ..errors import TransportError

TransportBuilder = Callable[..., TransportProtocol]


def _build_mqtt_transport(**opts: Any) -> TransportProtocol:
    """Default builder for MQTT transport.

    Supports two input forms:
    - `config=<MQTTConfig>`
    - plain kwargs accepted by MQTTConfig(...)
    """
    from .mqtt import MQTTConfig, MQTTTransport

    config = opts.pop("config", None)
    if config is not None:
        if not isinstance(config, MQTTConfig):
            raise TransportError("MQTT builder expected config=<MQTTConfig>")
        if opts:
            unknown = ", ".join(sorted(opts.keys()))
            raise TransportError(
                f"MQTT builder got extra kwargs with config: {unknown}"
            )
        return MQTTTransport(config)

    try:
        mqtt_config = MQTTConfig(**opts)
    except TypeError as exc:
        raise TransportError(f"Invalid MQTT transport options: {exc}") from exc
    return MQTTTransport(mqtt_config)


class TransportFactory:
    """Create transport instances by transport key."""

    _builders: ClassVar[dict[str, TransportBuilder]] = {
        "mqtt": _build_mqtt_transport,
    }

    @classmethod
    def register(cls, transport: str, builder: TransportBuilder) -> None:
        """Register or override a transport builder."""
        cls._builders[transport] = builder

    @classmethod
    def create(cls, transport: str, **opts: Any) -> TransportProtocol:
        """Create transport instance by key."""
        builder = cls._builders.get(transport)
        if builder is None:
            available = ", ".join(sorted(cls._builders.keys()))
            raise TransportError(
                f"Unknown transport '{transport}'. Available transports: {available}"
            )
        return builder(**opts)

    @classmethod
    def list_transports(cls) -> list[str]:
        """List registered transport keys."""
        return sorted(cls._builders.keys())
