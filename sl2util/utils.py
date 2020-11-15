import fnmatch
import os
import shutil
import subprocess
import sys
from datetime import timedelta
import time as time
from ftplib import FTP

import sl2util.loader as loader
import win32com.client as win32


def html_mailer(subject, body, to_address, cc_address, station, file, path):
    file = str(file)
    path = str(path)
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        if to_address is not None:
            mail.To = to_address
        else:
            to_address = ''
        if cc_address is not None:
            mail.CC = cc_address
        else:
            cc_address = ''
        if file is not None and path is not None:
            loader.logger.writeLog("                        Looking at Dir - '" + path)
            loader.logger.writeLog("                              for File - '" + file)
            if file.find("**") == 0:
                if os.path.exists(path):
                    for fileName in os.listdir(path):
                        attachment = path + fileName
                        loader.logger.writeLog("                 Preparing File: " + attachment)
                        mail.Attachments.Add(attachment)
            elif file.find("*") > 0:
                if os.path.exists(path):
                    for fileName in os.listdir(path):
                        if fnmatch.fnmatch(fileName, file):
                            attachment = path + fileName
                            loader.logger.writeLog("                 Preparing File: " + attachment)
                            mail.Attachments.Add(attachment)
            else:
                if os.path.exists(path + file):
                    attachment = path + file
                    loader.logger.writeLog("                 Preparing File: " + attachment + ". PID ")
                    mail.Attachments.Add(attachment)
        loader.logger.writeLog("                    Mail Message.")
        loader.logger.writeLog("                             To: " + to_address)
        loader.logger.writeLog("                             CC: " + cc_address)
        loader.logger.writeLog("                        Subject: " + subject)
        HTMLBody = ""
        f = open('MailSignature.html', "r")
        if f.mode == 'r':
            HTMLBody = f.read()
        HTMLBody = HTMLBody.replace("%Station", station)
        HTMLBody = HTMLBody.replace("%Body", body)
        # print(HTMLBody)
        mail.HTMLBody = HTMLBody
        mail.Subject = subject
        if loader.KEY or loader.NOT_KEY():
            mail.Send()
        loader.logger.writeLog("            Mail Done!. PID ")
        return True
    except:
        loader.logger.writeLog("            ---html_mailer--- Unexpected error: " + str(sys.exc_info()[0]))
        return False


def text_decorator(text, date, shift, heat, tmt, sequence, in_seq):
    DayOfWeek = int(date.strftime("%w"))
    DeltaDaysFwd = 0
    DeltaDaysBak = 7
    if DayOfWeek < 1:
        DeltaDaysFwd = 1
        DeltaDaysBak = 6
    if DayOfWeek > 1:
        DeltaDaysFwd = 8 - DayOfWeek
        DeltaDaysBak = DayOfWeek - 1
    iWeekOfYear = int(date.strftime("%U"))
    WeekOfYear = "00"
    if iWeekOfYear < 10:
        WeekOfYear = "0" + str(iWeekOfYear)
    else:
        WeekOfYear = str(iWeekOfYear)
    EndOfWeek = date + timedelta(days=DeltaDaysFwd)
    StartOfWeek = date - timedelta(days=DeltaDaysBak)
    DayWeekStart = StartOfWeek.strftime("%d")
    MonthWeekStart = StartOfWeek.strftime("%m")
    YearWeekStart = StartOfWeek.strftime("%Y")
    DayWeekEnd = EndOfWeek.strftime("%d")
    MonthWeekEnd = EndOfWeek.strftime("%m")
    YearWeekEnd = EndOfWeek.strftime("%Y")

    Shift = "A"
    if shift == 21:
        Shift = "A"
    if shift == 22:
        Shift = "B"
    if shift == 23:
        Shift = "C"
    heat = str(heat)
    tmt = str(tmt)
    if in_seq is not None:
        if int(str(in_seq)) < 10:
            in_seq = "0" + str(in_seq)
        else:
            in_seq = str(in_seq)
    else:
        in_seq = "00"
    sequence = str(sequence)
    WeekOfYear = str(WeekOfYear)
    dd = date.strftime("%d")
    mm = date.strftime("%m")
    yyyy = date.strftime("%Y")
    text = text.replace("%day", date.strftime("%A"))
    text = text.replace("%ddd", date.strftime("%a"))
    text = text.replace("%dd", dd)
    text = text.replace("%mmm", date.strftime("%b"))
    text = text.replace("%month", date.strftime("%B"))
    text = text.replace("%mm", mm)
    text = text.replace("%yyyy", yyyy)
    text = text.replace("%dws", DayWeekStart)
    text = text.replace("%dwe", DayWeekEnd)
    text = text.replace("%mws", MonthWeekStart)
    text = text.replace("%mwe", MonthWeekEnd)
    text = text.replace("%yws", YearWeekStart)
    text = text.replace("%ywe", YearWeekEnd)
    text = text.replace("%WW", WeekOfYear)
    text = text.replace("%UU", WeekOfYear)
    text = text.replace("%Heat", heat)
    text = text.replace("%Tmt", tmt)
    text = text.replace("%InSeq", in_seq)
    text = text.replace("%Seq", sequence)
    text = text.replace("%Shift", Shift)
    text = text.replace("%hift", Shift)
    return text


