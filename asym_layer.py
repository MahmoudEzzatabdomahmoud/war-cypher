"""
asym_layer.py — WarCyphere Pro | Unified Asymmetric Cryptography Layer
Strict separation: private keys stay here; KEY INPUT is only for friend's public key.
"""
import base64, json, math, random
from Crypto.PublicKey import RSA as _RSA, ECC as _ECC
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from Crypto.Util.number import getPrime, long_to_bytes, bytes_to_long
import ciphers

_DH_P = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE65381"
    "FFFFFFFFFFFFFFFF", 16)
_DH_G = 2

def _aes_enc(key32, data):
    c = AES.new(key32, AES.MODE_GCM)
    ct, tag = c.encrypt_and_digest(data)
    return base64.b64encode(c.nonce).decode(), base64.b64encode(tag).decode(), base64.b64encode(ct).decode()

def _aes_dec(key32, nonce_b64, tag_b64, ct_b64):
    c = AES.new(key32, AES.MODE_GCM, nonce=base64.b64decode(nonce_b64))
    return c.decrypt_and_verify(base64.b64decode(ct_b64), base64.b64decode(tag_b64))

def _b64j(obj): return base64.b64encode(json.dumps(obj).encode()).decode()
def _j64(s):    return json.loads(base64.b64decode(s))


