from dataclasses import dataclass


@dataclass
class ChatFile:
    """Metadata for an uploaded chat file."""

    id:            str
    user_id:       int
    message_id:    int | None
    original_name: str
    stored_name:   str
    category:      str
    mime_type:     str
    file_size:     int
    storage_path:  str
    created_at:    str

    def to_dict(self) -> dict:
        """Serialize to dict for API responses."""

        return {
            "id":            self.id,
            "user_id":       self.user_id,
            "message_id":    self.message_id,
            "original_name": self.original_name,
            "stored_name":   self.stored_name,
            "category":      self.category,
            "mime_type":     self.mime_type,
            "file_size":     self.file_size,
            "storage_path":  self.storage_path,
            "created_at":    str(self.created_at),
        }
