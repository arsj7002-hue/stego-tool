"""
steganalysis.py — Detect Hidden Data in Images
-----------------------------------------------
Two analysis methods:

1. LSB Pattern Analysis
   Checks if the least-significant bits of pixel channels
   look suspiciously uniform (random LSBs = likely hidden data).

2. Chi-Square Statistical Test
   Compares observed frequency of pixel values vs. expected frequency.
   Hidden data flattens the distribution — chi-square catches this.
   This is the standard academic method for detecting LSB steganography.

Returns a verdict: CLEAN / SUSPICIOUS / LIKELY_STEGO
"""

import math
from PIL import Image


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_lsbs(pixels: list, channel: int = 0) -> list:
    """Extract LSBs from a single channel (0=R, 1=G, 2=B)."""
    return [(p[channel] & 1) for p in pixels]


def _entropy(bits: list) -> float:
    """Shannon entropy of a bit list (0.0 = all same, 1.0 = perfectly random)."""
    if not bits:
        return 0.0
    ones  = sum(bits)
    zeros = len(bits) - ones
    total = len(bits)
    h = 0.0
    for count in (ones, zeros):
        if count > 0:
            p = count / total
            h -= p * math.log2(p)
    return h


# ── Method 1: LSB Pattern Analysis ────────────────────────────────────────

def lsb_analysis(img: Image.Image) -> dict:
    """
    Analyse LSB randomness across all three channels.
    Natural images have structured (non-random) LSBs.
    Stego images have near-random LSBs (entropy close to 1.0).
    """
    pixels = list(img.convert("RGB").getdata())

    results = {}
    total_entropy = 0.0

    for ch_idx, ch_name in enumerate(("R", "G", "B")):
        bits    = _get_lsbs(pixels, ch_idx)
        ones    = sum(bits)
        zeros   = len(bits) - ones
        ent     = _entropy(bits)
        balance = ones / len(bits) if bits else 0.5

        results[ch_name] = {
            "entropy":  round(ent, 4),
            "ones_pct": round(balance * 100, 2),
            "verdict":  "suspicious" if ent > 0.97 else "normal",
        }
        total_entropy += ent

    avg_entropy = total_entropy / 3

    # Natural image LSB entropy is usually 0.85–0.94
    # LSB steganography pushes it above 0.97
    if avg_entropy > 0.97:
        verdict = "LIKELY_STEGO"
        confidence = min(100, int((avg_entropy - 0.97) / 0.03 * 100))
    elif avg_entropy > 0.93:
        verdict = "SUSPICIOUS"
        confidence = int((avg_entropy - 0.93) / 0.04 * 60)
    else:
        verdict = "CLEAN"
        confidence = int((0.93 - avg_entropy) / 0.93 * 100)

    return {
        "method":       "LSB Pattern Analysis",
        "avg_entropy":  round(avg_entropy, 4),
        "channels":     results,
        "verdict":      verdict,
        "confidence":   confidence,
        "explanation": (
            f"Average LSB entropy: {avg_entropy:.4f}. "
            + ("High entropy indicates LSB manipulation." if avg_entropy > 0.93
               else "Normal entropy — LSBs look natural.")
        ),
    }


# ── Method 2: Chi-Square Test ──────────────────────────────────────────────

