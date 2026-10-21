"""
SL2Utilities (sl2util)
Steelmaking Automation Level 2 Utilities - Modernized Cross-Platform Suite.

Modules:
- configdatareader: Fernet symmetric encryption and decryption for configuration.
- logger: Rolling file logger and purger with standard logging compatibility.
- dbhandler: Database access layer for Oracle (via python-oracledb) and SQL Server.
- l1handler: Level 1 PLC communication via OPC-UA.
- watchdog: Service monitoring daemon & heartbeat server.
- watchdog_reader: Service monitoring client.
- utils: Steelmaking text formatting, email notifications, archiving, and file utils.
- loader: Application bootstrapper and configuration loader.
"""

__version__ = "2.0.0"
__author__ = "Sergio Chavez Rangel"
__license__ = "MIT"
