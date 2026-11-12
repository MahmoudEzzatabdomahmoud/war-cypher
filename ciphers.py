"""
ciphers.py — WarCyphere Pro | All 12 Cipher Implementations
pip install pycryptodome
"""
import math, random, base64, json

from Crypto.PublicKey import RSA as _RSA, ECC as _ECC
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from Crypto.Util.number import getPrime, long_to_bytes, bytes_to_long

# ══════════════════════════════════════════════════════════════════════════════
# GROUP 1 — CLASSIC / STANDARD
# ══════════════════════════════════════════════════════════════════════════════

def caesar_encrypt(text, shift):
    out = []
    for c in text:
        if c.isalpha():
            b = ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c)-b+shift)%26+b))
        else: out.append(c)
    return "".join(out)

def caesar_decrypt(text, shift): return caesar_encrypt(text, -shift)
def caesar_brute_force(text): return [(s, caesar_decrypt(text, s)) for s in range(26)]
def rot13(text): return caesar_encrypt(text, 13)

# ── Playfair ──────────────────────────────────────────────────────────────────
def _pf_sq(key):
    key = key.upper().replace("J","I")
    seen, seq = set(), []
    for c in key+"ABCDEFGHIKLMNOPQRSTUVWXYZ":
        if c.isalpha() and c not in seen: seen.add(c); seq.append(c)
    return [seq[i*5:(i+1)*5] for i in range(5)]

def _pf_pos(sq, ch):
    for r,row in enumerate(sq):
        if ch in row: return r, row.index(ch)

def _pf_prep(text):
    t = [c for c in text.upper().replace("J","I") if c.isalpha()]
    dg=[]; i=0
    while i<len(t):
        a=t[i]
        if i+1==len(t): dg+=[a,"X"]; i+=1
        elif t[i]==t[i+1]: dg+=[a,"X"]; i+=1
        else: dg+=[t[i],t[i+1]]; i+=2
    return dg

def playfair_encrypt(text, key):
    sq=_pf_sq(key); dg=_pf_prep(text); out=[]
    for i in range(0,len(dg),2):
        r1,c1=_pf_pos(sq,dg[i]); r2,c2=_pf_pos(sq,dg[i+1])
        if r1==r2: out+=[sq[r1][(c1+1)%5],sq[r2][(c2+1)%5]]
        elif c1==c2: out+=[sq[(r1+1)%5][c1],sq[(r2+1)%5][c2]]
        else: out+=[sq[r1][c2],sq[r2][c1]]
    return "".join(out)

def playfair_decrypt(text, key):
    sq=_pf_sq(key)
    f=[c for c in text.upper().replace("J","I") if c.isalpha()]; out=[]
    for i in range(0,len(f),2):
        r1,c1=_pf_pos(sq,f[i]); r2,c2=_pf_pos(sq,f[i+1])
        if r1==r2: out+=[sq[r1][(c1-1)%5],sq[r2][(c2-1)%5]]
        elif c1==c2: out+=[sq[(r1-1)%5][c1],sq[(r2-1)%5][c2]]
        else: out+=[sq[r1][c2],sq[r2][c1]]
    return "".join(out)

# ── Vigenere ──────────────────────────────────────────────────────────────────
def vigenere_encrypt(text, key):
    if not key: return text
    key=key.upper(); out=[]; ki=0
    for c in text:
        if c.isalpha():
            b=ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c)-b+ord(key[ki%len(key)])-ord('A'))%26+b)); ki+=1
        else: out.append(c)
    return "".join(out)

def vigenere_decrypt(text, key):
    if not key: return text
    key=key.upper(); out=[]; ki=0
    for c in text:
        if c.isalpha():
            b=ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c)-b-(ord(key[ki%len(key)])-ord('A')))%26+b)); ki+=1
        else: out.append(c)
    return "".join(out)

# ── Rail Fence ────────────────────────────────────────────────────────────────
def rail_fence_encrypt(text, rails):
    if rails<2: return text
    f=[[] for _ in range(rails)]; r,d=0,1
    for c in text:
        f[r].append(c)
        if r==0: d=1
        elif r==rails-1: d=-1
        r+=d
    return "".join("".join(x) for x in f)

def rail_fence_decrypt(text, rails):
    if rails<2: return text
    n=len(text); pat=[]; r,d=0,1
    for _ in range(n):
        pat.append(r)
        if r==0: d=1
        elif r==rails-1: d=-1
        r+=d
    idx=sorted(range(n),key=lambda i:pat[i]); out=[""]*n
    for i,c in zip(idx,text): out[i]=c
    return "".join(out)

