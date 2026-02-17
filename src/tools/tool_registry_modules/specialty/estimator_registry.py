"""
Estimator Tools Registry

Requires: 'estimator' specialty role
Display Category: Estimator
"""

from src.tools.specialty_tools.estimator import (
    oa_est_classify_and_breakout,
    oa_est_get_default_output_path,
)


EST_TOOLS = [
    {
        "name": "classify_and_breakout_pdf",
        "description": (
            "Classify a construction plan PDF by discipline and split into "
            "separate files (Structural.pdf, Architectural.pdf, etc.). "
            "Output defaults to ~/Desktop/Fabcore/EstimatorTools/Classification."
        ),
        "category": "plan_classification",
        "display_category": "Estimator",

        "parameters": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Full path to the plan PDF on the user's machine",
                },
                "output_path": {
                    "type": "string",
                    "description": "Output directory for breakout PDFs. Uses default if omitted.",
                },
            },
            "required": ["pdf_path"],
        },

        "executor":      oa_est_classify_and_breakout,
        "is_async":      True,
        "needs_user_id": True,

        "chat_toolbox":       True,
        "data_visualization": False,
    },

    {
        "name": "get_classification_output_path",
        "description": "Get the default output path for classification breakout files.",
        "category": "plan_classification",
        "display_category": "Estimator",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },

        "executor":      oa_est_get_default_output_path,
        "is_async":      True,
        "needs_user_id": True,

        "chat_toolbox":       False,
        "data_visualization": False,
    },
]


__all__ = ["EST_TOOLS"]
