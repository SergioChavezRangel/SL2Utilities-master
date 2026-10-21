"""
Automation Utility Helpers
Provides steelmaking text decorators, cross-platform file and zip management,
email notifications (SMTP with Windows Outlook fallback), and FTP upload utilities.
"""
import datetime
import fnmatch
import os
import shutil
import smtplib
import subprocess
import sys
import time
import zipfile
from datetime import timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from sl2util import logger

# Attempt pywin32 import only on Windows platforms
_WIN32_AVAILABLE = False
if sys.platform == "win32":
    try:
        import win32com.client as win32
        _WIN32_AVAILABLE = True
    except ImportError:
        _WIN32_AVAILABLE = False


def html_mailer(
    subject: str,
    body: str,
    to_address: str | None = None,
    cc_address: str | None = None,
    station: str = "",
    file: str | None = None,
    path: str | None = None,
) -> bool:
    """
    Send an HTML email with optional attachments.
    Prefers standard SMTP (via env vars SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM)
    and falls back to Windows Outlook COM if running on Windows with pywin32 installed.
    """
    to_address = to_address or ""
    cc_address = cc_address or ""
    file = str(file) if file is not None else ""
    path = str(path) if path is not None else ""

    logger.writeLog("                    Mail Message.")
    logger.writeLog(f"                             To: {to_address}")
    logger.writeLog(f"                             CC: {cc_address}")
    logger.writeLog(f"                        Subject: {subject}")

    # Build HTML body from signature template if present
    html_body = body
    sig_file = Path("MailSignature.html")
    if sig_file.exists():
        try:
            with open(sig_file, encoding="utf-8") as f:
                sig_content = f.read()
                html_body = sig_content.replace("%Station", station).replace("%Body", body)
        except Exception as e:
            logger.writeLog(f"html_mailer: could not read MailSignature.html: {e}")

    # Resolve attachments
    attachments: list[Path] = []
    if path and file and Path(path).exists():
        dir_path = Path(path)
        logger.writeLog(f"                        Looking at Dir - '{path}'")
        logger.writeLog(f"                              for File - '{file}'")
        if file.startswith("**"):
            attachments = [p for p in dir_path.iterdir() if p.is_file()]
        elif "*" in file:
            attachments = [p for p in dir_path.iterdir() if p.is_file() and fnmatch.fnmatch(p.name, file)]
        else:
            single = dir_path / file
            if single.exists() and single.is_file():
                attachments = [single]

        for att in attachments:
            logger.writeLog(f"                 Preparing File: {att}")

    # Strategy 1: Standard SMTP (ideal for Docker, Linux, macOS, and modern servers)
    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        try:
            smtp_port = int(os.environ.get("SMTP_PORT", 25))
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASSWORD", "")
            smtp_from = os.environ.get("SMTP_FROM", smtp_user or "sl2util@automation.local")

            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = to_address
            if cc_address:
                msg["Cc"] = cc_address

            msg.attach(MIMEText(html_body, "html", "utf-8"))

            for att in attachments:
                with open(att, "rb") as af:
                    part = MIMEApplication(af.read(), Name=att.name)
                    part["Content-Disposition"] = f'attachment; filename="{att.name}"'
                    msg.attach(part)

            recipients = [addr.strip() for addr in to_address.split(";") if addr.strip()]
            if cc_address:
                recipients += [addr.strip() for addr in cc_address.split(";") if addr.strip()]

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                if os.environ.get("SMTP_TLS", "").lower() in ("1", "true", "yes"):
                    server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, recipients, msg.as_string())

            logger.writeLog("            Mail Sent via SMTP!")
            return True
        except Exception as e:
            logger.writeLog(f"            ---html_mailer (SMTP)--- Error: {e}")

    # Strategy 2: Windows Outlook COM Automation (fallback if on Windows)
    if _WIN32_AVAILABLE:
        try:
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            if to_address:
                mail.To = to_address
            if cc_address:
                mail.CC = cc_address
            mail.Subject = subject
            mail.HTMLBody = html_body

            for att in attachments:
                mail.Attachments.Add(str(att.resolve()))

            mail.Send()
            logger.writeLog("            Mail Sent via Outlook COM!")
            return True
        except Exception as e:
            logger.writeLog(f"            ---html_mailer (Outlook)--- Error: {e}")
            return False

    logger.writeLog("            ---html_mailer--- Neither SMTP nor Windows Outlook available. Mail logged.")
    return False


def mail_test(subject: str, to: str) -> bool:
    """Send a simple test email."""
    return html_mailer(subject=subject, body="<h2>HTML Message body</h2>", to_address=to)


