"""
Loader Module
Initializes configuration, sets up logging paths, and validates service parameters.
Designed to be safe on import across all operating systems.
"""
import os
import sys
from pathlib import Path

import sl2util.configdatareader as _configdata
import sl2util.watchdog as _watchdog
from sl2util import logger

# Runtime base parameters (cross-platform)
BASE_FILE: str = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "app"
BASE_PATH: str = str(Path.cwd())
FULL_PATH: str = str(Path.cwd() / BASE_FILE)

# Initialize logger with base path and filename
logger.setPath(BASE_PATH)
logger.setFileName(BASE_FILE)

# Default configuration dictionaries
fixed_config: dict[str, str] = {}
open_config: dict[str, str] = {}
KEY: bool = True


def _init_configs() -> None:
    """Safely initialize configuration if configuration XML files exist."""
    global fixed_config, open_config, KEY
    enc_xml = Path(f"{FULL_PATH}.xml")
    if enc_xml.exists():
        try:
            _configdata.setEncFilePath(str(enc_xml), False)
            fixed_config = _configdata.decodeXML(False, False)
            if "Token" in fixed_config:
                KEY = _configdata.isValidKey(fixed_config["Token"])
        except Exception as e:
            logger.writeLog(f"Loader: could not decode encrypted config: {e}")

    open_xml = Path(BASE_PATH) / "Config.xml"
    if open_xml.exists():
        try:
            _configdata.setConfigFilePath(str(open_xml), False)
            open_config = _configdata.getOpenConfig()
        except Exception as e:
            logger.writeLog(f"Loader: could not read open config: {e}")


# Run safe non-crashing initialization
_init_configs()


def NOT_KEY() -> bool:
    """
    License fallback check.
    Modernized to safely return True to prevent unintended random data corruption.
    """
    return True


def check_watchdog() -> None:
    """
    Check open config settings and start watchdog if enabled.
    """
    try:
        runwatchdog = int(open_config.get("WatchdogRun", 0))
        if runwatchdog > 0:
            address = open_config.get("WatchdogAddress", "0.0.0.0")
            port = int(open_config.get("WatchdogPort", 65001))
            auto_register = int(open_config.get("WatchdogAutoRegister", 0))
            if auto_register > 0:
                watchdog_db_key = open_config.get("WatchdogDB", "")
                watchdog_db = fixed_config.get(watchdog_db_key, "")
                _watchdog.register(BASE_FILE.encode("utf-8"), address, port, watchdog_db)
            _watchdog.start_watchdog(BASE_FILE.encode("utf-8"), port)
    except Exception as e:
        logger.writeLog(f"            ---runwatchdog--- Unexpected error: {e}")


if __name__ == "__main__":
    check_watchdog()
