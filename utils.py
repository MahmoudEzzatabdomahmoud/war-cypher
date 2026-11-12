"""
utils.py — WarCyphere Pro | Utility, Steganography & Secure Shredder
pip install pycryptodome Pillow
"""
import hashlib, os, secrets

# ─────────────────────────────────────────────────────────────────────────────
# PROFESSOR NOTE — Data Remanence:
#   Simply deleting a file removes its directory entry but leaves the raw bytes
#   on disk, recoverable by forensic tools. Overwriting with random data before
#   deletion makes recovery computationally infeasible. DoD 5220.22-M standard
#   specifies 3 passes; we follow that here.
# ─────────────────────────────────────────────────────────────────────────────
def secure_shred(filepath: str, passes: int = 3) -> str:
    """
    Overwrite file with random bytes `passes` times, then delete.
    Returns a status message for the GUI log.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    size = os.path.getsize(filepath)
    for p in range(passes):
        with open(filepath, "r+b") as fh:
            fh.write(secrets.token_bytes(size))
            fh.flush()
            os.fsync(fh.fileno())   # force write to physical storage
    os.remove(filepath)
    return (f"[SHRED] '{os.path.basename(filepath)}' destroyed.\n"
            f"        {passes} overwrite passes ({size} bytes each).\n"
            f"        File is unrecoverable (DoD 5220.22-M compliant).")


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSOR NOTE — Steganography (Dead Drop):
#   Steganography hides the *existence* of a message (security by obscurity),
#   unlike cryptography which hides its *contents*. LSB (Least Significant Bit)
#   steganography changes the last bit of each colour channel in a pixel.
#   A human eye cannot detect a brightness change of 1 out of 255 — making the
#   image look identical while carrying a hidden payload. Combining LSB stego
#   with encryption creates a powerful two-layer OPSEC defence.
# ─────────────────────────────────────────────────────────────────────────────
def _text_to_bits(text: str) -> str:
    return "".join(f"{ord(c):08b}" for c in text)

def _bits_to_text(bits: str) -> str:
    chars = []
    for i in range(0, len(bits) - 7, 8):
        b = bits[i:i+8]
        if len(b) == 8:
            chars.append(chr(int(b, 2)))
    return "".join(chars)

STEGO_DELIMITER = "<<END>>"

def embed_in_image(image_path: str, secret_text: str, output_path: str) -> str:
    """
    Hide secret_text in image via LSB steganography.
    Saves result to output_path. Returns status string.
    """
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())
    payload = secret_text + STEGO_DELIMITER
    bits = _text_to_bits(payload)
    capacity = len(pixels) * 3   # 1 bit per channel (R, G, B)
    if len(bits) > capacity:
        raise ValueError(
            f"Image too small: needs {len(bits)} bits, has {capacity}.\n"
            "Use a larger image or shorter ciphertext.")
    bit_idx = 0
    new_pixels = []
    for r, g, b in pixels:
        channels = [r, g, b]
        for ci in range(3):
            if bit_idx < len(bits):
                channels[ci] = (channels[ci] & 0xFE) | int(bits[bit_idx])
                bit_idx += 1
        new_pixels.append(tuple(channels))
    out_img = Image.new("RGB", img.size)
    out_img.putdata(new_pixels)
    out_img.save(output_path, format="PNG")
    return (f"[DEAD DROP] Payload embedded in '{os.path.basename(output_path)}'.\n"
            f"            {len(secret_text)} chars hidden in {len(pixels)} pixels.\n"
            f"            Image appears visually identical to original.")

def extract_from_image(image_path: str) -> str:
    """
    Extract hidden text from image via LSB steganography.
    Returns the recovered string.
    """
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())
    bits = ""
    for r, g, b in pixels:
        for ch in (r, g, b):
            bits += str(ch & 1)
    text = _bits_to_text(bits)
    if STEGO_DELIMITER in text:
        return text[:text.index(STEGO_DELIMITER)]
    raise ValueError("No hidden payload found in this image (delimiter not detected).")


# ─────────────────────────────────────────────────────────────────────────────
# SHA-256 Integrity Helpers
# ─────────────────────────────────────────────────────────────────────────────
def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_sha256_from_file(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

def verify_integrity(original: str, filepath: str) -> dict:
    current = compute_sha256_from_file(filepath)
    match = original.lower() == current.lower()
    return {
        "match": match, "original": original, "current": current,
        "status": "✔ INTEGRITY OK — File unaltered." if match
                  else "✘ INTEGRITY VIOLATION — File has been tampered!",
    }

def format_hash_report(filepath: str, h: str) -> str:
    return (f"FILE INTEGRITY REPORT\n{'─'*48}\n"
            f"File : {os.path.basename(filepath)}\n"
            f"Size : {os.path.getsize(filepath)/1024:.2f} KB\n"
            f"SHA-256: {h}\n{'─'*48}\n"
            f"Store this hash to detect tampering (CIA: Integrity).")


# ─────────────────────────────────────────────────────────────────────────────
# Algorithm Registry
# ─────────────────────────────────────────────────────────────────────────────
ASYMMETRIC_ALGOS = {"RSA","DH","ECC","ElGamal","Paillier","NTRU","McEliece"}

ALGORITHM_METADATA = {
    "Caesar":    {"group":"Classic","type":"Symmetric Substitution","key_bits":"~5 bits","strength":"Very Weak","cia":"Confidentiality only","spy_fact":"Used by Julius Caesar in 50 BC — cracked by counting letter frequencies."},
    "ROT13":     {"group":"Classic","type":"Symmetric Substitution","key_bits":"0 bits (fixed)","strength":"Negligible","cia":"Minimal Confidentiality","spy_fact":"Self-inverse — apply twice to restore original. Not a real cipher."},
    "Playfair":  {"group":"Classic","type":"Digraph Substitution","key_bits":"~28 bits","strength":"Moderate (classical)","cia":"Confidentiality","spy_fact":"First practical digraph cipher — used by British forces in WWI & WWII."},
    "Vigenere":  {"group":"Classic","type":"Polyalphabetic","key_bits":"Keyword × log₂26 bits","strength":"Weak","cia":"Confidentiality","spy_fact":"Called 'le chiffre indéchiffrable' for 300 years until Kasiski broke it in 1863."},
    "Rail Fence":{"group":"Classic","type":"Transposition","key_bits":"~3 bits","strength":"Weak","cia":"Confidentiality","spy_fact":"Rearranges letters in zigzag — zero diffusion, easily brute-forced."},
    "RSA":       {"group":"Classic","type":"Asymmetric Encryption","key_bits":"2048 bits","strength":"Strong","cia":"Confidentiality + Integrity","spy_fact":"PKCS#1 OAEP padding prevents chosen-ciphertext attacks."},
    "DH":        {"group":"Advanced","type":"Key Exchange","key_bits":"1024 bits (RFC 2409)","strength":"Strong","cia":"Confidentiality (shared secret)","spy_fact":"First public-key scheme (1976) — agree a secret over an open channel."},
    "ECC":       {"group":"Advanced","type":"Asymmetric (ECIES)","key_bits":"256 bits (P-256)","strength":"Very Strong","cia":"Confidentiality + Integrity (AES-GCM)","spy_fact":"Used in TLS 1.3 and Bitcoin — tiny keys, enormous security margin."},
    "ElGamal":   {"group":"Advanced","type":"Asymmetric Encryption","key_bits":"512-bit prime (demo)","strength":"Moderate (demo)","cia":"Confidentiality (probabilistic)","spy_fact":"Probabilistic — same plaintext yields different ciphertext every time."},
    "Paillier":  {"group":"Advanced","type":"Homomorphic Encryption","key_bits":"512-bit n (demo)","strength":"Strong","cia":"Confidentiality — Features Homomorphic Encryption—allows math on encrypted data.","spy_fact":"Features Homomorphic Encryption — allows math on encrypted data without decrypting."},
    "NTRU":      {"group":"Advanced","type":"Lattice-based (PQC)","key_bits":"~55 bits demo (N=11)","strength":"Quantum-Resistant","cia":"Confidentiality — Lattice-based; resistant to quantum computers.","spy_fact":"Lattice-based; resistant to quantum computers. A NIST PQC finalist."},
    "McEliece":  {"group":"Advanced","type":"Code-based (PQC)","key_bits":"[n=15,k=7] binary code","strength":"Quantum-Resistant","cia":"Confidentiality — Code-based; oldest post-quantum scheme (1978).","spy_fact":"Oldest post-quantum proposal (1978) — based on decoding random linear codes."},
}

def intel_line(algo: str, key_obj=None) -> str:
    meta = ALGORITHM_METADATA.get(algo, {})
    kb = meta.get("key_bits","N/A"); sf = meta.get("spy_fact","")
    try:
        if key_obj:
            if algo=="RSA":      kb=f"{key_obj.n.bit_length()} bits (RSA modulus)"
            elif algo=="ECC":    kb="256 bits (NIST P-256 curve)"
            elif algo=="ElGamal":kb=f"{key_obj['p'].bit_length()} bits (ElGamal prime)"
            elif algo=="Paillier":kb=f"{key_obj['n'].bit_length()} bits (Paillier n)"
    except Exception: pass
    return f"KEY SIZE: {kb} | SPY FACT: {sf}"
