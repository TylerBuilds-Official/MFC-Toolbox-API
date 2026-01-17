"""
Filesystem Tools Registry - User Level

Accessible by: user, manager, admin
Category: filesystem
Display Category: Filesystem

Tools for reading/writing files on user's computer via the agent connector.
Requires Filesystem Connector enabled and paths in allowed folders.
All tools except fs_get_allowed_folders are async and require agent connection.
"""

from src.tools.local_mcp_tools.filesystem_tools import (
    # Directory operations
    oa_fs_list_directory,
    oa_fs_create_directory,
    oa_fs_directory_tree,
    # File operations
    oa_fs_read_file,
    oa_fs_write_file,
    oa_fs_edit_file,
    oa_fs_delete_file,
    oa_fs_copy_file,
    oa_fs_move_file,
    # Search & info
    oa_fs_search_files,
    oa_fs_get_file_info,
    oa_fs_file_exists,
    # Non-async
    oa_fs_get_allowed_folders,
)


FILESYSTEM_TOOLS = [
    # =========================================================================
    # Directory Operations
    # =========================================================================
    {
        "name": "fs_list_directory",
        "description": "List contents of a directory on the user's computer. Returns files and folders with metadata. Requires the user to have the Filesystem Connector enabled and the path to be in their allowed folders. Use fs_get_allowed_folders first to see what paths are accessible.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (e.g., 'C:\\Projects' or 'D:\\Data')"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_list_directory,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_create_directory",
        "description": "Create a directory on the user's computer. Creates parent directories automatically if needed. Requires write permission on the parent folder.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to create (e.g., 'C:\\Projects\\NewFolder')"
                },
                "parents": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist (default true)"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_create_directory,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_directory_tree",
        "description": "Get a recursive tree view of a directory on the user's computer. Returns nested structure with files and folders. Useful for understanding project structure. Use max_depth to limit recursion for large directories.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Root directory path to scan"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth (default 5, max 10)"
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Include files in output, not just directories (default true)"
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files and folders (default false)"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_directory_tree,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    # =========================================================================
    # File Operations
    # =========================================================================
    {
        "name": "fs_read_file",
        "description": "Read the contents of a text file on the user's computer. Returns the file content as text. Use for reading code files, config files, logs, text documents, etc. Requires read permission on the containing folder.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to read (e.g., 'C:\\Projects\\app\\config.json')"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_read_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_write_file",
        "description": "Write content to a file on the user's computer. Creates the file if it doesn't exist, overwrites if it does. Use for creating/updating code files, configs, scripts, etc. Requires write permission on the containing folder.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to write (e.g., 'C:\\Projects\\output.txt')"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        },

        "executor": oa_fs_write_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_edit_file",
        "description": "Edit a file by finding and replacing text. The old_text must appear exactly once in the file (for safe, unambiguous replacement). Use for targeted code edits, config changes, etc. If text appears multiple times, add more surrounding context to make it unique.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "Text to find and replace (must appear exactly once in file)"
                },
                "new_text": {
                    "type": "string",
                    "description": "Replacement text (can be empty to delete the old_text)"
                }
            },
            "required": ["path", "old_text", "new_text"]
        },

        "executor": oa_fs_edit_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_delete_file",
        "description": "Delete a file on the user's computer. This is permanent and cannot be undone. Requires delete permission on the containing folder. Use with caution.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to delete"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_delete_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_copy_file",
        "description": "Copy a file to a new location on the user's computer. If destination is a directory, the file is copied into it with the same name. Creates parent directories if needed. Requires read permission on source and write permission on destination.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source file path to copy from"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path (file or directory)"
                }
            },
            "required": ["source", "destination"]
        },

        "executor": oa_fs_copy_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_move_file",
        "description": "Move or rename a file or directory on the user's computer. Works for both files and directories. If destination is an existing directory, the source is moved into it. Requires delete permission on source and write permission on destination.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source path (file or directory) to move"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path"
                }
            },
            "required": ["source", "destination"]
        },

        "executor": oa_fs_move_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    # =========================================================================
    # Search & Info
    # =========================================================================
    {
        "name": "fs_search_files",
        "description": "Search for files matching a pattern on the user's computer. Supports glob patterns (*.py, **/*.txt) or simple substring matching. Searches recursively from the given path. Use for finding files when you don't know the exact location.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to search in"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern - glob (*.py, *.txt) or substring to match in filename"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return (default 100, max 500)"
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files in results (default false)"
                }
            },
            "required": ["path", "pattern"]
        },

        "executor": oa_fs_search_files,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_get_file_info",
        "description": "Get detailed metadata about a file or directory on the user's computer. Returns name, size, type (file/directory), and timestamps (created, modified, accessed). Use to check file details before operations.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file or directory"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_get_file_info,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_file_exists",
        "description": "Check if a file or directory exists on the user's computer. Returns existence status and whether it's a file or directory. Quick check before attempting operations.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to check"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_file_exists,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    # =========================================================================
    # Non-Async (doesn't need agent)
    # =========================================================================
    {
        "name": "fs_get_allowed_folders",
        "description": "Get the list of folders the user has allowed access to via the Filesystem Connector. Shows which paths you can read/write/delete. Call this first before attempting file operations to understand what's accessible.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_fs_get_allowed_folders,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        # Note: fs_get_allowed_folders is NOT async - doesn't need agent.
    },
]
