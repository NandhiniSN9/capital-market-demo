"""Pydantic v2 request models for the Deal Intelligence Agent API."""

from __future__ import annotations

from typing import Optional

from pydantic import UUID4, BaseModel, model_validator

from BE.models.enums import (
    ANALYST_SCENARIO_MAPPING,
    AgentType,
    AnalystType,
    ScenarioType,
)


class CreateChatRequest(BaseModel):
    """Request body for creating a new chat or uploading documents to an existing chat."""

    company_name: str
    analyst_type: AnalystType
    company_url: Optional[str] = None
    chat_id: Optional[UUID4] = None


class SendMessageRequest(BaseModel):
    """Request body for sending a message to the AI agent."""

    content: str
    analyst_type: AnalystType
    scenario_type: ScenarioType
    session_id: Optional[UUID4] = None
    session_title: Optional[str] = None
    agent_type: AgentType = AgentType.deal

    @model_validator(mode="after")
    def validate_scenario_for_analyst(self) -> SendMessageRequest:
        """Validate that scenario_type is valid for the given analyst_type."""
        valid_scenarios = ANALYST_SCENARIO_MAPPING.get(self.analyst_type, [])
        if self.scenario_type not in valid_scenarios:
            valid_names = [s.value for s in valid_scenarios]
            raise ValueError(
                f"Scenario '{self.scenario_type.value}' is not valid for analyst type "
                f"'{self.analyst_type.value}'. Valid scenarios: {valid_names}"
            )
        return self
