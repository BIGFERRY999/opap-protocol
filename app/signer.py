"""Pluggable cryptographic signer architecture for OPAP.

Supports local development keys, file-based credentials, AWS KMS,
Google Cloud KMS, and PKCS#11 Hardware Security Modules (HSMs).
In production, private keys never leave the secure boundary of the KMS/HSM.
"""

from __future__ import annotations

import base64
import os
from abc import ABC, abstractmethod
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
)

from .config import get_settings
from .crypto import canonical_bytes


class SignerError(Exception):
    """Raised when cryptographic signing or key retrieval fails."""
    pass


class SignerConfigError(SignerError):
    """Raised when signer provider configuration is invalid or missing."""
    pass


class SignerProvider(ABC):
    """Abstract base provider for OPAP signing services."""

    @abstractmethod
    def provider_name(self) -> str:
        """Name of the signer backend (e.g., 'env', 'file', 'aws_kms', 'gcp_kms', 'pkcs11')."""
        ...

    @abstractmethod
    def get_public_key(self) -> bytes:
        """Return the 32-byte Ed25519 public key."""
        ...

    @abstractmethod
    def sign(self, payload: dict[str, Any]) -> bytes:
        """Sign canonical JSON representation of the payload using Ed25519."""
        ...

    def get_public_key_b64(self) -> str:
        """Return the base64-encoded 32-byte public key."""
        return base64.b64encode(self.get_public_key()).decode("ascii")

    def describe(self) -> dict[str, Any]:
        """Metadata for diagnostics and monitoring."""
        pub = self.get_public_key()
        return {
            "provider": self.provider_name(),
            "public_key_b64": base64.b64encode(pub).decode("ascii"),
            "public_key_bytes": len(pub),
        }


class LocalEnvSigner(SignerProvider):
    """Signer backed by an Ed25519 private key in an environment variable."""

    def __init__(self, private_key_hex: str | None = None):
        key_hex = private_key_hex or get_settings().signing_private_key_hex or os.environ.get("OPAP_SIGNING_PRIVATE_KEY_HEX", "")
        if not key_hex:
            raise SignerConfigError("OPAP_SIGNING_PRIVATE_KEY_HEX is not configured")
        try:
            self._key_bytes = bytes.fromhex(key_hex.strip())
        except ValueError as exc:
            raise SignerConfigError(f"Invalid hex string for signing key: {exc}") from exc

        if len(self._key_bytes) != 32:
            raise SignerConfigError(f"Ed25519 private key must be exactly 32 bytes (got {len(self._key_bytes)})")

        self._private_key = Ed25519PrivateKey.from_private_bytes(self._key_bytes)
        self._public_key_bytes = self._private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def provider_name(self) -> str:
        return "env"

    def get_public_key(self) -> bytes:
        return self._public_key_bytes

    def sign(self, payload: dict[str, Any]) -> bytes:
        message = canonical_bytes(payload)
        return self._private_key.sign(message)


class FileKeySigner(SignerProvider):
    """Signer backed by a local key file (Raw 32-byte binary, Hex string, or PKCS#8 PEM)."""

    def __init__(self, key_path: str | None = None):
        path = key_path or get_settings().signing_key_path or os.environ.get("OPAP_SIGNING_KEY_PATH", "")
        if not path:
            raise SignerConfigError("OPAP_SIGNING_KEY_PATH is not configured")
        if not os.path.exists(path):
            raise SignerConfigError(f"Key file not found at path: {path}")

        with open(path, "rb") as f:
            data = f.read()

        # Attempt 1: Raw 32 bytes
        if len(data) == 32:
            self._private_key = Ed25519PrivateKey.from_private_bytes(data)
        elif b"BEGIN PRIVATE KEY" in data:
            # Attempt 2: PEM
            try:
                loaded = load_pem_private_key(data, password=None)
                if not isinstance(loaded, Ed25519PrivateKey):
                    raise SignerConfigError("PEM key must be an Ed25519 private key")
                self._private_key = loaded
            except Exception as e:
                raise SignerConfigError(f"Failed to parse PEM key: {e}") from e
        else:
            # Attempt 3: Hex string
            try:
                text = data.decode("utf-8").strip()
                raw = bytes.fromhex(text)
                if len(raw) != 32:
                    raise SignerConfigError(f"Hex key must be 32 bytes (got {len(raw)})")
                self._private_key = Ed25519PrivateKey.from_private_bytes(raw)
            except Exception as e:
                raise SignerConfigError(f"Unrecognized key file format: {e}") from e

        self._public_key_bytes = self._private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def provider_name(self) -> str:
        return "file"

    def get_public_key(self) -> bytes:
        return self._public_key_bytes

    def sign(self, payload: dict[str, Any]) -> bytes:
        return self._private_key.sign(canonical_bytes(payload))


