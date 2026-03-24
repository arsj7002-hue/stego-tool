"""
steganalysis.py — Detect Hidden Data in Images
-----------------------------------------------
Implements two standard academic methods for LSB steganalysis:

1. Chi-Square Test (RS Analysis variant)
   Detects equalisation of even/odd pixel pair frequencies caused
   by LSB embedding. Most reliable on images with varied pixel values.

2. LSB Run-Length Analysis
   Short LSB runs + near-50/50 balance indicates random (hidden) data.
   Works best on images with structured regions (screenshots, graphics).

⚠️  Known limitation (standard in the field):
   Smooth images (strong blur, gradients) already have near-random LSBs
   due to pixel smoothing — these cannot be reliably analysed with LSB
   methods alone. This is a limitation of ALL LSB steganalysis tools,
   not specific to this implementation.
   Best results: use on photographs, screenshots, and PNG graphics.
"""

import math
from PIL import Image


# ── Method 1: Chi-Square Test ──────────────────────────────────────────────

def chi_square_analysis(img: Image.Image) -> dict:
    """
    Chi-square test on pixel value pair frequencies.
    LSB embedding equalises (2k, 2k+1) pairs — we detect this.
    """
    pixels = list(img.convert("RGB").getdata())
    n = len(pixels)
    channel_results = {}

    for ch_idx, ch_name in enumerate(("R", "G", "B")):
        freq = [0] * 256
        for p in pixels:
            freq[p[ch_idx]] += 1

        chi_sq = 0.0
        pairs_used = 0
        balanced_pairs = 0

        for i in range(0, 256, 2):
            obs_e = freq[i]
            obs_o = freq[i + 1]
            total = obs_e + obs_o
            expected = total / 2.0
            if expected > 2:
                chi_sq += ((obs_e - expected) ** 2) / expected
                chi_sq += ((obs_o - expected) ** 2) / expected
                pairs_used += 1
                if total > 0 and abs(obs_e - obs_o) / total < 0.05:
                    balanced_pairs += 1

        chi_per_px    = chi_sq / max(n, 1)
        balance_ratio = balanced_pairs / max(pairs_used, 1)

        # Stego signal: low chi_per_px + high balance_ratio
        suspicious = (chi_per_px < 0.003) and (balance_ratio > 0.55)

        channel_results[ch_name] = {
            "chi_square":    round(chi_sq, 2),
            "chi_per_pixel": round(chi_per_px, 6),
            "balance_ratio": round(balance_ratio, 4),
            "verdict":       "suspicious" if suspicious else "normal",
        }

    sus_count = sum(1 for r in channel_results.values() if r["verdict"] == "suspicious")
    avg_chi   = sum(r["chi_per_pixel"] for r in channel_results.values()) / 3

    if sus_count >= 2:
        verdict    = "LIKELY_STEGO"
        confidence = min(99, 60 + sus_count * 15)
    elif sus_count == 1:
        verdict    = "SUSPICIOUS"
        confidence = 45
    else:
        verdict    = "CLEAN"
        confidence = min(95, int(min(avg_chi * 2000 + 40, 95)))

    return {
        "method":              "Chi-Square Pair Analysis",
        "channels":            channel_results,
        "suspicious_channels": sus_count,
        "avg_chi_per_pixel":   round(avg_chi, 6),
        "verdict":             verdict,
        "confidence":          confidence,
        "explanation": (
            f"{sus_count}/3 channels show equalised pixel-pair distribution. "
            + ("Balanced pairs indicate LSB manipulation." if sus_count >= 2
               else "Pixel pairs show natural distribution.")
        ),
    }


# ── Method 2: LSB Run-Length Analysis ─────────────────────────────────────

def lsb_analysis(img: Image.Image) -> dict:
    """
    Measures LSB run lengths and balance.
    Random (stego) data produces very short runs and near-50/50 balance.
    """
    pixels = list(img.convert("RGB").getdata())
    channel_results = {}
    total_suspicion = 0.0

    for ch_idx, ch_name in enumerate(("R", "G", "B")):
        lsbs = [(p[ch_idx] & 1) for p in pixels]

        # Average run length
        run_lengths = []
        cur = 1
        for i in range(1, len(lsbs)):
            if lsbs[i] == lsbs[i-1]:
                cur += 1
            else:
                run_lengths.append(cur)
                cur = 1
        run_lengths.append(cur)
        avg_run = sum(run_lengths) / len(run_lengths)

        # Balance
        ones    = sum(lsbs)
        balance = ones / len(lsbs)
        bal_dev = abs(balance - 0.5)

        run_sus = avg_run < 2.05
        bal_sus = bal_dev < 0.01

        suspicion = (0.5 if run_sus else 0.0) + (0.5 if bal_sus else 0.0)
        total_suspicion += suspicion

        channel_results[ch_name] = {
            "avg_run_length":  round(avg_run, 4),
            "lsb_balance":     round(balance, 4),
            "suspicion_score": round(suspicion, 2),
            "verdict":         "suspicious" if suspicion >= 0.5 else "normal",
        }

    avg_sus   = total_suspicion / 3
    sus_count = sum(1 for r in channel_results.values() if r["verdict"] == "suspicious")

    if avg_sus >= 0.8 and sus_count >= 2:
        verdict    = "LIKELY_STEGO"
        confidence = min(99, int(avg_sus * 99))
    elif avg_sus >= 0.4 or sus_count >= 1:
        verdict    = "SUSPICIOUS"
        confidence = int(avg_sus * 70)
    else:
        verdict    = "CLEAN"
        confidence = min(95, int((1.0 - avg_sus) * 80 + 15))

    return {
        "method":              "LSB Run-Length Analysis",
        "avg_suspicion_score": round(avg_sus, 4),
        "channels":            channel_results,
        "verdict":             verdict,
        "confidence":          confidence,
        "explanation": (
            f"Avg suspicion: {avg_sus:.2f}. "
            + ("Short runs + near-50/50 balance = likely hidden data."
               if avg_sus >= 0.5
               else "LSB structure looks natural.")
        ),
    }


# ── Combined Analysis ──────────────────────────────────────────────────────

def analyze(image_path: str) -> dict:
    """Main entry point — runs both methods and returns combined verdict."""
    img        = Image.open(image_path)
    chi_result = chi_square_analysis(img)
    lsb_result = lsb_analysis(img)

    rank = {"CLEAN": 0, "SUSPICIOUS": 1, "LIKELY_STEGO": 2}
    cr   = rank[chi_result["verdict"]]
    lr   = rank[lsb_result["verdict"]]

    if cr == 2 and lr == 2:
        final_verdict    = "LIKELY_STEGO"
        final_confidence = max(chi_result["confidence"], lsb_result["confidence"])
    elif cr >= 1 and lr >= 1:
        final_verdict    = "SUSPICIOUS"
        final_confidence = (chi_result["confidence"] + lsb_result["confidence"]) // 2
    elif cr >= 1 or lr >= 1:
        final_verdict    = "SUSPICIOUS"
        final_confidence = 30
    else:
        final_verdict    = "CLEAN"
        final_confidence = min(chi_result["confidence"], lsb_result["confidence"])

    summary = {
        "LIKELY_STEGO": "⚠️  This image very likely contains hidden data.",
        "SUSPICIOUS":   "🔍 This image shows some signs of possible steganography.",
        "CLEAN":        "✅ No steganographic content detected.",
    }[final_verdict]

    return {
        "image":         image_path,
        "final_verdict": final_verdict,
        "confidence":    final_confidence,
        "summary":       summary,
        "lsb_analysis":  lsb_result,
        "chi_square":    chi_result,
    }