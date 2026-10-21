"""
Settings Encoder/Decoder
Provides Fernet symmetric encryption for XML configuration files,
key generation, and license/token expiration calculation.
"""
import base64
import binascii
import datetime
import xml.etree.ElementTree as Xml
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from sl2util import logger

# Default runtime state
key: bytes = Fernet.generate_key()
decryptedFile: str = "Decrypted.xml"
encryptedFile: str = "Encrypted.xml"
configFile: str = "Config.xml"


def get_key(password: str | bytes) -> bytes:
    """
    Derive a URL-safe base64-encoded 32-byte key from a password using SHA-256.
    """
    if isinstance(password, str):
        password = password.encode("utf-8")
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(password)
    return base64.urlsafe_b64encode(digest.finalize())


def set_key(mykey: str | bytes) -> None:
    """Set the active encryption/decryption key."""
    global key
    if isinstance(mykey, str):
        mykey = mykey.encode("utf-8")
    key = mykey


def getEncText(plain_text: str | bytes, log: bool = False) -> bytes:
    """Encrypt plain text bytes using the active Fernet key."""
    global key
    if isinstance(plain_text, str):
        plain_text = plain_text.encode("utf-8")

    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(plain_text)
    cipher = binascii.hexlify(bytearray(cipher_text))

    if log:
        print(cipher_text)
        print("Cipher: ", cipher)
        print("\nVersion:\t", cipher[0:2])
        print("Time stamp:\t", cipher[2:18])
        print("IV:\t\t", cipher[18:50])
        print("HMAC:\t\t", cipher[-64:])
        logger.writeLog("getEncText: " + cipher_text.decode("utf-8", errors="replace"))

    return cipher_text


def getDecText(cipher_text: str | bytes, log: bool = False) -> bytes:
    """Decrypt cipher text bytes using the active Fernet key."""
    global key
    if isinstance(cipher_text, str):
        cipher_text = cipher_text.encode("utf-8")

    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(cipher_text)

    if log:
        print("\nPlain text: ", plain_text)
        logger.writeLog("getDecText: " + plain_text.decode("utf-8", errors="replace"))

    return plain_text


def setDecFilePath(file_path: str | Path, log: bool = False) -> None:
    """Set the path to the decrypted XML file."""
    global decryptedFile
    decryptedFile = str(file_path)
    if log:
        logger.writeLog("setDecFilePath: " + decryptedFile)


def getDecFilePath(log: bool = False) -> str:
    """Get the path to the decrypted XML file."""
    global decryptedFile
    if log:
        print(decryptedFile)
        logger.writeLog("getDecFilePath: " + decryptedFile)
    return decryptedFile


def setEncFilePath(file_path: str | Path, log: bool = False) -> None:
    """Set the path to the encrypted XML file."""
    global encryptedFile
    encryptedFile = str(file_path)
    if log:
        logger.writeLog("setEncFilePath: " + encryptedFile)


def getEncFilePath(log: bool = False) -> str:
    """Get the path to the encrypted XML file."""
    global encryptedFile
    if log:
        print(encryptedFile)
        logger.writeLog("getEncFilePath: " + encryptedFile)
    return encryptedFile


def setConfigFilePath(file_path: str | Path, log: bool = False) -> None:
    """Set the path to the open configuration XML file."""
    global configFile
    configFile = str(file_path)
    if log:
        logger.writeLog("setConfigFilePath: " + configFile)


