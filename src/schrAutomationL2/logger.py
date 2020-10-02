"""
An alternative to the logging lib

"""

import os
from time import localtime, strftime
import time
import fnmatch
import sys
from os import stat

Path = os.getcwd() + '\\log'
File_Name = os.path.basename(sys.argv[0]).replace(".py", "")
fKeepDays = 30.0
fKeepSize = 10485760


def purger():
    global Path
    global File_Name
    global fKeepDays
    global fKeepSize

    fKeepSeconds = fKeepDays * 86400
    writeLog("        Working Directory: " + Path)
    writeLog("        Delete LogFiles older than %3.0f days" % fKeepDays)
    writeLog("        Rename LogFiles bigger than %d Mbytes" % (fKeepSize / 1024.0 / 1024.0))
    for fileName in os.listdir(Path):
        sPath = Path + "\\"
        try:
            fileStats = stat(sPath + fileName)
            lSize = fileStats.st_size
            tCreationTime = time.ctime(fileStats.st_mtime)
            tCreated = time.strptime(tCreationTime, "%a %b %d %H:%M:%S %Y")
            sNow = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
            tNow = time.strptime(sNow, "%a %b %d %H:%M:%S %Y")
            fOld = time.mktime(tNow) - time.mktime(tCreated)
            ################## RENAME REOPEN FILES BECAUSE OF SIZE #######################
            if fnmatch.fnmatch(fileName, File_Name + '.txt'):
                if lSize > fKeepSize:
                    writeLog("      ==============================================================================")
                    sNewFile = File_Name + time.strftime(" %b %d %Y %H%M%S", time.localtime()) + '.txt'
                    writeLog('           File: ' + fileName)
                    writeLog('           Size: ' + str(lSize / 1024.0 / 1024.0) + " Mbytes")
                    writeLog('                    Closing: ' + fileName + ' -> ' + sNewFile)
                    os.rename(sPath + fileName, sPath + sNewFile)
                    writeLog('                      Opened: ' + fileName)
                    writeLog('                     OldFile: ' + sNewFile + ' -> Size: ' + str(
                        lSize / 1024.0 / 1024.0) + " Mbytes")
                    writeLog("      ==============================================================================")
            ################## OLD LOG FILES #######################
            if fnmatch.fnmatch(fileName, File_Name + ' *.txt'):
                if fOld > fKeepSeconds:
                    writeLog("      ==============================================================================")
                    writeLog('           File: ' + fileName)
                    writeLog('           Life: %5.2f days old' % (fOld / 86400))
                    os.remove(sPath + fileName)
                    writeLog('                    Deleting.... %s' % fileName)
                    writeLog("      ==============================================================================")
        except Exception as e:
            writeLog('Error Purger: ' + fileName)
            writeLog('Exception:    ' + str(e))


def purgeFiles(days, path, file):
    fKeepSeconds = days * 86400
    writeLog("        Working Directory: " + path)
    writeLog("        Delete Files '%s' older than %3.0f days" % (file, days))
    for fileName in os.listdir(path):
        sPath = path + "\\"
        try:
            fileStats = stat(sPath + fileName)
            lSize = fileStats.st_size
            tCreationTime = time.ctime(fileStats.st_mtime)
            tCreated = time.strptime(tCreationTime, "%a %b %d %H:%M:%S %Y")
            sNow = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
            tNow = time.strptime(sNow, "%a %b %d %H:%M:%S %Y")
            fOld = time.mktime(tNow) - time.mktime(tCreated)
            ################## OLD LOG FILES #######################
            if fnmatch.fnmatch(fileName, file):
                if fOld > fKeepSeconds:
                    writeLog("      ==============================================================================")
                    writeLog('           File: ' + fileName)
                    writeLog('           Life: %5.2f days old' % (fOld / 86400))
                    os.remove(sPath + fileName)
                    writeLog('                    Deleting.... %s' % fileName)
                    writeLog("      ==============================================================================")
        except Exception as e:
            writeLog('Error PurgeFiles: ' + fileName)
            writeLog('Exception:    ' + str(e))


def writeLog(log):
    global Path
    global File_Name
    f = open(Path + "\\" + File_Name + '.txt', 'a')
    f.write("\n")
    f.write(strftime("%d/%b/%Y %H:%M:%S %a. ", localtime()))
    f.write(log)
    f.close()


def setPath(path):
    global Path
    Path = path + '\\log'


def setFileName(file):
    global File_Name
    File_Name = file


def setKeepDays(keep_days):
    global fKeepDays
    fKeepDays = keep_days


def setKeepSize(keep_size):
    global fKeepSize
    fKeepSize = keep_size