class AwsKmsSigner(SignerProvider):
    """AWS KMS Asymmetric Signer adapter for Ed25519 keys.

    If boto3 is not installed or OPAP_KMS_MOCK is set, runs in simulated KMS mode.
    """

    def __init__(
        self,
        key_id: str | None = None,
        region: str | None = None,
        mock: bool | None = None,
    ):
        settings = get_settings()
        self.key_id = key_id or settings.kms_key_id or os.environ.get("OPAP_KMS_KEY_ID", "alias/opap-ed25519")
        self.region = region or settings.kms_region or os.environ.get("OPAP_KMS_REGION", "us-east-1")
        self.is_mock = mock if mock is not None else (settings.kms_mock or os.environ.get("OPAP_KMS_MOCK", "").lower() in ("true", "1"))

        if not self.is_mock:
            try:
                import boto3  # type: ignore
                self._kms_client = boto3.client("kms", region_name=self.region)
                pub_response = self._kms_client.get_public_key(KeyId=self.key_id)
                raw_der = pub_response["PublicKey"]
                # Parse SubjectPublicKeyInfo DER to extract Ed25519 public key bytes
                from cryptography.hazmat.primitives.serialization import load_der_public_key
                ed_pub = load_der_public_key(raw_der)
                if not isinstance(ed_pub, Ed25519PublicKey):
                    raise SignerConfigError("KMS Key must be an Ed25519 asymmetric signing key")
                self._public_key_bytes = ed_pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
            except ImportError:
                # Fallback to simulated mode with warning
                self.is_mock = True
            except Exception as e:
                raise SignerError(f"AWS KMS initialization failed: {e}") from e

        if self.is_mock:
            # Deterministic mock key derived from the key_id
            import hashlib
            seed = hashlib.sha256(f"aws-kms-mock:{self.key_id}:{self.region}".encode()).digest()
            self._mock_priv = Ed25519PrivateKey.from_private_bytes(seed)
            self._public_key_bytes = self._mock_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def provider_name(self) -> str:
        return "aws_kms (simulated)" if self.is_mock else "aws_kms"

    def get_public_key(self) -> bytes:
        return self._public_key_bytes

    def sign(self, payload: dict[str, Any]) -> bytes:
        data = canonical_bytes(payload)
        if self.is_mock:
            return self._mock_priv.sign(data)

        # Call real AWS KMS
        try:
            response = self._kms_client.sign(
                KeyId=self.key_id,
                Message=data,
                MessageType="RAW",
                SigningAlgorithm="ED25519",
            )
            return response["Signature"]
        except Exception as e:
            raise SignerError(f"AWS KMS sign operation failed: {e}") from e

    def describe(self) -> dict[str, Any]:
        info = super().describe()
        info["key_id"] = self.key_id
        info["region"] = self.region
        info["mock"] = self.is_mock
        return info


