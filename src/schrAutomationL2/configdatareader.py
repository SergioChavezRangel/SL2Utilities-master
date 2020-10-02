"""
Settings Encoder/Decoder

* Initially, Encode an xml file to dist with apps
* On runtime apps, decode settings and useful key
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import time
import binascii
import base64
import schrAutomationL2.logger as logger
import xml.etree.ElementTree as Xml

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
        logger.writeLog('getEncText: ' + cipher_text.decode())
    return cipher_text


def getDecText(cipher_text, log):
    global key
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(cipher_text)
    if log:
        print("\nPlain text: ", plain_text)
        logger.writeLog('getDecText: ' + plain_text.decode())
    return plain_text


def setDecFilePath(file_path, log):
    global decryptedFile
    decryptedFile = file_path
    if log:
        logger.writeLog('setDecFilePath: ' + decryptedFile)


def getDecFilePath(log):
    global decryptedFile
    if log:
        print(decryptedFile)
        logger.writeLog('getDecFilePath: ' + decryptedFile)
    return decryptedFile


def setEncFilePath(file_path, log):
    global encryptedFile
    encryptedFile = file_path
    if log:
        logger.writeLog('setEncFilePath: ' + encryptedFile)


def getEncFilePath(log):
    global encryptedFile
    if log:
        print(encryptedFile)
        logger.writeLog('getEncFilePath: ' + encryptedFile)
    return encryptedFile


def encodeXML(log):
    global decryptedFile
    global encryptedFile
    filename = decryptedFile
    tree = Xml.ElementTree(file=filename)
    root = tree.getroot()
    fileEraser(encryptedFile)
    fileWriter('<?xml version="1.0"?>', encryptedFile)
    fileWriter('<root>', encryptedFile)
    fileWriter('    <KEYDATA value="%s"/>' % (key.decode()), encryptedFile)
    i = 0
    for elt in root:
        Tag = getEncText(elt.tag.encode(), log)
        if log:
            print("%s:" % elt.tag)
            print("   value = '%s'" % (elt.get('value')))
        Value = getEncText(elt.get('value').encode(), log)
        fileWriter('    <VALUE%i Tag="%s" value="%s"/>' % (i, Tag.decode(), Value.decode()), encryptedFile)
        i = i + 1
    fileWriter('</root>', encryptedFile)


def decodeXML(save_file, log):
    global decryptedFile
    global encryptedFile
    global key
    filename = encryptedFile
    tree = Xml.ElementTree(file=filename)
    root = tree.getroot()
    Values = []
    if save_file:
        fileEraser(decryptedFile)
        fileWriter('<?xml version="1.0"?>', decryptedFile)
        fileWriter('<root>', decryptedFile)
    for elt in root:
        if elt.tag == 'KEYDATA':
            key = elt.get('value')
            if save_file:
                fileWriter('    < Token value="%s" / >' % key, decryptedFile)
        if 'VALUE' in elt.tag:
            Tag = getDecText(elt.get('Tag').encode(), log)
            Value = getDecText(elt.get('value').encode(), log)
            Values.append((Tag.decode(), Value.decode()))
            if save_file:
                fileWriter('    <%s value="%s"/>' % (Tag.decode(), Value.decode()), decryptedFile)
    if save_file:
        fileWriter('</root>', decryptedFile)
    return dict(Values)


def fileWriter(line, file_name):
    f = open(file_name, 'a')
    f.write(line)
    print(line)
    f.write("\n")
    f.close()


def fileEraser(file_name):
    try:
        f = open(file_name, 'w')
        f.write("")
        f.close()
    except:
        logger.writeLog('Error Deleting file: ' + file_name)


def isValidKey(token=None):
    try:
        if token is None:
            token = decodeXML(False, False)["Token"]
        ActKey = int(time.strftime("%y", time.localtime())) * 20000
        ActKey = ActKey + (
                (int(time.strftime("%y", time.localtime())) + int(time.strftime("%m", time.localtime()))) * 100)
        ActKey = ActKey + int(time.strftime("%m", time.localtime())) + int(time.strftime("%d", time.localtime())) + int(
            time.strftime("%y", time.localtime()))
        token = int(token)
    except:
        return False
    if ActKey > token:
        return False
    else:
        return True


def getExpireDate(token=None):
    try:
        if token is None:
            token = decodeXML(False)["Token"]
        tk = int(token)
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
        return '{:04d}-{:02d}-{:02d}'.format(y, m, d)
    except:
        return '2000-01-01'


def getTokenDate(expire_date):
    try:
        tk = int(expire_date.strftime("%y")) * 20000
        tk = tk + ((int(expire_date.strftime("%y")) + int(expire_date.strftime("%m"))) * 100)
        tk = tk + int(expire_date.strftime("%m")) + int(expire_date.strftime("%d")) + int(expire_date.strftime("%y"))
        return tk
    except:
        return 122353


print("DefaultKey: ", binascii.hexlify(bytearray(key)))
print("DefaultFile: ", decryptedFile)
