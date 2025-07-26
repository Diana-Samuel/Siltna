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

from typing_extensions import Literal

dt = datetime.datetime.now(datetime.UTC)
ph = argon2.PasswordHasher()

enc_types = Literal['u','p','email']

# --- Master Key Functions ---
def createMK() -> None:
    k = Fernet.generate_key()
    mk_dir = "keys"
    if not os.path.exists(mk_dir):
        os.makedirs(mk_dir)
    with open(os.path.join(mk_dir, "mk.key"), "wb") as f:
        f.write(k)

def getMK() -> bytes:
    mk_path = os.path.join("keys", "mk.key")
    if not os.path.exists(mk_path):
        createMK()
    
    with open(mk_path, "rb") as f:
        k = f.read()
    return k


def get_canonical_date_str(input_date: str) -> str:
    try:
        parsed_date = datetime.datetime.strptime(str(input_date), "%Y-%m-%d").date()
    except ValueError:
        try:
            parsed_date = datetime.datetime.strptime(input_date, "%Y-%#m-%#d").date()
        except ValueError:
            raise ValueError(f"Unsupported date format: '{input_date}'. Expected YYYY-MM-DD or YYYY-M-D.")
    return parsed_date.strftime("%Y-%m-%d")


# --- Everyday key functions ---
def createKey(canonical_date_str: str, encType :enc_types = "u") -> None:
    key_dir = "keys"
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)

    key_for_aesgcm = os.urandom(32)
    
    mk = Fernet(getMK())
    enc_key = mk.encrypt(key_for_aesgcm)
    if encType == "p":
        key_filepath = os.path.join("keys",f"{canonical_date_str}_posts.key")
    elif encType == "u":
        key_filepath = os.path.join("keys",f"{canonical_date_str}_users.key")
    with open(key_filepath, "wb") as f:
        f.write(enc_key)
    return key_filepath

def loadKey(date: str = None, encType :enc_types = "u") -> bytes:
    if date is None:
        date_to_use = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_to_use = get_canonical_date_str(date)
    if encType == "p":
        key_filepath = os.path.join("keys",f"{date_to_use}_posts.key")
    elif encType == "u":
        key_filepath = os.path.join("keys",f"{date_to_use}_users.key")
    mk = Fernet(getMK())
    
    try:
        with open(key_filepath, "rb") as f:
            encrypted_key_from_file = f.read()
        
        decrypted_aesgcm_key = mk.decrypt(encrypted_key_from_file)
        
    except FileNotFoundError:
        key_filepath = createKey(date_to_use,encType=encType)
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
"""
TEXT ENCRYPTION
"""
def encrypt(data: str, date: str = None, encType :enc_types = "u") -> str:
    if date is None:
        date_for_key = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_for_key = get_canonical_date_str(date)
    key = loadKey(date_for_key,encType=encType)

    data_bytes = data.encode('utf-8')
    if encType == "email":
        nonce = b'\x0f\r@\x1aa\x9b62\xc5\x85\x9c\x04'
    else:
        nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    enctext_and_tag = aesgcm.encrypt(nonce=nonce, data=data_bytes, associated_data="m7".encode())
    combined_data = nonce + enctext_and_tag

    return base64.urlsafe_b64encode(combined_data).decode('utf-8')


def decrypt(data_b64_str: str, date: str = None, encType :enc_types = "u") -> str:
    if date is None:
        date_for_key = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_for_key = get_canonical_date_str(date)

    key = loadKey(date_for_key,encType=encType)

    combined_data = base64.urlsafe_b64decode(data_b64_str.encode('utf-8'))
    nonce = combined_data[:12]
    enctext_and_tag = combined_data[12:]

    aesgcm = AESGCM(key)
    try:
        dectext_bytes = aesgcm.decrypt(nonce=nonce, data=enctext_and_tag, associated_data="m7".encode())
        return dectext_bytes.decode('utf-8')
    except InvalidToken as e:
        raise e
    except Exception as e:
        raise e
        




"""
VERIFY LINK ENCRYPTION
"""
def encryptVerify(data: str) -> str:
    key = b'N\xfe\xd9\x84\xf3x\xab\xbd\xf9\xcf\xf9Bz"k\xe5\xab]\x15\x0e\x00\xc8\xd8S\xe7/?\x8d\x8f\xc5\x04\t'

    data_bytes = data.encode('utf-8')
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    enctext_and_tag = aesgcm.encrypt(nonce=nonce, data=data_bytes, associated_data="verify".encode())
    combined_data = nonce + enctext_and_tag

    return base64.urlsafe_b64encode(combined_data).decode('utf-8')