def text_decorator(
    text: str,
    date: datetime.date,
    shift: int | str,
    heat: Any,
    tmt: Any,
    sequence: Any,
    in_seq: Any,
) -> str:
    """
    Format steelmaking heat and production tracking tokens in a template string.
    Supported placeholders:
      %day, %ddd, %dd, %mmm, %month, %mm, %yyyy
      %dws, %dwe, %mws, %mwe, %yws, %ywe (Week start/end dates)
      %WW, %UU (Week of year)
      %Heat, %Tmt, %InSeq, %Seq, %Shift, %hift
    """
    day_of_week = int(date.strftime("%w"))
    if day_of_week < 1:
        delta_fwd = 1
        delta_bak = 6
    else:
        delta_fwd = 8 - day_of_week
        delta_bak = day_of_week - 1

    week_num = int(date.strftime("%U"))
    week_of_year = f"{week_num:02d}"

    start_of_week = date - timedelta(days=delta_bak)
    end_of_week = date + timedelta(days=delta_fwd)

    # Steelmaking Shift mapping: 21->A, 22->B, 23->C
    shift_code = str(shift)
    if shift_code in ("21", "A", "a"):
        shift_str = "A"
    elif shift_code in ("22", "B", "b"):
        shift_str = "B"
    elif shift_code in ("23", "C", "c"):
        shift_str = "C"
    else:
        shift_str = shift_code

    heat_str = str(heat)
    tmt_str = str(tmt)
    sequence_str = str(sequence)

    if in_seq is not None:
        try:
            in_seq_str = f"{int(in_seq):02d}"
        except (ValueError, TypeError):
            in_seq_str = str(in_seq)
    else:
        in_seq_str = "00"

    replacements = {
        "%day": date.strftime("%A"),
        "%ddd": date.strftime("%a"),
        "%dd": date.strftime("%d"),
        "%mmm": date.strftime("%b"),
        "%month": date.strftime("%B"),
        "%mm": date.strftime("%m"),
        "%yyyy": date.strftime("%Y"),
        "%dws": start_of_week.strftime("%d"),
        "%dwe": end_of_week.strftime("%d"),
        "%mws": start_of_week.strftime("%m"),
        "%mwe": end_of_week.strftime("%m"),
        "%yws": start_of_week.strftime("%Y"),
        "%ywe": end_of_week.strftime("%Y"),
        "%WW": week_of_year,
        "%UU": week_of_year,
        "%Heat": heat_str,
        "%Tmt": tmt_str,
        "%InSeq": in_seq_str,
        "%Seq": sequence_str,
        "%Shift": shift_str,
        "%hift": shift_str,
    }

    result = text
    for token, val in replacements.items():
        result = result.replace(token, val)

    return result


def zipper(file: str | Path, path: str | Path, zippath: str | Path) -> bool:
    """
    Archive a file into a zip archive using Python's standard zipfile library.
    Cross-platform replacement for legacy 7z execution.
    """
    try:
        file_name = str(file)
        stem = Path(file_name).stem
        zipfile_name = f"{stem}.zip"
        return zipper2(file_name, path, zipfile_name, zippath)
    except Exception as e:
        logger.writeLog(f"            ---zipper--- Unexpected error: {e}")
        return False


def zipper2(
    file: str | Path,
    path: str | Path,
    zipfile_name: str | Path,
    zippath: str | Path,
) -> bool:
    """
    Compress a file into a zip archive placed at zippath.
    Pure-Python implementation working seamlessly across Linux, macOS, Windows, and Docker.
    """
    try:
        src = Path(path) / file
        dest_dir = Path(zippath)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_zip = dest_dir / zipfile_name

        if not src.exists():
            logger.writeLog(f"zipper2: source file does not exist: {src}")
            return False

        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(src, arcname=Path(file).name)

        return True
    except Exception as e:
        logger.writeLog(f"            ---zipper2--- Unexpected error: {e}")
        return False


def xls_to_pdf_publisher(
    xls_file: str | Path,
    pdf_file: str | Path,
    sent_to_print: int,
    script_path: str,
    pause: float,
) -> int:
    """
    Convert an Excel file to PDF and optionally print.
    Windows-specific functionality with safe fallback on non-Windows hosts.
    """
    xls_path = Path(xls_file)
    if not xls_path.exists():
        logger.writeLog(f"File Not found: {xls_file}")
        return 4

    logger.writeLog(f"File found: {xls_file}")
    logger.writeLog(f"Try to save to: {pdf_file}")

    if sys.platform != "win32":
        logger.writeLog("xls_to_pdf_publisher: printing/COM is only supported on Windows host.")
        return 1

    try:
        subprocess.call(f'cmd /c "{script_path}" "{xls_file}"', shell=True)
        if sent_to_print == 1:
            if hasattr(os, "startfile"):
                os.startfile(str(pdf_file), "print")
            logger.writeLog("                       Waiting to Printer....")
            time.sleep(pause)
            subprocess.run("taskkill /im AcroRd32.exe /f", shell=True, capture_output=True)
        return 1
    except Exception as e:
        logger.writeLog(f"            ---xls_to_pdf_publisher--- Unexpected error: {e}")
        return 4


