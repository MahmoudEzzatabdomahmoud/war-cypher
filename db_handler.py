import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ENDPOINT = f"{SUPABASE_URL}/rest/v1/messages" if SUPABASE_URL else None

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# FIX: The "All Clear" signal that main.py is looking for
is_configured = True

def send_message(sender, ciphertext):
    """Pushes an encrypted message to the cloud database."""
    data = {
        "sender": sender,
        "ciphertext": ciphertext
    }
    try:
        response = requests.post(ENDPOINT, headers=HEADERS, json=data)
        if response.status_code == 201:
            print("[+] Transmission Successful.")
            return True
        else:
            print(f"[-] Transmission Failed. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[-] Network Error: {e}")
        return False

def fetch_messages():
    """Pulls all messages from the cloud database."""
    try:
        # Ask Supabase to return all columns, ordered by the time they were created
        params = {"select": "*", "order": "created_at.asc"}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        
        if response.status_code == 200:
            return response.json()  # Returns a list of message dictionaries
        else:
            print(f"[-] Fetch Failed. Status: {response.status_code}")
            return []
    except Exception as e:
        print(f"[-] Network Error: {e}")
        return []

# Adding a function version just in case Claude wrote it as a function call instead of a variable
def is_configured():
    return True

def delete_latest_message():
    """
    Deletes the most recent message from the Supabase messages table.
    Strategy: fetch all rows, grab the last row's id, then send DELETE filtered to that id.
    Returns True on success, False on failure.
    """
    try:
        # Step 1 — find the latest message id
        rows = fetch_messages()
        if not rows:
            print("[-] No messages to delete.")
            return False
        latest_id = rows[-1].get("id")
        if latest_id is None:
            print("[-] Latest message has no id field — cannot delete.")
            return False

        # Step 2 — DELETE that specific row via Supabase REST API
        # Supabase uses PostgREST filter syntax: id=eq.<value>
        del_headers = dict(HEADERS)
        del_headers["Prefer"] = "return=minimal"
        response = requests.delete(
            ENDPOINT,
            headers=del_headers,
            params={"id": f"eq.{latest_id}"}
        )
        if response.status_code in (200, 204):
            print(f"[+] Message id={latest_id} deleted from database.")
            return True
        else:
            print(f"[-] Delete failed. Status: {response.status_code} | Body: {response.text}")
            return False
    except Exception as e:
        print(f"[-] Network Error during delete: {e}")
        return False