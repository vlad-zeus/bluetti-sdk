# ADR-003: TLS Certificate Lifecycle Management

**Status**: Proposed
**Date**: 2026-02-14
**Author**: Zeus Fabric Team

## Context

Current MQTTConfig handles TLS certificates as raw bytes:

```python
config = MQTTConfig(
    device_sn="...",
    pfx_cert=cert_bytes,        # Raw bytes, in memory
    cert_password="password"     # Plain text password
)
```

### Security Concerns

1. **Memory exposure**: Certificates/passwords in memory as strings
2. **No lifecycle**: Certificates loaded once, never cleared
3. **No validation**: No cert expiry checks, chain validation
4. **Logging risk**: Passwords might leak in debug logs
5. **File handling**: No secure file reading patterns

### Requirements

- Secure certificate loading from files/memory
- Automatic cert validation (expiry, chain)
- Secure password handling (no plain text in memory)
- Proper cleanup (zero memory after use)
- Audit trail for security events

## Decision

Implement **secure certificate lifecycle** with proper handling:

### Architecture

```
CertificateStore (new)
  ├── load_from_file(path, password) -> TLSContext
  ├── load_from_bytes(data, password) -> TLSContext
  └── validate(cert) -> ValidationResult

TLSContext (new)
  ├── ssl_context: ssl.SSLContext
  ├── expiry: datetime
  ├── subject: str
  └── __del__() -> secure cleanup
```

### Key Principles

1. **Minimal memory exposure**: Load cert → create context → clear bytes
2. **Automatic validation**: Check expiry, chain on load
3. **Secure cleanup**: Zero sensitive data in __del__
4. **Audit logging**: Security events logged
5. **Type safety**: No raw strings for passwords

## Design

### Certificate Store

```python
from pathlib import Path
from ssl import SSLContext
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TLSContext:
    """Secure TLS context with metadata."""
    ssl_context: SSLContext
    expiry: datetime
    subject: str
    issuer: str

    def is_valid(self) -> bool:
        """Check if certificate is still valid."""
        return datetime.now() < self.expiry

    def __del__(self):
        """Secure cleanup."""
        # Zero sensitive data
        del self.ssl_context


class CertificateStore:
    """Secure certificate loading and validation."""

    @staticmethod
    def load_from_pfx(
        cert_path: Path,
        password: str,
        validate: bool = True
    ) -> TLSContext:
        """Load PFX certificate with validation.

        Args:
            cert_path: Path to .pfx file
            password: Certificate password
            validate: Validate cert (expiry, chain)

        Returns:
            TLSContext with SSL context

        Raises:
            CertificateError: If invalid or expired
        """
        # Load PFX file
        cert_bytes = cert_path.read_bytes()

        try:
            # Create SSL context
            context = CertificateStore._create_context(cert_bytes, password)

            # Validate if requested
            if validate:
                metadata = CertificateStore._validate_cert(cert_bytes, password)

                if metadata.expiry < datetime.now():
                    raise CertificateError(
                        f"Certificate expired: {metadata.expiry}"
                    )

            return TLSContext(
                ssl_context=context,
                expiry=metadata.expiry,
                subject=metadata.subject,
                issuer=metadata.issuer
            )
        finally:
            # Clear cert bytes from memory
            del cert_bytes
```

### Integration with MQTTConfig

```python
@dataclass
class MQTTConfig:
    """MQTT configuration with secure TLS."""
    device_sn: str
    broker: str = "mqtt-e.bluetti.com"
    port: int = 8883

    # NEW: Secure TLS context
    tls_context: Optional[TLSContext] = None

    # DEPRECATED: Raw bytes (backward compatibility)
    pfx_cert: Optional[bytes] = None
    cert_password: Optional[str] = None

    @classmethod
    def from_pfx_file(cls, device_sn: str, cert_path: Path, password: str):
        """Create config from PFX file (recommended)."""
        tls_context = CertificateStore.load_from_pfx(
            cert_path, password, validate=True
        )

        return cls(
            device_sn=device_sn,
            tls_context=tls_context
        )
```

### Usage

```python
# NEW: Secure loading
config = MQTTConfig.from_pfx_file(
    device_sn="...",
    cert_path=Path("cert.pfx"),
    password=os.environ["CERT_PASSWORD"]  # From env, not hardcoded
)

# OLD: Still supported (backward compatibility)
config = MQTTConfig(
    device_sn="...",
    pfx_cert=cert_bytes,
    cert_password="password"
)
```

## Consequences

### Positive

✅ **Security**: No plain text passwords in memory longer than needed
✅ **Validation**: Automatic cert expiry checks
✅ **Audit**: Security events logged
✅ **Best practices**: Follows OWASP secure cert handling
✅ **Type safety**: TLSContext type prevents misuse

### Negative

⚠️ **Complexity**: More code than raw bytes
⚠️ **Breaking**: Old raw bytes pattern deprecated
⚠️ **Dependencies**: May need cryptography library

### Migration

**Phase 1**: Add TLSContext (backward compatible)
- Keep pfx_cert/cert_password support
- Add tls_context option
- Deprecation warnings

**Phase 2**: Remove raw bytes (breaking)
- Only TLSContext supported
- Clear migration path documented

## Implementation Plan

### Out of Scope (Separate Increment)

TLS certificate handling is **separate from Architecture Hardening core**.
This ADR documents best practices for **future implementation**.

**Recommended approach**:
1. Keep current pfx_cert/password for now
2. Implement TLS hardening in dedicated security sprint
3. Focus Architecture Hardening on: Async API, Registry, Typed Transforms

### Future Files (when implemented)

- `bluetti_sdk/security/certificates.py` - CertificateStore, TLSContext
- `bluetti_sdk/security/__init__.py` - Public security API
- `tests/unit/security/test_certificates.py` - Certificate tests

## References

- [OWASP: Secure Certificate Handling](https://owasp.org/www-community/vulnerabilities/Insecure_Certificate_Validation)
- [Python ssl module](https://docs.python.org/3/library/ssl.html)
- [cryptography library](https://cryptography.io/)

## Acceptance Criteria (Future)

- [ ] CertificateStore validates cert expiry
- [ ] Secure cleanup in __del__
- [ ] No plain text passwords in memory
- [ ] Audit logging for security events
- [ ] Migration guide from raw bytes
- [ ] 100% test coverage for security code