def fileWriter(line: str, file_name: str | Path) -> None:
    """Append a line to a file, creating parent directories if needed."""
    path = Path(file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fileEraser(file_name: str | Path) -> None:
    """Clear or truncate a file."""
    path = Path(file_name)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
    except Exception as e:
        logger.writeLog(f"Error Deleting file: {file_name} ({e})")


def encodeXML(log: bool = False) -> None:
    """
    Encode the decrypted XML configuration file into an encrypted XML file.
    """
    global decryptedFile, encryptedFile, key

    tree = Xml.ElementTree(file=decryptedFile)
    root = tree.getroot()

    fileEraser(encryptedFile)
    fileWriter('<?xml version="1.0"?>', encryptedFile)
    fileWriter("<root>", encryptedFile)
    key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
    fileWriter(f'    <KEYDATA value="{key_str}"/>', encryptedFile)

    for i, elt in enumerate(root):
        tag_enc = getEncText(elt.tag.encode("utf-8"), log).decode("utf-8")
        val_raw = elt.get("value", "")
        if log:
            print(f"{elt.tag}:")
            print(f"   value = '{val_raw}'")
        val_enc = getEncText(val_raw.encode("utf-8"), log).decode("utf-8")
        fileWriter(f'    <VALUE{i} Tag="{tag_enc}" value="{val_enc}"/>', encryptedFile)

    fileWriter("</root>", encryptedFile)


def decodeXML(save_file: bool = False, log: bool = False) -> dict[str, str]:
    """
    Decode an encrypted XML file and return its values as a dictionary.
    Optionally saves the decoded content to decryptedFile.
    """
    global decryptedFile, encryptedFile, key

    tree = Xml.ElementTree(file=encryptedFile)
    root = tree.getroot()
    values = []

    if save_file:
        fileEraser(decryptedFile)
        fileWriter('<?xml version="1.0"?>', decryptedFile)
        fileWriter("<root>", decryptedFile)

    for elt in root:
        if elt.tag == "KEYDATA":
            key_val = elt.get("value", "")
            key = key_val.encode("utf-8") if isinstance(key_val, str) else key_val
            if save_file:
                fileWriter(f'    <Token value="{key_val}"/>', decryptedFile)
        elif "VALUE" in elt.tag:
            tag_attr = elt.get("Tag", "")
            val_attr = elt.get("value", "")
            dec_tag = getDecText(tag_attr.encode("utf-8"), log).decode("utf-8")
            dec_val = getDecText(val_attr.encode("utf-8"), log).decode("utf-8")
            values.append((dec_tag, dec_val))
            if save_file:
                fileWriter(f'    <{dec_tag} value="{dec_val}"/>', decryptedFile)

    if save_file:
        fileWriter("</root>", decryptedFile)

    return dict(values)


def isValidKey(token: Any | None = None) -> bool:
    """
    Validate whether a license token is still active based on the date algorithm.
    """
    try:
        if token is None:
            token = decodeXML(False, False).get("Token")
        now = datetime.datetime.now()
        yy = int(now.strftime("%y"))
        mm = int(now.strftime("%m"))
        dd = int(now.strftime("%d"))
        act_key = yy * 20000 + ((yy + mm) * 100) + mm + dd + yy
        token_num = int(token)
    except Exception:
        return False
    return act_key <= token_num


def getExpireDate(token: Any | None = None) -> str:
    """
    Calculate and format the expiration date (YYYY-MM-DD) from a token.
    """
    try:
        if token is None:
            token = decodeXML(False).get("Token")
        tk = int(token)
        y = int((tk - (tk % 20000)) / 20000)
        m = int(((tk % 20000) // 100) - y)
        d = int((tk % 20000) - (tk % 20000 // 100 * 100) - (y + m))
        y = 2001 if y < 1 else 2000 + y
        m = 1 if (m < 1 or m > 12) else m
        d = 1 if (d < 1 or d > 31) else d
        return f"{y:04d}-{m:02d}-{d:02d}"
    except Exception:
        return "2000-01-01"


def getTokenDate(expire_date: datetime.date | datetime.datetime) -> int:
    """
    Generate an integer token representing an expiration date.
    """
    try:
        yy = int(expire_date.strftime("%y"))
        mm = int(expire_date.strftime("%m"))
        dd = int(expire_date.strftime("%d"))
        tk = yy * 20000 + ((yy + mm) * 100) + mm + dd + yy
        return tk
    except Exception:
        return 122353


def getOpenConfig() -> dict[str, str]:
    """
    Parse the unencrypted configuration XML and return tag-value pairs.
    """
    global configFile
    tree = Xml.ElementTree(file=configFile)
    root = tree.getroot()
    values = [(elt.tag, elt.get("value", "")) for elt in root]
    return dict(values)