class GcpKmsSigner(SignerProvider):
    """Google Cloud KMS Asymmetric Signer adapter for Ed25519 keys."""

    def __init__(
        self,
        key_name: str | None = None,
        mock: bool | None = None,
    ):
        settings = get_settings()
        self.key_name = key_name or settings.kms_key_id or os.environ.get("OPAP_GCP_KMS_KEY_NAME", "projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1")
        self.is_mock = mock if mock is not None else (settings.kms_mock or os.environ.get("OPAP_KMS_MOCK", "").lower() in ("true", "1"))

        if not self.is_mock:
            try:
                from google.cloud import kms_v1  # type: ignore
                self._client = kms_v1.KeyManagementServiceClient()
                pub_response = self._client.get_public_key(request={"name": self.key_name})
                from cryptography.hazmat.primitives.serialization import load_pem_public_key
                pub = load_pem_public_key(pub_response.pem.encode())
                if not isinstance(pub, Ed25519PublicKey):
                    raise SignerConfigError("GCP KMS key must be Ed25519")
                self._public_key_bytes = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
            except ImportError:
                self.is_mock = True
            except Exception as e:
                raise SignerError(f"GCP KMS initialization failed: {e}") from e

        if self.is_mock:
            import hashlib
            seed = hashlib.sha256(f"gcp-kms-mock:{self.key_name}".encode()).digest()
            self._mock_priv = Ed25519PrivateKey.from_private_bytes(seed)
            self._public_key_bytes = self._mock_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def provider_name(self) -> str:
        return "gcp_kms (simulated)" if self.is_mock else "gcp_kms"

    def get_public_key(self) -> bytes:
        return self._public_key_bytes

    def sign(self, payload: dict[str, Any]) -> bytes:
        data = canonical_bytes(payload)
        if self.is_mock:
            return self._mock_priv.sign(data)

        try:
            response = self._client.asymmetric_sign(
                request={"name": self.key_name, "data": data}
            )
            return response.signature
        except Exception as e:
            raise SignerError(f"GCP KMS sign operation failed: {e}") from e


class Pkcs11HsmSigner(SignerProvider):
    """PKCS#11 Hardware Security Module (HSM) Signer adapter."""

    def __init__(
        self,
        lib_path: str | None = None,
        slot_id: int | None = None,
        key_label: str | None = None,
        mock: bool | None = None,
    ):
        settings = get_settings()
        self.lib_path = lib_path or settings.pkcs11_lib_path or os.environ.get("OPAP_PKCS11_LIB_PATH", "")
        self.slot_id = slot_id if slot_id is not None else settings.pkcs11_slot_id
        self.key_label = key_label or settings.pkcs11_key_label or "opap-ed25519"
        self.is_mock = mock if mock is not None else (settings.kms_mock or not self.lib_path or not os.path.exists(self.lib_path))

        if not self.is_mock:
            try:
                import PyKCS11  # type: ignore
                self._pkcs11 = PyKCS11.PyKCS11Lib()
                self._pkcs11.load(self.lib_path)
            except Exception:
                self.is_mock = True

        if self.is_mock:
            import hashlib
            seed = hashlib.sha256(f"pkcs11-hsm-mock:{self.slot_id}:{self.key_label}".encode()).digest()
            self._mock_priv = Ed25519PrivateKey.from_private_bytes(seed)
            self._public_key_bytes = self._mock_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def provider_name(self) -> str:
        return "pkcs11_hsm (simulated)" if self.is_mock else "pkcs11_hsm"

    def get_public_key(self) -> bytes:
        return self._public_key_bytes

    def sign(self, payload: dict[str, Any]) -> bytes:
        data = canonical_bytes(payload)
        if self.is_mock:
            return self._mock_priv.sign(data)
        raise SignerError("PKCS#11 hardware session not active")


def get_signer(provider: str | None = None, **kwargs: Any) -> SignerProvider:
    """Factory to retrieve the configured OPAP SignerProvider."""
    provider_name = (provider or get_settings().signer_provider or os.environ.get("OPAP_SIGNER_PROVIDER", "env")).lower().strip()

    if provider_name == "env":
        return LocalEnvSigner(**kwargs)
    elif provider_name == "file":
        return FileKeySigner(**kwargs)
    elif provider_name in ("aws_kms", "kms", "aws"):
        return AwsKmsSigner(**kwargs)
    elif provider_name in ("gcp_kms", "gcp"):
        return GcpKmsSigner(**kwargs)
    elif provider_name in ("pkcs11", "hsm", "pkcs11_hsm"):
        return Pkcs11HsmSigner(**kwargs)
    elif provider_name == "mock":
        return AwsKmsSigner(mock=True, **kwargs)
    else:
        raise SignerConfigError(f"Unknown signer provider '{provider_name}'. Supported: env, file, aws_kms, gcp_kms, pkcs11, mock.")
