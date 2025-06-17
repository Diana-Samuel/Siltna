import bcrypt
import argon2

import os
import datetime

import binascii
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from cryptography.fernet import InvalidToken

import base64

dt = datetime.datetime.now(datetime.UTC)
ph = argon2.PasswordHasher()


# --- Master Key Functions ---
def createMK() -> None:
    k = Fernet.generate_key()
    mk_dir = "keys"
    if not os.path.exists(mk_dir):
        os.makedirs(mk_dir)
    with open(os.path.join(mk_dir, "mk.key"), "wb") as f:
        f.write(k)
    print("Master Key 'mk.key' created.")

def getMK() -> bytes:
    mk_path = os.path.join("keys", "mk.key")
    if not os.path.exists(mk_path):
        print("Master Key 'mk.key' not found. Creating it...")
        createMK()
    
    with open(mk_path, "rb") as f:
        k = f.read()
    return k


def get_canonical_date_str(input_date: str) -> str:
    try:
        parsed_date = datetime.datetime.strptime(input_date, "%Y-%m-%d").date()
    except ValueError:
        try:
            parsed_date = datetime.datetime.strptime(input_date, "%Y-%#m-%#d").date()
        except ValueError:
            raise ValueError(f"Unsupported date format: '{input_date}'. Expected YYYY-MM-DD or YYYY-M-D.")
    return parsed_date.strftime("%Y-%m-%d")


# --- Everyday key functions ---
def createKey(canonical_date_str: str) -> None:
    key_dir = "keys"
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)

    key_for_aesgcm = os.urandom(32)
    
    mk = Fernet(getMK())
    enc_key = mk.encrypt(key_for_aesgcm)

    key_filepath = os.path.join(key_dir, f"{canonical_date_str}.key")
    with open(key_filepath, "wb") as f:
        f.write(enc_key)
    print(f"Created and saved new encrypted key to {key_filepath}")

def loadKey(date: str = None) -> bytes:
    if date is None:
        date_to_use = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_to_use = get_canonical_date_str(date)

    key_filepath = os.path.join("keys", f"{date_to_use}.key")
    mk = Fernet(getMK())
    
    print(f"loadKey: Attempting to load key from: {key_filepath}")

    try:
        with open(key_filepath, "rb") as f:
            encrypted_key_from_file = f.read()
        
        decrypted_aesgcm_key = mk.decrypt(encrypted_key_from_file)
        
    except FileNotFoundError:
        createKey(date_to_use)
        try:
            with open(key_filepath, "rb") as f:
                encrypted_key_from_file = f.read()
            decrypted_aesgcm_key = mk.decrypt(encrypted_key_from_file)
        except InvalidToken as e:
            raise
        except Exception as e:
            raise
    except InvalidToken as e:
        raise
    except Exception as e:
        raise

    if not isinstance(decrypted_aesgcm_key, bytes) or len(decrypted_aesgcm_key) != 32:
        raise ValueError(f"loadKey returned an invalid key: type {type(decrypted_aesgcm_key)}, length {len(decrypted_aesgcm_key) if isinstance(decrypted_aesgcm_key, bytes) else 'N/A'}. Expected 32 bytes.")
        
    return decrypted_aesgcm_key


# --- Encrypting ---
def encrypt(data: str, date: str = None) -> str:
    if date is None:
        date_for_key = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_for_key = get_canonical_date_str(date)

    key = loadKey(date_for_key)

    data_bytes = data.encode('utf-8')
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    enctext_and_tag = aesgcm.encrypt(nonce=nonce, data=data_bytes, associated_data="m7".encode())
    combined_data = nonce + enctext_and_tag

    return base64.urlsafe_b64encode(combined_data).decode('utf-8')


def decrypt(data_b64_str: str, date: str = None) -> str:
    if date is None:
        date_for_key = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_for_key = get_canonical_date_str(date)

    key = loadKey(date_for_key)

    combined_data = base64.urlsafe_b64decode(data_b64_str.encode('utf-8'))
    nonce = combined_data[:12]
    enctext_and_tag = combined_data[12:]

    aesgcm = AESGCM(key)
    try:
        dectext_bytes = aesgcm.decrypt(nonce=nonce, data=enctext_and_tag, associated_data="m7".encode())
        return dectext_bytes.decode('utf-8')
    except InvalidToken as e:
        print(f"Decryption failed: {e} - Invalid tag or corrupted data/key/nonce/associated data.")
        raise
    except Exception as e:
        print(f"Decryption failed with unexpected error: {e}")
        raise
        



# Password Hashing
def hashpw(pw: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw.encode(),salt)
    hashed2 = ph.hash(hashed)
    return hashed2

def checkpw(pw: str,hashedpw: str) -> bool:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw.encode(),salt)
    try:
        if ph.verify(hashed,hashedpw):
            return True
    except argon2.exceptions.VerifyMismatchError:
        return False

