# src/tools/sql_tools/pools/__init__.py
"""
Database connection pools for MFC Toolbox.

- MSSQL: Application database (users, settings, conversations)
- MySQL: Fabrication database (job info, org data)
- Voltron: Production/operational data (FabTracker)
"""

from src.tools.sql_tools.pools.mssql_pool import (
    get_mssql_connection,
    close_mssql_pool,
    SCHEMA,
)
from src.tools.sql_tools.pools.mysql_pool import (
    get_mysql_connection,
    close_mysql_pool,
)
from src.tools.sql_tools.pools.voltron_pool import (
    get_voltron_connection,
    close_voltron_pool,
)

__all__ = [
    # MSSQL
    "get_mssql_connection",
    "close_mssql_pool",
    "SCHEMA",
    # MySQL
    "get_mysql_connection",
    "close_mysql_pool",
    # Voltron
    "get_voltron_connection",
    "close_voltron_pool",
]
