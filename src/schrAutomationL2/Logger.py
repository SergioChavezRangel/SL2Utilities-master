# -*- coding: cp1252 -*-
import os
import win32com.client
import win32net
import datetime
from datetime import timedelta
from time import localtime, strftime #gmtime, strftime
import time
from os import system, name
import fnmatch
import sys
from os import stat


def purger():
    #sPath = os.getcwd()
    global Path
    global File_Name
    global fKeepDays
    global fKeepSize
    
    fKeepSeconds = fKeepDays * 86400 
    writeLog("        Working Directory: " + Path)
    writeLog("        Delete LogFiles older than %3.0f days" % fKeepDays)
    writeLog("        Rename LogFiles bigger than %d Mbytes" % (fKeepSize/1024.0/1024.0))
    for fileName in os.listdir ( Path ):
        sPath = Path + "\\"
        try:
            fileStats = stat (sPath + fileName)
            lSize = fileStats.st_size
            tCreationTime = time.ctime (fileStats.st_mtime)
            tCreated = time.strptime(tCreationTime, "%a %b %d %H:%M:%S %Y")#parse string to time_struc ->
            sNow = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
            tNow = time.strptime(sNow, "%a %b %d %H:%M:%S %Y")
            fOld = time.mktime(tNow) - time.mktime(tCreated)
            ################## RENAME REOPEN FILES BECAUSE OF SIZE #######################
            if (fnmatch.fnmatch (fileName, File_Name + '.txt')):
                #print '   File: ' + fileName
                #print '   Size: ' + str(lSize) + " bytes"
                if (lSize > fKeepSize):
                    writeLog("      ==============================================================================")
                    sNewFile = File_Name + time.strftime(" %b %d %Y %H%M%S", time.localtime()) + '.txt'
                    writeLog( '           File: ' + fileName)
                    writeLog( '           Size: ' + str(lSize/1024.0/1024.0) + " Mbytes")
                    writeLog('                    Closing: ' + fileName + ' -> ' + sNewFile)
                    os.rename(sPath + fileName, sPath + sNewFile)
                    writeLog('                      Opened: ' + fileName)
                    writeLog('                     OldFile: ' + sNewFile + ' -> Size: ' + str(lSize/1024.0/1024.0) + " Mbytes")
                    #print '.'
                    writeLog("      ==============================================================================")
            ################## OLD LOG FILES #######################
            if (fnmatch.fnmatch (fileName, File_Name + ' *.txt')):
                #print '   File: ' + fileName
                #print '   Life: %5.2f days old' % (fOld / 86400)
                if (fOld > fKeepSeconds):
                    writeLog("      ==============================================================================")
                    writeLog( '           File: ' + fileName)
                    writeLog( '           Life: %5.2f days old' % (fOld / 86400))
                    os.remove(sPath + fileName)
                    writeLog('                    Deleting.... %s' % fileName)
                    #print '..'
                    writeLog("      ==============================================================================")
        except Exception as e:
            writeLog('Error Purger: ' + fileName)
            writeLog('Exception:    ' + str(e))

def purgeFiles(iDays, sPath, sFile):
    #sPath = os.getcwd()
    
    fKeepSeconds = iDays * 86400 
    writeLog("        Working Directory: " + sPath)
    writeLog("        Delete Files '%s' older than %3.0f days" % (sFile, iDays))
    for fileName in os.listdir ( sPath ):
        sPath = sPath + "\\"
        try:
            fileStats = stat (sPath + fileName)
            lSize = fileStats.st_size
            tCreationTime = time.ctime (fileStats.st_mtime)
            tCreated = time.strptime(tCreationTime, "%a %b %d %H:%M:%S %Y")#parse string to time_struc ->
            sNow = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
            tNow = time.strptime(sNow, "%a %b %d %H:%M:%S %Y")
            fOld = time.mktime(tNow) - time.mktime(tCreated)
            ################## OLD LOG FILES #######################
            if (fnmatch.fnmatch (fileName, sFile)):
                #print '   File: ' + fileName
                #print '   Life: %5.2f days old' % (fOld / 86400)
                if (fOld > fKeepSeconds):
                    writeLog("      ==============================================================================")
                    writeLog( '           File: ' + fileName)
                    writeLog( '           Life: %5.2f days old' % (fOld / 86400))
                    os.remove(sPath + fileName)
                    writeLog('                    Deleting.... %s' % fileName)
                    #print '..'
                    writeLog("      ==============================================================================")
        except Exception as e:
            writeLog('Error PurgeFiles: ' + fileName)
            writeLog('Exception:    ' + str(e))
    
def writeLog(log):
    global Path
    global File_Name
    f = open(Path + "\\" + File_Name + '.txt', 'a')
    #"%a, %d %b %Y %H:%M:%S +0000", gmtime())
    #'Thu, 28 Jun 2001 14:17:15 +0000'
    f.write("\n")
    f.write(strftime("%d/%b/%Y %H:%M:%S %a. ", localtime()))
    #print strftime("%d/%b/%Y %H:%M:%S %a. ", localtime()) + log
    f.write(log)
    f.close()

def setPath(path):
    global Path
    Path = path

def setFileName(file):
    global File_Name
    File_Name = file

def setKeepDays(KeepDays):
    global fKeepDays
    fKeepDays = KeepDays

def setKeepSize(KeepSize):
    global fKeepSize
    fKeepSize = KeepSize
    
Path = os.getcwd()
File_Name =  os.path.basename(sys.argv[0]).replace(".py","")
fKeepDays = 30.0
fKeepSize = 10485760 #10485760 = 10 Mb #bytes
#print Path + "\\" + FileName + '.txt'
#print Path
#print FileName
