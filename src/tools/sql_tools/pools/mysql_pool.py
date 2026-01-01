from contextlib import contextmanager
from mysql.connector import pooling

POOL_CONFIG = {
    "pool_name": "mfc_toolbox_pool",
    "pool_size": 5,
    "pool_reset_session": True,
    "host": "strider",
    "user": "admin",
    "password": "fab",
    "database": "fabrication",
    "autocommit": True,
    "use_pure": True,
    "auth_plugin": "mysql_native_password",
}

_pool = None


def _get_pool() -> pooling.MySQLConnectionPool:
    """Get or create the connection pool (lazy initialization)."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(**POOL_CONFIG)
    return _pool


@contextmanager
def get_mysql_connection():
    """
    Context manager for safely checking out a MySQL connection from the pool.

    Yields:
        MySQLConnection: A connection from the pool
    
    Example:
        with get_mysql_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("CALL MyProcedure()")
                results = cursor.fetchall()
    """
    conn = None
    try:
        conn = _get_pool().get_connection()
        
        try:
            with conn.cursor() as cur:
                cur.execute("SET @@session.lc_time_names = %s", ("en_US",))
        except Exception:
            pass
            
        yield conn
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def close_mysql_pool():
    """Close all connections in the pool. Call on app shutdown."""
    global _pool
    if _pool is not None:
        _pool = None
