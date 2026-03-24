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
  analyze        Detect if an image contains hidden data
  keygen         Generate RSA key pair for encryption
"""

import argparse
import os
import sys
import time

# ── Path fix so imports work from any directory ────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stego import lsb_text, lsb_image, lsb_file, steganalysis


# ── Progress bar (no external dependency) ─────────────────────────────────

def progress_bar(label: str, total_steps: int = 20, delay: float = 0.04):
    """Simple animated progress bar."""
    print(f"\n  {label}")
    bar = ""
    for i in range(total_steps + 1):
        pct  = int(i / total_steps * 100)
        done = "█" * i
        left = "░" * (total_steps - i)
        print(f"\r  [{done}{left}] {pct}%", end="", flush=True)
        time.sleep(delay)
    print()   # newline after bar


# ── Colour helpers (Windows + Unix) ───────────────────────────────────────

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


# ── Banner ─────────────────────────────────────────────────────────────────

BANNER = f"""{CYAN}{BOLD}
  ███████╗████████╗███████╗ ██████╗  ██████╗
  ██╔════╝╚══██╔══╝██╔════╝██╔════╝ ██╔═══██╗
  ███████╗   ██║   █████╗  ██║  ███╗██║   ██║
  ╚════██║   ██║   ██╔══╝  ██║   ██║██║   ██║
  ███████║   ██║   ███████╗╚██████╔╝╚██████╔╝
  ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝
        S T E G A N O G R A P H Y   T O O L
{RESET}"""


# ── Interactive menu ───────────────────────────────────────────────────────

MENU = f"""
{BOLD}  Choose an operation:{RESET}

  {CYAN}[1]{RESET} Hide text in image
  {CYAN}[2]{RESET} Reveal text from image
  {CYAN}[3]{RESET} Hide image inside image
  {CYAN}[4]{RESET} Extract hidden image
  {CYAN}[5]{RESET} Hide any file (PDF, ZIP, DOCX...) inside image
  {CYAN}[6]{RESET} Extract hidden file
  {CYAN}[7]{RESET} Analyze image for hidden data
  {CYAN}[8]{RESET} Generate RSA key pair
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
            _menu_analyze()
        elif choice == "8":
            _menu_keygen()
        else:
            warn("Invalid choice. Enter a number from the menu.")

        input(f"\n  {YELLOW}Press Enter to continue...{RESET}")


# ── Menu handlers ──────────────────────────────────────────────────────────

def _menu_encode_text():
    print(f"\n{BOLD}  ── Hide Text in Image ──{RESET}")
    cover   = prompt("Cover image path (PNG/JPG)")
    message = prompt("Secret message")
    output  = prompt("Output image path", "stego_text.png")

    use_enc = prompt_yes("Encrypt message with RSA? (needs public key)")
    pub_key = None
    if use_enc:
        kpath = prompt("Public key path", "keys/public.pem")
        if not os.path.exists(kpath):
            err(f"Key not found: {kpath}. Run option [8] to generate keys first.")
            return
        with open(kpath, "rb") as f:
            pub_key = f.read()

    try:
        progress_bar("Encoding...", total_steps=15)
        result = lsb_text.encode(cover, message, output, public_key_pem=pub_key)
        ok(f"Done! Saved to: {result['output']}")
        info(f"Message length: {result['message_len']} chars")
        info(f"Capacity used:  {result['usage_pct']}%")
    except Exception as e:
        err(str(e))


def _menu_decode_text():
    print(f"\n{BOLD}  ── Reveal Text from Image ──{RESET}")
    stego = prompt("Stego image path")

    use_enc = prompt_yes("Was message encrypted with RSA?")
    priv_key = None
    if use_enc:
        kpath = prompt("Private key path", "keys/private.pem")
        if not os.path.exists(kpath):
            err(f"Key not found: {kpath}.")
            return
        with open(kpath, "rb") as f:
            priv_key = f.read()

    try:
        progress_bar("Decoding...", total_steps=15)
        result = lsb_text.decode(stego, private_key_pem=priv_key)
        ok("Message revealed:")
        print(f"\n  {GREEN}{'─'*50}{RESET}")
        print(f"  {result['message']}")
        print(f"  {GREEN}{'─'*50}{RESET}\n")
    except Exception as e:
        err(str(e))


