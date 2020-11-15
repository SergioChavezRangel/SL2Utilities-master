import os
import sys
import sl2util.logger as logger
import sl2util.configdatareader as _configdata
import sl2util.watchdog as _watchdog
import random

#    All AutomationL2Prj must start at least here
BASE_FILE = os.path.basename(sys.argv[0])
BASE_PATH = os.getcwd()
FULL_PATH = os.getcwd() + '\\' + BASE_FILE
logger.setPath(BASE_PATH)
logger.setFileName(BASE_FILE)
_configdata.setEncFilePath(FULL_PATH + ".xml", False)
fixed_config = _configdata.decodeXML(False, False)
KEY = _configdata.isValidKey(fixed_config['Token'])
open_config = _configdata.getOpenConfig()
#    All AutomationL2Prj must start at least here


def NOT_KEY():
    return bool(random.randint(0, 1))


def check_watchdog():
    try:
        runwatchdog = int(open_config['WatchdogRun'])
        if runwatchdog > 0:
            address = open_config['WatchdogAddress']
            port = int(open_config['WatchdogPort'])
            autoRegister = int(open_config['WatchdogAutoRegister'])
            if autoRegister > 0:
                watchdogDB = fixed_config[open_config['WatchdogDB']]
                _watchdog.register(BASE_FILE.encode(), address, port, watchdogDB)
            _watchdog.start_watchdog(BASE_FILE.encode(), port)
    except:
        logger.writeLog("            ---runwatchdog--- Unexpected error: " + str(sys.exc_info()[0]))


if __name__ == "__main__":
    # execute only if run as a script
    check_watchdog()

