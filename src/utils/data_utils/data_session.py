from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import json


@dataclass
class VisualizationConfig:
    chart_type: str  # bar, line, table, pie
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    options: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {"chart_type": self.chart_type}
        if self.x_axis:
            result["x_axis"] = self.x_axis
        if self.y_axis:
            result["y_axis"] = self.y_axis
        if self.options:
            result["options"] = self.options
        return result

    @staticmethod
    def from_dict(data: dict) -> "VisualizationConfig":
        return VisualizationConfig(
            chart_type=data.get("chart_type", "table"),
            x_axis=data.get("x_axis"),
            y_axis=data.get("y_axis"),
            options=data.get("options")
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str) -> "VisualizationConfig":
        return VisualizationConfig.from_dict(json.loads(json_str))


@dataclass
class DataSession:
    id: int
    user_id: int
    message_id: Optional[int]
    session_group_id: Optional[int]
    parent_session_id: Optional[int]
    tool_name: str
    tool_params: Optional[dict]
    visualization_config: Optional[VisualizationConfig]
    status: str  # pending, running, success, error
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "message_id": self.message_id,
            "session_group_id": self.session_group_id,
            "parent_session_id": self.parent_session_id,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "visualization_config": self.visualization_config.to_dict() if self.visualization_config else None,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return result

    def __repr__(self):
        return (
            f"DataSession(id={self.id}, user_id={self.user_id}, "
            f"tool_name='{self.tool_name}', status='{self.status}', "
            f"session_group_id={self.session_group_id})"
        )
