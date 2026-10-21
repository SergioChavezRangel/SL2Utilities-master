"""
DataBase Handler
Provides abstracted access to Oracle and Microsoft SQL Server databases.
Supports modern python-oracledb (thin mode, clientless) with fallback to cx_Oracle,
and pyodbc for SQL Server.
"""
from collections.abc import Sequence
from typing import Any

# Attempt modern python-oracledb first, fall back to legacy cx_Oracle
try:
    import oracledb

    # Enable thin mode by default; works out of the box in containers and macOS/Linux
    _ORA_MODULE = oracledb
except ImportError:
    try:
        import cx_Oracle as _cx_Oracle
        _ORA_MODULE = _cx_Oracle
    except ImportError:
        _ORA_MODULE = None

try:
    import pyodbc
except ImportError:
    pyodbc = None


def rows_to_dict_list(cursor: Any) -> list[dict[str, Any]]:
    """Convert cursor results to a list of column-to-value dictionaries."""
    if cursor.description is None:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class DbSQL:
    """SQL Server database connection handler using pyodbc."""

    def __init__(self, dbconn: str):
        """Initialize connection to SQL Server."""
        if pyodbc is None:
            raise ImportError(
                "pyodbc is required for DbSQL. Install via 'pip install pyodbc' "
                "or install sl2util[mssql]."
            )
        self.dbconn = dbconn
        self.dbSQL = pyodbc.connect(dbconn)

    def getrows(
        self, query: str, params: Sequence[Any] | dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute SELECT query and return all rows as a list of dicts."""
        cursor = self.dbSQL.cursor()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if cursor.description is None:
                return []
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def getrow(
        self, query: str, params: Sequence[Any] | dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute SELECT query and return the first row as a dict."""
        cursor = self.dbSQL.cursor()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if cursor.description is None:
                return {}
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row is not None else {}
        finally:
            cursor.close()

    def setrow(
        self, query: str, params: Sequence[Any] | dict[str, Any] | None = None
    ) -> None:
        """Execute INSERT / UPDATE / DDL query and commit."""
        cursor = self.dbSQL.cursor()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.dbSQL.commit()
        finally:
            cursor.close()

    def close(self) -> None:
        """Close database connection."""
        if self.dbSQL:
            self.dbSQL.close()

    def __enter__(self) -> "DbSQL":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class DbOra:
    """Oracle database connection handler supporting python-oracledb & cx_Oracle."""

    def __init__(self, dbconn: str):
        """Initialize connection to Oracle."""
        if _ORA_MODULE is None:
            raise ImportError(
                "python-oracledb is required for DbOra. Install via 'pip install oracledb' "
                "or install sl2util[all]."
            )
        self.dbconn = dbconn
        # Support connection string or DSN
        if hasattr(_ORA_MODULE, "connect"):
            self.dbOra = _ORA_MODULE.connect(dbconn)
        else:
            self.dbOra = _ORA_MODULE.Connection(dbconn)

    def getrows(
        self, query: str, params: Sequence[Any] | dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute SELECT query and return all rows as a list of dicts."""
        cursor = self.dbOra.cursor()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return rows_to_dict_list(cursor)
        finally:
            cursor.close()

    def getrow(
        self, query: str, params: Sequence[Any] | dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute SELECT query and return the first row as a dict."""
        rows = self.getrows(query, params)
        return rows[0] if rows else {}

    def setrow(
        self, query: str, params: Sequence[Any] | dict[str, Any] | None = None
    ) -> None:
        """Execute INSERT / UPDATE / DDL query and commit."""
        cursor = self.dbOra.cursor()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.dbOra.commit()
        finally:
            cursor.close()

    def close(self) -> None:
        """Close database connection."""
        if self.dbOra:
            self.dbOra.close()

    def __enter__(self) -> "DbOra":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
