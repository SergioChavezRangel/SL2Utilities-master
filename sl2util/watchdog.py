"""
Watchdog Service
Provides a TCP heartbeat listener and service registration for Level 2 automation.
Can run as a standalone daemon in Docker or as a background service.
"""
import argparse
import os
import socket
import threading
import time
from typing import Optional

from sl2util import logger

_server_instance: Optional["WatchdogServer"] = None

# Backward compatibility globals
_port: int = 12345
_service_name: bytes = b"main_watchdog"
_dbconn: str = ""
autoset: bool = False


class WatchdogServer:
    """Manages a TCP heartbeat server responding with RUN to client pings."""

    def __init__(self, service_name: str | bytes, port: int = 12345):
        self.service_name = service_name if isinstance(service_name, bytes) else service_name.encode("utf-8")
        self.port = int(port)
        self.socket: socket.socket | None = None
        self.running = False
        self.thread: threading.Thread | None = None

    def start(self, host: str = "0.0.0.0") -> None:
        """Start the watchdog server listening on the specified port."""
        if self.running:
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, self.port))
        self.socket.listen(5)
        self.socket.settimeout(1.0)
        self.running = True

        self.thread = threading.Thread(target=self._run_loop, daemon=True, name="sl2util-watchdog")
        self.thread.start()
        logger.writeLog(f"Watchdog server started on {host}:{self.port} for {self.service_name.decode('utf-8', errors='replace')}")
        print(f"Watchdog running on {host}:{self.port}...")

    def _run_loop(self) -> None:
        while self.running:
            try:
                client, addr = self.socket.accept()
            except TimeoutError:
                continue
            except Exception:
                if not self.running:
                    break
                continue

            try:
                # Python 3 socket expects bytes
                client.sendall(b"RUN\n")
            except Exception as e:
                logger.writeLog(f"Watchdog client send error: {e}")
            finally:
                try:
                    client.close()
                except Exception:
                    pass

    def stop(self) -> None:
        """Gracefully stop the watchdog server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        logger.writeLog(f"Watchdog server stopped on port {self.port}")


def start_watchdog(service_name: str | bytes, port: int) -> WatchdogServer:
    """Start watchdog background listener (backward compatible function)."""
    global _server_instance, _service_name, _port, autoset
    _service_name = service_name if isinstance(service_name, bytes) else service_name.encode("utf-8")
    _port = int(port)

    if _server_instance:
        _server_instance.stop()

    _server_instance = WatchdogServer(_service_name, _port)
    _server_instance.start()

    if autoset:
        update()

    return _server_instance


def stop_watchdog() -> None:
    """Stop active watchdog background listener."""
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None


def register(service_name: str | bytes, address: str, port: int, dbconn: str) -> None:
    """Register service in the database."""
    global _service_name, _port, _dbconn, autoset
    autoset = True
    _service_name = service_name if isinstance(service_name, bytes) else service_name.encode("utf-8")
    _port = int(port)
    _dbconn = dbconn

    if not _dbconn:
        return

    try:
        import sl2util.dbhandler as db
        watchdogdb = db.DbSQL(_dbconn)
        svc_name_str = _service_name.decode("utf-8", errors="replace")
        sql = "PROC_SL2_SET_SERVICE ?, ?, ?"
        try:
            watchdogdb.setrow(sql, (svc_name_str, address, port))
        except Exception:
            # Fallback to direct string if driver does not support params for stored procedures
            fallback_sql = f"PROC_SL2_SET_SERVICE '{svc_name_str}', '{address}', {port}"
            watchdogdb.setrow(fallback_sql)
    except Exception as e:
        logger.writeLog(f"Watchdog register error: {e}")


def update() -> None:
    """Update service heartbeat status in the database."""
    global _service_name, _dbconn
    if not _dbconn:
        return

    try:
        import sl2util.dbhandler as db
        watchdogdb = db.DbSQL(_dbconn)
        svc_name_str = _service_name.decode("utf-8", errors="replace")
        sql = "UPDATE SL2_SERVICES_CONFIG SET STATUS = 1, TIME_STAMP = getdate() WHERE SERVICE_NAME = ?"
        try:
            watchdogdb.setrow(sql, (svc_name_str,))
        except Exception:
            fallback_sql = (
                f"UPDATE SL2_SERVICES_CONFIG SET STATUS = 1, TIME_STAMP = getdate() "
                f"WHERE SERVICE_NAME = '{svc_name_str}'"
            )
            watchdogdb.setrow(fallback_sql)
    except Exception as e:
        logger.writeLog(f"Watchdog update error: {e}")


def main() -> None:
    """CLI entrypoint for running the watchdog service daemon (e.g. in Docker)."""
    parser = argparse.ArgumentParser(description="SL2 Watchdog Service Daemon")
    parser.add_argument("--port", type=int, default=int(os.environ.get("WATCHDOG_PORT", 65001)), help="Watchdog port")
    parser.add_argument("--name", type=str, default=os.environ.get("WATCHDOG_NAME", "sl2_watchdog"), help="Service name")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host")
    args = parser.parse_args()

    print(f"Starting SL2 Watchdog '{args.name}' on {args.host}:{args.port}...")
    server = WatchdogServer(args.name, args.port)
    server.start(args.host)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Watchdog...")
        server.stop()
        print("Watchdog stopped.")


if __name__ == "__main__":
    main()
