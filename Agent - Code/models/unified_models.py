"""Unified request/response models for the combined serving endpoint.

The unified endpoint accepts both Deal and RFQ requests via a single
`predict()` function. The `agent_type` field routes to the correct agent.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Unified Request
# ---------------------------------------------------------------------------


class UnifiedRequest(BaseModel):
    """Inbound payload for the unified serving endpoint.

    agent_type: "deal" or "rfq" — determines which agent handles the request.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    agent_type: str = Field(..., description="'deal' or 'rfq'")
    conversation_id: str
    session_id: str
    user_id: str = ""
    user_message: str = ""

    # ── RFQ-specific fields ──────────────────────────────────────────────
    persona: str = ""
    simulation: str = ""
    conversation_history: list[dict[str, str]] = Field(default_factory=list)

    # ── Deal-specific fields ─────────────────────────────────────────────
    analyst_type: str = ""
    scenario_type: str = ""
    chat_id: str = ""