class AsymLayer:
    """
    Single object managing all 7 asymmetric algorithms with strict key separation.
    generate_keys(algo) → public_key_str  (stores private key internally)
    encrypt(algo, pub_key_str, plaintext) → base64_ciphertext
    decrypt(algo, base64_ciphertext)      → plaintext  (uses stored private key)
    """
    def __init__(self):
        self._priv = {}   # algo → private key object; NEVER exposed to GUI

    def has_private(self, algo): return algo in self._priv

    # ── Key Generation ────────────────────────────────────────────────────────
    def generate_keys(self, algo) -> str:
        """Generate key pair. Store private. Return public key string."""
        if algo == "RSA":
            k = _RSA.generate(2048); self._priv["RSA"] = k
            return k.public_key().export_key().decode()

        if algo == "ECC":
            k = _ECC.generate(curve="P-256"); self._priv["ECC"] = k
            return k.public_key().export_key(format="PEM")

        if algo == "DH":
            a = random.randrange(2, _DH_P - 2)
            self._priv["DH"] = a
            # Public value = g^a mod p, returned as hex for copy-paste
            return hex(pow(_DH_G, a, _DH_P))

        if algo == "ElGamal":
            p = getPrime(512); g = 2
            x = random.randrange(2, p-2); y = pow(g, x, p)
            self._priv["ElGamal"] = {"p": p, "g": g, "x": x, "y": y}
            return json.dumps({"p": hex(p), "g": g, "y": hex(y)})

        if algo == "Paillier":
            p = getPrime(256); q = getPrime(256)
            while p == q: q = getPrime(256)
            n = p*q; lam = ((p-1)*(q-1))//math.gcd(p-1,q-1)
            g = n+1; mu = pow(lam,-1,n)
            self._priv["Paillier"] = {"n":n,"g":g,"lam":lam,"mu":mu}
            return json.dumps({"n": hex(n), "g": hex(g)})

        if algo == "NTRU":
            k = ciphers.ntru_generate_keys(); self._priv["NTRU"] = k
            return json.dumps({"h":k["h"],"N":k["N"],"p":k["p"],"q":k["q"]})

        if algo == "McEliece":
            k = ciphers.mceliece_generate_keys(); self._priv["McEliece"] = k
            return json.dumps({"Gpub":k["Gpub"],"k":k["k"],"n":k["n"]})

        raise ValueError(f"Unknown algorithm: {algo}")

    # ── Encryption (uses FRIEND's public key string from KEY INPUT) ───────────
    def encrypt(self, algo, pub_key_str: str, plaintext: str) -> str:
        """Encrypt with friend's public key. Returns base64 ciphertext."""
        data = plaintext.encode("utf-8")

        if algo == "RSA":
            pub = _RSA.import_key(pub_key_str)
            ciph = PKCS1_OAEP.new(pub)
            lim = pub.n.bit_length()//8 - 42
            parts = [base64.b64encode(ciph.encrypt(data[i:i+lim])).decode()
                     for i in range(0, len(data), lim)]
            return _b64j(parts)

        if algo == "ECC":
            pub = _ECC.import_key(pub_key_str)
            eph = _ECC.generate(curve="P-256")
            sp  = pub.pointQ * int(eph.d)
            key = SHA256.new(int(sp.x).to_bytes(32,"big")).digest()
            nonce, tag, ct = _aes_enc(key, data)
            epk = base64.b64encode(eph.public_key().export_key(format="DER")).decode()
            return _b64j({"epk":epk,"nonce":nonce,"tag":tag,"ct":ct})

        if algo == "DH":
            # PROFESSOR NOTE — DH Key Exchange:
            #   DH cannot encrypt directly. Both parties first exchange public
            #   values (g^a, g^b). Then each derives the same shared secret
            #   S = g^(ab) mod p, used as an AES key for actual encryption.
            if "DH" not in self._priv:
                raise ValueError("Generate DH keys first, then share your public value.")
            a = self._priv["DH"]
            B = int(pub_key_str.strip(), 16)          # friend's public value
            S = pow(B, a, _DH_P)
            key = SHA256.new(S.to_bytes(128,"big")).digest()
            A   = pow(_DH_G, a, _DH_P)               # include ours so receiver can derive S
            nonce, tag, ct = _aes_enc(key, data)
            return _b64j({"A":hex(A),"nonce":nonce,"tag":tag,"ct":ct})

        if algo == "ElGamal":
            pub = json.loads(pub_key_str)
            p = int(pub["p"],16); g = int(pub["g"]); y = int(pub["y"],16)
            chunk = (p.bit_length()-1)//8
            pairs = []
            for i in range(0, len(data), chunk):
                m = bytes_to_long(data[i:i+chunk])
                k = random.randrange(2, p-2)
                pairs.append({"c1":hex(pow(g,k,p)),"c2":hex(m*pow(y,k,p)%p)})
            return _b64j(pairs)

        if algo == "Paillier":
            pub = json.loads(pub_key_str)
            n = int(pub["n"],16); g = int(pub["g"],16); n2 = n*n
            chunk = (n.bit_length()-1)//8; out = []
            for i in range(0, len(data), chunk):
                m = bytes_to_long(data[i:i+chunk])
                r = random.randrange(1,n)
                while math.gcd(r,n)!=1: r = random.randrange(1,n)
                out.append(hex(pow(g,m,n2)*pow(r,n,n2)%n2))
            return _b64j(out)

        if algo == "NTRU":
            pub = json.loads(pub_key_str)
            enc = ciphers.ntru_encrypt_bytes(data, pub)
            return _b64j(enc)

        if algo == "McEliece":
            pub = json.loads(pub_key_str)
            enc = ciphers.mceliece_encrypt_bytes(data, pub)
            return _b64j(enc)

        raise ValueError(f"Unknown algorithm: {algo}")

    # ── Decryption (uses STORED private key — KEY INPUT ignored) ─────────────
    def decrypt(self, algo, b64_ciphertext: str) -> str:
        """Decrypt using stored private key. KEY INPUT box is NOT consulted."""
        if algo not in self._priv:
            raise ValueError(
                f"No private key for {algo}.\n"
                "Click [*] GEN KEYS first, then share your public key with your contact.")
        priv = self._priv[algo]
        d = _j64(b64_ciphertext)

        if algo == "RSA":
            ciph = PKCS1_OAEP.new(priv)
            return b"".join(ciph.decrypt(base64.b64decode(p)) for p in d).decode()

        if algo == "ECC":
            eph_pub = _ECC.import_key(base64.b64decode(d["epk"]))
            sp  = eph_pub.pointQ * int(priv.d)
            key = SHA256.new(int(sp.x).to_bytes(32,"big")).digest()
            return _aes_dec(key, d["nonce"], d["tag"], d["ct"]).decode()

        if algo == "DH":
            A   = int(d["A"], 16)     # sender's public value embedded in ciphertext
            S   = pow(A, priv, _DH_P) # priv = our private scalar b
            key = SHA256.new(S.to_bytes(128,"big")).digest()
            return _aes_dec(key, d["nonce"], d["tag"], d["ct"]).decode()

        if algo == "ElGamal":
            p = priv["p"]; x = priv["x"]; parts = []
            for pair in d:
                c1 = int(pair["c1"],16); c2 = int(pair["c2"],16)
                parts.append(long_to_bytes(c2 * pow(pow(c1,x,p),-1,p) % p))
            return b"".join(parts).decode("utf-8")

        if algo == "Paillier":
            n = priv["n"]; lam = priv["lam"]; mu = priv["mu"]; n2 = n*n
            parts = []
            for cs in d:
                c = int(cs,16)
                m = ((pow(c,lam,n2)-1)//n) * mu % n
                parts.append(long_to_bytes(m))
            return b"".join(parts).decode("utf-8")

        if algo == "NTRU":
            return ciphers.ntru_decrypt_bytes(d, priv)

        if algo == "McEliece":
            return ciphers.mceliece_decrypt_bytes(d, priv)

        raise ValueError(f"Unknown algorithm: {algo}")