def chi_square_analysis(img: Image.Image) -> dict:
    """
    Chi-square test on pixel value pairs (0,1), (2,3), (4,5), ...
    In natural images, neighbouring even/odd pixel values are NOT equally likely.
    LSB steganography equalises them — chi-square detects this flattening.

    Lower chi-square p-value → more likely to contain hidden data.
    """
    pixels  = list(img.convert("RGB").getdata())
    channel_results = {}

    for ch_idx, ch_name in enumerate(("R", "G", "B")):
        # Count occurrences of each pixel value 0–255
        freq = [0] * 256
        for p in pixels:
            freq[p[ch_idx]] += 1

        # Pair up (0,1), (2,3), ..., (254,255)
        chi_sq = 0.0
        pairs_used = 0
        for i in range(0, 256, 2):
            observed_even = freq[i]
            observed_odd  = freq[i + 1]
            expected      = (observed_even + observed_odd) / 2.0
            if expected > 0:
                chi_sq += ((observed_even - expected) ** 2) / expected
                chi_sq += ((observed_odd  - expected) ** 2) / expected
                pairs_used += 1

        # Degrees of freedom = pairs_used - 1
        dof = max(pairs_used - 1, 1)

        # Approximate p-value using chi-square CDF approximation
        # p < 0.05 → statistically significant flattening → suspicious
        p_value = _chi_sq_p_value(chi_sq, dof)

        channel_results[ch_name] = {
            "chi_square": round(chi_sq, 2),
            "p_value":    round(p_value, 6),
            "verdict":    "suspicious" if p_value < 0.05 else "normal",
        }

    # Overall verdict: if any 2+ channels are suspicious → flag it
    suspicious_count = sum(
        1 for r in channel_results.values() if r["verdict"] == "suspicious"
    )

    if suspicious_count >= 2:
        verdict    = "LIKELY_STEGO"
        confidence = min(100, suspicious_count * 40)
    elif suspicious_count == 1:
        verdict    = "SUSPICIOUS"
        confidence = 35
    else:
        verdict    = "CLEAN"
        confidence = 90

    avg_p = sum(r["p_value"] for r in channel_results.values()) / 3

    return {
        "method":       "Chi-Square Statistical Test",
        "channels":     channel_results,
        "suspicious_channels": suspicious_count,
        "avg_p_value":  round(avg_p, 6),
        "verdict":      verdict,
        "confidence":   confidence,
        "explanation": (
            f"{suspicious_count}/3 channels show statistically significant "
            f"pixel-pair flattening (avg p={avg_p:.4f}). "
            + ("Low p-value indicates likely LSB manipulation."
               if avg_p < 0.05 else "P-values look natural.")
        ),
    }


def _chi_sq_p_value(chi_sq: float, dof: int) -> float:
    """
    Approximate p-value for chi-square distribution.
    Uses the regularised incomplete gamma function approximation.
    Good enough for our purposes without scipy dependency.
    """
    # Using the Wilson-Hilferty normal approximation for large dof
    if dof <= 0:
        return 1.0
    # Normal approximation: Z = ((chi_sq/dof)^(1/3) - (1 - 2/(9*dof))) / sqrt(2/(9*dof))
    k = dof
    z = ((chi_sq / k) ** (1/3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    # Survival function of standard normal (upper tail)
    return _standard_normal_sf(z)


def _standard_normal_sf(z: float) -> float:
    """Approximate upper-tail probability P(Z > z) for standard normal."""
    # Abramowitz & Stegun approximation
    if z < -6:
        return 1.0
    if z > 6:
        return 0.0
    t = 1.0 / (1.0 + 0.2316419 * abs(z))
    poly = t * (0.319381530
              + t * (-0.356563782
              + t * (1.781477937
              + t * (-1.821255978
              + t * 1.330274429))))
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    p   = pdf * poly
    return p if z >= 0 else 1.0 - p


# ── Combined Analysis ──────────────────────────────────────────────────────

def analyze(image_path: str) -> dict:
    """
    Run both analyses and return a combined report.
    This is the main entry point.
    """
    img = Image.open(image_path)

    lsb_result  = lsb_analysis(img)
    chi_result  = chi_square_analysis(img)

    # Combine verdicts — take the more alarming of the two
    rank = {"CLEAN": 0, "SUSPICIOUS": 1, "LIKELY_STEGO": 2}
    if rank[chi_result["verdict"]] >= rank[lsb_result["verdict"]]:
        final_verdict    = chi_result["verdict"]
        final_confidence = chi_result["confidence"]
    else:
        final_verdict    = lsb_result["verdict"]
        final_confidence = lsb_result["confidence"]

    # Human-readable summary
    if final_verdict == "LIKELY_STEGO":
        summary = "⚠️  This image very likely contains hidden data."
    elif final_verdict == "SUSPICIOUS":
        summary = "🔍 This image shows signs of possible steganography."
    else:
        summary = "✅ No steganographic content detected."

    return {
        "image":          image_path,
        "final_verdict":  final_verdict,
        "confidence":     final_confidence,
        "summary":        summary,
        "lsb_analysis":   lsb_result,
        "chi_square":     chi_result,
    }
