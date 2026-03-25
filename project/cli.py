"""
cli.py — StegoTool Command Line Interface
-----------------------------------------
Usage:
  python cli.py              → interactive menu (recommended)
  python cli.py --help       → see all commands

Commands:
  encode-text    Hide a text message in an image
  decode-text    Reveal a hidden text message
  encode-image   Hide an image inside another image
  decode-image   Extract a hidden image
  encode-file    Hide any file (PDF, ZIP, etc.) inside an image
  decode-file    Extract a hidden file
  keygen         Generate RSA key pair for encryption
"""

import argparse
import os
import sys
import time

# ── Path fix so imports work from any directory ────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stego import lsb_text, lsb_image, lsb_file


# ── Progress bar ──────────────────────────────────────────────────────────

def progress_bar(label: str, total_steps: int = 20, delay: float = 0.04):
    print(f"\n  {label}")
    for i in range(total_steps + 1):
        pct  = int(i / total_steps * 100)
        done = "█" * i
        left = "░" * (total_steps - i)
        print(f"\r  [{done}{left}] {pct}%", end="", flush=True)
        time.sleep(delay)
    print()


# ── Colours ───────────────────────────────────────────────────────────────

try:
    import colorama
    colorama.init()
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""


def ok(msg):   print(f"{GREEN}  ✓ {msg}{RESET}")
def err(msg):  print(f"{RED}  ✗ {msg}{RESET}")
def info(msg): print(f"{CYAN}  → {msg}{RESET}")
def warn(msg): print(f"{YELLOW}  ⚠ {msg}{RESET}")


# ── Banner ────────────────────────────────────────────────────────────────

BANNER = f"""{CYAN}{BOLD}
  ███████╗████████╗███████╗ ██████╗  ██████╗
  ██╔════╝╚══██╔══╝██╔════╝██╔════╝ ██╔═══██╗
  ███████╗   ██║   █████╗  ██║  ███╗██║   ██║
  ╚════██║   ██║   ██╔══╝  ██║   ██║██║   ██║
  ███████║   ██║   ███████╗╚██████╔╝╚██████╔╝
  ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝
        S T E G A N O G R A P H Y   T O O L
{RESET}"""


# ── Menu ──────────────────────────────────────────────────────────────────

MENU = f"""
{BOLD}  Choose an operation:{RESET}

  {CYAN}[1]{RESET} Hide text in image
  {CYAN}[2]{RESET} Reveal text from image
  {CYAN}[3]{RESET} Hide image inside image
  {CYAN}[4]{RESET} Extract hidden image
  {CYAN}[5]{RESET} Hide any file inside image
  {CYAN}[6]{RESET} Extract hidden file
  {CYAN}[7]{RESET} Generate RSA key pair
  {CYAN}[0]{RESET} Exit
"""


def prompt(label: str, default: str = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {CYAN}?{RESET} {label}{suffix}: ").strip()
    return val if val else (default or "")


def prompt_yes(label: str) -> bool:
    val = input(f"  {CYAN}?{RESET} {label} [y/N]: ").strip().lower()
    return val in ("y", "yes")


def interactive_menu():
    print(BANNER)
    while True:
        print(MENU)
        choice = input(f"  {BOLD}>{RESET} ").strip()

        if choice == "0":
            print(f"\n{CYAN}  Goodbye.{RESET}\n")
            break

        elif choice == "1":
            _menu_encode_text()
        elif choice == "2":
            _menu_decode_text()
        elif choice == "3":
            _menu_encode_image()
        elif choice == "4":
            _menu_decode_image()
        elif choice == "5":
            _menu_encode_file()
        elif choice == "6":
            _menu_decode_file()
        elif choice == "7":
            _menu_keygen()
        else:
            warn("Invalid choice.")

        input(f"\n  {YELLOW}Press Enter to continue...{RESET}")


# ── Menu Handlers ─────────────────────────────────────────────────────────

def _menu_encode_text():
    cover   = prompt("Cover image")
    message = prompt("Secret message")
    output  = prompt("Output", "stego_text.png")

    progress_bar("Encoding...")
    r = lsb_text.encode(cover, message, output)
    ok(f"Saved: {r['output']}")


def _menu_decode_text():
    stego = prompt("Stego image")

    progress_bar("Decoding...")
    r = lsb_text.decode(stego)
    print(f"\n  Message: {r['message']}\n")


def _menu_encode_image():
    cover  = prompt("Cover image")
    secret = prompt("Secret image")
    output = prompt("Output", "stego_image.png")

    progress_bar("Encoding...")
    r = lsb_image.encode(cover, secret, output)
    ok(f"Saved: {r['output']}")


def _menu_decode_image():
    stego  = prompt("Stego image")
    output = prompt("Output", "extracted.png")

    progress_bar("Extracting...")
    r = lsb_image.decode(stego, output)
    ok(f"Saved: {r['output']}")


def _menu_encode_file():
    cover  = prompt("Cover image")
    secret = prompt("File")
    output = prompt("Output", "stego_file.png")

    progress_bar("Encoding...")
    r = lsb_file.encode(cover, secret, output)
    ok(f"Saved: {r['output']}")


def _menu_decode_file():
    stego   = prompt("Stego image")
    out_dir = prompt("Output dir", "extracted")

    progress_bar("Extracting...")
    r = lsb_file.decode(stego, out_dir)
    ok(f"Saved: {r['saved_to']}")


def _menu_keygen():
    from stego.crypto import generate_keypair, save_keypair

    progress_bar("Generating keys...", delay=0.1)
    priv, pub = generate_keypair()
    p1, p2 = save_keypair(priv, pub, "keys")
    ok(f"Private: {p1}")
    ok(f"Public:  {p2}")


# ── CLI Commands ──────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("encode-text")
    sub.add_parser("decode-text")
    sub.add_parser("encode-image")
    sub.add_parser("decode-image")
    sub.add_parser("encode-file")
    sub.add_parser("decode-file")
    sub.add_parser("keygen")

    return parser


# ── Entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_menu()
    else:
        parser = build_parser()
        args = parser.parse_args()