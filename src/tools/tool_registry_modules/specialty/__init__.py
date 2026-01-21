"""
Specialty Tool Registries

Aggregates tools that require specialty role grants.
These tools are gated by SPECIALTY_CATEGORIES rather than TOOL_CATEGORIES.

Structure:
- drawing_coordinator_registry.py  → DC tools
- (future) estimator_registry.py   → Estimator tools
- (future) project_manager_registry.py → PM tools
"""

from .drawing_coordinator_registry import DC_TOOLS


# Aggregate all specialty tools
SPECIALTY_TOOLS = [
    *DC_TOOLS,
    # Future:
    # *ESTIMATOR_TOOLS,
    # *PROJECT_MANAGER_TOOLS,
]

__all__ = [
    "SPECIALTY_TOOLS",
    "DC_TOOLS",
]