def _menu_encode_image():
    print(f"\n{BOLD}  ── Hide Image Inside Image ──{RESET}")
    cover  = prompt("Cover image path")
    secret = prompt("Secret image path (to hide)")
    output = prompt("Output image path", "stego_image.png")

    try:
        progress_bar("Encoding...", total_steps=20)
        result = lsb_image.encode(cover, secret, output)
        ok(f"Done! Saved to: {result['output']}")
        info(f"Cover size:  {result['cover_size']}")
        info(f"Secret size: {result['secret_size']}")
    except Exception as e:
        err(str(e))


def _menu_decode_image():
    print(f"\n{BOLD}  ── Extract Hidden Image ──{RESET}")
    stego  = prompt("Stego image path")
    output = prompt("Output image path", "extracted_image.png")

    try:
        progress_bar("Extracting...", total_steps=20)
        result = lsb_image.decode(stego, output)
        ok(f"Done! Saved to: {result['output']}")
        info(f"Extracted size: {result['secret_size']}")
    except Exception as e:
        err(str(e))


def _menu_encode_file():
    print(f"\n{BOLD}  ── Hide Any File Inside Image ──{RESET}")
    cover  = prompt("Cover image path")
    secret = prompt("File to hide (PDF, ZIP, DOCX...)")
    output = prompt("Output image path", "stego_file.png")

    try:
        progress_bar("Encoding file...", total_steps=25)
        result = lsb_file.encode(cover, secret, output)
        ok(f"Done! Saved to: {result['output']}")
        info(f"File hidden:   {result['filename']} ({result['file_size']:,} bytes)")
        info(f"Capacity used: {result['usage_pct']}%")
    except Exception as e:
        err(str(e))


def _menu_decode_file():
    print(f"\n{BOLD}  ── Extract Hidden File ──{RESET}")
    stego     = prompt("Stego image path")
    out_dir   = prompt("Output directory", "extracted")

    try:
        progress_bar("Extracting file...", total_steps=25)
        result = lsb_file.decode(stego, out_dir)
        ok(f"Done! Saved to: {result['saved_to']}")
        info(f"Filename: {result['filename']} ({result['file_size']:,} bytes)")
    except Exception as e:
        err(str(e))


def _menu_analyze():
    print(f"\n{BOLD}  ── Analyze Image for Hidden Data ──{RESET}")
    image = prompt("Image path to analyze")

    try:
        progress_bar("Analyzing...", total_steps=20)
        result = steganalysis.analyze(image)

        print(f"\n  {BOLD}Results:{RESET}")
        print(f"  {'-'*48}")

        v = result["final_verdict"]
        color = GREEN if v == "CLEAN" else (YELLOW if v == "SUSPICIOUS" else RED)
        print(f"  Final verdict:  {color}{BOLD}{v}{RESET}")
        print(f"  Confidence:     {result['confidence']}%")
        print(f"  Summary:        {result['summary']}")

        print(f"\n  {CYAN}LSB Analysis:{RESET}")
        lsb = result["lsb_analysis"]
        print(f"    Avg entropy:  {lsb['avg_entropy']} (>0.97 = suspicious)")
        for ch, data in lsb["channels"].items():
            flag = "⚠" if data["verdict"] == "suspicious" else "✓"
            print(f"    {ch} channel:  entropy={data['entropy']}  {flag}")

        print(f"\n  {CYAN}Chi-Square Test:{RESET}")
        chi = result["chi_square"]
        print(f"    Suspicious channels: {chi['suspicious_channels']}/3")
        print(f"    Avg p-value:  {chi['avg_p_value']} (<0.05 = suspicious)")
        for ch, data in chi["channels"].items():
            flag = "⚠" if data["verdict"] == "suspicious" else "✓"
            print(f"    {ch} channel:  χ²={data['chi_square']}  p={data['p_value']}  {flag}")

        print(f"  {'-'*48}\n")

    except Exception as e:
        err(str(e))


def _menu_keygen():
    print(f"\n{BOLD}  ── Generate RSA Key Pair ──{RESET}")
    directory = prompt("Save keys to directory", "keys")

    try:
        from stego.crypto import generate_keypair, save_keypair
        progress_bar("Generating 2048-bit RSA key pair...", total_steps=10, delay=0.1)
        priv, pub = generate_keypair()
        priv_path, pub_path = save_keypair(priv, pub, directory)
        ok(f"Private key → {priv_path}")
        ok(f"Public key  → {pub_path}")
        warn("Keep private.pem secret! Share only public.pem.")
    except Exception as e:
        err(str(e))


