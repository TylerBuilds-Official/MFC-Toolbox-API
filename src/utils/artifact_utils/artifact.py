"""
Artifact Models

Dataclasses for ChatArtifacts and related structures.
Matches the toolbox_web.ChatArtifacts table schema.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from datetime import datetime
import json


# =============================================================================
# Type Definitions
# =============================================================================

ArtifactType   = Literal['data', 'word', 'excel', 'pdf', 'image']
ArtifactStatus = Literal['ready', 'pending', 'error', 'opened']
ChartType      = Literal['line', 'bar', 'pie', 'table', 'card', 'area', 'scatter']


# =============================================================================
# Generation Parameters (Metadata)
# =============================================================================

@dataclass
class ArtifactGenerationParams:
    """
    Parameters needed to recreate/execute the artifact.
    Stored as JSON in ChatArtifacts.GenerationParams.
    
    Simplified from original design - just the essentials:
    - Tool execution info
    - Basic chart config hints
    - Traceability (jobNumber)
    - Lineage (parentSessionId)
    """
    tool_name:    str
    tool_params:  dict = field(default_factory=dict)
    
    # Chart hints (nullable - use backend defaults if not set)
    chart_type:   Optional[ChartType] = None
    x_axis:       Optional[str]       = None
    y_axis:       Optional[str]       = None
    group_by:     Optional[str]       = None
    series_hints: Optional[List[str]] = None
    
    # Traceability
    job_number:   Optional[str]       = None
    
    # Lineage - links new session to parent for re-runs/refinements
    parent_session_id: Optional[int]  = None

    def to_dict(self) -> dict:
        result = {
            "toolName":   self.tool_name,
            "toolParams": self.tool_params,
        }
        
        if self.chart_type:
            result["chartType"] = self.chart_type
        if self.x_axis:
            result["xAxis"] = self.x_axis
        if self.y_axis:
            result["yAxis"] = self.y_axis
        if self.group_by:
            result["groupBy"] = self.group_by
        if self.series_hints:
            result["seriesHints"] = self.series_hints
        if self.job_number:
            result["jobNumber"] = self.job_number
        if self.parent_session_id is not None:
            result["parentSessionId"] = self.parent_session_id
        
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(data: dict) -> "ArtifactGenerationParams":
        return ArtifactGenerationParams(
            tool_name         = data.get("toolName", ""),
            tool_params       = data.get("toolParams", {}),
            chart_type        = data.get("chartType"),
            x_axis            = data.get("xAxis"),
            y_axis            = data.get("yAxis"),
            group_by          = data.get("groupBy"),
            series_hints      = data.get("seriesHints"),
            job_number        = data.get("jobNumber"),
            parent_session_id = data.get("parentSessionId"),
        )

    @staticmethod
    def from_json(json_str: str) -> "ArtifactGenerationParams":
        return ArtifactGenerationParams.from_dict(json.loads(json_str))


# =============================================================================
# Generation Results (Cached Summary)
# =============================================================================

@dataclass
class ArtifactGenerationResults:
    """
    Lightweight summary of execution results.
    Stored as JSON in ChatArtifacts.GenerationResults.
    
    NOT the full data - just metadata for display.
    Full data lives in DataResults after DataSession creation.
    """
    row_count:    int
    column_count: int
    columns:      Optional[List[str]] = None
    error:        Optional[str]       = None

    def to_dict(self) -> dict:
        result = {
            "rowCount":    self.row_count,
            "columnCount": self.column_count,
        }
        
        if self.columns:
            result["columns"] = self.columns
        if self.error:
            result["error"] = self.error
        
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_summary_string(self) -> str:
        """Human-readable summary like 'Success: 52 rows, 5 columns'"""
        if self.error:
            return f"Error: {self.error}"
        return f"Success: {self.row_count} rows, {self.column_count} columns"

    @staticmethod
    def from_dict(data: dict) -> "ArtifactGenerationResults":
        return ArtifactGenerationResults(
            row_count    = data.get("rowCount", 0),
            column_count = data.get("columnCount", 0),
            columns      = data.get("columns"),
            error        = data.get("error"),
        )

    @staticmethod
    def from_json(json_str: str) -> "ArtifactGenerationResults":
        return ArtifactGenerationResults.from_dict(json.loads(json_str))

    @staticmethod
    def success(row_count: int, column_count: int, columns: List[str] = None) -> "ArtifactGenerationResults":
        return ArtifactGenerationResults(
            row_count    = row_count,
            column_count = column_count,
            columns      = columns,
        )

    @staticmethod
    def failure(error: str) -> "ArtifactGenerationResults":
        return ArtifactGenerationResults(
            row_count    = 0,
            column_count = 0,
            error        = error,
        )


# =============================================================================
# Main Artifact Dataclass
# =============================================================================

@dataclass
class Artifact:
    """
    Represents a ChatArtifact record.
    
    Artifacts are "recipes" for creating DataSessions.
    They're created during chat and persist so users can
    click them later to open visualizations.
    """
    id:                 str  # UUID
    user_id:            int
    conversation_id:    int
    message_id:         Optional[int]
    artifact_type:      ArtifactType
    title:              str
    generation_params:  Optional[ArtifactGenerationParams]
    generation_results: Optional[ArtifactGenerationResults]
    status:             ArtifactStatus
    error_message:      Optional[str]
    created_at:         datetime
    updated_at:         datetime
    accessed_at:        Optional[datetime]
    access_count:       int
    metadata:           Optional[dict]  # Type-specific extra data

    def to_dict(self) -> dict:
        return {
            "id":                self.id,
            "user_id":           self.user_id,
            "conversation_id":   self.conversation_id,
            "message_id":        self.message_id,
            "artifact_type":     self.artifact_type,
            "title":             self.title,
            "generation_params": self.generation_params.to_dict() if self.generation_params else None,
            "generation_results": self.generation_results.to_dict() if self.generation_results else None,
            "status":            self.status,
            "error_message":     self.error_message,
            "created_at":        self.created_at.isoformat() if self.created_at else None,
            "updated_at":        self.updated_at.isoformat() if self.updated_at else None,
            "accessed_at":       self.accessed_at.isoformat() if self.accessed_at else None,
            "access_count":      self.access_count,
            "metadata":          self.metadata,
        }

    def __repr__(self):
        return (
            f"Artifact(id={self.id[:8]}..., type={self.artifact_type}, "
            f"title='{self.title}', status={self.status})"
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'ArtifactType',
    'ArtifactStatus',
    'ChartType',
    'ArtifactGenerationParams',
    'ArtifactGenerationResults',
    'Artifact',
]
