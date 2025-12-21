# src/tools/sql_tools/mssql_pool.py
"""
MS SQL Server connection pool for application data (users, settings, conversations).
Uses pyodbc with ODBC Driver 17 for SQL Server.
"""
import os
import pyodbc
from contextlib import contextmanager
from queue import Queue, Empty
from threading import Lock


class MSSQLConnectionPool:
    """Thread-safe connection pool for MS SQL Server using pyodbc."""
    
    def __init__(self, connection_string: str, pool_size: int = 5):
        self._connection_string = connection_string
        self._pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._lock = Lock()
        self._created_connections = 0
    
    def _create_connection(self) -> pyodbc.Connection:
        """Create a new database connection."""
        return pyodbc.connect(self._connection_string, autocommit=False)
    
    def get_connection(self) -> pyodbc.Connection:
        """Get a connection from the pool or create a new one."""
        try:
            conn = self._pool.get_nowait()
            # Test if connection is still valid
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return conn
            except pyodbc.Error:
                # Connection is stale, create a new one
                with self._lock:
                    self._created_connections -= 1
                return self._create_connection()
        except Empty:
            with self._lock:
                if self._created_connections < self._pool_size:
                    self._created_connections += 1
                    return self._create_connection()
            # Pool exhausted, wait for one to be returned
            return self._pool.get(timeout=30)
    
    def return_connection(self, conn: pyodbc.Connection):
        """Return a connection to the pool."""
        try:
            conn.rollback()
            self._pool.put_nowait(conn)

        except Exception:
            with self._lock:
                self._created_connections -= 1
            try:
                conn.close()
            except Exception:
                pass
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        with self._lock:
            self._created_connections = 0


_mssql_pool: MSSQLConnectionPool | None = None
SCHEMA = "toolbox_web"


def _get_mssql_pool() -> MSSQLConnectionPool:
    """Get or create the MS SQL connection pool (lazy initialization)."""
    global _mssql_pool
    if _mssql_pool is None:
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.getenv('MSSQL_SERVER')};"
            f"DATABASE={os.getenv('MSSQL_DATABASE')};"
            f"UID={os.getenv('MSSQL_USER')};"
            f"PWD={os.getenv('MSSQL_PASSWORD')};"
            "TrustServerCertificate=yes;"
        )
        _mssql_pool = MSSQLConnectionPool(connection_string, pool_size=5)
    return _mssql_pool


@contextmanager
def get_mssql_connection():
    """
    Context manager for MS SQL connections.
    Auto-commits on success, rolls back on exception.
    
    Example:
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM toolbox_web.Users WHERE Id = ?", (user_id,))
            row = cursor.fetchone()
    """
    pool = _get_mssql_pool()
    conn = pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.return_connection(conn)


def close_mssql_pool():
    """Close the MS SQL pool. Call on app shutdown."""
    global _mssql_pool
    if _mssql_pool is not None:
        _mssql_pool.close_all()
        _mssql_pool = None
