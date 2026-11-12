# WarCyphere Pro: E2EE Asynchronous Chat Terminal

**WarCyphere Pro** is a high-security, tactical end-to-end encrypted (E2EE) chat terminal designed for secure asynchronous communication. Built with a focus on OPSEC (Operations Security) and cryptographic robustness, it leverages a hybrid suite of classical and post-quantum resistant asymmetric algorithms.

## Overview

In an era of ubiquitous surveillance, WarCyphere Pro provides a dedicated environment for secure data exchange. By utilizing a Supabase REST backend as an untrusted relay, the system ensures that plaintext never touches the wire. All encryption and decryption occur locally on the client-side, maintaining a strict Zero-Trust architecture.

## Features

### 1. Cryptographic Suite
*   **Group 1 (Classical Ciphers):** Caesar, ROT13, Playfair, Vigenère, Rail Fence. These are included for educational purposes and legacy compatibility.
*   **Group 2 (Advanced Asymmetric):**
    *   **RSA & ECC:** Standard industry-grade asymmetric encryption.
    *   **ElGamal & Paillier:** Mathematical primitives based on the Discrete Logarithm Problem and Composite Residuosity.
    *   **NTRU & McEliece:** Lattice-based and Code-based cryptography designed to be resistant to future quantum computing attacks.
    *   **Diffie-Hellman (DH):** Secure key exchange protocol for deriving shared secrets.

### 2. Tactical OPSEC Tools
*   **Burn Latest Message:** Instantly purge the most recent communication from both the local UI and the remote database.
*   **Dead Drop (LSB Steganography):** Hide encrypted payloads within innocent-looking image files (.png, .jpg, .bmp) for covert transmission.
*   **Wiretap Simulation:** Real-time visualization of intercepted network traffic, demonstrating the efficacy of E2EE.
*   **Intel Feed:** Detailed system logs providing visibility into cryptographic operations and transmission status.

### 3. Unified Serialization
*   Public keys and ciphertexts are serialized into clean, copy-pasteable Base64/JSON strings, ensuring cross-platform data integrity and preventing UTF-8 corruption during relay.

## Tech Stack
*   **Language:** Python 3.x
*   **GUI Framework:** Tkinter (Retro Terminal Aesthetic)
*   **Cryptography:** PyCryptodome
*   **Backend:** Supabase (REST API Interaction)
*   **Environment Management:** python-dotenv

## Installation & Setup

### Prerequisites
*   Python 3.10+
*   A Supabase account and project.

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/warcyphere.git
cd warcyphere
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```
*(Note: Create a `requirements.txt` with `pycryptodome`, `requests`, `python-dotenv`, `Pillow`, and `stegano`.)*

### Step 3: Configure Environment Variables
1. Copy the template: `cp .env.example .env`
2. Open `.env` and enter your Supabase credentials:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### Step 4: Database Setup
Ensure your Supabase project has a table named `messages` with the following columns:
*   `id`: int8 (Primary Key, Auto-increment)
*   `created_at`: timestamptz (Default: now())
*   `sender`: text
*   `ciphertext`: text
*   `algorithm`: text (Optional)

### Step 5: Launch the Terminal
```bash
python main.py
```

## Security Warning
*   **Zero-Trust:** The developers of WarCyphere Pro assume the relay server is compromised. Always verify public keys via a secondary out-of-band channel.
*   **Key Management:** Private keys are stored in volatile memory and are lost upon closing the application. This is a deliberate design choice to prevent local data leakage.

---
*Developed for Academic and Tactical Cybersecurity Research.*