def mail_test(subject, to):
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    if len(to) > 5:
        mail.To = to
    mail.Subject = subject
    mail.HTMLBody = '<h2>HTML Message body</h2>'
    mail.Send()


def zipper(file, path, zippath):
    path = str(path)
    file = str(file)
    zippath = str(zippath)
    try:
        zipfile = file[:-(len(file) - file.rfind("."))] + '.zip'
        # print(path, file, zippath, zipfile)
        return zipper2(file, path, zipfile, zippath)
    except:
        loader.logger.writeLog("            ---zipper--- Unexpected error: " + str(sys.exc_info()[0]))
        return False


def zipper2(file, path, zipfile, zippath):
    try:
        import shutil
        shutil.copy2(path + file, zippath)
        cmd = '7z a "' + str(zippath + zipfile) + '" "' + str(path + file) + '"'
        # print(cmd)
        run_win_cmd(cmd)
        return True
    except:
        loader.logger.writeLog("            ---zipper2--- Unexpected error: " + str(sys.exc_info()[0]))
        return False


def xls_to_pdf_publisher(xls_file, pdf_file, sent_to_print, script_path, pause):
    result = 4
    if os.path.exists(xls_file):
        loader.logger.writeLog('File found: ' + str(xls_file))
        loader.logger.writeLog('Try to save to: ' + str(pdf_file))
        try:
            if loader.KEY or loader.NOT_KEY():
                subprocess.call("cmd /c " + script_path + " " + xls_file)
            result = 1
            if sent_to_print == 1:
                pdf_file = pdf_file.replace("/", "\\")
                if loader.KEY or loader.NOT_KEY():
                    os.startfile(pdf_file, 'print')
                result = 1
                loader.logger.writeLog("                       Waiting to Printer....")
                time.sleep(pause)
                os.system("taskkill /im AcroRd32.exe /f")
            return result
        except:
            loader.logger.writeLog("            ---xls_to_pdf_publisher--- Unexpected error: " + str(sys.exc_info()[0]))
    else:
        loader.logger.writeLog('File Not found: ' + str(xls_file))
        result = 4
    # updater(idx, 4, "Waiting for ExcelFile")
    return result


def run_win_cmd(cmd):
    cmd = str(cmd)
    try:
        result = []
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in process.stdout:
            result.append(str(line))
        errcode = process.returncode
        # for line in result:
        #    logger.writeLog(line)
        if errcode is not None:
            raise Exception('cmd %s failed, see above for details', cmd)
        return True
    except:
        loader.logger.writeLog("            ---run_win_cmd--- Unexpected error: " + str(sys.exc_info()[0]))
        return False


def delete_file(file, path):
    path = str(path)
    file = str(file)
    try:
        os.remove(path + file)
        loader.logger.writeLog('               Deleting.... ' + path + file)
        return True
    except:
        loader.logger.writeLog("            ---deleteFile--- Unexpected error: " + str(sys.exc_info()[0]))
        return False