def decryptVerify(data_b64_str: str) -> str:
    key = b'N\xfe\xd9\x84\xf3x\xab\xbd\xf9\xcf\xf9Bz"k\xe5\xab]\x15\x0e\x00\xc8\xd8S\xe7/?\x8d\x8f\xc5\x04\t'

    combined_data = base64.urlsafe_b64decode(data_b64_str.encode('utf-8'))
    nonce = combined_data[:12]
    enctext_and_tag = combined_data[12:]

    aesgcm = AESGCM(key)
    try:
        dectext_bytes = aesgcm.decrypt(nonce=nonce, data=enctext_and_tag, associated_data="verify".encode())
        return dectext_bytes.decode('utf-8')
    except InvalidToken as e:
        raise e
    except Exception as e:
        raise e





"""
FILE ENCRYPTION
"""
def encryptFile(path: str, date: str) -> str:
    if date is None:
        date_for_key = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_for_key = get_canonical_date_str(date)

    key = loadKey(date_for_key, "p")
    with open(path, 'rb') as f:
        data_bytes = f.read()

    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(nonce=nonce, data=data_bytes, associated_data=b"m7")
    combined_data = nonce + encrypted
    return base64.urlsafe_b64encode(combined_data).decode('utf-8')    


def decryptFile(encoded_data, date=None):
    if date is None:
        date_for_key = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    else:
        date_for_key = get_canonical_date_str(date)

    key = loadKey(date_for_key, encType='p')

    combined_data = base64.urlsafe_b64decode(encoded_data.encode('utf-8'))
    nonce = combined_data[:12]
    encrypted_data = combined_data[12:]

    aesgcm = AESGCM(key)
    decrypted_data = aesgcm.decrypt(nonce=nonce, data=encrypted_data, associated_data=b"m7")

    return decrypted_data










"""
PASSWORD HASHING
"""
# Password Hashing
def hashpw(pw: str) -> str:
    salt = bcrypt.gensalt(12)
    bcrypt_hash = bcrypt.hashpw(pw.encode(), salt)
    final_hash = ph.hash(bcrypt_hash.decode())
    final_hash = salt.decode() + final_hash
    return final_hash

def checkpw(pw: str, stored_hash: str) -> bool:
    try:
        salt = stored_hash[:29].encode()
        stored_hash = stored_hash[29:]
        bcrypt_hash = bcrypt.hashpw(pw.encode(), salt)
        return ph.verify(stored_hash, bcrypt_hash.decode())
    except argon2.exceptions.VerifyMismatchError:
        return False
    



"""
E2EE (End to End Encryption)
"""
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

def createE2EEKeys(password: str) -> tuple[bool, tuple[str, str] | str | None]:
    """
    Create Private and Public PEM Keys for E2EE

    Inputs:
    password:   str                 # Password needed for encrypting private key

    Outputs:
    publicKey:  str                 # Public key of the user
    privateKey: str                 # private key of the user
    """

    # To Catch any Unexpected Exceptions
    try:
        if not password:
            return False, "Please Input the password"

        # Create New Private Key
        privateKey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Create new Public Key
        publicKey = privateKey.public_key()

        # Create Encryption Algorithm
        encryptionAlg = serialization.BestAvailableEncryption(password.encode())

        # Serialize Private Key
        privateKeyPEM = privateKey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryptionAlg
        ).decode()

        # Serialize Public Key
        publicKeyPEM = publicKey.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        return True, (publicKeyPEM, privateKeyPEM)
    
    # Handle Unknown Exceptions
    except Exception as e:
        from modules import logs
        logs.addLog(f"[enc.createE2EEKeys] Unexpected Exception: {e}")
        return False, str(e)
    

def decryptPrivateKey(privateKey: str, password: str) -> str | None:
    """
    Decrypts the Private key with Password

    Inputs:
    privateKey: str                 # private key to decrypt it
    password:   str                 # password for decryption
    
    Outputs:
    privateKey: str                 # decrypted private key
    """

    # To prevent Unknown Exceptions
    try:
        decryptedPrivateKey = serialization.load_pem_private_key(
            data=privateKey,
            password=password,
            backend=default_backend()
        )

        return decryptedPrivateKey
    
    except Exception as e:
        from modules import logs
        logs.addLog(f"[enc.decryptPrivateKey] Unexpected Exception: {e}")
        return None
    

def encryptMessage(message: str, publicKey: str) -> str:
    """
    Encrypt Message using Public Key

    Inputs:
    message:            str                 # Message needed to encrypt
    publicKey:          str                 # Public key for encryption

    Outputs:
    encryptedMessage:   str                 # Message after Encryption
    """

    encryptedMessage = publicKey.encrypt(
        message.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return base64.urlsafe_b64encode(encryptedMessage).decode('utf-8')


def decryptMessage(message: str, privateKey: str) -> str:
    """
    Decrypt Message using Private Key

    Inputs:
    message:            str                 # Message needed to decrypt
    privateKey:         str                 # Private key for Decryption

    Outputs:
    decryptedMessage:   str                 # Message after Decryption
    """

    message = base64.urlsafe_b64decode(message).decode('utf-8')

    decryptedMessage = privateKey.decrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decryptedMessage.decode()