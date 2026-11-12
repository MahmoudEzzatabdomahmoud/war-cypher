"""
main.py - WarCyphere Pro | Cyberpunk Chat Terminal
pip install pycryptodome Pillow requests
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os, threading, json, ciphers, utils, db_handler
from asym_layer import AsymLayer
from stegano import lsb

BG="#000000";GRN="#00FF00";AMB="#FFB000";RED="#FF2200";DIM="#007700"
DRK="#0A0A0A";PNL="#050505";WGT="#0D0D0D";BODY="#AAFFAA"
MONO=("Courier New",10);MONOB=("Courier New",11,"bold")
TTL=("Courier New",14,"bold");SML=("Courier New",8);BF=("Courier New",9,"bold")

_keys={};_dh_key=None;_fpath="";_fhash=""
_last_id=0;_messages=[];_seen_ids=set()

def _btn(p,t,cmd,fg=BG,bg=GRN,w=18):
    return tk.Button(p,text=t,command=cmd,fg=fg,bg=bg,activebackground=BODY,
        activeforeground=BG,font=BF,relief="flat",bd=1,
        highlightthickness=1,highlightbackground=bg,cursor="hand2",width=w,pady=3)

def _txt(p,h=10,fg=GRN,state="normal"):
    return tk.Text(p,height=h,bg=WGT,fg=fg,insertbackground=fg,font=MONO,
        relief="flat",bd=0,highlightthickness=1,highlightbackground=DIM,
        wrap="word",selectbackground=DIM,state=state)

def _ent(p,w=20):
    return tk.Entry(p,bg=WGT,fg=GRN,insertbackground=GRN,font=MONO,
        relief="flat",bd=0,highlightthickness=1,highlightbackground=DIM,width=w)

def _lbl(p,t,fg=GRN,font=SML,bg=PNL,**kw):
    return tk.Label(p,text=t,fg=fg,bg=bg,font=font,**kw)

def _bar(p,col=DIM): tk.Frame(p,bg=col,height=1).pack(fill="x",pady=2)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WARCYPHERE // SECURE CHAT TERMINAL")
        self.configure(bg=BG);self.minsize(1060,820)
        self.algo=tk.StringVar(value="Caesar")
        self.handle=tk.StringVar(value="AGENT_X")
        self.asym = AsymLayer()   # unified asymmetric layer — strict key separation
        self._build();self._on_algo()
        self._start_poll()

    def _build(self):
        self._hdr();self._algo_row();self._workspace();self._statusbar()

    def _hdr(self):
        h=tk.Frame(self,bg=BG,pady=6,highlightthickness=1,highlightbackground=GRN)
        h.pack(fill="x",padx=8,pady=(8,0))
        _lbl(h,"[ WARCYPHERE PRO ] // E2EE SECURE CHAT TERMINAL",fg=GRN,font=TTL,bg=BG).pack(side="left",padx=10)
        _lbl(h,"[ TOP SECRET ]",fg=AMB,font=("Courier New",10,"bold"),bg=BG).pack(side="right",padx=10)
        hf=tk.Frame(self,bg=DRK,pady=3,highlightthickness=1,highlightbackground=DIM)
        hf.pack(fill="x",padx=8,pady=2)
        self._cia=_lbl(hf,"  CIA STATUS: —",fg=AMB,bg=DRK,font=SML)
        self._cia.pack(side="left",padx=8)
        _lbl(hf,"HANDLE:",fg=DIM,bg=DRK,font=SML).pack(side="left",padx=(20,4))
        tk.Entry(hf,textvariable=self.handle,bg=WGT,fg=AMB,insertbackground=AMB,
            font=("Courier New",9),relief="flat",bd=0,width=14).pack(side="left")

    def _algo_row(self):
        outer=tk.Frame(self,bg=BG);outer.pack(fill="x",padx=8,pady=4)
        groups=[("[ GRP-1 CLASSIC ]",["Caesar","ROT13","Playfair","Vigenere","Rail Fence","RSA"],DIM),
                ("[ GRP-2 ADVANCED]",["DH","ECC","ElGamal","Paillier","NTRU","McEliece"],AMB)]
        for label,algos,col in groups:
            row=tk.Frame(outer,bg=BG);row.pack(fill="x",pady=1)
            _lbl(row,label,fg=col,font=("Courier New",8,"bold"),bg=BG,width=20,anchor="e").pack(side="left",padx=(0,4))
            for a in algos:
                tk.Radiobutton(row,text=a,variable=self.algo,value=a,command=self._on_algo,
                    fg=GRN,bg=BG,selectcolor=WGT,activebackground=BG,activeforeground=AMB,
                    font=BF,indicatoron=0,padx=8,pady=2,relief="flat",bd=1,
                    highlightthickness=1,highlightbackground=DIM,cursor="hand2").pack(side="left",padx=2)
        self._info_v=tk.StringVar()
        tk.Label(outer,textvariable=self._info_v,fg=BODY,bg=DRK,font=SML,anchor="w",padx=8,pady=4).pack(fill="x",pady=(3,0))

    def _workspace(self):
        m=tk.Frame(self,bg=BG);m.pack(fill="both",expand=True,padx=8,pady=4)
        m.columnconfigure(0,weight=1);m.columnconfigure(1,weight=0);m.columnconfigure(2,weight=1)

        # LEFT: plaintext input
        lf=tk.Frame(m,bg=PNL,padx=6,pady=6,highlightthickness=1,highlightbackground=DIM)
        lf.grid(row=0,column=0,sticky="nsew",padx=(0,3))
        _lbl(lf,"[ PLAINTEXT // MESSAGE INPUT ]",fg=GRN,font=MONOB,bg=PNL).pack(anchor="w")
        _bar(lf)
        self._plain=_txt(lf,h=11);self._plain.pack(fill="both",expand=True)
        _btn(lf,"CLR",self._clrp,bg=DIM,w=6).pack(pady=(4,0),anchor="w")

        # CENTRE: controls
        cf=tk.Frame(m,bg=BG,padx=6);cf.grid(row=0,column=1,sticky="ns")
        self._ctrl(cf)

        # RIGHT: live chat history
        rf=tk.Frame(m,bg=PNL,padx=6,pady=6,highlightthickness=1,highlightbackground=AMB)
        rf.grid(row=0,column=2,sticky="nsew",padx=(3,0))
        _lbl(rf,"[ LIVE CHAT HISTORY // ENCRYPTED ]",fg=AMB,font=MONOB,bg=PNL).pack(anchor="w")
        _bar(rf,AMB)
        self._chat=_txt(rf,h=11,fg=AMB,state="disabled");self._chat.pack(fill="both",expand=True)
        _btn(rf,"CLR CHAT",self._clrc,bg=DIM,w=10).pack(pady=(4,0),anchor="w")

        # BOTTOM panels
        bot=tk.Frame(self,bg=BG);bot.pack(fill="x",padx=8,pady=(2,4))
        bot.columnconfigure(0,weight=1);bot.columnconfigure(1,weight=1)

        # PROFESSOR NOTE — MITM / Packet Interception:
        #   This panel shows what a network attacker intercepts.
        #   All they see is ciphertext — E2EE means the server (Supabase)
        #   is also an untrusted relay that never holds plaintext keys.
        wf=tk.Frame(bot,bg=PNL,padx=6,pady=4,highlightthickness=1,highlightbackground=RED)
        wf.grid(row=0,column=0,sticky="nsew",padx=(0,3))
        _lbl(wf,"[ ENEMY INTERCEPT LOG — WIRETAP ]",fg=RED,font=("Courier New",9,"bold"),bg=PNL).pack(anchor="w")
        _bar(wf,RED)
        self._wire=_txt(wf,h=5,fg=RED,state="disabled");self._wire.pack(fill="both",expand=True)

        inf=tk.Frame(bot,bg=PNL,padx=6,pady=4,highlightthickness=1,highlightbackground=DIM)
        inf.grid(row=0,column=1,sticky="nsew",padx=(3,0))
        _lbl(inf,"[ INTEL FEED // SYSTEM LOG ]",fg=GRN,font=("Courier New",9,"bold"),bg=PNL).pack(anchor="w")
        _bar(inf)
        self._log=_txt(inf,h=5,fg=BODY,state="disabled");self._log.pack(fill="both",expand=True)

    def _ctrl(self,p):
        def sec(t,col=GRN):
            _lbl(p,f"[{t}]",fg=col,font=("Courier New",8,"bold"),bg=BG).pack(pady=(8,2))

        sec("KEY INPUT")
        self._key=_txt(p, h=5);self._key.pack(fill="x", pady=2)
        _lbl(p,"shift/keyword/rails",fg=DIM,bg=BG,font=SML).pack()

        sec("SECURE CHAT")
        _btn(p,">> SEND SECURE MSG",self._send,bg=GRN,w=20).pack(pady=2)
        _btn(p,"<< DECRYPT MSG",self._dec_selected,bg=AMB,w=20).pack(pady=2)

        sec("KEY GEN")
        self._gkbtn=_btn(p,"[*] GEN KEYS",self._genk,bg="#004499",fg=GRN,w=20)
        self._gkbtn.pack(pady=2)
        self._ki_v=tk.StringVar(value="[ no keys ]")
        tk.Label(p,textvariable=self._ki_v,fg="#4499FF",bg=BG,
            font=("Courier New",7),justify="left",wraplength=170).pack()

        sec("FILE OPS")
        _btn(p,"[+] UPLOAD",self._upload,bg="#330066",fg=GRN,w=20).pack(pady=2)
        _btn(p,"[-] DOWNLOAD",self._download,bg="#330066",fg=GRN,w=20).pack(pady=2)
        _btn(p,"[X] BURN LATEST MSG",self._burn_msg,bg=RED,fg=BG,w=20).pack(pady=2)

        sec("DEAD DROP",AMB)
        _btn(p,"[~] EXTRACT IMG",self._extract,bg="#663300",fg=AMB,w=20).pack(pady=2)

        sec("CRYPTANALYSIS",RED)
        _btn(p,"[!] BRUTE FORCE",self._brute,bg=RED,fg=BG,w=20).pack(pady=2)
        _lbl(p,"Caesar only",fg=DIM,bg=BG,font=SML).pack()

    def _statusbar(self):
        bar=tk.Frame(self,bg=DRK,pady=2,highlightthickness=1,highlightbackground=DIM)
        bar.pack(fill="x",side="bottom")
        self._sv=tk.StringVar(value="SYSTEM READY // AWAITING ORDERS")
        tk.Label(bar,textvariable=self._sv,fg=GRN,bg=DRK,font=SML,anchor="w").pack(side="left",padx=10)
        self._conn=tk.Label(bar,text="● DB: OFFLINE",fg=RED,bg=DRK,font=SML)
        self._conn.pack(side="right",padx=10)

    def _on_algo(self):
        a=self.algo.get();meta=utils.ALGORITHM_METADATA.get(a,{})
        self._info_v.set(f"  {a}  |  {meta.get('type','—')}  |  KEY: {meta.get('key_bits','—')}  |  {meta.get('strength','—')}")
        self._cia.config(text=f"  CIA STATUS: {meta.get('cia','—')}")
        is_a=a in utils.ASYMMETRIC_ALGOS
        self._gkbtn.config(state="normal" if is_a else "disabled",bg="#004499" if is_a else "#111111")
        if not is_a:self._ki_v.set("[ classic — use key field ]")
        self._sv.set(f"CIPHER: {a} SELECTED")

    def _pt(self): return self._plain.get("1.0","end-1c")
    def _spt(self,t): self._plain.delete("1.0","end");self._plain.insert("end",t)
    def _clrp(self): self._plain.delete("1.0","end")
    def _clrc(self): self._chat.config(state="normal");self._chat.delete("1.0","end");self._chat.config(state="disabled")

    def _emit(self,msg,w=None):
        widget=w or self._log
        widget.config(state="normal");widget.insert("end",f"{msg}\n")
        widget.see("end");widget.config(state="disabled")

    def _chat_add(self, ts, sender, algo, ct, is_me=False, is_key=False):
        import base64 as _b64
        self._chat.config(state="normal")
        if is_key:
            # Key broadcasts get a distinct gold banner — never rendered as ciphertext
            try:
                raw     = _b64.b64decode(ct[len("KEY_BROADCAST::"):]).decode()
                preview = raw[:55].replace("\n"," ") + ("…" if len(raw) > 55 else "")
            except Exception:
                preview = ct[:55]
            direction = "YOU →" if is_me else f"← {sender}"
            self._chat.insert("end",
                f"[{ts}] ╔═ KEY EXCHANGE ══════════════════════════════\n"
                f"         {direction} sent a [{algo}] PUBLIC KEY\n"
                f"         {preview}\n"
                f"         ╚═══════════════════════════════════════════\n")
        else:
            tag     = ">>" if is_me else "<<"
            preview = ct[:60].replace("\n"," ") + ("…" if len(ct) > 60 else "")
            self._chat.insert("end", f"[{ts}] {tag} {sender} [{algo}]: {preview}\n")
        self._chat.see("end")
        self._chat.config(state="disabled")
        _messages.append({"sender": sender, "algo": algo, "ct": ct, "is_me": is_me})

    def _wiretap(self,encrypted=True,payload=""):
        if encrypted:
            self._emit("[!] Packet Intercepted... Payload Unreadable (Encrypted)",self._wire)
        else:
            self._emit(f"[!] PLAINTEXT EXPOSED — No Encryption!\n    {payload[:70]}",self._wire)

    # ── key gen ───────────────────────────────────────────────────────────────
    def _genk(self):
        a=self.algo.get();self._ki_v.set("Generating…")
        threading.Thread(target=self._genk_bg,args=(a,),daemon=True).start()

    def _genk_bg(self, a):
        """Background thread: generate keys via AsymLayer, paste public key to buffer."""
        try:
            pub_str = self.asym.generate_keys(a)   # stores private; returns public
            info_map = {
                "RSA":"RSA 2048-bit","ECC":"ECC P-256","DH":"DH 1024-bit (RFC 3526)",
                "ElGamal":"ElGamal 512-bit","Paillier":"Paillier 512-bit",
                "NTRU":"NTRU N=11","McEliece":"McEliece [15,7]"
            }
            info = info_map.get(a, a)
            self.after(0, lambda s=pub_str: self._spt(s))
            self.after(0, lambda: self._ki_v.set(info))
            self.after(0, lambda: self._emit(
                f"[KEYGEN] {a} ready. Public key pasted into buffer — hit SEND to share.\n"
                f"         Your contact must paste it into their KEY INPUT box to encrypt for you."))
            self.after(0, lambda: self._sv.set(f"{a} KEYS GENERATED"))
        except Exception as e:
            self.after(0, lambda: self._ki_v.set(f"ERR:{e}"))
            self.after(0, lambda: self._emit(f"[ERROR] {e}"))

    # ── Public-key broadcast detection ────────────────────────────────────────
    @staticmethod
    def _is_pubkey_broadcast(text: str) -> bool:
        """
        Returns True if the plaintext buffer contains a generated public key
        that should be sent as a raw broadcast (no encryption needed).
        Detects: PEM blocks, DH hex values (0x...), JSON with known pub-key fields.
        """
        t = text.strip()
        if t.startswith("-----BEGIN"):          return True   # RSA / ECC PEM
        if t.startswith("0x") and len(t) > 64: return True   # DH hex public value
        if t.startswith("[DH]"):               return True   # DH info string
        try:
            import json
            d = json.loads(t)
            # ElGamal public key has p, g, y  |  Paillier has n, g
            # NTRU has h, N, p, q  |  McEliece has Gpub, k, n
            pub_fields = ({"p","g","y"}, {"n","g"}, {"h","N","p","q"}, {"Gpub","k","n"})
            keys = set(d.keys())
            if any(fields <= keys for fields in pub_fields): return True
        except Exception:
            pass
        return False

    @staticmethod
    def _clean_key(key_str: str, algo: str) -> str:
        """
        Cleans the pasted key string to prevent formatting errors.
        For RSA and ECC, wraps bare base64 in PEM headers if they are missing.
        """
        k = key_str.strip()
        if not k: return ""
        
        if algo in ("RSA", "ECC"):
            # If it looks like base64 but missing PEM headers, wrap it gracefully
            if not k.startswith("-----BEGIN"):
                k = f"-----BEGIN PUBLIC KEY-----\n{k}\n-----END PUBLIC KEY-----"
        return k

    # ── send message ──────────────────────────────────────────────────────────
    def _send(self):
        a      = self.algo.get()
        pt     = self._pt()
        # Grab raw key from Text widget, clean it based on selected algo
        raw_key = self._key.get("1.0", "end-1c")
        key     = self._clean_key(raw_key, a)
        sender = self.handle.get().strip() or "AGENT"
        if not pt.strip():
            messagebox.showwarning("Empty", "Type a message first."); return
        try:
            # ── Smart routing: is this a public-key broadcast? ──────────────────
            if self._is_pubkey_broadcast(pt):
                import base64
                # Tag it so the receiver knows NOT to decrypt it
                tagged = "KEY_BROADCAST::" + base64.b64encode(pt.encode()).decode()
                self._spt("")
                ts = __import__("datetime").datetime.now().strftime("%H:%M:%S")
                self._chat_add(ts, sender, a, tagged, is_me=True, is_key=True)
                self._emit(f"[KEY BROADCAST] {a} public key sent — contact must paste it into their KEY INPUT box.")
                self._sv.set(f"PUBLIC KEY BROADCAST SENT // {a}")
                threading.Thread(target=self._push, args=(sender, tagged), daemon=True).start()
                return
            # ── Normal encrypted message path ──────────────────────────────────
            ct = self._encrypt(a, pt, key)
            self._spt("")
            ts = __import__("datetime").datetime.now().strftime("%H:%M:%S")
            self._chat_add(ts, sender, a, ct, is_me=True)
            self._wiretap(encrypted=True)
            self._emit(f"[SEND] {a} | {utils.intel_line(a, _keys.get(a))}")
            self._sv.set(f"MSG SENT // {a} ENCRYPTED")
            threading.Thread(target=self._push, args=(sender, ct), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", str(e)); self._emit(f"[ERROR] {e}")

    def _push(self, sender, ct):
        """Background thread: sends ciphertext to Supabase then triggers a poll."""
        try:
            ok = db_handler.send_message(sender, ct)  # exactly 2 args — matches db_handler
            if ok:
                self.after(0, lambda: self._conn.config(text="● DB: ONLINE", fg=GRN))
                self.after(100, self._poll)  # immediate refresh so sent msg shows up
            else:
                self.after(0, lambda: self._emit("[DB] send_message returned False — check Supabase logs"))
                self.after(0, lambda: self._conn.config(text="● DB: WARN", fg=AMB))
        except Exception as e:
            self.after(0, lambda: self._emit(f"[DB ERROR] {e}"))
            self.after(0, lambda: self._conn.config(text="● DB: ERROR", fg=RED))

    def _encrypt(self, a, pt, key):
        """Encrypt plaintext. Asymmetric algos use KEY INPUT as friend's public key."""
        # ── Group 1: Classic (key = shift / keyword / rails) ──────────────────
        if a=="Caesar":    return ciphers.caesar_encrypt(pt, int(key) if key.lstrip("-").isdigit() else 3)
        if a=="ROT13":     return ciphers.rot13(pt)
        if a=="Playfair":
            if not key: raise ValueError("Playfair needs a keyword.")
            return ciphers.playfair_encrypt(pt, key)
        if a=="Vigenere":
            if not key: raise ValueError("Vigenere needs a keyword.")
            return ciphers.vigenere_encrypt(pt, key)
        if a=="Rail Fence": return ciphers.rail_fence_encrypt(pt, int(key) if key.isdigit() else 3)
        # ── Group 2: Asymmetric (key = friend's public key string from KEY INPUT) ─
        if a in utils.ASYMMETRIC_ALGOS:
            if not key.strip():
                raise ValueError(
                    f"KEY INPUT is empty.\n"
                    f"Paste your contact's {a} public key into the KEY INPUT box first.")
            return self.asym.encrypt(a, key.strip(), pt)
        raise ValueError(f"Unknown algorithm: {a}")

    # ── decrypt last received message ─────────────────────────────────────────
    def _dec_selected(self):
        if not _messages: messagebox.showinfo("Empty", "No messages to decrypt."); return
        a       = self.algo.get()
        last    = _messages[-1]
        ct      = last["ct"]
        raw_key = self._key.get("1.0", "end-1c")
        key     = self._clean_key(raw_key, a)
        try:
            # ── Classic algorithms: use KEY INPUT (shift/keyword/rails) ───────
            if a=="Caesar":      pt=ciphers.caesar_decrypt(ct, int(key) if key.lstrip("-").isdigit() else 3)
            elif a=="ROT13":     pt=ciphers.rot13(ct)
            elif a=="Playfair":  pt=ciphers.playfair_decrypt(ct, key)
            elif a=="Vigenere":  pt=ciphers.vigenere_decrypt(ct, key)
            elif a=="Rail Fence":pt=ciphers.rail_fence_decrypt(ct, int(key) if key.isdigit() else 3)
            # ── Asymmetric algorithms: use STORED private key (KEY INPUT ignored) ─
            elif a in utils.ASYMMETRIC_ALGOS:
                pt = self.asym.decrypt(a, ct)   # KEY INPUT is NOT used here
            else:
                raise ValueError(f"Unknown algorithm: {a}")
            self._spt(pt)
            self._emit(f"[DECRYPT] {a} — decrypted using stored private key.")
            self._sv.set("MSG DECRYPTED")
        except Exception as e:
            messagebox.showerror("Decrypt Error", str(e))
            self._emit(f"[ERROR] {e}")

    # ── polling (self.after — runs on main thread, safe for Tkinter) ───────────
    def _start_poll(self):
        """Kick off the non-blocking poll loop using Tkinter's scheduler."""
        self._poll()          # first call immediately on startup

    def _poll(self):
        """Fetch new messages from Supabase and schedule the next poll."""
        global _seen_ids
        import base64 as _b64
        try:
            msgs = db_handler.fetch_messages()
            my_handle = self.handle.get().strip()
            new_count = 0
            for m in msgs:
                mid = m.get("id") or m.get("created_at")
                if mid in _seen_ids:
                    continue
                _seen_ids.add(mid)
                is_me = (m.get("sender","") == my_handle)
                ts    = m.get("created_at","")[:19].replace("T"," ")[-8:]
                algo  = m.get("algorithm", self.algo.get())
                ct    = m.get("ciphertext","")
                # ── Detect public-key broadcasts — display as key, never decrypt ──
                if ct.startswith("KEY_BROADCAST::"):
                    raw_key = _b64.b64decode(ct[len("KEY_BROADCAST::"):]).decode()
                    self._chat_add(ts, m.get("sender","?"), algo, ct,
                                   is_me=is_me, is_key=True)
                    if not is_me:
                        # Auto-fill KEY INPUT with their public key for convenience
                        self._key.delete("1.0", "end")
                        self._key.insert("end", raw_key)
                        self._emit(f"[KEY EXCHANGE] {algo} public key received from "
                                   f"{m.get('sender','?')} — pasted into KEY INPUT automatically.")
                        self._sv.set(f"KEY RECEIVED FROM {m.get('sender','?')} — READY TO ENCRYPT")
                else:
                    self._chat_add(ts, m.get("sender","?"), algo, ct, is_me=is_me)
                    if not is_me:
                        self._wiretap(encrypted=True)
                new_count += 1
            if new_count:
                self._conn.config(text="● DB: ONLINE", fg=GRN)
        except Exception as e:
            self._conn.config(text="● DB: ERROR", fg=RED)
            self._emit(f"[POLL ERROR] {e}")
        self.after(3000, self._poll)

    # ── file ops ──────────────────────────────────────────────────────────────
    def _upload(self):
        global _fpath,_fhash
        p=filedialog.askopenfilename(title="Open file to send",
            filetypes=[("Text","*.txt"),("All","*.*")])
        if not p: return
        with open(p,"r",encoding="utf-8",errors="replace") as f:
            content=f.read()
        # Always paste straight into the plaintext/message input box
        self._spt(content)
        _fpath=p; _fhash=utils.compute_sha256_from_file(p)
        self._emit(utils.format_hash_report(p,_fhash))
        self._sv.set(f"LOADED → PLAINTEXT BUFFER: {os.path.basename(p)}")

    def _download(self):
        # Save whatever is currently in the plaintext buffer.
        # If the user decrypted a message it will be there.
        # Fall back to the last ciphertext only if plaintext buffer is empty.
        text = self._pt().strip()
        if text:
            content  = text
            label    = "PLAINTEXT (decrypted)"
        elif _messages:
            content  = _messages[-1]["ct"]
            label    = "CIPHERTEXT (encrypted)"
        else:
            messagebox.showwarning("Nothing to save",
                "Decrypt a message first, or send/receive one."); return
        p=filedialog.asksaveasfilename(
            title=f"Save {label}",
            defaultextension=".txt",
            filetypes=[("Text","*.txt"),("All","*.*")])
        if not p: return
        with open(p,"w",encoding="utf-8") as f: f.write(content)
        sha=utils.compute_sha256(content.encode())
        self._emit(f"[SAVE] {os.path.basename(p)} ({label}) | SHA-256: {sha}")
        self._sv.set(f"SAVED: {os.path.basename(p)}")

    def _burn_msg(self):
        """Delete the latest message from Supabase and redraw chat history."""
        if not _messages:
            messagebox.showinfo("Nothing to Burn", "No messages in chat history."); return
        last = _messages[-1]
        preview = last["ct"][:40] + ("…" if len(last["ct"]) > 40 else "")
        if not messagebox.askyesno(
            "BURN LATEST MSG",
            f"Permanently delete this message from the database?\n\n"
            f"Sender : {last.get('sender','?')}\n"
            f"Preview: {preview}\n\n"
            "This cannot be undone."):
            return
        threading.Thread(target=self._burn_bg, daemon=True).start()

    def _burn_bg(self):
        """Background thread: delete from Supabase then force a full chat redraw."""
        try:
            ok = db_handler.delete_latest_message()
            if ok:
                self.after(0, self._redraw_chat)
                self.after(0, lambda: self._emit("[BURN] Latest message deleted from database."))
                self.after(0, lambda: self._sv.set("MSG BURNED // DATABASE UPDATED"))
                self.after(0, lambda: self._conn.config(text="● DB: ONLINE", fg=GRN))
            else:
                self.after(0, lambda: self._emit("[BURN] Delete failed — check Supabase logs."))
                self.after(0, lambda: self._conn.config(text="● DB: WARN", fg=AMB))
        except Exception as e:
            self.after(0, lambda: self._emit(f"[BURN ERROR] {e}"))
            self.after(0, lambda: self._conn.config(text="● DB: ERROR", fg=RED))

    def _redraw_chat(self):
        """Clear chat widget + _messages/_seen_ids, then re-fetch from DB."""
        global _messages, _seen_ids
        _messages = []; _seen_ids = set()
        self._clrc()          # clear the chat widget
        self._poll()          # re-fetch; _seen_ids is empty so all rows redisplay

    def _extract(self):
        src = filedialog.askopenfilename(
            title="Select stego image",
            filetypes=[("Images", "*.png *.jpg *.bmp"), ("All", "*.*")])
        if not src: return
        try:
            secret_text = lsb.reveal(src)
            if secret_text is None:
                self._spt("[ ERROR: No Hidden Payload Detected in Image ]")
                self._emit("[DEAD DROP] lsb.reveal() returned None — image may not contain hidden data.")
                self._sv.set("DEAD DROP: NO PAYLOAD FOUND")
                return
            # Paste the extracted secret directly into the PLAINTEXT BUFFER
            self._spt(secret_text)
            self._emit(f"[DEAD DROP] {len(secret_text)} chars extracted → pasted into plaintext buffer.")
            self._sv.set("DEAD DROP: EXTRACTED — Select algo and click DECRYPT")
        except IndexError:
            self._spt("[ ERROR: No Hidden Payload Detected in Image ]")
            self._emit("[DEAD DROP] IndexError — image contains no LSB-encoded payload.")
            self._sv.set("DEAD DROP: NO PAYLOAD FOUND")
        except Exception as e:
            messagebox.showerror("Extract Error", str(e))
            self._emit(f"[DEAD DROP ERROR] {e}")

    def _brute(self):
        if self.algo.get() != "Caesar":
            messagebox.showinfo("Caesar Only", "Brute-force is for Caesar only."); return
        text = _messages[-1]["ct"] if _messages else ""
        if not text.strip():
            messagebox.showwarning("Empty", "No message in chat to brute-force."); return

        # ── Build scrollable cyberpunk popup ─────────────────────────────────
        pop = tk.Toplevel(self)
        pop.title("CRYPTANALYSIS // CAESAR BRUTE-FORCE")
        pop.configure(bg=BG)
        pop.geometry("720x480")
        pop.resizable(True, True)

        tk.Label(pop, text="[ CAESAR BRUTE-FORCE — ALL 26 SHIFTS ]",
                 fg=RED, bg=BG, font=("Courier New", 11, "bold")).pack(pady=(10,2))
        tk.Label(pop, text="Find the shift where the output looks like English:",
                 fg=DIM, bg=BG, font=("Courier New", 9)).pack()
        tk.Frame(pop, bg=RED, height=1).pack(fill="x", padx=10, pady=4)

        frame = tk.Frame(pop, bg=BG)
        frame.pack(fill="both", expand=True, padx=10, pady=4)
        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")
        box = tk.Text(frame, bg=WGT, fg=GRN, font=("Courier New", 10),
                      relief="flat", bd=0, highlightthickness=1,
                      highlightbackground=RED, yscrollcommand=sb.set,
                      state="normal", wrap="word")
        box.pack(fill="both", expand=True)
        sb.config(command=box.yview)

        box.insert("end", f"INPUT: {text[:80]}{'…' if len(text)>80 else ''}\n")
        box.insert("end", "─"*64 + "\n")
        for s, decoded in ciphers.caesar_brute_force(text):
            line = f"  Shift {s:>2}: {decoded[:60].replace(chr(10),' ')}\n"
            box.insert("end", line)
        box.insert("end", "─"*64 + "\n")
        box.insert("end", "KEY SIZE: ~5 bits — only 26 keys. Trivially crackable.\n")
        box.config(state="disabled")

        # ── Apply shift button ────────────────────────────────────────────────
        bf = tk.Frame(pop, bg=BG)
        bf.pack(fill="x", padx=10, pady=(0,8))
        tk.Label(bf, text="Apply shift:", fg=GRN, bg=BG,
                 font=("Courier New", 9)).pack(side="left")
        shift_v = tk.StringVar(value="0")
        tk.Entry(bf, textvariable=shift_v, bg=WGT, fg=AMB,
                 insertbackground=AMB, font=("Courier New", 10),
                 width=4, relief="flat").pack(side="left", padx=6)

        def apply_shift():
            try:
                s = int(shift_v.get())
                result = ciphers.caesar_decrypt(text, s)
                self._spt(result)
                self._emit(f"[BRUTE] Applied shift {s} → result in plaintext buffer.")
                pop.destroy()
            except ValueError:
                messagebox.showerror("Bad shift", "Enter an integer 0-25.", parent=pop)

        tk.Button(bf, text="DECRYPT WITH THIS SHIFT", command=apply_shift,
                  fg=BG, bg=AMB, font=("Courier New", 9, "bold"),
                  relief="flat", cursor="hand2", padx=8, pady=3).pack(side="left")
        tk.Button(bf, text="CLOSE", command=pop.destroy,
                  fg=BG, bg=DIM, font=("Courier New", 9, "bold"),
                  relief="flat", cursor="hand2", padx=8, pady=3).pack(side="right")

        self._sv.set("BRUTE FORCE POPUP OPEN")

if __name__=="__main__":
    App().mainloop()
