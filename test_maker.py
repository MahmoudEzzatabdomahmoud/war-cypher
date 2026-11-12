"""
test_maker.py — Creates a test PNG with a secret message hidden inside it using LSB steganography.
Run this once to generate 'test_stego.png', then use [~] EXTRACT IMG in WarCyphere to pull it out.
"""
from PIL import Image
from stegano import lsb
import os

# ── 1. Create a simple carrier image (solid green, 200x200) ──────────────────
OUT_DIR  = os.path.dirname(os.path.abspath(__file__))
CARRIER  = os.path.join(OUT_DIR, "test_carrier.png")
STEGO    = os.path.join(OUT_DIR, "test_stego.png")
SECRET   = "WARCYPHERE_TEST: If you can read this, LSB extraction is working correctly!"

# Draw a simple 200x200 image — any PNG works as a carrier
img = Image.new("RGB", (200, 200), color=(0, 80, 0))
img.save(CARRIER)
print(f"[+] Carrier image saved: {CARRIER}")

# ── 2. Embed the secret message using stegano LSB ────────────────────────────
stego_img = lsb.hide(CARRIER, SECRET)
stego_img.save(STEGO)
print(f"[+] Stego image saved:   {STEGO}")
print(f"    Hidden message: {SECRET}")

# ── 3. Quick verify — reveal it back ─────────────────────────────────────────
revealed = lsb.reveal(STEGO)
print(f"\n[✓] Verification — lsb.reveal() returned:\n    {revealed}")

if revealed == SECRET:
    print("\n[✓] SUCCESS — EXTRACT IMG in WarCyphere will find this message.")
    print(f"    Load this file: {STEGO}")
else:
    print("\n[!] Something went wrong — revealed text doesn't match.")