def run_win_cmd(cmd: str) -> bool:
    """Execute a system shell command safely using subprocess."""
    try:
        proc = subprocess.run(str(cmd), shell=True, capture_output=True, text=True)
        return proc.returncode == 0
    except Exception as e:
        logger.writeLog(f"            ---run_win_cmd--- Unexpected error: {e}")
        return False


def delete_file(file: str | Path, path: str | Path) -> bool:
    """Delete a file from the specified path."""
    try:
        target = Path(path) / file
        if target.exists():
            target.unlink()
            logger.writeLog(f"               Deleting.... {target}")
        return True
    except Exception as e:
        logger.writeLog(f"            ---deleteFile--- Unexpected error: {e}")
        return False


def files_exists(file: str, path: str | Path) -> bool:
    """Check if file or files matching a glob pattern exist in directory."""
    target_dir = Path(path)
    if not target_dir.exists():
        return False

    if "*" in file:
        return any(fnmatch.fnmatch(p.name, file) for p in target_dir.iterdir() if p.is_file())
    return (target_dir / file).exists()


def path_exists(path: str | Path) -> bool:
    """Check if path exists."""
    return Path(path).exists()


def clean_dir(path: str | Path) -> bool:
    """Delete all files within a directory."""
    try:
        target_dir = Path(path)
        if target_dir.exists():
            for p in target_dir.iterdir():
                if p.is_file():
                    p.unlink()
        return True
    except Exception as e:
        logger.writeLog(f"            ---clean_dir--- Unexpected error: {e}")
        return False


def copy_file(file: str | Path, from_path: str | Path, to_path: str | Path) -> bool:
    """Copy a file from one directory to another."""
    try:
        src = Path(from_path) / file
        dest = Path(to_path)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return True
    except Exception as e:
        logger.writeLog(f"            ---copy_file--- Unexpected error: {e}")
        return False


def clean_old_files(file: str, path: str | Path, old_days: float) -> bool:
    """Delete files matching pattern in path that are older than old_days."""
    target_dir = Path(path)
    if not target_dir.exists():
        return True

    keep_seconds = float(old_days) * 86400.0
    now = time.time()
    logger.writeLog(f"        Delete files older than {old_days:3.0f} days")

    for p in target_dir.iterdir():
        if not p.is_file():
            continue
        if fnmatch.fnmatch(p.name, file):
            age_seconds = now - p.stat().st_mtime
            if age_seconds > keep_seconds:
                try:
                    p.unlink()
                    logger.writeLog(f"               Deleting old file.... {p}")
                except Exception as e:
                    logger.writeLog(f"clean_old_files: could not delete {p}: {e}")
    return True


def map_network_drive(
    drive: str,
    host: str,
    path: str,
    user: str | None = None,
    password: str | None = None,
) -> bool:
    """
    Map a network share to a drive letter on Windows, or verify network path.
    """
    if sys.platform != "win32":
        network_path = f"//{host}/{path.lstrip('/')}"
        return Path(network_path).exists()

    network_path = f"\\\\{host}{path}"
    if user and password:
        cmd = f'net use {drive} {network_path} /USER:{user} {password} /PERSISTENT:NO'
    else:
        cmd = f'net use {drive} {network_path} /PERSISTENT:NO'

    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return proc.returncode == 0
    except Exception:
        return False


def file_append(line: str, path: str | Path, file: str | Path) -> None:
    """Append a line to a file."""
    target = Path(path) / file
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def file_empty(path: str | Path, file: str | Path) -> None:
    """Truncate or create an empty file."""
    target = Path(path) / file
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write("")


def ftp_upload_file(
    path: str | Path,
    file: str | Path,
    ftp_server: str,
    ftp_user: str,
    ftp_password: str,
    ftp_root: str,
) -> bool:
    """Upload a local file to an FTP server."""
    from ftplib import FTP

    local_file = Path(path) / file
    if not local_file.exists():
        logger.writeLog(f"FTP Error: local file not found: {local_file}")
        return False

    try:
        with FTP(ftp_server) as ftp:
            ftp.login(user=ftp_user, passwd=ftp_password)
            ftp.cwd(ftp_root)
            with open(local_file, "rb") as fp:
                ftp.storbinary(f"STOR {local_file.name}", fp, 1024)
            logger.writeLog(f" FTP File Uploaded: {file}@{ftp_server}{ftp_root}")
            return True
    except Exception as e:
        logger.writeLog(f" FTP Error Uploading file: {file}@{ftp_server}{ftp_root} ({e})")
        return False
