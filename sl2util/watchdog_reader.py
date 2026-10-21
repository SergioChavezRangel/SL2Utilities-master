"""
Watchdog Reader
Polls registered Level 2 automation services over TCP and records their health
status in the database. Can also be used as a container probe/healthchecker.
"""
import socket

from sl2util import logger

_dbconn: str = ""
data: dict[str, str | None] = dict()


def call_service(address: str, port: int, timeout: float = 3.0) -> str | None:
    """
    Connect to a service over TCP and receive heartbeat status (e.g. 'RUN').
    Uses a configurable socket timeout to prevent hanging.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((address, int(port)))
            result = s.recv(1024).decode("utf-8", errors="replace").strip()
            return result if result else None
    except Exception:
        return None


def get_services() -> dict[str, str | None]:
    """
    Query active services from database, probe each via TCP, and update status.
    """
    global data, _dbconn
    data.clear()

    if not _dbconn:
        return data

    try:
        import sl2util.dbhandler as db
        watchdogdb = db.DbSQL(_dbconn)
        sql = "SELECT * FROM SL2_SERVICES_CONFIG WHERE USED > 0"
        rows = watchdogdb.getrows(sql)

        for row in rows:
            svc_name = row.get("SERVICE_NAME", "")
            address = row.get("ADDRESS", "127.0.0.1")
            port = int(row.get("PORT", 65001))

            res = call_service(address, port)
            data[svc_name] = "RUN" if res is not None else None
            status = 1 if res is not None else 0
            update(status, svc_name)
    except Exception as e:
        logger.writeLog(f"watchdog_reader.get_services error: {e}")

    return data


def register(watchdogdb: str) -> None:
    """Initialize watchdog database connection and perform an immediate poll."""
    global _dbconn
    _dbconn = watchdogdb
    get_services()


def update(status: int, service_name: str) -> None:
    """Update service health status in the database."""
    global _dbconn
    if not _dbconn:
        return

    try:
        import sl2util.dbhandler as db
        watchdogdb = db.DbSQL(_dbconn)
        sql = "UPDATE SL2_SERVICES_CONFIG SET STATUS = ?, TIME_STAMP = getdate() WHERE SERVICE_NAME = ?"
        try:
            watchdogdb.setrow(sql, (int(status), service_name))
        except Exception:
            fallback_sql = (
                f"UPDATE SL2_SERVICES_CONFIG SET STATUS = {int(status)}, TIME_STAMP = getdate() "
                f"WHERE SERVICE_NAME = '{service_name}'"
            )
            watchdogdb.setrow(fallback_sql)
    except Exception as e:
        logger.writeLog(f"watchdog_reader.update error: {e}")
