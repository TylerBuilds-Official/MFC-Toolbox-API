from dataclasses import dataclass
from typing import List, Any
from datetime import datetime
import json


@dataclass
class DataResult:
    id: int
    session_id: int
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return (
            f"DataResult(id={self.id}, session_id={self.session_id}, "
            f"row_count={self.row_count}, columns={self.columns[:3]}...)"
        )


@dataclass
class NormalizedResult:
    """
    Intermediate representation of normalized tool output.
    Used by ToolNormalizer before storing to DataResult.
    """
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    meta: dict = None  # Optional metadata (source tool, processing notes, etc.)

    def to_dict(self) -> dict:
        result = {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
        }
        if self.meta:
            result["meta"] = self.meta
        return result

    @staticmethod
    def empty() -> "NormalizedResult":
        """Return an empty result for error cases."""
        return NormalizedResult(columns=[], rows=[], row_count=0)
