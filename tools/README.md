# User Tools

**Command-line utilities for Bluetti SDK users**

---

## Available Tools

### 🚧 Coming Soon

This directory will contain CLI tools for SDK users:

- `bluetti-cli` - Interactive CLI for device monitoring
- `bluetti-export` - Export device data to CSV/JSON
- `bluetti-monitor` - Real-time monitoring dashboard

---

## Installation

After installing the SDK:

```bash
pip install bluetti-sdk
```

CLI tools will be available as console commands:

```bash
bluetti-cli --help
```

---

## For Now

Use the Python SDK directly:

```python
from power_sdk import BluettiClient, MQTTTransport, MQTTConfig

# See examples/ directory for usage
```

---

**Note:** For SDK development tools (reverse engineering, etc.), see `_research/tools_dev/`