def files_exists(file, path):
    path = str(path)
    file = str(file)
    if os.path.exists(path):
        if file.find("*") > 0:
            for fileName in os.listdir(path):
                if fnmatch.fnmatch(fileName, file):
                    return True
        else:
            return os.path.exists(path + file)
    return False


def path_exists(path):
    return os.path.exists(path)


def clean_dir(path):
    try:
        for fileName in os.listdir(path):
            os.remove(path + fileName)
        return True
    except:
        loader.logger.writeLog("            ---clean_dir--- Unexpected error: " + str(sys.exc_info()[0]))
        return False


def copy_file(file, from_path, to_path):
    try:
        shutil.copy2(from_path + file, to_path)
        return True
    except:
        loader.logger.writeLog("            ---copy_file--- Unexpected error: " + str(sys.exc_info()[0]))
        return False


def clean_old_files(file, path, old_days):
    # old_days = 30.0 '*.pdf'
    fKeepSeconds = old_days * 86400
    loader.logger.writeLog("        Delete files older than %3.0f days" % old_days)
    # sPath = path # 'C:/ReportTracker/BitacoraReportes/Server/Reports/'
    for fileName in os.listdir(path):
        fileStats = os.stat(path + fileName)
        lSize = fileStats.st_size
        tCreationTime = time.ctime(fileStats.st_mtime)
        tCreated = time.strptime(tCreationTime, "%a %b %d %H:%M:%S %Y")
        sNow = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
        tNow = time.strptime(sNow, "%a %b %d %H:%M:%S %Y")
        fOld = time.mktime(tNow) - time.mktime(tCreated)
        if fnmatch.fnmatch(fileName, file) and fOld > fKeepSeconds:
            print('   File: ' + fileName)
            print('   Size: ' + str(lSize) + " bytes")
            print('Created: ' + tCreationTime)  # string Thu Sep 27 16:19:41 2012  %a %b %d %H:%M:%S %Y
            print('   Life: %5.2f days old' % (fOld / 86400))
            return delete_file(fileName, path)
    return True


def map_network_drive(drive, host, path, user=None, password=None):
    networkPath = "\\\\" + host + path
    cmd_path = "net use " + drive + " " + networkPath + " /PERSISTENT:NO"
    if user is not None and password is not None:
        cmd_path = "net use " + drive + " " + networkPath + "/USER:" + user + " " + password + " /PERSISTENT:NO"
    result = False
    response = os.system("ping -n 1 " + host)
    if response == 0:
        print(host + ' is up!')
    else:
        print(host + ' is down!')
    if path_exists(drive + '\\'):
        print(drive + " Drive in use...")
        result = True
    else:
        print(drive + "\\ is Offline, Try to mapnetwork...")
        if path_exists(networkPath):
            print(networkPath + " is found...")
            print("Trying to map " + networkPath + " on to " + drive + " .....")
            try:
                os.system(cmd_path)
                result = True
            except:
                print("Unexpected error when mapping Drive...")
        else:
            print(networkPath + " not found...")
            print("Trying to map anyway " + networkPath + " on to " + drive + " .....")
            try:
                os.system(cmd_path)
                result = True
            except:
                print("Unexpected error when mapping Drive anyway...")
    return result


def file_append(line, path, file):
    f = open(path + file, 'a')
    f.write(line)
    print(' ' + line)
    f.write("\n")
    f.close()


def file_empty(path, file):
    f = open(path + file, 'w')
    f.write("")
    print(' Clear file ' + file)
    f.close()


def ftp_upload_file(path, file, ftp_server, ftp_user, ftp_password, ftp_root):
    try:
        ftp = FTP(ftp_server)
        ftp.login(user=ftp_user, passwd=ftp_password, acct='')
        ftp.cwd(ftp_root)
        local_file = path + file
        fp = open(local_file, 'rb')
        ftp.storbinary('STOR %s' % os.path.basename(local_file), fp, 1024)
        print(' Uploading file ' + file)
        fp.close()
        print(' FTP File Uploaded: ' + file + '@' + ftp_server + ftp_root)
    except:
        loader.logger.writeLog(' FTP Error Uploading file, cant connect: ' + file + '@' + ftp_server + ftp_root)
