"""
crypto.py — RSA + AES-256-GCM Hybrid Encryption
-------------------------------------------------
How it works:
  1. Generate a random 32-byte AES session key
  2. Encrypt the actual data with AES-256-GCM (fast, authenticated)
  3. Encrypt the AES key with RSA-2048 OAEP (asymmetric, secure)
  4. Bundle: [rsa_encrypted_key | aes_nonce | aes_tag | ciphertext]

Why hybrid?
  - RSA alone can't encrypt large data
  - AES alone requires secure key exchange
  - Together: best of both worlds
"""

import os
import struct
from Crypto.PublicKey import RSA
from Crypto.Cipher  import AES, PKCS1_OAEP
from Crypto.Random  import get_random_bytes


# ── Key Generation ─────────────────────────────────────────────────────────

def generate_keypair(bits: int = 2048):
    """
    Generate an RSA key pair.
    Returns (private_key_pem, public_key_pem) as bytes.
    """
    key = RSA.generate(bits)
    private_pem = key.export_key()          # PEM bytes
    public_pem  = key.publickey().export_key()
    return private_pem, public_pem


def save_keypair(private_pem: bytes, public_pem: bytes, directory: str = "keys"):
    """Save PEM key files to disk."""
    os.makedirs(directory, exist_ok=True)
    priv_path = os.path.join(directory, "private.pem")
    pub_path  = os.path.join(directory, "public.pem")
    with open(priv_path, "wb") as f:
        f.write(private_pem)
    with open(pub_path, "wb") as f:
        f.write(public_pem)
    return priv_path, pub_path


def load_private_key(path: str) -> RSA.RsaKey:
    with open(path, "rb") as f:
        return RSA.import_key(f.read())


def load_public_key(path: str) -> RSA.RsaKey:
    with open(path, "rb") as f:
        return RSA.import_key(f.read())


# ── Encrypt ────────────────────────────────────────────────────────────────

def encrypt(data: bytes, public_key_pem: bytes) -> bytes:
    """
    Encrypt data using RSA+AES hybrid.

    Output format (all lengths fixed except ciphertext):
      [2 bytes: rsa_block_len][rsa_block][12 bytes: nonce][16 bytes: tag][ciphertext]
    """
    # 1. Random AES-256 session key
    session_key = get_random_bytes(32)

    # 2. Encrypt session key with RSA-OAEP
    rsa_key    = RSA.import_key(public_key_pem)
    rsa_cipher = PKCS1_OAEP.new(rsa_key)
    enc_session_key = rsa_cipher.encrypt(session_key)

    # 3. Encrypt data with AES-256-GCM
    aes_cipher = AES.new(session_key, AES.MODE_GCM)
    ciphertext, tag = aes_cipher.encrypt_and_digest(data)

    # 4. Pack everything together — nonce is 16 bytes (pycryptodome default)
    rsa_len = struct.pack(">H", len(enc_session_key))   # 2-byte big-endian length
    return rsa_len + enc_session_key + aes_cipher.nonce + tag + ciphertext


def decrypt(blob: bytes, private_key_pem: bytes) -> bytes:
    """
    Decrypt a hybrid-encrypted blob.
    Raises ValueError if decryption or authentication fails.
    """
    offset = 0

    # 1. Read RSA block length
    rsa_len = struct.unpack(">H", blob[offset:offset+2])[0]
    offset += 2

    # 2. Decrypt session key with RSA
    enc_session_key = blob[offset:offset+rsa_len]
    offset += rsa_len

    rsa_key    = RSA.import_key(private_key_pem)
    rsa_cipher = PKCS1_OAEP.new(rsa_key)
    try:
        session_key = rsa_cipher.decrypt(enc_session_key)
    except Exception:
        raise ValueError("RSA decryption failed — wrong private key?")

    # 3. Extract nonce (16 bytes) and tag (16 bytes)
    nonce = blob[offset:offset+16]; offset += 16
    tag   = blob[offset:offset+16]; offset += 16

    # 4. Decrypt + verify with AES-GCM
    aes_cipher = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
    try:
        plaintext = aes_cipher.decrypt_and_verify(blob[offset:], tag)
    except ValueError:
        raise ValueError("AES-GCM authentication failed — data may be tampered")

    return plaintext


# ── Password-based fallback (for CLI convenience) ──────────────────────────

def encrypt_with_password(data: bytes, password: str) -> bytes:
    """
    AES-256-GCM encryption using a password (PBKDF2 key derivation).
    Output: [16 bytes salt][12 bytes nonce][16 bytes tag][ciphertext]
    """
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Hash import SHA256

    salt       = get_random_bytes(16)
    key        = PBKDF2(password, salt, dkLen=32, count=200_000,
                        prf=lambda p, s: __import__('hmac').new(
                            p if isinstance(p, bytes) else p.encode(),
                            s, SHA256).digest())
    cipher     = AES.new(key, AES.MODE_GCM)
    ct, tag    = cipher.encrypt_and_digest(data)
    return salt + cipher.nonce + tag + ct


def decrypt_with_password(blob: bytes, password: str) -> bytes:
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Hash import SHA256

    salt   = blob[0:16]
    nonce  = blob[16:32]
    tag    = blob[32:48]
    ct     = blob[48:]
    key    = PBKDF2(password, salt, dkLen=32, count=200_000,
                    prf=lambda p, s: __import__('hmac').new(
                        p if isinstance(p, bytes) else p.encode(),
                        s, SHA256).digest())
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    try:
        return cipher.decrypt_and_verify(ct, tag)
    except ValueError:
        raise ValueError("Wrong password or data tampered")
