"""
lsb_file.py — Hide Any File Inside an Image (LSB)
--------------------------------------------------
Supports any file type: PDF, ZIP, DOCX, MP3, etc.

Payload format embedded in image:
  [4 bytes: filename length][filename bytes][4 bytes: file size][file bytes]

Uses 2 LSBs per channel (R, G, B) for faster encoding of larger payloads.
"""

import struct
from PIL import Image


# bits per channel — 2 gives 6 bits/pixel, balancing capacity vs. quality
_BITS = 2
_MASK = (1 << _BITS) - 1       # e.g. 0b11 for 2 bits


def _capacity_bytes(img: Image.Image) -> int:
    """Max bytes we can hide in this image."""
    w, h = img.size
    total_bits = w * h * 3 * _BITS   # 3 channels
    return (total_bits // 8) - 8      # minus 8 bytes for the two length headers


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


def encode(cover_path: str, file_path: str, output_path: str) -> dict:
    """
    Hide file_path inside cover_path, save to output_path.
    Returns info dict with capacity stats.
    """
    img = Image.open(cover_path).convert("RGB")
    pixels = list(img.getdata())

    # Read file to hide
    with open(file_path, "rb") as f:
        file_data = f.read()

    import os
    filename = os.path.basename(file_path).encode("utf-8")

    # Build payload: [4B fname_len][fname][4B data_len][data]
    payload = (
        struct.pack(">I", len(filename)) +
        filename +
        struct.pack(">I", len(file_data)) +
        file_data
    )

    cap = _capacity_bytes(img)
    if len(payload) > cap:
        raise ValueError(
            f"File too large. Max capacity: {cap:,} bytes, "
            f"file+header: {len(payload):,} bytes. "
            f"Use a larger cover image."
        )

    bits = _to_bits(payload)
    bit_idx = 0
    new_pixels = []

    for pixel in pixels:
        r, g, b = pixel
        channels = [r, g, b]
        new_channels = []
        for ch in channels:
            if bit_idx < len(bits):
                # embed _BITS bits into LSBs
                chunk = 0
                for _ in range(_BITS):
                    chunk = (chunk << 1) | (bits[bit_idx] if bit_idx < len(bits) else 0)
                    bit_idx += 1
                ch = (ch & ~_MASK) | chunk
            new_channels.append(ch)
        new_pixels.append(tuple(new_channels))

    out_img = Image.new("RGB", img.size)
    out_img.putdata(new_pixels)
    out_img.save(output_path, "PNG")

    return {
        "filename": os.path.basename(file_path),
        "file_size": len(file_data),
        "payload_size": len(payload),
        "capacity": cap,
        "usage_pct": round(len(payload) / cap * 100, 2),
        "output": output_path,
    }


def decode(stego_path: str, output_dir: str = ".") -> dict:
    """
    Extract a hidden file from stego_path, save to output_dir.
    Returns info dict with filename and size.
    """
    import os
    img = Image.open(stego_path).convert("RGB")
    pixels = list(img.getdata())

    # Extract all bits from LSBs
    bits = []
    for pixel in pixels:
        for ch in pixel[:3]:
            for i in range(_BITS - 1, -1, -1):
                bits.append((ch >> i) & 1)

    def read_bits(start, n_bits):
        return _from_bits(bits[start:start + n_bits])

    # Read filename length (32 bits = 4 bytes)
    fname_len = struct.unpack(">I", read_bits(0, 32))[0]
    if fname_len == 0 or fname_len > 512:
        raise ValueError("No hidden file found or image is not a valid stego image.")

    offset = 32
    fname_bytes = read_bits(offset, fname_len * 8)
    filename = fname_bytes.decode("utf-8")
    offset += fname_len * 8

    # Read file data length
    data_len = struct.unpack(">I", read_bits(offset, 32))[0]
    offset += 32

    if data_len == 0 or data_len > len(bits) // 8:
        raise ValueError("Corrupt stego image — invalid data length.")

    file_data = read_bits(offset, data_len * 8)

    # Save extracted file
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, filename)
    with open(out_path, "wb") as f:
        f.write(file_data)

    return {
        "filename": filename,
        "file_size": len(file_data),
        "saved_to": out_path,
    }