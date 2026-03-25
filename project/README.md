# 🔐 StegoTool — Steganography Suite

Hide text, images, and files inside ordinary images using LSB steganography with RSA+AES-256-GCM encryption.

## ⚡ Quick Start

```bash
git clone https://github.com/arsj7002-hue/stego-tool.git
cd stego-tool
pip install -r requirements.txt
python app.py
```

Browser opens automatically at `http://localhost:5000`

---

## 🧰 Features

| Feature | Description |
|---|---|
| **Hide Text in Image** | Embed secret messages using LSB encoding |
| **Hide Image in Image** | Conceal one image inside another |
| **Hide Any File** | Hide PDF, ZIP, DOCX or any file inside a PNG |
| **RSA+AES-256-GCM Encryption** | Hybrid encryption — RSA for key exchange, AES-GCM for data |
| **Steganalysis** | Detect hidden data using LSB entropy + Chi-square test |
| **Key Generator** | Generate 2048-bit RSA key pairs in the browser |
| **CLI Interface** | Full terminal interface with interactive menu |

---

## 💻 CLI Usage

```bash
# Interactive menu (recommended)
python cli.py

# Direct commands
python cli.py encode-text cover.png "secret message" output.png
python cli.py decode-text output.png
python cli.py encode-text cover.png "secret" output.png --pubkey keys/public.pem
python cli.py decode-text output.png --privkey keys/private.pem
python cli.py encode-image cover.png secret.png output.png
python cli.py decode-image output.png extracted.png
python cli.py encode-file cover.png document.pdf output.png
python cli.py decode-file output.png --outdir ./extracted
python cli.py analyze suspicious.png
python cli.py keygen --dir keys/
```

---

## 📁 Project Structure

```
stego-tool/
├── stego/
│   ├── __init__.py
│   ├── lsb_text.py        ← hide/reveal text in images
│   ├── lsb_image.py       ← hide/reveal image in image
│   ├── lsb_file.py        ← hide/reveal any file in image
│   ├── steganalysis.py    ← detect hidden data (LSB + chi-square)
│   └── crypto.py          ← RSA+AES-256-GCM hybrid encryption
├── web/
│   ├── server.py          ← Flask API
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── app.js
├── uploads/               ← auto-created (gitignored)
├── outputs/               ← auto-created (gitignored)
├── keys/                  ← auto-created (gitignored)
├── app.py                 ← entry point (starts web + opens browser)
├── cli.py                 ← terminal interface
└── requirements.txt
```

---

## 🔐 How Encryption Works

**RSA + AES-256-GCM Hybrid:**
1. A random 32-byte AES session key is generated
2. Your message is encrypted with AES-256-GCM (authenticated encryption)
3. The AES key is encrypted with RSA-2048 OAEP (asymmetric)
4. Both are bundled together and hidden in the image

This means even if someone extracts the hidden data, they can't read it without the RSA private key.

---

## 🧪 How Steganalysis Works

**LSB Entropy Analysis:**  
Natural images have structured (non-random) LSBs with entropy ~0.85–0.94. LSB steganography pushes entropy above 0.97 by randomising the least significant bits.

**Chi-Square Test:**  
In natural images, even and odd pixel values have different frequencies. LSB encoding equalises them — the chi-square test detects this statistical flattening. p-value < 0.05 indicates suspicious content.

---

## 📦 Requirements

- Python 3.8+
- Flask, Flask-Cors
- Pillow
- pycryptodome
- colorama (CLI colours)
