# import base64
# import os
# from cryptography.fernet import Fernet
# from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
#
# password = b"password"
# salt = os.urandom(16)
# kdf = PBKDF2HMAC(
#     algorithm=hashes.SHA256(),
#     length=32,
#     salt=salt,
#     iterations=100000,
# )
# key = base64.urlsafe_b64encode(kdf.derive(password))
# f = Fernet(key)
# token = f.encrypt(b"Secret message!")
# print(token)
# print(f.decrypt(token))

# https://asecuritysite.com/encryption/fernet
from datetime import datetime
import time

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import binascii
import base64
import schrAutomationL2.Logger as Logger
import xml.etree.ElementTree as xml

key = Fernet.generate_key()
decryptedFile = 'Decrypted.xml'
encryptedFile = 'Encrypted.xml'


def get_key(password):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(password)
    return base64.urlsafe_b64encode(digest.finalize())


def set_key(mykey):
    global key
    key = mykey


def getEncText(plain_text, log):
    global key
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
        Logger.writeLog('getEncText: ' + cipher_text.decode())
    return cipher_text


def getDecText(cipher_text, log):
    global key
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(cipher_text)
    if log:
        print("\nPlain text: ", plain_text)
        Logger.writeLog('getDecText: ' + plain_text.decode())
    return plain_text


def setDecFilePath(FilePath, log):
    global decryptedFile
    decryptedFile = FilePath
    if log:
        Logger.writeLog('setDecFilePath: ' + decryptedFile)


def getDecFilePath(log):
    global decryptedFile
    if log:
        print(decryptedFile)
        Logger.writeLog('getDecFilePath: ' + decryptedFile)
    return decryptedFile


def setEncFilePath(FilePath, log):
    global encryptedFile
    encryptedFile = FilePath
    if log:
        Logger.writeLog('setEncFilePath: ' + encryptedFile)


def getEncFilePath(log):
    global encryptedFile
    if log:
        print(encryptedFile)
        Logger.writeLog('getEncFilePath: ' + encryptedFile)
    return encryptedFile


def encodeXML(log):
    global decryptedFile
    global encryptedFile
    filename = decryptedFile
    # Start with the root element
    tree = xml.ElementTree(file=filename)
    root = tree.getroot()
    fileEraser(encryptedFile)
    fileWriter('<?xml version="1.0"?>', encryptedFile)
    fileWriter('<root>', encryptedFile)
    fileWriter('    <KEYDATA value="%s"/>' % (key.decode()), encryptedFile)
    i = 0
    for elt in root:
        Tag = getEncText(elt.tag.encode(), log)
        if log:
            print("%s:" % (elt.tag))
            print("   value = '%s'" % (elt.get('value')))
        Value = getEncText(elt.get('value').encode(), log)
        # <EAFDB value="AHMSASPEEAF1/0815Pwd!@AHMSA_SPE_EAF"/>
        fileWriter('    <VALUE%i Tag="%s" value="%s"/>' % (i, Tag.decode(), Value.decode()), encryptedFile)
        i = i + 1
    fileWriter('</root>', encryptedFile)


def decodeXML(createFile, log):
    global decryptedFile
    global encryptedFile
    global key
    filename = encryptedFile
    # print(filename)
    tree = xml.ElementTree(file=filename)
    root = tree.getroot()
    Values = []
    if createFile:
        fileEraser(decryptedFile)
        fileWriter('<?xml version="1.0"?>', decryptedFile)
        fileWriter('<root>', decryptedFile)
    for elt in root:
        if elt.tag == 'KEYDATA':
            key = elt.get('value')
            if createFile:
                fileWriter('    < Token value="%s" / >' % (key), decryptedFile)
        if 'VALUE' in elt.tag:
            Tag = getDecText(elt.get('Tag').encode(), log)
            Value = getDecText(elt.get('value').encode(), log)
            Values.append((Tag.decode(), Value.decode()))
            if createFile:
                fileWriter('    <%s value="%s"/>' % (Tag.decode(), Value.decode()), decryptedFile)
    if createFile:
        fileWriter('</root>', decryptedFile)
    return dict(Values)


def fileWriter(line, fileName):
    f = open(fileName, 'a')
    f.write(line)
    print(line)
    f.write("\n")
    f.close()


def fileEraser(fileName):
    try:
        f = open(fileName, 'w')
        f.write("")
        f.close()
    except:
        Logger.writeLog('Error Deleting file: ' + fileName)


def isValidKey(Token=None):
    try:
        if (Token is None):
            Token = decodeXML(False, False)["Token"]
        ActKey = int(time.strftime("%y", time.localtime())) * 20000
        ActKey = ActKey + (
                (int(time.strftime("%y", time.localtime())) + int(time.strftime("%m", time.localtime()))) * 100)
        ActKey = ActKey + int(time.strftime("%m", time.localtime())) + int(time.strftime("%d", time.localtime())) + int(
            time.strftime("%y", time.localtime()))
        Token = int(Token)
    except:
        return False
    if (ActKey > Token):
        return False
    else:
        return True


def getExpireDate(Token=None):
    try:
        if Token is None:
            Token = decodeXML(False)["Token"]
        tk = int(Token)
        y = int((tk - (tk % 20000)) / 20000)
        m = int(((tk % 20000) // 100) - y)
        d = int((tk % 20000) - (tk % 20000 // 100 * 100) - (y + m))
        if y < 1:
            y = 2001
        else:
            y = 2000 + y
        if m < 1 or m > 12:
            m = 1
        if d < 1 or d > 31:
            d = 1
        # dt = datetime.datetime(y, m, d)
        return '{:04d}-{:02d}-{:02d}'.format(y, m, d)
        # dt.isoformat()''
    except:
        return '2000-01-01'


def getTokenDate(ExpDate):
    try:
        tk = int(ExpDate.strftime("%y")) * 20000
        tk = tk + ((int(ExpDate.strftime("%y")) + int(ExpDate.strftime("%m"))) * 100)
        tk = tk + int(ExpDate.strftime("%m")) + int(ExpDate.strftime("%d")) + int(ExpDate.strftime("%y"))
        return tk
    except:
        return 122353


print("DefaultKey: ", binascii.hexlify(bytearray(key)))
print("DefaultFile: ", decryptedFile)
