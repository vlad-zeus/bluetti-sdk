"""Plugin registry for power_sdk.

Each plugin lives under plugins/<vendor>/<protocol>/ and exposes a PluginManifest.
The core never imports vendor or protocol code directly — it discovers plugins
via load_plugins() in power_sdk.core.bootstrap.
"""
