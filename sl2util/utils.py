import fnmatch
import os
import sys
from datetime import timedelta
import win32com.client as win32
import sl2util.logger as logger


def html_mailer(subject, body, to_address, cc_address, station, file, path):
    try:
        logger.writeLog('html_mailer')
        oOutlook = win32.Dispatch("outlook.Application")
        Msg = oOutlook.CreateItem(0)
        if len(to_address) > 3:
            Msg.To = to_address
        if len(cc_address) > 3:
            Msg.CC = cc_address
        logger.writeLog('{};{};{};{};{};{};{}'.format(subject, body, to_address, cc_address, station, file, path))
        if len(file) > 0 and len(path) > 0:
            logger.writeLog("                        Looking at Dir - '" + path + "'. PID ")
            logger.writeLog("                              for File - '" + file + "'. PID ")
            if file.find("*") > 0:
                if os.path.exists(path):
                    for fileName in os.listdir(path):
                        if fnmatch.fnmatch(fileName, file):
                            attachment = path + fileName
                            logger.writeLog("                 Preparing File: " + attachment + ". PID ")
                            Msg.Attachments.Add(attachment)
            else:
                if os.path.exists(path + file):
                    attachment = path + file
                    logger.writeLog("                 Preparing File: " + attachment + ". PID ")
                    Msg.Attachments.Add(attachment)
        logger.writeLog("                    Mail Message. PID ")
        logger.writeLog("                             To: " + to_address)
        logger.writeLog("                             CC: " + cc_address)
        logger.writeLog("                        Subject: " + subject)
        HTMLBody = ""
        f = open('MailSignature.html', "r")
        if f.mode == 'r':
            HTMLBody = f.read()
        HTMLBody = HTMLBody.replace("%Station", station)
        HTMLBody = HTMLBody.replace("%Body", body)
        print(HTMLBody)
        Msg.HTMLBody = HTMLBody
        Msg.Subject = subject
        Msg.Send()
        logger.writeLog("            Mail Done!. PID ")
        return True
    except:
        logger.writeLog("            ---mailer--- Unexpected error: " + str(sys.exc_info()[0]))
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
    if in_seq is None:
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
    return text


def mail_test():
    import win32com.client as win32
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail.To = 'schavezr@gan.com.mx'
    mail.Subject = 'Message subject'
    # mail.Body = 'Message body'
    mail.HTMLBody = '<h2>HTML Message body</h2>'  # this field is optional

    # To attach a file to the email (optional):
    # attachment  = "Path to the attachment"
    # mail.Attachments.Add(attachment)

    mail.Send()
