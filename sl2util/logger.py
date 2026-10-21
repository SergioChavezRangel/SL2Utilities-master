"""
Modernized Logger & File Purger Utility
Provides rolling file logging and automated file purging with full cross-platform
support (Linux, macOS, Windows, Docker).
"""
import datetime
import fnmatch
import logging
import os
import sys
import time
from pathlib import Path as FilePath

# Default configurations (cross-platform)
_default_app_name = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "app"
File_Name: str = _default_app_name.replace(".py", "").replace(".exe", "")
Path: str = str(FilePath.cwd() / "log")
fKeepDays: float = 30.0
fKeepSize: int = 10485760  # 10 MB in bytes


def setPath(path: str | FilePath) -> None:
    """Set the logging directory path."""
    global Path
    base = FilePath(path)
    # Maintain backwards compatibility: append 'log' if not already pointing to a log directory
    if base.name.lower() == "log":
        Path = str(base)
    else:
        Path = str(base / "log")


def setFileName(file: str) -> None:
    """Set the active base file name for logging."""
    global File_Name
    File_Name = str(file).replace(".py", "").replace(".exe", "")


def setKeepDays(keep_days: float) -> None:
    """Set the retention period in days for old log files."""
    global fKeepDays
    fKeepDays = float(keep_days)


def setKeepSize(keep_size: int) -> None:
    """Set the maximum log file size in bytes before file rotation."""
    global fKeepSize
    fKeepSize = int(keep_size)


def writeLog(log: str) -> None:
    """
    Write a timestamped log entry to the active log file.
    Automatically creates the target directory if it does not exist.
    """
    global Path, File_Name
    try:
        log_dir = FilePath(Path)
        log_dir.mkdir(parents=True, exist_ok=True)
        target_file = log_dir / f"{File_Name}.txt"

        now_local = datetime.datetime.now().astimezone()
        timestamp = now_local.strftime("%d/%b/%Y %H:%M:%S %a. ")

        with open(target_file, "a", encoding="utf-8") as f:
            f.write(f"\n{timestamp}{log}")
    except Exception as e:
        sys.stderr.write(f"[sl2util.logger.writeLog error: {e}]\n")


def purger() -> None:
    """
    Rotate active log file if its size exceeds `fKeepSize`,
    and delete old rotated logs exceeding `fKeepDays`.
    """
    global Path, File_Name, fKeepDays, fKeepSize

    log_dir = FilePath(Path)
    if not log_dir.exists():
        return

    f_keep_seconds = fKeepDays * 86400.0
    now = time.time()

    writeLog(f"        Working Directory: {Path}")
    writeLog(f"        Delete LogFiles older than {fKeepDays:3.0f} days")
    writeLog(f"        Rename LogFiles bigger than {fKeepSize / (1024.0 * 1024.0):.0f} Mbytes")

    for file_path in log_dir.iterdir():
        if not file_path.is_file():
            continue

        file_name = file_path.name
        try:
            file_stats = file_path.stat()
            file_size = file_stats.st_size
            file_age_seconds = now - file_stats.st_mtime

            # 1. Rotate active file if size exceeds threshold
            if fnmatch.fnmatch(file_name, f"{File_Name}.txt"):
                if file_size > fKeepSize:
                    timestamp_suffix = time.strftime(" %b %d %Y %H%M%S", time.localtime())
                    new_file_name = f"{File_Name}{timestamp_suffix}.txt"
                    new_file_path = log_dir / new_file_name

                    writeLog("      ==============================================================================")
                    writeLog(f"           File: {file_name}")
                    writeLog(f"           Size: {file_size / (1024.0 * 1024.0):.2f} Mbytes")
                    writeLog(f"                    Closing: {file_name} -> {new_file_name}")
                    file_path.rename(new_file_path)
                    writeLog(f"                      Opened: {file_name}")
                    writeLog(f"                     OldFile: {new_file_name} -> Size: {file_size / (1024.0 * 1024.0):.2f} Mbytes")
                    writeLog("      ==============================================================================")

            # 2. Delete rotated files older than threshold
            if fnmatch.fnmatch(file_name, f"{File_Name} *.txt"):
                if file_age_seconds > f_keep_seconds:
                    writeLog("      ==============================================================================")
                    writeLog(f"           File: {file_name}")
                    writeLog(f"           Life: {file_age_seconds / 86400.0:5.2f} days old")
                    file_path.unlink()
                    writeLog(f"                    Deleting.... {file_name}")
                    writeLog("      ==============================================================================")
        except Exception as e:
            writeLog(f"Error Purger: {file_name}")
            writeLog(f"Exception:    {e}")


def purgeFiles(days: float, path: str | FilePath, file: str) -> None:
    """
    Purge files in a specific directory matching pattern that are older than `days`.
    """
    target_dir = FilePath(path)
    if not target_dir.exists():
        return

    f_keep_seconds = float(days) * 86400.0
    now = time.time()

    writeLog(f"        Working Directory: {target_dir}")
    writeLog(f"        Delete Files '{file}' older than {days:3.0f} days")

    for file_path in target_dir.iterdir():
        if not file_path.is_file():
            continue

        file_name = file_path.name
        try:
            file_stats = file_path.stat()
            file_age_seconds = now - file_stats.st_mtime
            if fnmatch.fnmatch(file_name, file) and file_age_seconds > f_keep_seconds:
                writeLog("      ==============================================================================")
                writeLog(f"           File: {file_name}")
                writeLog(f"           Life: {file_age_seconds / 86400.0:5.2f} days old")
                file_path.unlink()
                writeLog(f"                    Deleting.... {file_name}")
                writeLog("      ==============================================================================")
        except Exception as e:
            writeLog(f"Error PurgeFiles: {file_name}")
            writeLog(f"Exception:    {e}")


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a standard Python logging.Logger configured to bridge with sl2util.
    """
    logger = logging.getLogger(name or "sl2util")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