# ── RSA (PyCryptodome) ────────────────────────────────────────────────────────
def rsa_generate_keys(bits=2048): return _RSA.generate(bits)

def rsa_encrypt(text, pub_key):
    cipher=PKCS1_OAEP.new(pub_key)
    lim=pub_key.n.bit_length()//8-42
    data=text.encode(); parts=[]
    for i in range(0,len(data),lim):
        parts.append(base64.b64encode(cipher.encrypt(data[i:i+lim])).decode())
    return "|".join(parts)

def rsa_decrypt(ct, priv_key):
    cipher=PKCS1_OAEP.new(priv_key)
    return "".join(cipher.decrypt(base64.b64decode(p)).decode() for p in ct.split("|"))

# ══════════════════════════════════════════════════════════════════════════════
# GROUP 2 — ADVANCED ASYMMETRIC
# ══════════════════════════════════════════════════════════════════════════════

# ── Diffie-Hellman (RFC 2409 Oakley Group 2 — 1024-bit MODP) ─────────────────
# PROFESSOR NOTE: DH security relies on the Discrete Logarithm Problem.
# Given g^a mod p it is computationally infeasible to recover a.
# Two parties compute the same shared secret without ever transmitting it.
_DH_P = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE65381"
    "FFFFFFFFFFFFFFFF", 16)
_DH_G = 2

def dh_encrypt(plaintext):
    """Simulate Alice↔Bob DH exchange; XOR-encrypt with shared secret."""
    p=_DH_P; g=_DH_G
    a=random.randrange(2,p-2); b=random.randrange(2,p-2)
    A=pow(g,a,p); B=pow(g,b,p); S=pow(B,a,p)
    key=S.to_bytes(128,'big')
    data=plaintext.encode()
    ct=bytes(data[i]^key[i%128] for i in range(len(data)))
    info={"A":str(A)[:40]+"...","B":str(B)[:40]+"...","S":str(S)[:40]+"..."}
    return base64.b64encode(ct).decode(), json.dumps(info), key

def dh_decrypt(ct_b64, key_bytes):
    data=base64.b64decode(ct_b64)
    return bytes(data[i]^key_bytes[i%128] for i in range(len(data))).decode()

# ── ECC / ECIES (PyCryptodome) ────────────────────────────────────────────────
# PROFESSOR NOTE: ECC security is based on the Elliptic Curve Discrete Logarithm
# Problem (ECDLP). Scalar multiplication k·P is easy; finding k from P and k·P
# is computationally infeasible. ECIES wraps ECDH key agreement with AES-GCM
# encryption — a "hybrid" scheme combining asymmetric and symmetric strengths.
def ecc_generate_keys(curve='P-256'): return _ECC.generate(curve=curve)

def ecc_encrypt(plaintext, pub_key):
    eph=_ECC.generate(curve='P-256')
    sp=pub_key.pointQ*int(eph.d)
    aes_key=SHA256.new(int(sp.x).to_bytes(32,'big')).digest()
    cipher=AES.new(aes_key,AES.MODE_GCM)
    ct,tag=cipher.encrypt_and_digest(plaintext.encode())
    epk=eph.public_key().export_key(format='DER')
    return json.dumps({
        "epk":base64.b64encode(epk).decode(),
        "nonce":base64.b64encode(cipher.nonce).decode(),
        "tag":base64.b64encode(tag).decode(),
        "ct":base64.b64encode(ct).decode()})

def ecc_decrypt(ct_json, priv_key):
    d=json.loads(ct_json)
    eph_pub=_ECC.import_key(base64.b64decode(d["epk"]))
    sp=eph_pub.pointQ*int(priv_key.d)
    aes_key=SHA256.new(int(sp.x).to_bytes(32,'big')).digest()
    cipher=AES.new(aes_key,AES.MODE_GCM,nonce=base64.b64decode(d["nonce"]))
    return cipher.decrypt_and_verify(
        base64.b64decode(d["ct"]),base64.b64decode(d["tag"])).decode()

# ── ElGamal (pure Python, PyCryptodome prime generation) ─────────────────────
# PROFESSOR NOTE: ElGamal is based on the Discrete Logarithm Problem.
# Probabilistic encryption — a fresh random k is chosen per chunk,
# so the same plaintext produces different ciphertext every run.
# bytes_to_long / long_to_bytes gives robust encoding with no chr() range errors.
def elgamal_generate_keys():
    p=getPrime(512); g=2; x=random.randrange(2,p-2); y=pow(g,x,p)
    return {"p":p,"g":g,"x":x,"y":y}

