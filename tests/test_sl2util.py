"""SL2Utilities.
Min xml to encode structure:
    <?xml version="1.0"?>
    <root>
        <Token value="123456"/>
        <Key1 value="val1"/>
        ...
        <Keyn value="valn"/>
    </root>
"""
import datetime
import os
import sys
import sl2util.logger as logger
import sl2util.configdatareader as cryptlib
import sl2util.dbhandler as db
import sl2util.utils as util
import sl2util.watchdog as watchdog

##### All AutomationL2Prj must start at least here #####
BASE_FILE = os.path.basename(sys.argv[0])
BASE_PATH = os.getcwd()
FULL_PATH_FILE = os.getcwd() + '\\' + BASE_FILE
logger.setPath(BASE_PATH)
logger.setFileName(BASE_FILE)


def _test():
    option = -1
    while option != 0:
        os.system('cls')
        print('OPTIONS: \n1. Encode Settings (File->File)\n2. Decode Settings (File->File)')
        print('3. Decode Settings (File->Memory)\n4. Get Token from Date\n5. Get Expiredate from Token')
        print('6. Check DataBase (MSSQL)\n7. Check DataBase (Oracle)\n8. Mail\n0. EXIT')
        option = int(input('Choose what to do??:'))
        if option == 1:
            KeyPassword = input('Personal KeyPassword:')
            print('BASE_PATH: ' + BASE_PATH)
            DecFile = input('Decoded ProjectFile Name(./):')
            key = cryptlib.get_key(KeyPassword.encode())
            cryptlib.set_key(key)
            cryptlib.setDecFilePath(BASE_PATH + '\\' + DecFile, True)
            cryptlib.setEncFilePath(BASE_PATH + '\\' + 'enc' + DecFile, True)
            cryptlib.setConfigFilePath(BASE_PATH + '\\' + 'Config.xml', True)
            cryptlib.encodeXML(False)

        if option in (2, 3):
            print('BASE_PATH: ' + BASE_PATH)
            EncFile = input('Encoded ProjectFile Name(./):')
            cryptlib.setDecFilePath(BASE_PATH + '\\' + EncFile, True)
            cryptlib.setEncFilePath(BASE_PATH + '\\' + EncFile, True)
            cryptlib.setConfigFilePath(BASE_PATH + '\\' + 'Config.xml', True)
            createFile = False
            if option == 2:
                createFile = True
            Config = (cryptlib.decodeXML(createFile, False))
            print(Config)
            Key = cryptlib.isValidKey(Config["Token"])
            print('TokenValid: ' + str(Key))
            print('Config.ExpireDate: ' + cryptlib.getExpireDate(Config["Token"]))
            print('OpenConfig')
            Config = (cryptlib.getOpenConfig())
            print(Config)

        if option == 4:
            date = input('Date (YYYY-MM-DD):')
            yyyy = int(date[:4])
            mm = int(date[5:-3])
            dd = int(date[-2:])
            print('TokenDate: ' + str(cryptlib.getTokenDate(datetime.date(yyyy, mm, dd))))

        if option == 5:
            tk = input('Token to validate:')
            print('ExpireDate: ' + cryptlib.getExpireDate(tk))

        if option == 6:
            dbconn = input('DB Conn string:')
            testdb = db.DbSQL(dbconn)
            sql = 'SELECT getdate() as date'
            print(testdb.getrow(sql))

        if option == 7:
            dbconn = input('DB Conn string:')
            testdb = db.DbOra(dbconn)
            sql = 'SELECT sysdate as now from dual'
            print(testdb.getrow(sql))

        if option == 8:
            util.mail_test('Subject','schavezr@gan.com.mx', '')
            # util.html_mailer('Example','body text', 'schavezr@gan.com.mx','','MNTTO', '','')

        if option == 9:
            # watchdog.service_name = BASE_FILE.encode()

            port = int(cryptlib.getOpenConfig()['WatchdogPort'])
            watchdog.start_watchdog(BASE_FILE.encode(), port)

    logger.purger()


##### All AutomationL2Prj must start at least here #####


if __name__ == '__main__':
    _test()
