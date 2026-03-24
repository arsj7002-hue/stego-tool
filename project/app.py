"""
app.py — StegoTool Entry Point
--------------------------------
Run:  python app.py
Opens http://localhost:5000 in your browser automatically.
"""

import os
import sys
import threading
import webbrowser

# Fix import paths — works from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.server import app

PORT = 5000
URL  = f"http://localhost:{PORT}"


def open_browser():
    """Open browser after a short delay to let Flask start."""
    import time
    time.sleep(1.2)
    webbrowser.open(URL)


if __name__ == "__main__":
    print(f"""
  ███████╗████████╗███████╗ ██████╗  ██████╗
  ██╔════╝╚══██╔══╝██╔════╝██╔════╝ ██╔═══██╗
  ███████╗   ██║   █████╗  ██║  ███╗██║   ██║
  ╚════██║   ██║   ██╔══╝  ██║   ██║██║   ██║
  ███████║   ██║   ███████╗╚██████╔╝╚██████╔╝
  ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝

  Starting StegoTool at {URL}
  Opening browser automatically...
  Press Ctrl+C to stop.
    """)

    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    app.run(host="0.0.0.0", port=PORT, debug=False)
