"""Unified Intelligence Agent — Databricks Model Serving Endpoint.

Exposes:
  - ``predict(request_dict)``  – primary serving handler (sync wrapper over async)
  - ``health()``               – liveness check
  - ``ready()``                – readiness check

Routes requests to either the Deal agent or RFQ agent based on `agent_type`.

Docs:
  https://docs.databricks.com/en/machine-learning/model-serving/index.html
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any


# ---------------------------------------------------------------------------
# Persistent event loop — survives across requests, avoids "Event loop is
# closed" errors when gunicorn/gevent reuses workers for concurrent calls.
# ---------------------------------------------------------------------------
_loop = asyncio.new_event_loop()
_loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_loop_thread.start()

from agents.deal_agent import DealIntelligenceAgent
from agents.rtq_agent import RTQAgent
from models.unified_models import UnifiedRequest
from repositories.databricks_repository import DatabricksRepository
from repositories.genie_repository import GenieRepository
from services.unified_service import UnifiedService
from utils.exceptions import AgentBaseError
from utils.logger import logger


def _build_service() -> UnifiedService:
    """Build a fresh UnifiedService per request — avoids stale async connections."""
    rtq_agent = RTQAgent(genie_repo=GenieRepository())
    return UnifiedService(
        rtq_agent=rtq_agent,
        deal_agent=DealIntelligenceAgent(),
        db_repo=DatabricksRepository(),
    )


# ---------------------------------------------------------------------------
# Request normalisation — maps frontend field names → internal model fields
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Persona label → internal persona key mapping
# Keys are lowercased session-endpoint labels → YAML persona keys
# ---------------------------------------------------------------------------
_PERSONA_MAP: dict[str, str] = {
    "credit_trader": "credit_trader",
    "credit_trader_sell": "credit_trader",
    "sales_trader": "sales_trader",
    "sales_trader_sell": "sales_trader",
    "portfolio_manager": "portfolio_manager",
    "portfolio_manager_buy": "portfolio_manager",
    "trader_buy": "buy_side_trader",
    "buy_side_trader": "buy_side_trader",
    "buyside_trader": "buy_side_trader",
    "desk_head": "desk_head",
}

# ---------------------------------------------------------------------------
# Simulation label → internal simulation key mapping
# Session-endpoint labels (lowercased) → YAML simulation keys
# ---------------------------------------------------------------------------
_SIMULATION_MAP: dict[str, str] = {
    # ── passthrough: already-correct keys ──
    "default": "default",
    "pre_market_preparation": "pre_market_preparation",
    "rfq_quoting": "rfq_quoting",
    "trade_execution": "trade_execution",
    "end_of_day_analysis": "end_of_day_analysis",
    "client_interaction_rfq_routing": "client_interaction_rfq_routing",
    "post_trade_follow_up": "post_trade_follow_up",
    "end_of_day_client_review": "end_of_day_client_review",
    "client_relationship_management": "client_relationship_management",
    "portfolio_review_investment_decisions": "portfolio_review_investment_decisions",
    "rfq_initiation": "rfq_initiation",
    "quote_comparison_execution": "quote_comparison_execution",
    "post_trade_review": "post_trade_review",
    "compliance_reporting": "compliance_reporting",
    "pre_market_prep_pm_coordination": "pre_market_prep_pm_coordination",
    "order_intake_rfq_execution": "order_intake_rfq_execution",
    "dealer_quote_comparison": "dealer_quote_comparison",
    "post_trade_followup_dealer_management": "post_trade_followup_dealer_management",
    "compliance_tca_reporting": "compliance_tca_reporting",

    # ── session-endpoint simulation IDs → YAML keys ──
    # CREDIT_TRADER_SELL (credit_trader)
    "ct-pre-market": "pre_market_preparation",
    "ct-rfq-quoting": "rfq_quoting",
    "ct-trade-execution": "trade_execution",
    "ct-end-of-day": "end_of_day_analysis",

    # SALES_TRADER_SELL (sales_trader)
    "st-pre-market": "pre_market_preparation",
    "st-client-interaction": "client_interaction_rfq_routing",
    "st-post-trade": "post_trade_follow_up",
    "st-end-of-day": "end_of_day_client_review",
    "st-relationship": "client_relationship_management",
    "pre-market preparation": "pre_market_preparation",

    # PORTFOLIO_MANAGER_BUY (portfolio_manager)
    "pm-portfolio-review": "portfolio_review_investment_decisions",
    "pm-rfq-initiation": "rfq_initiation",
    "pm-quote-comparison": "quote_comparison_execution",
    "pm-post-trade": "post_trade_review",
    "pm-compliance": "compliance_reporting",

    # TRADER_BUY (buy_side_trader)
    # NOTE: tb-* IDs map to buy_side_trader YAML prompts where they exist.
    # The following have NO matching buy_side_trader prompt yet:
    #   tb-portfolio-review → portfolio_review_investment_decisions (exists under portfolio_manager only)
    #   tb-rfq-initiation   → rfq_initiation (exists under portfolio_manager only)
    #   tb-quote-comparison → quote_comparison_execution (exists under portfolio_manager only)
    #   tb-post-trade       → post_trade_review (exists under portfolio_manager only)
    # Prompts need to be added under buy_side_trader for these to work.
    "tb-portfolio-review": "portfolio_review_investment_decisions",
    "tb-rfq-initiation": "rfq_initiation",
    "tb-quote-comparison": "quote_comparison_execution",
    "tb-post-trade": "post_trade_review",
    "tb-compliance": "compliance_tca_reporting",
}


def _normalise_request(raw: dict[str, Any]) -> dict[str, Any]:
    """Map frontend payload fields to UnifiedRequest field names.

    Supports both Deal and RFQ frontend payloads:
      - intelligence="rfq" or intelligence="deal" → agent_type
      - user_persona → persona
      - chat_message → user_message
      - simulation title-case → snake_case
    """
    normalised = dict(raw)

    # Determine agent_type from 'intelligence' field or explicit 'agent_type'
    if "agent_type" not in normalised:
        intelligence = normalised.pop("intelligence", "").lower().strip()
        if intelligence == "rfq":
            normalised["agent_type"] = "rfq"
        elif intelligence in ("deal", "deal_intelligence"):
            normalised["agent_type"] = "deal"
        else:
            # Infer from presence of persona/simulation vs analyst_type
            if normalised.get("persona") or normalised.get("user_persona"):
                normalised["agent_type"] = "rfq"
            elif normalised.get("analyst_type"):
                normalised["agent_type"] = "deal"
            else:
                normalised["agent_type"] = "rfq"  # default

    # Map user_persona → persona
    if "user_persona" in normalised and "persona" not in normalised:
        normalised["persona"] = normalised.pop("user_persona")

    # Normalise persona label to internal key
    if "persona" in normalised:
        persona_raw = str(normalised["persona"]).strip().lower()
        normalised["persona"] = _PERSONA_MAP.get(persona_raw, persona_raw)

    # Map chat_message → user_message
    if "chat_message" in normalised and "user_message" not in normalised:
        normalised["user_message"] = normalised.pop("chat_message")

    # Normalise simulation to snake_case
    if "simulation" in normalised:
        sim_raw = str(normalised["simulation"]).strip().lower()
        normalised["simulation"] = _SIMULATION_MAP.get(
            sim_raw, sim_raw.replace(" ", "_").replace("-", "_")
        )

    # Drop unknown frontend-only fields
    for field in ("intelligence",):
        normalised.pop(field, None)

    normalised.setdefault("conversation_history", [])
    return normalised


# ---------------------------------------------------------------------------
# Async core handler
# ---------------------------------------------------------------------------


async def _predict_async(request_dict: dict[str, Any]) -> dict[str, Any]:
    """Async implementation of the predict handler."""
    try:
        request = UnifiedRequest(**_normalise_request(request_dict))
    except Exception as exc:
        logger.warning("Request validation failed", extra={"error": str(exc)})
        return {
            "success": False,
            "error": {"error_code": "UNI-400", "message": f"Invalid request: {exc}"},
        }

    try:
        service = _build_service()
        return await service.process(request)

    except AgentBaseError as exc:
        logger.warning("Agent domain error", extra={
            "error_code": exc.error_code, "error": str(exc),
        })
        return {
            "success": False,
            "error": {"error_code": exc.error_code, "message": str(exc)},
        }
    except Exception as exc:
        logger.exception("Unexpected error in predict()")
        return {
            "success": False,
            "error": {"error_code": "UNI-999", "message": f"Unexpected error: {str(exc)[:500]}"},
        }


# ---------------------------------------------------------------------------
# Serving entry points (Databricks Model Serving contract)
# ---------------------------------------------------------------------------


def predict(request_dict: dict[str, Any]) -> dict[str, Any]:
    """Primary Databricks Model Serving handler.

    Submits async work to a persistent background event loop so that
    httpx/openai connection pools are never destroyed between requests.
    """
    logger.info("predict() called", extra={
        "conversation_id": request_dict.get("conversation_id", ""),
        "agent_type": request_dict.get("agent_type", request_dict.get("intelligence", "")),
    })
    future = asyncio.run_coroutine_threadsafe(_predict_async(request_dict), _loop)
    return future.result(timeout=600)


def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


def ready() -> dict[str, str]:
    """Readiness probe."""
    return {"status": "ready"}