# ── Argparse commands (non-interactive) ───────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="stego",
        description="StegoTool — hide data inside images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # encode-text
    p = sub.add_parser("encode-text", help="Hide text in image")
    p.add_argument("cover",   help="Cover image")
    p.add_argument("message", help="Secret message")
    p.add_argument("output",  help="Output stego image")
    p.add_argument("--pubkey", help="RSA public key for encryption")

    # decode-text
    p = sub.add_parser("decode-text", help="Reveal hidden text")
    p.add_argument("stego", help="Stego image")
    p.add_argument("--privkey", help="RSA private key for decryption")

    # encode-image
    p = sub.add_parser("encode-image", help="Hide image inside image")
    p.add_argument("cover",  help="Cover image")
    p.add_argument("secret", help="Image to hide")
    p.add_argument("output", help="Output stego image")

    # decode-image
    p = sub.add_parser("decode-image", help="Extract hidden image")
    p.add_argument("stego",  help="Stego image")
    p.add_argument("output", help="Output extracted image")

    # encode-file
    p = sub.add_parser("encode-file", help="Hide any file inside image")
    p.add_argument("cover",  help="Cover image")
    p.add_argument("file",   help="File to hide")
    p.add_argument("output", help="Output stego image")

    # decode-file
    p = sub.add_parser("decode-file", help="Extract hidden file")
    p.add_argument("stego",   help="Stego image")
    p.add_argument("--outdir", default="extracted", help="Output directory")

    # analyze
    p = sub.add_parser("analyze", help="Detect hidden data in image")
    p.add_argument("image", help="Image to analyze")

    # keygen
    p = sub.add_parser("keygen", help="Generate RSA key pair")
    p.add_argument("--dir", default="keys", help="Output directory")

    return parser


def run_command(args):
    """Execute non-interactive commands."""
    cmd = args.command

    if cmd == "encode-text":
        pub = open(args.pubkey, "rb").read() if args.pubkey else None
        progress_bar("Encoding...")
        r = lsb_text.encode(args.cover, args.message, args.output, public_key_pem=pub)
        ok(f"Saved: {r['output']}  ({r['usage_pct']}% capacity used)")

    elif cmd == "decode-text":
        priv = open(args.privkey, "rb").read() if args.privkey else None
        progress_bar("Decoding...")
        r = lsb_text.decode(args.stego, private_key_pem=priv)
        print(f"\n  Message: {r['message']}\n")

    elif cmd == "encode-image":
        progress_bar("Encoding image...")
        r = lsb_image.encode(args.cover, args.secret, args.output)
        ok(f"Saved: {r['output']}")

    elif cmd == "decode-image":
        progress_bar("Extracting image...")
        r = lsb_image.decode(args.stego, args.output)
        ok(f"Saved: {r['output']}")

    elif cmd == "encode-file":
        progress_bar("Encoding file...")
        r = lsb_file.encode(args.cover, args.file, args.output)
        ok(f"Saved: {r['output']}  ({r['filename']}, {r['usage_pct']}% used)")

    elif cmd == "decode-file":
        progress_bar("Extracting file...")
        r = lsb_file.decode(args.stego, args.outdir)
        ok(f"Extracted: {r['saved_to']}")

    elif cmd == "analyze":
        progress_bar("Analyzing...")
        r = steganalysis.analyze(args.image)
        print(f"\n  Verdict: {r['final_verdict']}  ({r['confidence']}% confidence)")
        print(f"  {r['summary']}\n")

    elif cmd == "keygen":
        from stego.crypto import generate_keypair, save_keypair
        progress_bar("Generating RSA keys...", delay=0.1)
        priv, pub = generate_keypair()
        p1, p2 = save_keypair(priv, pub, args.dir)
        ok(f"Private: {p1}")
        ok(f"Public:  {p2}")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments → launch interactive menu
        interactive_menu()
    else:
        parser = build_parser()
        args   = parser.parse_args()
        if not args.command:
            parser.print_help()
        else:
            try:
                run_command(args)
            except Exception as e:
                err(str(e))
                sys.exit(1)