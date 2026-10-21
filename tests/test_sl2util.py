"""SL2Utilities Interactive Test CLI.
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
from pathlib import Path

import sl2util.configdatareader as cryptlib
import sl2util.dbhandler as db
import sl2util.utils as util
from sl2util import logger, watchdog

BASE_FILE = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "test_sl2util"
BASE_PATH = str(Path.cwd())
FULL_PATH_FILE = str(Path.cwd() / BASE_FILE)
logger.setPath(BASE_PATH)
logger.setFileName(BASE_FILE)


def interactive_test_menu():
    """Interactive CLI menu for manual smoke testing."""
    option = -1
    while option != 0:
        print("\nOPTIONS:")
        print("1. Encode Settings (File->File)")
        print("2. Decode Settings (File->File)")
        print("3. Decode Settings (File->Memory)")
        print("4. Get Token from Date")
        print("5. Get Expiredate from Token")
        print("6. Check DataBase (MSSQL)")
        print("7. Check DataBase (Oracle)")
        print("8. Mail")
        print("9. Watchdog")
        print("0. EXIT")
        try:
            choice = input("Choose what to do??:")
            option = int(choice)
        except (ValueError, EOFError):
            break

        if option == 1:
            KeyPassword = input("Personal KeyPassword:")
            print(f"BASE_PATH: {BASE_PATH}")
            DecFile = input("Decoded ProjectFile Name(./):")
            key = cryptlib.get_key(KeyPassword.encode())
            cryptlib.set_key(key)
            cryptlib.setDecFilePath(Path(BASE_PATH) / DecFile, True)
            cryptlib.setEncFilePath(Path(BASE_PATH) / f"enc{DecFile}", True)
            cryptlib.setConfigFilePath(Path(BASE_PATH) / "Config.xml", True)
            cryptlib.encodeXML(False)

        elif option in (2, 3):
            print(f"BASE_PATH: {BASE_PATH}")
            EncFile = input("Encoded ProjectFile Name(./):")
            cryptlib.setDecFilePath(Path(BASE_PATH) / EncFile, True)
            cryptlib.setEncFilePath(Path(BASE_PATH) / EncFile, True)
            cryptlib.setConfigFilePath(Path(BASE_PATH) / "Config.xml", True)
            createFile = option == 2
            Config = cryptlib.decodeXML(createFile, False)
            print("Decoded Config:", Config)
            if "Token" in Config:
                key_valid = cryptlib.isValidKey(Config["Token"])
                print(f"TokenValid: {key_valid}")
                print(f"Config.ExpireDate: {cryptlib.getExpireDate(Config['Token'])}")
            print("OpenConfig:")
            print(cryptlib.getOpenConfig())

        elif option == 4:
            date_str = input("Date (YYYY-MM-DD):")
            parts = [int(p) for p in date_str.split("-")]
            print(f"TokenDate: {cryptlib.getTokenDate(datetime.date(*parts))}")

        elif option == 5:
            tk = input("Token to validate:")
            print(f"ExpireDate: {cryptlib.getExpireDate(tk)}")

        elif option == 6:
            dbconn = input("DB Conn string:")
            testdb = db.DbSQL(dbconn)
            sql = "SELECT getdate() as date"
            print(testdb.getrow(sql))

        elif option == 7:
            dbconn = input("DB Conn string:")
            testdb = db.DbOra(dbconn)
            sql = "SELECT sysdate as now from dual"
            print(testdb.getrow(sql))

        elif option == 8:
            to = input("To email:")
            util.mail_test("Subject", to)

        elif option == 9:
            port = int(cryptlib.getOpenConfig().get("WatchdogPort", 65001))
            watchdog.start_watchdog(BASE_FILE.encode(), port)

    logger.purger()


if __name__ == "__main__":
    interactive_test_menu()
