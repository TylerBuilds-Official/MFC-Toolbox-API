# src/tools/sql_tools/__init__.py
"""
Database connection pools for MFC Toolbox.

- MySQL: Fabrication database (job info, org data)
- MSSQL: Application database (users, settings, conversations)
"""
from src.tools.sql_tools.mysql_pool import get_mysql_connection, close_mysql_pool
from src.tools.sql_tools.mssql_pool import get_mssql_connection, close_mssql_pool

__all__ = [
    "get_mysql_connection",
    "close_mysql_pool",
    "get_mssql_connection", 
    "close_mssql_pool",
]