def elgamal_encrypt(plaintext, keys):
    p,g,y = keys["p"],keys["g"],keys["y"]
    data  = plaintext.encode("utf-8")
    chunk = (p.bit_length()-1)//8   # max bytes per chunk that fit inside p
    pairs = []
    for i in range(0, len(data), chunk):
        m = bytes_to_long(data[i:i+chunk])
        k = random.randrange(2, p-2)
        pairs.append(f"{pow(g,k,p)}:{m*pow(y,k,p)%p}")
    return " | ".join(pairs)

def elgamal_decrypt(ct, keys):
    p,x = keys["p"],keys["x"]
    parts = []
    for pair in ct.split(" | "):
        c1s,c2s = pair.strip().split(":")
        c1,c2   = int(c1s),int(c2s)
        m = c2 * pow(pow(c1,x,p),-1,p) % p
        parts.append(long_to_bytes(m))
    return b"".join(parts).decode("utf-8")

# ── Paillier Homomorphic Encryption (pure Python) ─────────────────────────────
# PROFESSOR NOTE: Paillier is a Partially Homomorphic Encryption scheme.
# The key property: Enc(m1) × Enc(m2) mod n² = Enc(m1+m2).
# This means you can ADD encrypted values without ever decrypting them —
# critical for privacy-preserving computation (e-voting, medical analytics).
# Security rests on the Decisional Composite Residuosity Assumption (DCRA).
def paillier_generate_keys():
    p=getPrime(256); q=getPrime(256)
    while p==q: q=getPrime(256)
    n=p*q; lam=((p-1)*(q-1))//math.gcd(p-1,q-1)
    g=n+1          # Standard choice: L(g^λ mod n²)·μ ≡ 1 mod n
    mu=pow(lam,-1,n)
    return {"n":n,"g":g,"lam":lam,"mu":mu}

def _L(x,n): return (x-1)//n

def paillier_encrypt(plaintext, keys):
    n,g = keys["n"],keys["g"]; n2=n*n
    data  = plaintext.encode("utf-8")
    chunk = (n.bit_length()-1)//8   # bytes per chunk, guaranteed < n
    out   = []
    for i in range(0, len(data), chunk):
        m = bytes_to_long(data[i:i+chunk])
        r = random.randrange(1, n)
        while math.gcd(r,n)!=1: r=random.randrange(1,n)
        out.append(str(pow(g,m,n2)*pow(r,n,n2)%n2))
    return " | ".join(out)

def paillier_decrypt(ct, keys):
    n,lam,mu = keys["n"],keys["lam"],keys["mu"]; n2=n*n
    parts = []
    for cs in ct.split(" | "):
        c = int(cs.strip())
        m = _L(pow(c,lam,n2),n)*mu%n
        parts.append(long_to_bytes(m))
    return b"".join(parts).decode("utf-8")

# ── NTRU (pure Python, educational polynomial ring) ───────────────────────────
# PROFESSOR NOTE: NTRU operates in the Polynomial Ring Z[x]/(x^N - 1).
# Security comes from the Shortest Vector Problem (SVP) on a lattice —
# believed hard even for quantum computers. Shor's algorithm, which breaks
# RSA and ECC, does NOT apply here, making NTRU a NIST PQC finalist.
_N,_P,_Q,_D=11,3,31,2

def _pmul(a,b,N,mod):
    r=[0]*N
    for i in range(N):
        for j in range(N): r[(i+j)%N]=(r[(i+j)%N]+a[i]*b[j])%mod
    return r

def _padd(a,b,mod): return [(a[i]+b[i])%mod for i in range(len(a))]

