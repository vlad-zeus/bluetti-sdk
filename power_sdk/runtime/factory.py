"""Stage resolver — validates and resolves pipeline stage keys.

Maps PipelineSpec stage-keys to concrete builders via:
  - TransportFactory  (transport key)
  - PluginRegistry    (vendor / protocol key + factory presence)

Raises ValueError with field-level path info on any unresolvable stage.
Separating validation from client construction keeps core vendor-neutral.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..plugins.registry import PluginRegistry, load_plugins
from ..transport.factory import TransportFactory
from .spec import VALID_MODES, PipelineSpec


@dataclass
class ResolvedPipeline:
    """All stages validated and resolved — no I/O, no object construction."""

    pipeline_name: str
    mode: str
    transport: str
    vendor: str
    protocol: str
    parser: str            # plugin key (e.g. "bluetti/v2") or "?"
    model: str             # plugin key or "?"
    can_write: bool
    supports_streaming: bool


class StageResolver:
    """Validates pipeline stage keys against TransportFactory and PluginRegistry.

    Usage::

        resolver = StageResolver(plugin_registry)
        resolver.validate(pipeline_spec)          # raises ValueError on failure
        resolved = resolver.resolve(pipeline_spec) # returns ResolvedPipeline
    """

    def __init__(self, plugin_registry: PluginRegistry | None = None) -> None:
        self._registry = (
            plugin_registry if plugin_registry is not None else load_plugins()
        )

    def validate(self, spec: PipelineSpec) -> None:
        """Validate all stage keys in *spec*.

        Raises:
            ValueError: If any stage key cannot be resolved, with a descriptive
                message listing the pipeline name and the specific failure.
        """
        errors: list[str] = []

        # --- mode ---
        if spec.mode not in VALID_MODES:
            errors.append(
                f"pipeline {spec.name!r}: mode={spec.mode!r} is invalid; "
                f"expected one of {sorted(VALID_MODES)}"
            )

        # --- transport ---
        if spec.transport:
            available = TransportFactory.list_transports()
            if spec.transport not in available:
                errors.append(
                    f"pipeline {spec.name!r}: transport={spec.transport!r} "
                    f"is not registered; available: {available}"
                )

        # --- plugin (vendor + protocol) ---
        if spec.vendor and spec.protocol:
            manifest = self._registry.get(spec.vendor, spec.protocol)
            if manifest is None:
                errors.append(
                    f"pipeline {spec.name!r}: no plugin registered for "
                    f"vendor={spec.vendor!r} protocol={spec.protocol!r}; "
                    f"registered plugins: {self._registry.keys()}"
                )
            else:
                # All three factories are required for a functional pipeline
                for attr, label in [
                    ("protocol_layer_factory", "protocol_layer_factory"),
                    ("parser_factory", "parser_factory"),
                    ("profile_loader", "profile_loader"),
                ]:
                    if getattr(manifest, attr) is None:
                        errors.append(
                            f"pipeline {spec.name!r}: plugin {manifest.key!r} "
                            f"is missing {label}"
                        )

        if errors:
            raise ValueError("\n".join(errors))

    def resolve(self, spec: PipelineSpec) -> ResolvedPipeline:
        """Validate *spec* and return a fully resolved pipeline descriptor.

        Raises:
            ValueError: Propagated from validate() if any stage is unresolvable.
        """
        self.validate(spec)
        manifest = self._registry.get(spec.vendor, spec.protocol)
        return ResolvedPipeline(
            pipeline_name=spec.name,
            mode=spec.mode,
            transport=spec.transport,
            vendor=spec.vendor,
            protocol=spec.protocol,
            parser=manifest.key if manifest else "?",
            model=manifest.key if manifest else "?",
            can_write=manifest.can_write() if manifest else False,
            supports_streaming=(
                manifest.capabilities.supports_streaming if manifest else False
            ),
        )
