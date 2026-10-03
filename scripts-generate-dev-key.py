"""Generate a local development Ed25519 keypair; protect the private output."""
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat

key = Ed25519PrivateKey.generate()
print("OPAP_SIGNING_PRIVATE_KEY_HEX=" + key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex())
print("PUBLIC_KEY_B64=" + base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode())
