"""
Connection pool for Voltron server (MFC_NTLIVE database).

This server hosts production/operational data including:
- FabTracker schema (production logs, machine metrics)
- Other operational schemas as needed

Connection Details:
- Host: voltron
- Port: 1433
- Database: MFC_NTLIVE
- Auth: SQL Server authentication
"""
import pyodbc
from contextlib import contextmanager

# Connection settings
VOLTRON_HOST = "voltron"
VOLTRON_PORT = 1433
VOLTRON_DATABASE = "MFC_NTLIVE"
VOLTRON_USER = "SA"
VOLTRON_PASSWORD = "MetFab$"

# Connection string
VOLTRON_CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={VOLTRON_HOST},{VOLTRON_PORT};"
    f"DATABASE={VOLTRON_DATABASE};"
    f"UID={VOLTRON_USER};"
    f"PWD={VOLTRON_PASSWORD};"
    f"TrustServerCertificate=yes;"
)

# Module-level connection pool
_voltron_pool = None


def get_voltron_pool():
    """Get or create the Voltron connection pool."""
    global _voltron_pool
    if _voltron_pool is None:
        # pyodbc doesn't have built-in pooling, but we can enable it
        pyodbc.pooling = True
        _voltron_pool = True  # Flag that pooling is enabled
    return _voltron_pool


def close_voltron_pool():
    """Close the Voltron connection pool."""
    global _voltron_pool
    _voltron_pool = None


@contextmanager
def get_voltron_connection():
    """
    Context manager for Voltron database connections.
    
    Usage:
        with get_voltron_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM FabTracker.ProductionLog")
            data = cursor.fetchall()
    """
    get_voltron_pool()  # Ensure pooling is enabled
    
    conn = pyodbc.connect(VOLTRON_CONNECTION_STRING, autocommit=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
