import os
import uuid
import base64
from pathlib import Path


# Upload root — created on startup if missing
UPLOAD_ROOT = os.getenv("FABCORE_UPLOAD_ROOT", r"E:\Services\Fabcore\API\UPLOADS")

# Mime type → category mapping
MIME_CATEGORIES: dict[str, str] = {
    "image/png":       "images",
    "image/jpeg":      "images",
    "image/jpg":       "images",
    "image/gif":       "images",
    "image/webp":      "images",
    "application/pdf": "documents",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "documents",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":      "spreadsheets",
    "application/vnd.ms-excel":     "spreadsheets",
    "text/plain":      "text",
    "text/csv":        "text",
    "text/markdown":   "text",
}

ALLOWED_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".pdf", ".docx",
    ".xlsx", ".xls",
    ".txt", ".csv", ".md", ".log",
}

MAX_FILE_SIZE = 28 * 1024 * 1024  # 28 MB


class FileStorage:
    """Handles disk-level file operations for chat uploads."""

    def __init__(self, root: str = UPLOAD_ROOT):
        self.root = Path(root)
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Create category subdirectories if they don't exist."""

        for category in ("images", "documents", "spreadsheets", "text"):
            (self.root / category).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_category(mime_type: str) -> str | None:
        """Map mime type to storage category."""

        return MIME_CATEGORIES.get(mime_type)

    @staticmethod
    def validate_extension(filename: str) -> bool:
        """Check if file extension is allowed."""

        ext = Path(filename).suffix.lower()

        return ext in ALLOWED_EXTENSIONS

    @staticmethod
    def validate_size(size: int) -> bool:
        """Check if file size is within limits."""

        return 0 < size <= MAX_FILE_SIZE

    def generate_stored_name(self, original_name: str) -> str:
        """Generate a unique stored filename preserving the extension."""

        ext       = Path(original_name).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]

        return f"{unique_id}{ext}"

    def save_file(self, file_bytes: bytes, category: str, stored_name: str) -> str:
        """Save file bytes to disk and return the full storage path."""

        dest = self.root / category / stored_name
        dest.write_bytes(file_bytes)

        return str(dest)

    def read_file_bytes(self, storage_path: str) -> bytes:
        """Read raw bytes from a stored file."""

        return Path(storage_path).read_bytes()

    def read_file_base64(self, storage_path: str) -> str:
        """Read a file and return base64-encoded content."""

        raw = self.read_file_bytes(storage_path)

        return base64.b64encode(raw).decode("utf-8")

    def read_file_text(self, storage_path: str, encoding: str = "utf-8") -> str:
        """Read a text file and return its content as a string."""

        return Path(storage_path).read_text(encoding=encoding)

    def delete_file(self, storage_path: str) -> bool:
        """Delete a file from disk. Returns True if deleted."""

        path = Path(storage_path)
        if path.exists():
            path.unlink()

            return True

        return False

    def file_exists(self, storage_path: str) -> bool:
        """Check if a stored file exists on disk."""

        return Path(storage_path).exists()
