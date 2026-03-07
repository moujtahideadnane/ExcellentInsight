"""Single source of truth for pipeline step names, order, and status mappings.

This ensures the orchestrator, API (SSE), and frontend consistently
refer to the same execution phases.
"""

from app.models.job import JobStatus

# Ordered list of steps shown in the UI
PIPELINE_STEPS = ["parsing", "schema", "stats", "llm", "dashboard", "done"]

# Map JobStatus (DB) to UI step IDs
STATUS_TO_STEP: dict[JobStatus, str] = {
    JobStatus.PENDING: "parsing",
    JobStatus.PARSING: "parsing",
    JobStatus.DETECTING_SCHEMA: "schema",
    JobStatus.ANALYZING: "stats",
    JobStatus.ENRICHING: "llm",
    JobStatus.BUILDING: "dashboard",
    JobStatus.DONE: "done",
    JobStatus.FAILED: "failed",
    JobStatus.CANCELLED: "cancelled",
}

# Display names for UI progress updates
STEP_DISPLAY_NAMES = {
    "parsing": "Reading file...",
    "schema": "Analyzing columns...",
    "stats": "Computing statistics...",
    "llm": "AI generating insights...",
    "dashboard": "Finalizing dashboard...",
}
