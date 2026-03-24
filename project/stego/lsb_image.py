"""
lsb_image.py — Hide an Image Inside Another Image (LSB)
--------------------------------------------------------
Uses 4 LSBs per channel to store the secret image's pixel data.
The secret image is resized to fit inside the cover if needed.

Payload format:
  First 64 pixels (header): secret image width (32 bits) + height (32 bits)
  Remaining pixels: secret image pixel data (R, G, B per pixel)
"""

import struct
from PIL import Image


_BITS        = 4           # bits per channel used for hiding
_MASK_CLEAR  = 0xF0        # mask to clear lower 4 bits
_HEADER_PIX  = 64          # pixels used for width/height header (64 bits each = 2x 32-bit ints)


def _max_secret_pixels(cover: Image.Image) -> int:
    total_pixels = cover.size[0] * cover.size[1]
    return total_pixels - _HEADER_PIX


def encode(cover_path: str, secret_path: str, output_path: str) -> dict:
    """
    Hide secret_path image inside cover_path, save to output_path.
    """
    cover  = Image.open(cover_path).convert("RGB")
    secret = Image.open(secret_path).convert("RGB")

    cover_w, cover_h = cover.size
    max_px = _max_secret_pixels(cover)

    # Resize secret if it won't fit
    sec_w, sec_h = secret.size
    if sec_w * sec_h > max_px:
        ratio  = (max_px / (sec_w * sec_h)) ** 0.5
        sec_w  = max(1, int(sec_w * ratio))
        sec_h  = max(1, int(sec_h * ratio))
        secret = secret.resize((sec_w, sec_h), Image.LANCZOS)

    cover_pixels  = list(cover.getdata())
    secret_pixels = list(secret.getdata())

    # --- Encode header (width + height) into first _HEADER_PIX pixels ---
    # Each pixel channel stores 1 bit of header using 4-bit slots
    header_bits = []
    for val in (sec_w, sec_h):
        for i in range(31, -1, -1):
            header_bits.append((val >> i) & 1)

    new_pixels = list(cover_pixels)  # copy

    # Write header bits (1 bit per pixel into R channel LSB of 4-bit slot)
    for i, bit in enumerate(header_bits):
        r, g, b = new_pixels[i]
        r = (r & _MASK_CLEAR) | (bit << 3)   # store in top bit of 4-bit slot
        new_pixels[i] = (r, g, b)

    # --- Encode secret pixel data starting at pixel _HEADER_PIX ---
    for idx, (sr, sg, sb) in enumerate(secret_pixels):
        px_idx = _HEADER_PIX + idx
        if px_idx >= len(new_pixels):
            break
        cr, cg, cb = new_pixels[px_idx]
        # Store upper 4 bits of secret channel into lower 4 bits of cover channel
        cr = (cr & _MASK_CLEAR) | (sr >> 4)
        cg = (cg & _MASK_CLEAR) | (sg >> 4)
        cb = (cb & _MASK_CLEAR) | (sb >> 4)
        new_pixels[px_idx] = (cr, cg, cb)

    out_img = Image.new("RGB", cover.size)
    out_img.putdata(new_pixels)
    out_img.save(output_path, "PNG")

    return {
        "output":      output_path,
        "cover_size":  f"{cover_w}x{cover_h}",
        "secret_size": f"{sec_w}x{sec_h}",
    }


def decode(stego_path: str, output_path: str) -> dict:
    """
    Extract hidden image from stego_path, save to output_path.
    """
    img    = Image.open(stego_path).convert("RGB")
    pixels = list(img.getdata())

    # --- Read header ---
    header_bits = []
    for i in range(_HEADER_PIX):
        r = pixels[i][0]
        header_bits.append((r >> 3) & 1)

    def bits_to_int(bits):
        val = 0
        for b in bits:
            val = (val << 1) | b
        return val

    sec_w = bits_to_int(header_bits[:32])
    sec_h = bits_to_int(header_bits[32:64])

    if sec_w <= 0 or sec_h <= 0 or sec_w > 10000 or sec_h > 10000:
        raise ValueError("No hidden image found or image is not a valid stego image.")

    # --- Read secret pixels ---
    secret_pixels = []
    for idx in range(sec_w * sec_h):
        px_idx = _HEADER_PIX + idx
        if px_idx >= len(pixels):
            break
        cr, cg, cb = pixels[px_idx]
        # Recover upper 4 bits (shift left, lower bits are approximate)
        sr = (cr & 0x0F) << 4
        sg = (cg & 0x0F) << 4
        sb = (cb & 0x0F) << 4
        secret_pixels.append((sr, sg, sb))

    out_img = Image.new("RGB", (sec_w, sec_h))
    out_img.putdata(secret_pixels)
    out_img.save(output_path, "PNG")

    return {
        "output":      output_path,
        "secret_size": f"{sec_w}x{sec_h}",
    }
