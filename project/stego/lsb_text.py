"""
lsb_text.py — Hide / Reveal Text in Images (LSB)
-------------------------------------------------
Optionally encrypts the message with RSA+AES-256-GCM before hiding.

Payload format embedded in image pixels:
  [4 bytes: payload length][1 byte: encrypted flag][payload bytes]

Uses 1 LSB per channel (R, G, B) — minimal visual impact.
"""

import struct
from PIL import Image


def _to_bits(data: bytes) -> list:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _from_bits(bits: list) -> bytes:
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i+8]:
            byte = (byte << 1) | b
        result.append(byte)
    return bytes(result)


def _capacity_bytes(img: Image.Image) -> int:
    w, h = img.size
    return (w * h * 3) // 8 - 5   # 3 channels, 1 bit each, minus 5-byte header


def encode(cover_path: str, message: str, output_path: str,
           public_key_pem: bytes = None) -> dict:
    """
    Hide message in cover_path, save to output_path.
    If public_key_pem is given, encrypts with RSA+AES-256-GCM first.
    """
    img    = Image.open(cover_path).convert("RGB")
    pixels = list(img.getdata())

    # Prepare payload
    msg_bytes = message.encode("utf-8")
    encrypted = False

    if public_key_pem:
        from stego.crypto import encrypt
        msg_bytes = encrypt(msg_bytes, public_key_pem)
        encrypted = True

    cap = _capacity_bytes(img)
    payload = struct.pack(">I", len(msg_bytes)) + bytes([1 if encrypted else 0]) + msg_bytes

    if len(payload) > cap:
        raise ValueError(
            f"Message too long. Max: {cap - 5:,} bytes, "
            f"message: {len(msg_bytes):,} bytes."
        )

    bits    = _to_bits(payload)
    bit_idx = 0
    new_pixels = []

    for pixel in pixels:
        r, g, b = pixel
        channels = [r, g, b]
        new_ch   = []
        for ch in channels:
            if bit_idx < len(bits):
                ch = (ch & ~1) | bits[bit_idx]
                bit_idx += 1
            new_ch.append(ch)
        new_pixels.append(tuple(new_ch))

    out_img = Image.new("RGB", img.size)
    out_img.putdata(new_pixels)
    out_img.save(output_path, "PNG")

    return {
        "output":      output_path,
        "message_len": len(message),
        "payload_size": len(payload),
        "capacity":    cap,
        "usage_pct":   round(len(payload) / cap * 100, 2),
        "encrypted":   encrypted,
    }


def decode(stego_path: str, private_key_pem: bytes = None) -> dict:
    """
    Reveal hidden message from stego_path.
    If message was encrypted, private_key_pem is required.
    """
    img    = Image.open(stego_path).convert("RGB")
    pixels = list(img.getdata())

    # Extract all LSBs
    bits = []
    for pixel in pixels:
        for ch in pixel[:3]:
            bits.append(ch & 1)

    def read_bits(start, n):
        return _from_bits(bits[start:start + n])

    # Read 4-byte length header
    payload_len = struct.unpack(">I", read_bits(0, 32))[0]
    if payload_len == 0 or payload_len > len(bits) // 8:
        raise ValueError("No hidden message found in this image.")

    # Read encrypted flag (1 byte)
    encrypted = bool(read_bits(32, 8)[0])
    offset    = 40

    msg_bytes = read_bits(offset, payload_len * 8)

    if encrypted:
        if private_key_pem is None:
            raise ValueError(
                "Message was encrypted. Provide --privkey to decrypt."
            )
        from stego.crypto import decrypt
        msg_bytes = decrypt(msg_bytes, private_key_pem)

    try:
        message = msg_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Decoding failed — wrong key or image not a stego image.")

    return {
        "message":   message,
        "encrypted": encrypted,
        "msg_len":   len(message),
    }