def _clift(poly,mod): return [x-mod if x>mod//2 else x for x in [c%mod for c in poly]]

def _pinv(f,N,mod):
    def deg(p):
        for i in range(len(p)-1,-1,-1):
            if p[i]%mod: return i
        return -1
    def pdiv(a,b):
        r=[x%mod for x in a]; q=[0]*len(a); li=pow(b[deg(b)],-1,mod)
        while deg(r)>=deg(b):
            d=deg(r)-deg(b); c=r[deg(r)]*li%mod; q[d]=(q[d]+c)%mod
            for i in range(deg(b)+1): r[d+i]=(r[d+i]-c*b[i])%mod
        return q,r
    def pmul(a,b):
        res=[0]*(len(a)+len(b)-1)
        for i,ai in enumerate(a):
            for j,bj in enumerate(b): res[i+j]=(res[i+j]+ai*bj)%mod
        return res
    xN1=[-1]+[0]*(N-1)+[1]; R,r=list(f)+[0],xN1[:]; S,s=[1]+[0]*N,[0]*(N+1)
    while deg(r)>=0:
        q,nr=pdiv(R,r); qs=pmul(q,s)
        ns=[(S[i] if i<len(S) else 0)-(qs[i] if i<len(qs) else 0) for i in range(max(len(S),len(qs)))]
        R,r=r,[x%mod for x in nr]; S,s=s,[x%mod for x in ns]
    if deg(R)!=0: return None
    li=pow(R[0],-1,mod); return [S[i]*li%mod for i in range(N)]

def _tern(N,d):
    v=[1]*d+[-1]*d+[0]*(N-2*d); random.shuffle(v); return v

def ntru_generate_keys():
    for _ in range(300):
        f=_tern(_N,_D+1); fp=_pinv([x%_P for x in f],_N,_P); fq=_pinv([x%_Q for x in f],_N,_Q)
        if fp and fq:
            g=_tern(_N,_D); h=_pmul(fq,[_P*x%_Q for x in g],_N,_Q)
            return {"f":f,"fp":fp,"h":h,"N":_N,"p":_P,"q":_Q}
    raise RuntimeError("NTRU keygen failed — retry")

# PROFESSOR NOTE — NTRU binary encoding:
#   p=3 limits raw ordinals, so we encode each byte as 8 binary polynomial
#   coefficients (bits 7..0). Each bit is 0 or 1 — both valid ternary values.
#   N=11 has room for 8 message bits + 3 spare coefficients per polynomial.
def ntru_encrypt(plaintext, keys):
    h,N,p,q = keys["h"],keys["N"],keys["p"],keys["q"]
    enc = []
    for byte in plaintext.encode("utf-8"):
        # Spread 8 bits across the first 8 polynomial coefficients
        m = [(byte>>(7-i))&1 for i in range(8)] + [0]*(N-8)
        r = _tern(N, _D)
        enc.append(_padd(_pmul(r,h,N,q), m, q))
    return json.dumps([[int(x) for x in e] for e in enc])

def ntru_decrypt(ct_json, keys):
    f,fp,N,p,q = keys["f"],keys["fp"],keys["N"],keys["p"],keys["q"]
    out = []
    for e in json.loads(ct_json):
        a = _clift(_pmul(f,e,N,q), q)
        b = _pmul(fp, [x%p for x in a], N, p)
        # Reconstruct byte from first 8 recovered bits (values 0 or 1)
        byte_val = sum((b[i]%p) << (7-i) for i in range(8))
        out.append(byte_val)
    return bytes(out).decode("utf-8")

# ── McEliece (pure Python, binary linear code) ────────────────────────────────
# PROFESSOR NOTE: McEliece (1978) is based on the hardness of decoding a random
# linear code — a problem with no known quantum speedup. The public key is a
# scrambled generator matrix G' = S·G·P. Without the private S, G, P matrices,
# an attacker cannot distinguish G' from a random matrix, making it unbreakable.
# Parameters here: [n=15, k=7] binary code for demonstration.
_MCN,_MCK=15,7

def _mm2(A,B):
    rA,cA,cB=len(A),len(A[0]),len(B[0])
    C=[[sum(A[i][k]*B[k][j] for k in range(cA))%2 for j in range(cB)] for i in range(rA)]
    return C

def _inv2(M):
    n=len(M); A=[r[:] for r in M]; I=[[int(i==j) for j in range(n)] for i in range(n)]
    for c in range(n):
        piv=next((r for r in range(c,n) if A[r][c]),None)
        if piv is None: return None
        A[c],A[piv]=A[piv],A[c]; I[c],I[piv]=I[piv],I[c]
        for r in range(n):
            if r!=c and A[r][c]:
                A[r]=[A[r][j]^A[c][j] for j in range(n)]
                I[r]=[I[r][j]^I[c][j] for j in range(n)]
    return I

def _rinv2(k):
    for _ in range(500):
        M=[[random.randint(0,1) for _ in range(k)] for _ in range(k)]
        inv=_inv2(M)
        if inv: return M,inv
    raise RuntimeError("McEliece: invertible matrix generation failed")

def _rperm(n):
    p=list(range(n)); random.shuffle(p)
    P=[[int(i==p[j]) for j in range(n)] for i in range(n)]
    pi=[0]*n
    for i,v in enumerate(p): pi[v]=i
    return P,pi

def _rgen(k,n):
    A=[[random.randint(0,1) for _ in range(n-k)] for _ in range(k)]
    I=[[int(i==j) for j in range(k)] for i in range(k)]
    return [I[i]+A[i] for i in range(k)]

def mceliece_generate_keys():
    G=_rgen(_MCK,_MCN); S,Si=_rinv2(_MCK); P,Pi=_rperm(_MCN)
    Gpub=_mm2(_mm2(S,G),P)
    return {"Gpub":Gpub,"G":G,"Si":Si,"Pi":Pi,"k":_MCK,"n":_MCN}

def _i2b(x,l): return [(x>>(l-1-i))&1 for i in range(l)]
def _b2i(b): return sum(v<<(len(b)-1-i) for i,v in enumerate(b))

def mceliece_encrypt(plaintext,keys):
    Gpub,k,n=keys["Gpub"],keys["k"],keys["n"]; blocks=[]
    for ch in plaintext:
        # encode 7 bits per character (ASCII 0-127)
        m=_i2b(ord(ch)&0x7F,k)
        c=[sum(m[i]*Gpub[i][j] for i in range(k))%2 for j in range(n)]
        blocks.append("".join(str(b) for b in c))
    return " | ".join(blocks)

def mceliece_decrypt(ct,keys):
    G,Si,Pi,k,n=keys["G"],keys["Si"],keys["Pi"],keys["k"],keys["n"]; out=[]
    for block in ct.split(" | "):
        c=[int(b) for b in block.strip()]
        # Apply inverse permutation P^(-1)
        cp=[c[Pi[i]] for i in range(n)]
        # Systematic code: first k bits are the scrambled message
        me=[cp[i] for i in range(k)]
        # Apply S^(-1) to recover original message bits
        mb=[sum(Si[i][j]*me[j] for j in range(k))%2 for i in range(k)]
        v=_b2i(mb)
        out.append(chr(v) if 32<=v<128 else '?')
    return "".join(out)

# ── Byte-level helpers for asym_layer.py ─────────────────────────────────────
def ntru_encrypt_bytes(data: bytes, pub: dict) -> list:
    """Encrypt raw bytes using NTRU public key dict {h, N, p, q}."""
    h,N,p,q = pub["h"],pub["N"],pub["p"],pub["q"]; enc=[]
    for byte in data:
        m = [(byte>>(7-i))&1 for i in range(8)] + [0]*(N-8)
        r = _tern(N,_D)
        enc.append([int(x) for x in _padd(_pmul(r,h,N,q),m,q)])
    return enc

def ntru_decrypt_bytes(ct_list: list, priv: dict) -> str:
    """Decrypt NTRU ciphertext list using private key dict {f, fp, N, p, q}."""
    f,fp,N,p,q = priv["f"],priv["fp"],priv["N"],priv["p"],priv["q"]; out=[]
    for e in ct_list:
        a = _clift(_pmul(f,e,N,q),q)
        b = _pmul(fp,[x%p for x in a],N,p)
        out.append(sum((b[i]%p)<<(7-i) for i in range(8)))
    return bytes(out).decode("utf-8")

def mceliece_encrypt_bytes(data: bytes, pub: dict) -> list:
    """Encrypt raw bytes using McEliece public key dict {Gpub, k, n}."""
    Gpub,k,n = pub["Gpub"],pub["k"],pub["n"]; blocks=[]
    for byte in data:
        m = _i2b(byte&0x7F, k)
        c = [sum(m[i]*Gpub[i][j] for i in range(k))%2 for j in range(n)]
        blocks.append(c)
    return blocks

def mceliece_decrypt_bytes(ct_list: list, priv: dict) -> str:
    """Decrypt McEliece ciphertext list using private key dict."""
    G,Si,Pi,k,n = priv["G"],priv["Si"],priv["Pi"],priv["k"],priv["n"]; out=[]
    for c in ct_list:
        cp = [c[Pi[i]] for i in range(n)]
        me = [cp[i] for i in range(k)]
        mb = [sum(Si[i][j]*me[j] for j in range(k))%2 for i in range(k)]
        v  = _b2i(mb)
        out.append(v if 32<=v<128 else ord('?'))
    return bytes(out).decode("ascii", errors="replace")

