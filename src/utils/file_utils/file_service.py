import uuid

from src.utils.file_utils.file_storage import FileStorage
from src.utils.file_utils._dataclasses.chat_file import ChatFile
from src.tools.sql_tools.chat_files import (
    create_chat_file,
    get_chat_file,
    get_chat_files_by_ids,
    get_chat_files_by_message,
    get_chat_files_by_message_ids,
    link_files_to_message,
)


class FileService:
    """Coordinates file storage on disk with DB metadata."""

    _storage = FileStorage()

    @classmethod
    def upload_file(cls, user_id: int, filename: str, mime_type: str, file_bytes: bytes) -> ChatFile:
        """Upload a file: save to disk, create DB record, return metadata."""

        # Validate
        if not cls._storage.validate_extension(filename):
            raise ValueError(f"File type not allowed: {filename}")

        if not cls._storage.validate_size(len(file_bytes)):
            raise ValueError(f"File exceeds maximum size of 28MB")

        category = cls._storage.get_category(mime_type)
        if not category:
            raise ValueError(f"Unsupported mime type: {mime_type}")

        # Generate unique name and save to disk
        file_id     = str(uuid.uuid4())
        stored_name = cls._storage.generate_stored_name(filename)
        storage_path = cls._storage.save_file(file_bytes, category, stored_name)

        # Create DB record
        data = create_chat_file(
            file_id=file_id,
            user_id=user_id,
            original_name=filename,
            stored_name=stored_name,
            category=category,
            mime_type=mime_type,
            file_size=len(file_bytes),
            storage_path=storage_path,
        )

        return ChatFile(**data)

    @classmethod
    def get_file(cls, file_id: str) -> ChatFile | None:
        """Get a single file by ID."""

        data = get_chat_file(file_id)
        if not data:

            return None

        return ChatFile(**data)

    @classmethod
    def get_files(cls, file_ids: list[str]) -> list[ChatFile]:
        """Get multiple files by IDs."""

        rows = get_chat_files_by_ids(file_ids)

        return [ChatFile(**row) for row in rows]

    @classmethod
    def get_files_for_message(cls, message_id: int) -> list[ChatFile]:
        """Get all files attached to a message."""

        rows = get_chat_files_by_message(message_id)

        return [ChatFile(**row) for row in rows]

    @classmethod
    def link_to_message(cls, file_ids: list[str], message_id: int) -> int:
        """Link uploaded files to a saved message."""

        return link_files_to_message(file_ids, message_id)

    @classmethod
    def get_attachments_for_messages(cls, message_ids: list[int]) -> dict[int, list[dict]]:
        """Batch-fetch file attachments grouped by message ID.

        Returns {message_id: [{id, original_name, category, mime_type, file_size}, ...]}.
        Only returns the fields needed for frontend display (no storage_path).
        """

        raw = get_chat_files_by_message_ids(message_ids)

        result: dict[int, list[dict]] = {}
        for msg_id, files in raw.items():
            result[msg_id] = [
                {
                    "id":        f["id"],
                    "name":      f["original_name"],
                    "category":  f["category"],
                    "mime_type": f["mime_type"],
                    "file_size": f["file_size"],
                }
                for f in files
            ]

        return result

    @classmethod
    def read_base64(cls, file: ChatFile) -> str:
        """Read a file as base64 string."""

        return cls._storage.read_file_base64(file.storage_path)

    @classmethod
    def read_text(cls, file: ChatFile) -> str:
        """Read a text file as string."""

        return cls._storage.read_file_text(file.storage_path)
