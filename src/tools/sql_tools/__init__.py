# src/tools/sql_tools/__init__.py
"""
Database connection pools for MFC Toolbox.

- MySQL: Fabrication database (job info, org data)
- MSSQL: Application database (users, settings, conversations)
"""
from src.tools.sql_tools.mysql_pool import get_mysql_connection, close_mysql_pool
from src.tools.sql_tools.mssql_pool import get_mssql_connection, close_mssql_pool
from src.tools.sql_tools.get_jobs import get_jobs
from src.tools.sql_tools.get_job_info import get_job_info
from src.tools.sql_tools.get_conversation import get_conversation
from src.tools.sql_tools.create_new_conversation import create_new_conversation
from src.tools.sql_tools.get_conversations_list import get_conversations_list
from src.tools.sql_tools.update_conversation import update_conversation
from src.tools.sql_tools.delete_conversation import delete_conversation
from src.tools.sql_tools.update_conversations_summary import update_conversation_summary
from src.tools.sql_tools.add_message import add_message
from src.tools.sql_tools.get_messages import get_messages
from src.tools.sql_tools.get_message import get_message
from src.tools.sql_tools.admin_delete_messages_for_conversation import admin_delete_messages_for_conversation

__all__ = [
    "get_mysql_connection",
    "close_mysql_pool",
    "get_mssql_connection", 
    "close_mssql_pool",
    "get_jobs",
    "get_job_info",
    "get_conversation",
    "create_new_conversation",
    "get_conversations_list",
    "update_conversation",
    "delete_conversation",
    "update_conversation_summary",
    "add_message",
    "get_messages",
    "get_message",
    "admin_delete_messages_for_conversation",
]
