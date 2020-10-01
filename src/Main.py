import datetime
import os
import sys
import schrAutomationL2.Logger as Logger
import schrAutomationL2.ConfigData as CryptLib

##### All AutomationL2Prj must start at least here #####
BaseFile = os.path.basename(sys.argv[0])
BasePath = os.getcwd()
FullPath = os.getcwd() + '\\' + BaseFile
Logger.setPath(BasePath + '\\log')
Logger.setFileName(BaseFile)

print('OPTIONS: \n1. Encode Settings (File->File)\n2. Decode Settings (File->File)')
print('3. Decode Settings (File->Memory)\n4. Get Token from Date\n5. Get Expiredate from Token')
option = int(input('Choose what to do??:'))
if option == 1:
    KeyPassword = input('Personal KeyPassword:')
    print('BasePath: ' + BasePath + '\\DecodedFile\\')
    DecFile = input('Decoded ProjectFile Name(./DecodedFile/):')
    key = CryptLib.get_key(KeyPassword.encode())
    CryptLib.set_key(key)
    CryptLib.setDecFilePath(BasePath + '\\DecodedFile\\' + DecFile, True)
    CryptLib.setEncFilePath(BasePath + '\\EncodedFile\\' + DecFile, True)
    CryptLib.encodeXML(False)

if option in (2, 3):
    print('BasePath: ' + BasePath + '\\EncodedFile\\')
    EncFile = input('Encoded ProjectFile Name(./EncodedFile/):')
    CryptLib.setDecFilePath(BasePath + '\\DecodedFile\\' + EncFile, True)
    CryptLib.setEncFilePath(BasePath + '\\EncodedFile\\' + EncFile, True)
    createFile = False
    if option == 2:
        createFile = True
    Config = (CryptLib.decodeXML(createFile, False))
    print(Config)
    Key = CryptLib.isValidKey(Config["Token"])
    print('TokenValid: ' + str(Key))
    print('Config.ExpireDate: ' + CryptLib.getExpireDate(Config["Token"]))

if option == 4:
    date = input('Date (YYYY-MM-DD):')
    yyyy = int(date[:4])
    mm = int(date[5:-3])
    dd = int(date[-2:])
    print('TokenDate: ' + str(CryptLib.getTokenDate(datetime.date(yyyy, mm, dd))))

if option == 5:
    tk = input('Token to validate:')
    print('ExpireDate: ' + CryptLib.getExpireDate(tk))

##### All AutomationL2Prj must start at least here #####

Logger.purger()
