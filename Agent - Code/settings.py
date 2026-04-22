"""Unified agent settings — merged configuration for Deal + RFQ agents.

All environment variables from both agents are consolidated here.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# RFQ table constants
# ---------------------------------------------------------------------------
TABLE_WALLET_SHARE_SNAPSHOTS = "wallet_share_snapshots"
TABLE_TRACE_DATA = "trace_data"
TABLE_BONDS = "bonds"
TABLE_FIRMS = "firms"
TABLE_RFQ_TRADES = "rfq_trades"
TABLE_SESSIONS = "sessions"
TABLE_CONVERSATIONS = "conversations"
TABLE_TOKEN_CONSUMPTION = "token_consumption"
TABLE_ERROR_LOGS = "error_logs"

# ---------------------------------------------------------------------------
# RFQ persona / simulation constants
# ---------------------------------------------------------------------------
PERSONA_CREDIT_TRADER = "credit_trader"
PERSONA_SALES_TRADER = "sales_trader"
PERSONA_BUY_SIDE_TRADER = "buy_side_trader"
PERSONA_PORTFOLIO_MANAGER = "portfolio_manager"
PERSONA_DESK_HEAD = "desk_head"

VALID_PERSONAS = {
    PERSONA_CREDIT_TRADER,
    PERSONA_SALES_TRADER,
    PERSONA_BUY_SIDE_TRADER,
    PERSONA_PORTFOLIO_MANAGER,
    PERSONA_DESK_HEAD,
}

PERSONA_SIMULATION_MAP: dict[str, set[str]] = {
    PERSONA_CREDIT_TRADER: {
        "default", "pre_market_preparation", "rfq_quoting", "trade_execution", "end_of_day_analysis",
    },
    PERSONA_SALES_TRADER: {
        "default", "pre_market_preparation", "client_interaction_rfq_routing",
        "post_trade_follow_up", "end_of_day_client_review", "client_relationship_management",
    },
    PERSONA_PORTFOLIO_MANAGER: {
        "default", "portfolio_review_investment_decisions", "rfq_initiation",
        "quote_comparison_execution", "post_trade_review", "compliance_reporting",
    },
    PERSONA_BUY_SIDE_TRADER: {
        "default", "pre_market_prep_pm_coordination", "order_intake_rfq_execution",
        "dealer_quote_comparison", "post_trade_followup_dealer_management",
        "compliance_tca_reporting",
    },
}

VALID_SIMULATIONS: set[str] = {s for sims in PERSONA_SIMULATION_MAP.values() for s in sims}

# ---------------------------------------------------------------------------
# Deal agent analyst types
# ---------------------------------------------------------------------------
VALID_ANALYST_TYPES = {"buy_side", "sell_side", "credit", "dcm", "private_markets"}

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
STATUS_INPROGRESS = "inprogress"
STATUS_COMPLETED = "completed"

# Agent loop
DEFAULT_MAX_ITERATIONS = 4
TOKEN_BUDGET_HEADROOM = 512

# Prompt version
PROMPT_VERSION = "v1"


class Settings(BaseSettings):
    """Unified runtime configuration loaded from environment / .env file."""

    # ── Databricks (shared) ──────────────────────────────────────────────
    databricks_host: str
    databricks_token: str = ""
    databricks_http_path: str = ""
    databricks_catalog: str = "main"
    databricks_schema: str = "rtq"
    databricks_sql_warehouse_id: str = ""

    # ── LLM (RFQ — OpenAI-compatible Databricks Model Serving) ───────────
    llm_endpoint_url: str = ""
    llm_model_name: str = "databricks-meta-llama-3-3-70b-instruct"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096
    llm_timeout: int = 600

    # ── LLM (Deal — Claude Sonnet endpoint name) ────────────────────────
    llm_endpoint_sonnet: str = ""
    embedding_endpoint: str = ""

    # ── Vector Search (Deal agent) ───────────────────────────────────────
    vector_search_endpoint: str = ""
    vector_search_index: str = ""
    vector_search_top_k: int = 20

    # ── Genie MCP (RFQ agent) ───────────────────────────────────────────
    rfq_intelligence_genie_space_id: str = ""

    # ── UC Metrics (RFQ agent) ──────────────────────────────────────────
    uc_metrics_volume_path: str = "/Volumes/main/rtq/metrics"

    # ── Deal agent DB (optional SQLAlchemy URL for local dev) ───────────
    database_url: str | None = None

    # ── Deal agent settings ─────────────────────────────────────────────
    max_conversation_history: int = 6

    # ── App ─────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    max_agent_iterations: int = DEFAULT_MAX_ITERATIONS

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()  # type: ignore[call-arg]
